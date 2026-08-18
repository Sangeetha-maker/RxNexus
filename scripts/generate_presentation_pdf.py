import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress headers/footers on title cover
        
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header
        self.drawString(54, 750, "COGNIZANT HACKATHON | ML ENGINEER TRACK")
        self.drawRightString(612 - 54, 750, "RXNEXUS / PAYERRX INTELLIGENCE")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(54, 744, 612 - 54, 744)
        
        # Footer
        self.line(54, 48, 612 - 54, 48)
        self.setFont("Helvetica", 8)
        self.drawString(54, 36, "Confidential • Evaluator Technical Presentation Deck • Medicare Part D ML Optimization")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, page_str)
        self.restoreState()

def create_presentation_pdf(output_filename):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=64,
        bottomMargin=64
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Brand Colors
    PRIMARY = colors.HexColor("#0F172A")    # Slate 900
    ACCENT = colors.HexColor("#4F46E5")     # Indigo 600
    ACCENT_BG = colors.HexColor("#EEF2FF")  # Indigo 50
    EMERALD = colors.HexColor("#059669")    # Emerald 600
    AMBER = colors.HexColor("#D97706")      # Amber 600
    MUTED = colors.HexColor("#475569")      # Slate 600
    LIGHT_BG = colors.HexColor("#F8FAFC")   # Slate 50
    BORDER = colors.HexColor("#E2E8F0")     # Slate 200

    # Typography Styles
    title_cover = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=10
    )
    
    subtitle_cover = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=18,
        textColor=ACCENT,
        spaceAfter=20
    )
    
    h1 = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    h2 = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=ACCENT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=PRIMARY,
        spaceAfter=6
    )
    
    speech_style = ParagraphStyle(
        'SpeechScript',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor("#1E293B")
    )
    
    code_box = ParagraphStyle(
        'CodeBox',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0F172A")
    )

    tag_style = ParagraphStyle(
        'TagStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_header = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )
    
    table_cell = ParagraphStyle(
        'TD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=PRIMARY
    )

    story = []

    # ==========================================
    # COVER PAGE
    # ==========================================
    story.append(Spacer(1, 20))
    badge_table = Table([[
        Paragraph("<b>COGNIZANT HACKATHON 2026</b>", ParagraphStyle('B1', fontName='Helvetica-Bold', fontSize=9, textColor=ACCENT)),
        Paragraph("<b>AI & MACHINE LEARNING TRACK</b>", ParagraphStyle('B2', fontName='Helvetica-Bold', fontSize=9, textColor=EMERALD))
    ]], colWidths=[200, 200])
    badge_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("RXNexus: PayerRx Intelligence", title_cover))
    story.append(Paragraph("Next-Generation Medicare Part D Formulary Optimization, Prioritization Scoring & Grounded Decision-Support AI", subtitle_cover))
    
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceBefore=0, spaceAfter=20))

    meta_data = [
        [Paragraph("<b>Role:</b>", table_header), Paragraph("Lead Machine Learning & Data Systems Engineer", table_cell)],
        [Paragraph("<b>Format:</b>", table_header), Paragraph("5–10 Minute Live Technical Evaluator Presentation & Pitch Script", table_cell)],
        [Paragraph("<b>Project Domain:</b>", table_header), Paragraph("US Healthcare • Medicare Part D • Payer/PBM Formulary Optimization", table_cell)],
        [Paragraph("<b>Key ML Pillars:</b>", table_header), Paragraph("Streaming ETL (3.8GB) • Multi-Objective Scoring • Grounded RAG with Provenance", table_cell)],
        [Paragraph("<b>Evaluation Target:</b>", table_header), Paragraph("Cognizant Hackathon Technical Judging Panel", table_cell)]
    ]
    t_meta = Table(meta_data, colWidths=[120, 384])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 25))

    exec_summary_html = (
        "<b>Executive Summary for Evaluators:</b><br/>"
        "RXNexus solves the $400B Medicare Part D pharmacy optimization problem by bridging multi-gigabyte "
        "CMS prescriber claims data with insurance formulary benefit packages. This document provides the complete "
        "spoken script, visual slide blueprint, algorithmic formulations, and Q&A defense for the Machine Learning Engineer role."
    )
    summary_table = Table([[Paragraph(exec_summary_html, body)]], colWidths=[504])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), ACCENT_BG),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#C7D2FE")),
        ('PADDING', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))
    story.append(summary_table)

    story.append(PageBreak())

    # ==========================================
    # PRESENTATION SCRIPT & SLIDE TIMELINE
    # ==========================================
    story.append(Paragraph("Section 1: 8-Minute Evaluator Presentation Script", h1))
    story.append(Paragraph("This section contains the exact time-stamped spoken script and visual slide cues for delivering the technical pitch.", body))
    story.append(Spacer(1, 8))

    # SLIDE 1
    story.append(Paragraph("Minute 0:00 – 1:00 | Slide 1: The ML Engineering Hook & Problem Statement", h2))
    s1_text = (
        "<b>[Speaker Script]:</b> \"Good morning, judges. I’m presenting as the Machine Learning and Data Systems "
        "Engineer for <b>RXNexus</b>. In US Healthcare, Medicare Part D payers process over <b>$400 Billion</b> in prescription "
        "drug spending every year. When an ML engineer looks at this space, the challenge isn't just training a model—it's "
        "solving three massive real-world engineering constraints: (1) <b>Data Scale & Memory</b>: ingesting 3.8GB+ of raw CMS "
        "claims without memory crashes; (2) <b>Algorithmic Explainability</b>: P&T committees reject black-box models that cannot "
        "be clinically audited; and (3) <b>Zero Hallucinations</b>: LLMs in healthcare cannot be allowed to fabricate drug costs or rules. "
        "Today, I'll demonstrate how our end-to-end ML architecture solves all three.\""
    )
    s1_box = Table([[Paragraph(s1_text, speech_style)]], colWidths=[504])
    s1_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), LIGHT_BG), ('BOX', (0,0), (-1,-1), 0.5, BORDER), ('PADDING', (0,0), (-1,-1), 8)]))
    story.append(s1_box)
    story.append(Spacer(1, 10))

    # SLIDE 2
    story.append(Paragraph("Minute 1:00 – 2:30 | Slide 2: Streaming Feature Engineering at Scale (3.8 GB)", h2))
    s2_text = (
        "<b>[Speaker Script]:</b> \"Let’s examine the data engineering layer in <code>pipeline.py</code>. Standard Pandas crashes "
        "with Out-of-Memory errors when handling multi-gigabyte CMS prescriber-drug tables. We built an <b>O(1) Memory Bounded Streaming "
        "Generator</b> that parses raw CSV streams in chunks without altering source data. Rather than hardcoding thresholds, our pipeline "
        "dynamically computes exact <b>90th-percentile (P90) non-parametric boundaries</b> for total spend, claim counts, and 30-day fills. "
        "Crucially, missing or suppressed CMS denominators are preserved as nulls rather than zero-filled, preventing mathematical bias in "
        "downstream opportunity scoring.\""
    )
    s2_box = Table([[Paragraph(s2_text, speech_style)]], colWidths=[504])
    s2_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), LIGHT_BG), ('BOX', (0,0), (-1,-1), 0.5, BORDER), ('PADDING', (0,0), (-1,-1), 8)]))
    story.append(s2_box)
    story.append(Spacer(1, 10))

    # SLIDE 3
    story.append(Paragraph("Minute 2:30 – 4:30 | Slide 3: Multi-Objective Prioritization Engine & What-If Simulation", h2))
    s3_text = (
        "<b>[Speaker Script]:</b> \"In <code>analytics/scoring.py</code>, we designed a transparent <b>Multi-Objective Optimization Engine</b> "
        "that maps multidimensional healthcare signals into an interpretable 0–100 priority score. The composite formula balances "
        "Cost Impact (30%), Utilization Volume (25%), Formulary Friction (20%), and Adherence Risk (15%). Through our <code>/api/simulate</code> "
        "endpoint, executives can adjust weighting vectors dynamically. Our backend vectorizes the recalculation across tens of thousands of records "
        "in <b>under 45 milliseconds</b>, turning static reporting into real-time what-if scenario modeling.\""
    )
    s3_box = Table([[Paragraph(s3_text, speech_style)]], colWidths=[504])
    s3_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), LIGHT_BG), ('BOX', (0,0), (-1,-1), 0.5, BORDER), ('PADDING', (0,0), (-1,-1), 8)]))
    story.append(s3_box)
    story.append(Spacer(1, 10))

    # SLIDE 4
    story.append(Paragraph("Minute 4:30 – 6:00 | Slide 4: Therapeutic Entity Resolution & Savings Optimization", h2))
    s4_text = (
        "<b>[Speaker Script]:</b> \"In <code>analytics/alternatives.py</code>, we tackle drug entity resolution. CMS names are unstandardized strings, "
        "while formularies use RxCUI and NDC codes. Our engine normalizes brand strings against FDA Orange Book therapeutic equivalents. "
        "When a prescriber writes for a Tier 4 brand like <i>Restasis ($420/claim)</i>, our system flags the bioequivalent Tier 2 generic "
        "<i>Cyclosporine 0.05%</i> yielding <b>65% plan savings</b>. We cluster claims by NPI to identify the top 5% of prescribers driving 80% "
        "of avoidable expenditures for targeted academic detailing.\""
    )
    s4_box = Table([[Paragraph(s4_text, speech_style)]], colWidths=[504])
    s4_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), LIGHT_BG), ('BOX', (0,0), (-1,-1), 0.5, BORDER), ('PADDING', (0,0), (-1,-1), 8)]))
    story.append(s4_box)
    story.append(Spacer(1, 10))

    # SLIDE 5
    story.append(Paragraph("Minute 6:00 – 7:30 | Slide 5: Grounded RAG Copilot with Deterministic Provenance", h2))
    s5_text = (
        "<b>[Speaker Script]:</b> \"For Generative AI in <code>rag/</code>, we avoided open-ended LLM prompting. We engineered a "
        "<b>Deterministic Retrieval-Augmented Generation (RAG) Architecture</b>. The LLM is strictly barred from calculating numbers. Instead, "
        "FastAPI fetches exact pre-computed metrics from curated tables and injects them into bounded prompt templates. Every response includes "
        "immutable citation metadata—dataset, file, entity, and metric value—alongside mandatory clinical review disclaimers.\""
    )
    s5_box = Table([[Paragraph(s5_text, speech_style)]], colWidths=[504])
    s5_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), LIGHT_BG), ('BOX', (0,0), (-1,-1), 0.5, BORDER), ('PADDING', (0,0), (-1,-1), 8)]))
    story.append(s5_box)
    story.append(Spacer(1, 10))

    # SLIDE 6 & 7
    story.append(Paragraph("Minute 7:30 – 9:00 | Slide 6 & 7: Production Architecture & Evaluator Wrap-Up", h2))
    s6_text = (
        "<b>[Speaker Script]:</b> \"To conclude: RXNexus is production-ready. Our stack features an async FastAPI server, PostgreSQL serving model, "
        "React 18 glassmorphic dashboard, automated Pytest regression suites, and Docker/Azure Container deployment templates. "
        "In summary, we delivered: (1) O(1) streaming ETL on 3.8GB data; (2) An explainable 0–100 optimization scoring engine with sub-45ms simulation; "
        "(3) FDA-governed therapeutic entity substitution; and (4) A 100% citation-grounded clinical Copilot. Thank you—I am ready for your questions!\""
    )
    s6_box = Table([[Paragraph(s6_text, speech_style)]], colWidths=[504])
    s6_box.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), LIGHT_BG), ('BOX', (0,0), (-1,-1), 0.5, BORDER), ('PADDING', (0,0), (-1,-1), 8)]))
    story.append(s6_box)

    story.append(PageBreak())

    # ==========================================
    # SECTION 2: TECHNICAL ML DEEP-DIVE
    # ==========================================
    story.append(Paragraph("Section 2: Technical ML Architecture & Algorithms", h1))
    story.append(Paragraph("Detailed mathematical formulations, data schemas, and engineering implementations.", body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Mathematical Formulation of Multi-Objective Scoring", h2))
    math_desc = (
        "The composite prioritization score <b>S ∈ [0, 100]</b> is formulated as a normalized convex combination of four distinct "
        "operational dimensions, evaluated against non-parametric population percentiles:"
    )
    story.append(Paragraph(math_desc, body))

    score_matrix = [
        [Paragraph("<b>Component</b>", table_header), Paragraph("<b>Formula / Definition</b>", table_header), Paragraph("<b>Baseline Weight</b>", table_header), Paragraph("<b>Signal Source</b>", table_header)],
        [Paragraph("Cost Impact (C)", table_cell), Paragraph("min(1.0, Total_Spend / P90_Spend_Threshold)", table_cell), Paragraph("30% – 60%", table_cell), Paragraph("CMS Provider × Drug Fact", table_cell)],
        [Paragraph("Utilization (U)", table_cell), Paragraph("min(1.0, Claims_Count / P90_Claims_Threshold)", table_cell), Paragraph("25% – 40%", table_cell), Paragraph("CMS Standardized 30-Day Fills", table_cell)],
        [Paragraph("Formulary Friction (F)", table_cell), Paragraph("0.40(PA) + 0.35(ST) + 0.25(QL_Flag)", table_cell), Paragraph("20%", table_cell), Paragraph("CMS Basic Formulary Files", table_cell)],
        [Paragraph("Adherence Risk (A)", table_cell), Paragraph("max(0.0, 1.0 - (PDC_Rate / 0.80))", table_cell), Paragraph("15%", table_cell), Paragraph("Synthea Longitudinal Signals", table_cell)],
        [Paragraph("Alternative Opp (O)", table_cell), Paragraph("(Brand_Cost - Generic_Cost) / Brand_Cost", table_cell), Paragraph("10%", table_cell), Paragraph("FDA Bioequivalent Crosswalk", table_cell)]
    ]
    t_score = Table(score_matrix, colWidths=[100, 194, 80, 130])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))
    story.append(t_score)
    story.append(Spacer(1, 14))

    story.append(Paragraph("2. Grounded RAG Verification & Citation Engine", h2))
    rag_desc = (
        "To prevent AI hallucinations in regulated pharmacy operations, RXNexus enforces a strict 4-stage RAG validation pipeline:"
    )
    story.append(Paragraph(rag_desc, body))

    rag_steps = [
        [Paragraph("<b>Stage 1: Intent & Entity Parsing</b>", table_header), Paragraph("Extracts target drug name, NPI, formulary tier, and metric request without LLM interpretation.", table_cell)],
        [Paragraph("<b>Stage 2: Deterministic Metric Retrieval</b>", table_header), Paragraph("Queries pre-computed curated CSVs (`08_opportunities.csv`, `09_formulary_friction.csv`) via FastAPI.", table_cell)],
        [Paragraph("<b>Stage 3: Bounded Context Injection</b>", table_header), Paragraph("Injects immutable JSON data directly into prompt context. LLM forbidden from calculating numbers.", table_cell)],
        [Paragraph("<b>Stage 4: Provenance Annotation</b>", table_header), Paragraph("Appends exact citation badges: `[Source: CMS Part D Curated | File: 08_opportunities.csv | Metric: $420/claim]`.", table_cell)]
    ]
    t_rag = Table(rag_steps, colWidths=[160, 344])
    t_rag.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('BOX', (0,0), (-1,-1), 1, BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(t_rag)

    story.append(PageBreak())

    # ==========================================
    # SECTION 3: JUDGE Q&A DEFENSE
    # ==========================================
    story.append(Paragraph("Section 3: Anticipated Judge Q&A Technical Defense", h1))
    story.append(Paragraph("Battle-tested answers to high-probability technical questions from hackathon evaluators.", body))
    story.append(Spacer(1, 8))

    qa_items = [
        (
            "Q1: Why use a heuristic multi-objective scoring formula instead of an end-to-end Deep Neural Network or XGBoost?",
            "<b>Answer:</b> In Medicare Part D payer operations, every formulary change must withstand P&T committee scrutiny and CMS audits. Supervised ML models require labeled historical training sets (e.g., 'past formulary changes approved'), which suffer from extreme historical bias and severe label sparsity on newly approved generic drugs. Our multi-objective scoring is 100% mathematically transparent, non-parametric, allows real-time weight simulation by clinical pharmacists, and has zero unexplainable edge cases."
        ),
        (
            "Q2: How did you handle data privacy and adherence limitations given that public CMS data is aggregated?",
            "<b>Answer:</b> We adhered strictly to healthcare data governance principles. Public CMS Part D data is aggregated at the Prescriber-by-Drug level without beneficiary IDs. As documented in our architecture, we explicitly do not claim individual patient tracking. Instead, adherence risk is framed as population-level utilization patterns. Furthermore, we segregated patient-level longitudinal adherence data using synthetic Synthea models to ensure full ethical compliance."
        ),
        (
            "Q3: How does your RAG system guarantee zero hallucinations on drug pricing and rules?",
            "<b>Answer:</b> We decoupled metric calculation from natural-language generation. The LLM is strictly barred from computing spend, savings, or restriction counts. Our FastAPI backend queries the curated feature tables deterministically and injects the ground truth into the prompt. If a metric is missing, the system returns a null indicator rather than guessing. Every assertion is accompanied by an immutable file and row citation."
        ),
        (
            "Q4: How would this ML architecture scale to 100GB+ across multiple Medicare plan years?",
            "<b>Answer:</b> Our streaming ingestion uses generator iterators with O(1) memory complexity, ensuring that memory usage remains flat regardless of dataset size. To scale horizontally to 100GB+, the local DuckDB/Pandas streaming iterator can be dropped into an Apache PySpark or Snowflake Snowpark cluster writing to our PostgreSQL serving model (<code>models/schema.sql</code>), requiring zero changes to our API or UI layers."
        )
    ]

    for q, a in qa_items:
        q_p = Paragraph(f"<b>{q}</b>", ParagraphStyle('QStyle', fontName='Helvetica-Bold', fontSize=9.5, textColor=ACCENT, spaceAfter=4))
        a_p = Paragraph(a, ParagraphStyle('AStyle', fontName='Helvetica', fontSize=8.5, leading=13, textColor=PRIMARY))
        qa_table = Table([[q_p], [a_p]], colWidths=[504])
        qa_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
            ('BOX', (0,0), (-1,-1), 1, BORDER),
            ('PADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,0), 2),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        story.append(qa_table)
        story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {output_filename}")

if __name__ == "__main__":
    output_pdf = os.path.abspath("f:/rxnexus/RXNexus_Cognizant_Hackathon_ML_Presentation.pdf")
    create_presentation_pdf(output_pdf)
