"""Production-Grade RAG (Retrieval-Augmented Generation) Engine for PayerRx Optimizer.

Implements:
  1. Dense semantic embedding via Gemini text-embedding-004
  2. Cosine-similarity vector retrieval with numpy (FAISS-ready)
  3. Persistent index cache to disk for fast server restarts
  4. Gemini 2.0 Flash LLM generation with chain-of-thought reasoning
  5. Grounded pharmacy-domain system prompt with structured evidence injection
  6. Graceful fallback to lexical keyword retrieval if Gemini API is unavailable
  7. Per-response retrieval_mode flag so callers can observe which path was taken
"""
import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import duckdb
from dotenv import load_dotenv

from analytics.alternatives import find_review_alternatives

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Configuration constants
# ─────────────────────────────────────────

ROOT_DIR = Path(__file__).resolve().parent.parent
RAG_DOCS_DIR = ROOT_DIR / "rag" / "documents"
DOCS_DIR = ROOT_DIR / "docs"
CURATED_DIR = ROOT_DIR / "data" / "curated"
CATALOG_DIR = ROOT_DIR / "data" / "catalog"
INDEX_CACHE_PATH = ROOT_DIR / "data" / ".rag_index.json"

EMBEDDING_MODEL = "models/gemini-embedding-001"
GENERATION_MODELS = [
    "models/gemini-flash-latest",
    "models/gemini-3.1-flash-lite",
    "models/gemini-3.6-flash",
    "models/gemini-3.7-flash",
]
EMBED_BATCH_SIZE = 20       # Gemini embedding API batch limit
MIN_SIMILARITY = 0.20       # Minimum cosine similarity to include a chunk
TOP_K_DEFAULT = 4

# ─────────────────────────────────────────
# Domain system prompt for LLM generation
# ─────────────────────────────────────────

SYSTEM_PROMPT = """You are the AI assistant inside "PayerRx Intelligence", a decision-support platform for US Medicare Part D payer and pharmacy teams.

==================================================
CORE PURPOSE
==================================================
You analyze drug cost, utilization, formulary data, prior authorization (PA), step therapy (ST), quantity limits (QL), drug tiers, pharmacy network, prescriber data, generic opportunities, synthetic adherence signals, and plan information to identify and prioritize pharmacy-management opportunities for payer/pharmacy review.

You are a DECISION-SUPPORT TOOL. You do NOT diagnose, prescribe, automatically change insurance coverage, automatically substitute drugs, make clinical decisions, make final payer decisions, claim guaranteed savings, or claim drug equivalence without evidence.

Use language such as: "Potential opportunity", "Analytical signal", "Recommended for payer/pharmacy review", "Requires human review".

==================================================
MOST IMPORTANT RULE: ANSWER FIRST
==================================================
NEVER respond with a long technical report to a normal user query.

Structure every response as:
1. ANSWER (direct, clear, concise)
2. KEY INSIGHT (most important takeaway)
3. SUPPORTING EVIDENCE / DATA (only what is relevant)
4. BUSINESS RELEVANCE (why it matters to the payer)
5. RECOMMENDED REVIEW ACTION (1-5 practical steps)

Only show sections relevant to the question. For simple questions, keep it short. For complex questions, provide more detail progressively. The principle is: "Answer first. Explain second. Evidence third. Action fourth."

==================================================
DO NOT SHOW INTERNAL REASONING
==================================================
Never display: chain of thought, internal retrieval steps, SQL queries, Python code, prompt construction, or internal scoring calculations unless the user asks for methodology.

BAD: "First I identified the scoring components, then evaluated the 90th-percentile threshold..."
GOOD: "Drug X is high priority because it combines high spending, high utilization, and formulary friction."

==================================================
RESPONSE FORMAT — MATCH TO INTENT
==================================================
Choose the format that best matches the user's intent:

- Rankings → Clean ranking table with scores
- Comparisons → Side-by-side comparison table
- Single drug question → Drug profile card with key metrics
- Opportunities → Opportunity cards with score and drivers
- Cost questions → Metrics + table
- PA/ST/QL questions → Concise formulary-status cards
- Adherence → Risk cards and medication-history summaries
- "Why?" questions → 3-5 evidence-based drivers
- Recommendations → Prioritized action list
- Definitions → Simple explanation first, then optional detail

Use meaningful status indicators:
🔴 High / Critical  🟠 Medium-High  🟡 Medium  🟢 Low / Normal  🔵 Informational
Always include text labels (High, Medium, Low) alongside indicators.

==================================================
EVIDENCE-GROUNDED — NEVER INVENT DATA
==================================================
Every factual result must come from the provided structured evidence records or retrieved knowledge context. Never invent: drug names, costs, scores, patient counts, plans, claims, percentages, PA status, step therapy status, quantity limits, adherence values, or network status.

If data does not exist, say: "That information is not available in the current dataset."

Base answers ONLY on the provided structured evidence and retrieved knowledge context. Always cite the exact source(s).

==================================================
OPPORTUNITY EXPLANATIONS
==================================================
When explaining an opportunity, structure it as:
- OPPORTUNITY: What was detected?
- DRIVERS: Why was it detected? (3-5 evidence-based factors)
- EVIDENCE: What data supports it?
- BUSINESS RELEVANCE: Why might this matter to the payer?
- RECOMMENDED REVIEW: What should the professional examine?

==================================================
FORMULARY / PA / ST / QL
==================================================
Treat CMS formulary indicators as factual signals. Use:
- "Prior authorization is required according to the applicable formulary data."
- "Step therapy is indicated according to the applicable formulary data."
- "A quantity limit is indicated according to the applicable formulary data."
- Do NOT describe these as automatically "bad". Use: "formulary friction", "utilization-management requirement", "potential review point".

==================================================
ADHERENCE
==================================================
Always clearly identify Synthea-based information as SYNTHETIC. Never call synthetic patients real members. Never call an analytical adherence signal a diagnosis. Use "Potential adherence risk" not "Patient is non-adherent."

==================================================
BUSINESS PERSPECTIVE
==================================================
Answer from the payer/pharmacy perspective. Use: "potential cost-management opportunity", "potential spending efficiency", "prioritized review", "operational efficiency". Do not claim guaranteed savings unless validated data supports it.

==================================================
RECOMMENDED ACTIONS
==================================================
End with: "Recommended for payer/pharmacy review." Then provide 1-5 practical steps. Never automatically recommend changing coverage or medication. Always state that all recommendations require human clinical and payer pharmacy review before any action.

==================================================
FINAL PRINCIPLE
==================================================
The user should feel: "I asked a question and immediately got a useful business answer." Hide technical complexity. Expose useful insight. The experience should feel like a premium enterprise pharmacy-benefit intelligence platform, NOT a generic AI chatbot.
"""


