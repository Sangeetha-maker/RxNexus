# Evidence retrieval design

The current assistant is deliberately deterministic: it retrieves selected opportunity fields from `08_opportunity_features.csv` and returns a traceable review brief. It does **not** calculate from raw data and does not use an LLM as an analytical engine.

To connect an LLM later, index only `rag/documents/` plus approved data dictionary/join/scoring documents, attach the selected API evidence as structured context, and require citations back to those records. Keep provider credentials in environment variables; no Azure-specific AI service is required.