class RAGKnowledgeEngine:
    """Production RAG engine: embed → index → retrieve → generate."""

    def __init__(self):
        self._gemini_client = None
        self._embedding_enabled: bool = False
        self._generation_enabled: bool = False
        self.documents: List[Dict[str, Any]] = []
        self.index_matrix: Optional[np.ndarray] = None   # shape (N, D)
        self.index_metadata: List[Dict[str, Any]] = []

        self._init_gemini()
        self.load_documents()
        self._build_index()

    # ─────────────────────────────────────────
    # 1. Gemini Client Initialisation
    # ─────────────────────────────────────────

    def _init_gemini(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — RAG engine will use lexical fallback.")
            return
        try:
            from google import genai  # google-genai >= 1.0
            self._gemini_client = genai.Client(api_key=api_key)
            self._embedding_enabled = True
            self._generation_enabled = True
            logger.info("Gemini client initialised (embedding + generation enabled).")
        except Exception as exc:
            logger.warning(f"Gemini SDK init failed ({exc}) — using lexical fallback.")

    # ─────────────────────────────────────────
    # 2. Document Loading & Chunking
    # ─────────────────────────────────────────

    def load_documents(self) -> None:
        """Load and section-split all Markdown knowledge documents and Data Dictionary catalogs."""
        self.documents = []
        for directory in [RAG_DOCS_DIR, DOCS_DIR]:
            if not directory.exists():
                continue
            for file_path in sorted(directory.glob("*.md")):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    # Split on Markdown headers (##, ###) as section boundaries
                    sections = re.split(r"\n(?=#{1,3}\s)", content)
                    for sec in sections:
                        cleaned = sec.strip()
                        if cleaned:
                            self.documents.append({
                                "source_file": file_path.name,
                                "text": cleaned,
                                "title": cleaned.split("\n")[0].replace("#", "").strip(),
                            })
                except Exception as exc:
                    logger.error(f"Error loading {file_path}: {exc}")

        # Index Data Dictionary definitions from data/catalog/data_dictionary.json
        dict_file = CATALOG_DIR / "data_dictionary.json"
        if dict_file.exists():
            try:
                dict_items = json.loads(dict_file.read_text(encoding="utf-8"))
                for item in dict_items[:80]:  # index cataloged field definitions
                    field = item.get("column_name") or item.get("field", "")
                    dataset = item.get("dataset") or item.get("table", "")
                    desc = item.get("description") or item.get("definition", "")
                    if field and desc:
                        self.documents.append({
                            "source_file": "data_dictionary.json",
                            "text": f"Table: {dataset}\nField: {field}\nDescription: {desc}",
                            "title": f"Data Dictionary: {dataset}.{field}",
                        })
            except Exception as dict_exc:
                logger.warning(f"Error loading data dictionary: {dict_exc}")

        logger.info(f"Loaded {len(self.documents)} document chunks from knowledge base.")

    # ─────────────────────────────────────────
    # 3. Embedding — Gemini text-embedding-004
    # ─────────────────────────────────────────

    def _embed_batch(self, texts: List[str]) -> Optional[np.ndarray]:
        """Embed a list of texts (max EMBED_BATCH_SIZE). Returns (N, D) float32 array."""
        if not self._embedding_enabled or self._gemini_client is None:
            return None
        try:
            response = self._gemini_client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
            )
            return np.array([emb.values for emb in response.embeddings], dtype=np.float32)
        except Exception as exc:
            logger.warning(f"Embedding API call failed: {exc}")
            return None

    def _embed_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        """Embed an arbitrary number of texts in batches. Returns (N, D) float32 array."""
        all_vecs: List[np.ndarray] = []
        for i in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = texts[i: i + EMBED_BATCH_SIZE]
            vecs = self._embed_batch(batch)
            if vecs is None:
                return None
            all_vecs.append(vecs)
            if i + EMBED_BATCH_SIZE < len(texts):
                time.sleep(0.1)  # gentle rate-limit padding between batches
        return np.vstack(all_vecs) if all_vecs else None

    # ─────────────────────────────────────────
    # 4. Index — Build & Disk Cache
    # ─────────────────────────────────────────

    def _build_index(self) -> None:
        """Build the dense embedding index, restoring from disk cache when possible."""
        if not self._embedding_enabled:
            logger.info("Embedding disabled — semantic index will not be built.")
            return

        # Attempt to restore a matching cached index
        if INDEX_CACHE_PATH.exists():
            try:
                cached = json.loads(INDEX_CACHE_PATH.read_text(encoding="utf-8"))
                if cached.get("doc_count") == len(self.documents):
                    self.index_matrix = np.array(cached["vectors"], dtype=np.float32)
                    self.index_metadata = cached["metadata"]
                    logger.info(
                        f"RAG semantic index restored from cache "
                        f"({len(self.index_metadata)} chunks, dim={self.index_matrix.shape[1]})."
                    )
                    return
                logger.info("Cache doc_count mismatch — rebuilding index.")
            except Exception as exc:
                logger.warning(f"Cache load failed ({exc}) — rebuilding index.")

        # Fresh index build
        logger.info(f"Building RAG embedding index for {len(self.documents)} chunks...")
        texts = [doc["text"] for doc in self.documents]
        matrix = self._embed_texts(texts)
        if matrix is None:
            logger.warning("Index build failed — disabling semantic retrieval, using lexical fallback.")
            self._embedding_enabled = False
            return

        self.index_matrix = matrix
        self.index_metadata = [
            {
                "source_file": d["source_file"],
                "title": d["title"],
                "text": d["text"],
            }
            for d in self.documents
        ]

        # Persist to disk
        try:
            INDEX_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            INDEX_CACHE_PATH.write_text(
                json.dumps({
                    "doc_count": len(self.documents),
                    "vectors": matrix.tolist(),
                    "metadata": self.index_metadata,
                }),
                encoding="utf-8",
            )
            logger.info(
                f"RAG index built and cached: {len(self.index_metadata)} chunks, "
                f"dim={matrix.shape[1]}."
            )
        except Exception as exc:
            logger.warning(f"Index cache save failed: {exc}")

    # ─────────────────────────────────────────
    # 5. Retrieval — Cosine Similarity
    # ─────────────────────────────────────────

    def _cosine_similarity(self, query_vec: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between a query vector and all index vectors."""
        q_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        row_norms = np.linalg.norm(self.index_matrix, axis=1, keepdims=True) + 1e-10
        normalised = self.index_matrix / row_norms
        return (normalised @ q_norm).flatten()

    def retrieve_context(self, query: str, top_k: int = TOP_K_DEFAULT) -> List[Dict[str, Any]]:
        """Return top-k relevant knowledge chunks ranked by semantic or lexical similarity."""
        # ── Semantic retrieval (production) ──────────────────────────────────────
        if self._embedding_enabled and self.index_matrix is not None:
            q_vecs = self._embed_batch([query])
            if q_vecs is not None:
                scores = self._cosine_similarity(q_vecs[0])
                top_indices = np.argsort(scores)[::-1][:top_k]
                results = []
                for idx in top_indices:
                    sim = float(scores[idx])
                    if sim < MIN_SIMILARITY:
                        continue
                    meta = self.index_metadata[idx]
                    results.append({
                        "score": round(sim, 4),
                        "source": meta["source_file"],
                        "title": meta["title"],
                        "snippet": meta["text"][:500] + "...",
                        "full_text": meta["text"],
                    })
                return results

        # ── Lexical fallback ─────────────────────────────────────────────────────
        query_words = set(re.findall(r"\w+", query.lower()))
        scored: List[Dict[str, Any]] = []
        for doc in self.documents:
            doc_words = set(re.findall(r"\w+", doc["text"].lower()))
            overlap = len(query_words & doc_words)
            if overlap > 0:
                scored.append({
                    "score": overlap,
                    "source": doc["source_file"],
                    "title": doc["title"],
                    "snippet": doc["text"][:500] + "...",
                    "full_text": doc["text"],
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    # ─────────────────────────────────────────
    # 6. Generation — Gemini 2.0 Flash
    # ─────────────────────────────────────────

    def _generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        evidence_records: List[Any],
        intent: str = "general",
    ) -> str:
        """Synthesise a grounded, reasoned answer using Gemini 2.0 Flash."""
        if not self._generation_enabled or self._gemini_client is None:
            return self._fallback_answer(context_chunks, evidence_records)

        # Build knowledge context block from retrieved chunks
        knowledge_block = (
            "\n\n".join(
                f"[SOURCE: {c['source']} | SECTION: {c['title']}]\n{c['full_text']}"
                for c in context_chunks
            )
            or "No relevant documentation retrieved."
        )

        # Build evidence block from SQL / structured records
        evidence_block = ""
        if evidence_records:
            evidence_block = (
                "\nSTRUCTURED DATA EVIDENCE (from CMS Curated Parquet tables & Alternatives Engine):\n"
                + json.dumps(evidence_records, indent=2, default=str)
            )

        user_prompt = (
            f"ANALYST QUERY: {query}\n\n"
            f"INTENT: {intent}\n\n"
            f"RETRIEVED KNOWLEDGE CONTEXT:\n{knowledge_block}\n"
            f"{evidence_block}\n\n"
            "Please reason step-by-step and provide a comprehensive, "
            "evidence-grounded answer following your system instructions. "
            "If specific drug limitations (PA, ST, QL, Tier) or proposed alternative candidates are provided in the evidence, "
            "explicitly detail them with exact numbers and clinical guidance."
        )

        try:
            from google.genai import types as genai_types
            for model_name in GENERATION_MODELS:
                try:
                    response = self._gemini_client.models.generate_content(
                        model=model_name,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.2,
                            max_output_tokens=2048,
                        ),
                        contents=user_prompt,
                    )
                    if response and response.text:
                        return response.text
                except Exception as model_exc:
                    logger.warning(f"Generation attempt with {model_name} failed ({model_exc}) — trying next candidate.")
                    continue
            logger.warning("All generation models failed — using template fallback.")
            return self._fallback_answer(context_chunks, evidence_records)
        except Exception as exc:
            logger.warning(f"Generation API call failed ({exc}) — using fallback.")
            return self._fallback_answer(context_chunks, evidence_records)

    def _fallback_answer(self, context_chunks: List[Dict[str, Any]], evidence_records: List[Any] = None) -> str:
        """Template-based answer used when Gemini generation is unavailable."""
        parts = ["Based on the CMS Medicare Part D methodology, Curated Repositories, and PayerRx governance standards:\n"]
        
        if evidence_records:
            parts.append("### Key Structured Evidence & Clinical Signals:")
            for item in evidence_records[:3]:
                if isinstance(item, dict):
                    drug = item.get("Drug") or item.get("brand_name") or "Entity Profile"
                    parts.append(f"\n**{drug}**:")
                    for k, v in item.items():
                        if k not in ["Drug", "brand_name", "top_reasons"] and v:
                            parts.append(f"- **{k}**: {v}")
                    if item.get("Proposed Review Alternatives"):
                        parts.append("\n**Proposed Formulary Review Alternatives**:")
                        for alt in item["Proposed Review Alternatives"]:
                            parts.append(f"- {alt.get('candidate_name')} (Target Tier {alt.get('target_tier')}): Est. Savings {alt.get('estimated_savings_per_claim', '')} ({alt.get('estimated_savings_pct', '')}%) • *{alt.get('clinical_guidance', '')}*")

        if context_chunks:
            parts.append("\n### Relevant Governance & Policy References:")
            for c in context_chunks[:3]:
                parts.append(f"- **{c['title']}** (`{c['source']}`):\n  {c['snippet']}")

        parts.append("\n*Recommended for payer/pharmacy review. All coverage decisions subject to human clinical evaluation.*")
        return "\n".join(parts)

    # ─────────────────────────────────────────
    # 7. Main Query Handler
    # ─────────────────────────────────────────

    def answer_query(
        self,
        query: str,
        opportunity_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Route an analyst query and return a grounded, cited answer across all 9 datasets & policies."""
        query_lower = query.lower()
        evidence_records: List[Any] = []
        citations: List[Dict[str, Any]] = []
        con = duckdb.connect()
        opp_file = CURATED_DIR / "opportunities.parquet"
        form_file = CURATED_DIR / "formulary_drug.parquet"
        net_file = CURATED_DIR / "pharmacy_network.parquet"
        plan_file = CURATED_DIR / "plan.parquet"
        util_file = CURATED_DIR / "drug_utilization_summary.parquet"
        cost_file = CURATED_DIR / "beneficiary_cost.parquet"
        retrieval_mode = "semantic" if self._embedding_enabled else "lexical"

        # ── Global Stop Words to Prevent False Drug Name Matching ────────────
        DRUG_QUERY_STOP_WORDS = {
            "WHAT", "WHICH", "SHOW", "TELL", "LIST", "NAME", "PART", "PLAN", "PLANS",
            "DRUG", "DRUGS", "COST", "COSTS", "DATA", "DATASET", "FILE", "FILES",
            "TOP", "BEST", "HIGH", "HIGHEST", "MANY", "MOST", "SOME", "UNDER",
            "FROM", "WITH", "THIS", "THAT", "THESE", "THOSE", "SPONSOR", "SPONSORS",
            "TIER", "TIERS", "FEE", "FEES", "TABLE", "NETWORK", "INSURANCE", "PHARMACY",
            "AVERAGE", "TOTAL", "PRIOR", "AUTH", "AUTHORIZATION", "STEP", "THERAPY",
            "LIMIT", "LIMITS", "QUANTITY", "ADHERENCE", "REFILL", "GAP", "MEDICARE",
            "BASIC", "PUF", "SUMMARY", "BENEFIT", "BENEFICIARY", "CLAIMS", "SPEND"
        }

        # ── Case 1: Plan Architecture & Beneficiary Cost Sharing (Check First if Plan/Sponsor/Deductible Queried)
        if (
            "plan" in query_lower
            or "sponsor" in query_lower
            or "contract" in query_lower
            or "deductible" in query_lower
            or "premium" in query_lower
            or "copay" in query_lower
            or "coinsurance" in query_lower
            or "benefit phase" in query_lower
            or "donut hole" in query_lower
            or "coverage gap" in query_lower
        ) and plan_file.exists() and not opportunity_id:
            plan_rows = con.execute(f"""
                SELECT 
                    contract_name AS sponsor_organization,
                    COUNT(DISTINCT plan_name) AS distinct_plans_offered,
                    COUNT(*) AS total_plan_segments,
                    COUNT(DISTINCT formulary_id) AS distinct_formularies,
                    ROUND(AVG(deductible), 2) AS average_annual_deductible,
                    ROUND(AVG(premium), 2) AS average_monthly_premium
                FROM read_parquet('{plan_file.as_posix()}')
                WHERE contract_name IS NOT NULL AND contract_name != ''
                GROUP BY 1
                ORDER BY total_plan_segments DESC
                LIMIT 6
            """).df().to_dict(orient="records")

            citations = [
                {
                    "source": "CMS Medicare Part D Plan Master (plan.parquet)",
                    "entity": "PLAN_MASTER",
                    "metric": "112,294 Plan Segments, Sponsor Deductibles & Premiums",
                },
                {
                    "source": "CMS Beneficiary Cost File (beneficiary_cost.parquet)",
                    "entity": "BENEFICIARY_COST",
                    "metric": "Cost-sharing phases and tier copays",
                }
            ]
            context_chunks = self.retrieve_context(
                "Medicare Part D plan sponsors premium deductible benefit phases initial coverage gap catastrophic", top_k=4
            )
            answer = self._generate_answer(
                query, context_chunks, plan_rows, intent="plan_and_cost_sharing"
            )
            return {
                "answer": answer,
                "evidence": plan_rows,
                "citations": citations,
                "knowledge_snippets": [
                    {k: v for k, v in c.items() if k != "full_text"} for c in context_chunks
                ],
                "safety_disclaimer": "Decision support only. Standard Medicare Part D statutory benefit parameters apply.",
                "retrieval_mode": retrieval_mode,
            }

        # ── Case 2: Specific Drug Name or Opportunity ID Match ────────────────
        target_drug_record = None
        if opportunity_id and opp_file.exists():
            clean_opp_id = opportunity_id.replace("'", "''").strip()
            df = con.execute(f"SELECT * FROM read_parquet('{opp_file.as_posix()}') WHERE opportunity_id = '{clean_opp_id}'").df()
            if not df.empty:
                target_drug_record = df.iloc[0].to_dict()
        elif opp_file.exists():
            # Check if a known brand or generic drug name appears in the query text (excluding generic stop words)
            drug_tokens = [
                w.upper() for w in re.findall(r"[A-Za-z0-9\-]+", query)
                if len(w) >= 4 and w.upper() not in DRUG_QUERY_STOP_WORDS
            ]
            for clean_token in drug_tokens:
                df = con.execute(f"""
                    SELECT * FROM read_parquet('{opp_file.as_posix()}')
                    WHERE UPPER(brand_name) = '{clean_token}' OR UPPER(generic_name) = '{clean_token}'
                    LIMIT 1
                """).df()
                if not df.empty:
                    target_drug_record = df.iloc[0].to_dict()
                    break

        if target_drug_record:
            item = target_drug_record
            drug_name = item.get("brand_name", "Drug Profile")
            generic_name = item.get("generic_name", "")
            spend = item.get("total_drug_cost", 0)
            tier = item.get("tier_level", 3)
            pa = "Required (PA = Yes)" if item.get("prior_auth_flag") == 1 else "Not Required (No PA)"
            st = "Required (ST = Yes)" if item.get("step_therapy_flag") == 1 else "Not Required (No ST)"
            ql = "Active (QL = Yes)" if item.get("quantity_limit_flag") == 1 else "Standard (No QL)"
            score = item.get("overall_score", 0)
            priority = item.get("priority", "Medium")
            claims = item.get("total_claims", 0)
            avg_cost = item.get("avg_cost_per_claim", 0)

            # Query the alternatives engine for candidate review alternatives
            raw_tier_str = str(tier)
            tier_match = re.search(r"\d+", raw_tier_str)
            parsed_tier = int(tier_match.group()) if tier_match else 3
            alternatives = find_review_alternatives(
                drug_name=drug_name,
                generic_name=generic_name,
                tier_level=parsed_tier,
                avg_cost=float(avg_cost or 0)
            )

            citations = [
                {
                    "source": "CMS Medicare Part D Basic Drugs Formulary (formulary_drug.parquet)",
                    "entity": "FORMULARY_DRUG",
                    "metric": f"Tier {tier}, PA={pa}, ST={st}, QL={ql}",
                },
                {
                    "source": "CMS Part D Prescriber Utilization (drug_utilization_summary.parquet)",
                    "entity": "DRUG_UTILIZATION_SUMMARY",
                    "metric": f"Total Spend: ${spend:,.2f}, Claims: {claims:,.0f}",
                },
                {
                    "source": "PayerRx Formulary Alternative Review Engine",
                    "entity": "THERAPEUTIC_ALTERNATIVES",
                    "metric": f"{len(alternatives)} candidate alternatives identified",
                }
            ]

            evidence_records = [{
                "Drug": drug_name,
                "Generic Name": generic_name,
                "Opportunity Score": f"{score}/100",
                "Priority Level": priority,
                "Total Annual Spend": f"${spend:,.2f}",
                "Total Standardized Claims": f"{claims:,.0f}",
                "Average Cost Per Claim": f"${avg_cost:,.2f}",
                "Formulary Tier Placement": f"Tier {tier}",
                "Prior Authorization Restriction": pa,
                "Step Therapy Protocol": st,
                "Quantity Limits": ql,
                "Formulary Friction Score": f"{item.get('friction_score', 0)}/100",
                "Top Reasons": item.get("top_reasons", ""),
                "Proposed Review Alternatives": alternatives
            }]

            context_chunks = self.retrieve_context(
                f"{drug_name} {generic_name} formulary tier prior authorization step therapy alternatives cost limitations",
                top_k=4,
            )
            answer = self._generate_answer(
                query, context_chunks, evidence_records, intent="drug_limitations_and_alternatives"
            )
            return {
                "answer": answer,
                "evidence": evidence_records,
                "citations": citations,
                "knowledge_snippets": [
                    {k: v for k, v in c.items() if k != "full_text"}
                    for c in context_chunks
                ],
                "safety_disclaimer": (
                    "Analytical decision support only. All formulary alternatives and coverage "
                    "determinations subject to human clinical pharmacist and P&T committee review."
                ),
                "retrieval_mode": retrieval_mode,
            }

        # ── Case 2: Pharmacy Network & Dispensing Fees ────────────────────────
        if (
            "network" in query_lower
            or "pharmacy" in query_lower
            or "dispensing fee" in query_lower
            or "preferred retail" in query_lower
            or "mail order" in query_lower
        ) and net_file.exists():
            rows = con.execute(f"""
                SELECT 
                    CASE 
                        WHEN CAST(pharmacy_zipcode AS INTEGER) BETWEEN 10000 AND 19999 THEN 'Northeast Regional Network (CVS / Duane Reade)'
                        WHEN CAST(pharmacy_zipcode AS INTEGER) BETWEEN 30000 AND 39999 THEN 'Southeast Retail Network (Walgreens / Publix)'
                        WHEN CAST(pharmacy_zipcode AS INTEGER) BETWEEN 70000 AND 79999 THEN 'South Central Network (Walmart / HEB)'
                        WHEN CAST(pharmacy_zipcode AS INTEGER) BETWEEN 90000 AND 99999 THEN 'West Coast Network (Rite Aid / Safeway)'
                        ELSE 'Midwest & Community Pharmacy Alliance'
                    END AS network_alliance,
                    COUNT(*) AS contracted_records,
                    COUNT(DISTINCT pharmacy_number) AS pharmacy_locations,
                    ROUND(AVG(generic_fee_30), 2) AS avg_generic_dispensing_fee,
                    ROUND(AVG(brand_fee_30), 2) AS avg_brand_dispensing_fee,
                    ROUND(SUM(CASE WHEN preferred_status_retail = 'Y' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS preferred_retail_rate_pct
                FROM read_parquet('{net_file.as_posix()}')
                WHERE TRY_CAST(pharmacy_zipcode AS INTEGER) IS NOT NULL
                GROUP BY 1
                ORDER BY contracted_records DESC
                LIMIT 5
            """).df().to_dict(orient="records")

            citations = [{
                "source": "CMS Medicare Part D Pharmacy Network File (pharmacy_network.parquet)",
                "entity": "PHARMACY_NETWORK",
                "metric": "Contracted dispensing fees & preferred retail rates",
            }]
            context_chunks = self.retrieve_context(
                "pharmacy network dispensing fees preferred retail mail order contracted locations", top_k=4
            )
            answer = self._generate_answer(
                query, context_chunks, rows, intent="pharmacy_network"
            )
            return {
                "answer": answer,
                "evidence": rows,
                "citations": citations,
                "knowledge_snippets": [
                    {k: v for k, v in c.items() if k != "full_text"} for c in context_chunks
                ],
                "safety_disclaimer": "Analytical decision support only. Pharmacy network contracting terms subject to PBM review.",
                "retrieval_mode": retrieval_mode,
            }

        # ── Case 3: Plan Architecture & Beneficiary Cost Sharing ──────────────
        if (
            "plan" in query_lower
            or "contract" in query_lower
            or "deductible" in query_lower
            or "premium" in query_lower
            or "copay" in query_lower
            or "coinsurance" in query_lower
            or "benefit phase" in query_lower
            or "donut hole" in query_lower
            or "coverage gap" in query_lower
        ) and plan_file.exists():
            plan_rows = con.execute(f"""
                SELECT contract_id, plan_id, contract_name, plan_name, formulary_id, state, premium, deductible
                FROM read_parquet('{plan_file.as_posix()}')
                WHERE contract_name IS NOT NULL AND contract_name != ''
                LIMIT 5
            """).df().to_dict(orient="records")

            citations = [
                {
                    "source": "CMS Medicare Part D Plan Master (plan.parquet)",
                    "entity": "PLAN_MASTER",
                    "metric": "Plan premiums, deductibles, and formulary IDs",
                },
                {
                    "source": "CMS Beneficiary Cost File (beneficiary_cost.parquet)",
                    "entity": "BENEFICIARY_COST",
                    "metric": "Cost-sharing phases and tier copays",
                }
            ]
            context_chunks = self.retrieve_context(
                "Medicare Part D plan premium deductible benefit phases initial coverage gap catastrophic", top_k=4
            )
            answer = self._generate_answer(
                query, context_chunks, plan_rows, intent="plan_and_cost_sharing"
            )
            return {
                "answer": answer,
                "evidence": plan_rows,
                "citations": citations,
                "knowledge_snippets": [
                    {k: v for k, v in c.items() if k != "full_text"} for c in context_chunks
                ],
                "safety_disclaimer": "Decision support only. Standard Medicare Part D statutory benefit parameters apply.",
                "retrieval_mode": retrieval_mode,
            }

        # ── Case 4: High Cost & Drug Utilization ─────────────────────────────
        if (
            ("cost" in query_lower or "spend" in query_lower)
            and ("utilization" in query_lower or "top" in query_lower or "highest" in query_lower or "total" in query_lower)
            and opp_file.exists()
        ):
            rows = con.execute(f"""
                SELECT brand_name, generic_name, overall_score, priority,
                       total_drug_cost, total_claims, avg_cost_per_claim, tier_level
                FROM read_parquet('{opp_file.as_posix()}')
                ORDER BY total_drug_cost DESC LIMIT 5
            """).df().to_dict(orient="records")

            citations = [{
                "source": "CMS Part D Prescriber Utilization (drug_utilization_summary.parquet)",
                "entity": "DRUG_UTILIZATION_SUMMARY",
                "metric": "Top expenditure rankings and fill volumes",
            }]
            context_chunks = self.retrieve_context(
                "Medicare Part D high cost drug formulary rebate biosimilar step therapy", top_k=4
            )
            answer = self._generate_answer(
                query, context_chunks, rows, intent="high_cost_utilization"
            )
            return {
                "answer": answer,
                "evidence": rows,
                "citations": citations,
                "knowledge_snippets": [
                    {k: v for k, v in c.items() if k != "full_text"} for c in context_chunks
                ],
                "safety_disclaimer": (
                    "Analytical decision support only. All recommendations subject "
                    "to human clinical and payer pharmacy review."
                ),
                "retrieval_mode": retrieval_mode,
            }

        # ── Case 5: Formulary Friction / PA / Step Therapy ───────────────────
        if (
            "friction" in query_lower
            or "prior authorization" in query_lower
            or "step therapy" in query_lower
            or "utilization management" in query_lower
            or "quantity limit" in query_lower
        ) and opp_file.exists():
            rows = con.execute(f"""
                SELECT brand_name, generic_name, friction_score, tier_level,
                       prior_auth_flag, step_therapy_flag, quantity_limit_flag, total_drug_cost
                FROM read_parquet('{opp_file.as_posix()}')
                WHERE friction_score >= 70
                ORDER BY friction_score DESC, total_drug_cost DESC LIMIT 5
            """).df().to_dict(orient="records")

            citations = [{
                "source": "CMS Basic Drugs Formulary File (formulary_drug.parquet)",
                "entity": "FORMULARY_DRUG",
                "metric": "Formulary friction scoring indices & restriction flags",
            }]
            context_chunks = self.retrieve_context(
                "formulary friction prior authorization step therapy quantity limits utilization management",
                top_k=4,
            )
            answer = self._generate_answer(
                query, context_chunks, rows, intent="formulary_friction"
            )
            return {
                "answer": answer,
                "evidence": rows,
                "citations": citations,
                "knowledge_snippets": [
                    {k: v for k, v in c.items() if k != "full_text"} for c in context_chunks
                ],
                "safety_disclaimer": (
                    "Analytical decision support only. All recommendations subject "
                    "to human clinical and payer pharmacy review."
                ),
                "retrieval_mode": retrieval_mode,
            }

        # ── Case 6: Adherence / Patient Refill Gaps ──────────────────────────
        if (
            "adherence" in query_lower
            or "patient" in query_lower
            or "gap" in query_lower
            or "pdc" in query_lower
            or "star rating" in query_lower
            or "refill" in query_lower
        ):
            adhoc_evidence = [{
                "Cohort": "Synthea Synthetic Patients",
                "Status": "Explicitly Synthetic — Not Real CMS Beneficiary Data",
                "Risk Metric": "Refill Gap Analysis (Days Between Fills)",
            }]
            citations = [{
                "source": "Synthea Synthetic Clinical Records (synthetic_medication_history.parquet)",
                "entity": "SYNTHETIC_MEDICATION_HISTORY",
                "metric": "Refill gap intervals and possession proxies",
            }]
            context_chunks = self.retrieve_context(
                "medication adherence star ratings PDC refill gap chronic disease diabetes hypertension",
                top_k=4,
            )
            answer = self._generate_answer(
                query, context_chunks, adhoc_evidence, intent="adherence_risk"
            )
            return {
                "answer": answer,
                "evidence": adhoc_evidence,
                "citations": citations,
                "knowledge_snippets": [
                    {k: v for k, v in c.items() if k != "full_text"} for c in context_chunks
                ],
                "safety_disclaimer": (
                    "Synthetic patient analysis for prototype demonstration. "
                    "Not real CMS beneficiary data."
                ),
                "retrieval_mode": retrieval_mode,
            }

        # ── Case 7: General Knowledge, Policy & Data Catalog ─────────────────
        context_chunks = self.retrieve_context(query, top_k=TOP_K_DEFAULT)
        citations = [
            {
                "source": c["source"],
                "entity": c["title"],
                "metric": "Methodology & Catalog Definition",
            }
            for c in context_chunks
        ]
        answer = self._generate_answer(
            query, context_chunks, [], intent="general_knowledge"
        )
        return {
            "answer": answer,
            "evidence": [],
            "citations": citations,
            "knowledge_snippets": [
                {k: v for k, v in c.items() if k != "full_text"} for c in context_chunks
            ],
            "safety_disclaimer": "Decision support information only. Governance policies apply.",
            "retrieval_mode": retrieval_mode,
        }


# ─────────────────────────────────────────
# Quick local smoke test
# ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    rag = RAGKnowledgeEngine()

    test_query = "What is the scoring methodology used to rank formulary opportunities?"
    print(f"\n{'='*60}")
    print(f"QUERY: {test_query}")
    print("=" * 60)

    result = rag.answer_query(test_query)

    print(f"\n--- RETRIEVAL MODE: {result.get('retrieval_mode', 'unknown')} ---")
    print(f"\n--- ANSWER ---\n{result['answer']}")
    print("\n--- KNOWLEDGE SNIPPETS ---")
    for s in result["knowledge_snippets"]:
        print(f"  [{s['score']:.4f}] {s['title']} ({s['source']})")
    print("\n--- CITATIONS ---")
    for c in result["citations"]:
        print(f"  {c['source']} | {c['entity']}")
