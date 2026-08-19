"""Generate a professional PDF summary of the Plan & Strategy Setup features."""
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PDF = ROOT_DIR / "Plan_and_Strategy_Setup_Features_Summary.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "RXNexus | Plan & Strategy Setup Feature Summary")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)
        
        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 45, 8.5 * 72 - 54, 45)
        self.drawString(54, 32, "Confidential — Healthcare Payer Pharmacy Decision Support System")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 32, page_text)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0284c7")
    dark_navy = colors.HexColor("#081d36")
    text_dark = colors.HexColor("#0f172a")
    text_muted = colors.HexColor("#475569")
    bg_light = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=dark_navy,
        spaceAfter=3
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=primary_color,
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'Heading1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=dark_navy,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_dark,
        spaceAfter=5
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#0369a1")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#ffffff")
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=text_dark
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10.5,
        textColor=text_dark
    )

    story = []

    # Title & Header
    story.append(Paragraph("RXNEXUS • PAYERRX INTELLIGENCE PLATFORM", subtitle_style))
    story.append(Paragraph("Plan & Strategy Setup: Feature & Input Console Guide", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=2, spaceAfter=8))

    # Executive Overview Callout Box
    overview_text = (
        "<b>Executive Overview:</b> The <b>Plan & Strategy Setup Console</b> serves as the primary operational entry point "
        "for health plan pharmacy directors, actuaries, and formulary analysts. It translates high-level insurer business "
        "objectives (such as drug cost reduction, prior authorization review, or Medicare Star Rating compliance) into "
        "multi-dimensional mathematical weights without requiring technical or data science expertise."
    )
    
    callout_data = [[Paragraph(overview_text, callout_style)]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#bae6fd")),
        ('LINELEFT', (0, 0), (0, -1), 3.5, primary_color),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 8))

    # SECTION 1: Health Plan & Coverage Scope
    story.append(Paragraph("1. Health Plan & Coverage Scope Selectors", h1_style))
    story.append(Paragraph(
        "Allows users to scope analysis to specific federal contracts, benefit tiers, or query individual medications.", body_style
    ))

    sec1_data = [
        [Paragraph("Input Feature", table_header_style), Paragraph("Control Type", table_header_style), Paragraph("Description & Clinical / Insurance Purpose", table_header_style)],
        [
            Paragraph("Medicare Part D Health Plan", table_cell_bold),
            Paragraph("Dropdown", table_cell_style),
            Paragraph("Selects the contract scope: <b>All Plans (National)</b>, <b>SilverScript Choice (S5601)</b>, <b>Humana Gold Plus (H1036)</b>, <b>Aetna MA (H5521)</b>, or <b>UnitedHealthcare (S5820)</b>.", table_cell_style)
        ],
        [
            Paragraph("Plan Benefit Package (PBP)", table_cell_bold),
            Paragraph("Dropdown", table_cell_style),
            Paragraph("Filters down to specific benefit designs: <b>All PBPs</b>, <b>PBP 001 (Standard Rx)</b>, <b>PBP 002 (Enhanced Plus)</b>, <b>PBP 003 (Value Tier)</b>, or <b>PBP 004 (Dual-Eligible SNP)</b>.", table_cell_style)
        ],
        [
            Paragraph("Quick Search", table_cell_bold),
            Paragraph("Text Input", table_cell_style),
            Paragraph("Instant search targeting specific <b>Medicine Names</b> (e.g. <i>Restasis, Xtandi, Eliquis</i>) or <b>10-Digit Prescriber / Doctor NPI IDs</b> to isolate single-drug evidence.", table_cell_style)
        ]
    ]

    t1 = Table(sec1_data, colWidths=[120, 74, 310])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), dark_navy),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#ffffff"), bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t1)
    story.append(Spacer(1, 8))

    # SECTION 2: Primary Business Goal & Strategy Presets
    story.append(Paragraph("2. Primary Business Goal & Strategy Presets", h1_style))
    story.append(Paragraph(
        "Users select one primary business objective. The system automatically loads pre-calibrated multi-dimensional weights:", body_style
    ))

    sec2_data = [
        [
            Paragraph("Strategy Preset", table_header_style),
            Paragraph("Primary Focus", table_header_style),
            Paragraph("Cost", table_header_style),
            Paragraph("Vol.", table_header_style),
            Paragraph("Ctrl.", table_header_style),
            Paragraph("Comp.", table_header_style),
            Paragraph("Gen.", table_header_style),
            Paragraph("Core Business Outcome", table_header_style)
        ],
        [
            Paragraph("Lower Drug Costs", table_cell_bold),
            Paragraph("High Spend", table_cell_style),
            Paragraph("50%", table_cell_bold),
            Paragraph("20%", table_cell_style),
            Paragraph("10%", table_cell_style),
            Paragraph("10%", table_cell_style),
            Paragraph("10%", table_cell_style),
            Paragraph("Targets highest-spend specialty brand outliers for immediate budget relief.", table_cell_style)
        ],
        [
            Paragraph("Medication Control", table_cell_bold),
            Paragraph("Prior Auth / ST", table_cell_style),
            Paragraph("20%", table_cell_style),
            Paragraph("15%", table_cell_style),
            Paragraph("45%", table_cell_bold),
            Paragraph("10%", table_cell_style),
            Paragraph("10%", table_cell_style),
            Paragraph("Pinpoints heavy administrative approval barriers to streamline care delivery.", table_cell_style)
        ],
        [
            Paragraph("Improve Compliance", table_cell_bold),
            Paragraph("Refill Health", table_cell_style),
            Paragraph("20%", table_cell_style),
            Paragraph("15%", table_cell_style),
            Paragraph("10%", table_cell_style),
            Paragraph("45%", table_cell_bold),
            Paragraph("10%", table_cell_style),
            Paragraph("Identifies chronic disease cohorts at risk of refill gaps (PDC < 80%) to protect Star Ratings.", table_cell_style)
        ],
        [
            Paragraph("Switch to Generics", table_cell_bold),
            Paragraph("Generic / Bio", table_cell_style),
            Paragraph("35%", table_cell_style),
            Paragraph("15%", table_cell_style),
            Paragraph("10%", table_cell_style),
            Paragraph("10%", table_cell_style),
            Paragraph("30%", table_cell_bold),
            Paragraph("Prioritizes FDA Orange Book A-rated generic & biosimilar tier downshifts.", table_cell_style)
        ],
        [
            Paragraph("Balanced Strategy", table_cell_bold),
            Paragraph("Multi-factor", table_cell_style),
            Paragraph("30%", table_cell_style),
            Paragraph("25%", table_cell_style),
            Paragraph("20%", table_cell_style),
            Paragraph("15%", table_cell_style),
            Paragraph("10%", table_cell_style),
            Paragraph("Standard baseline balancing fiscal responsibility, patient access, and clinical quality.", table_cell_style)
        ],
    ]

    t2 = Table(sec2_data, colWidths=[90, 65, 28, 28, 28, 30, 28, 207])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (6, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#ffffff"), bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 6))

    # Optional Advanced Sliders Note
    story.append(Paragraph(
        "<b>⚙️ Optional Fine-Tuning Slider Module:</b> Clicking <i>Fine-Tune Weights</i> expands 5 precision sliders "
        "(Cost, Volume, Controls, Compliance, Generics). The interface features real-time validation ensuring total weights sum to 100%.", body_style
    ))
    story.append(Spacer(1, 8))

    # SECTION 3: Medication Focus Areas & Restriction Filters
    story.append(Paragraph("3. Medication Focus Areas & Spend Filters", h1_style))
    
    sec3_data = [
        [Paragraph("Filter Component", table_header_style), Paragraph("Input Values / Options", table_header_style), Paragraph("Operational Impact on Output", table_header_style)],
        [
            Paragraph("Medication Focus Areas (Scope Pills)", table_cell_bold),
            Paragraph("• All Medications<br/>• High-Cost Outliers<br/>• High Prescription Volume<br/>• Specialty Drugs (Tier 4 & 5)<br/>• Prior Authorization (PA)<br/>• Step Therapy (ST)<br/>• Refill Compliance Risk", table_cell_style),
            Paragraph("Multi-select pills that filter the target drug cohort before ranking. Enables rapid single-click isolation of specialty tiers or restricted medication classes.", table_cell_style)
        ],
        [
            Paragraph("Min. Annual Plan Spend ($)", table_cell_bold),
            Paragraph("Numeric ($0 to $100M+)<br/><i>Default: $50,000</i>", table_cell_style),
            Paragraph("Excludes low-financial-impact medications, ensuring committee time is concentrated on high-value savings opportunities.", table_cell_style)
        ],
        [
            Paragraph("Min. Prescription Claims", table_cell_bold),
            Paragraph("Numeric (0 to 100,000+)<br/><i>Default: 500 fills</i>", table_cell_style),
            Paragraph("Filters out low-volume outlier prescriptions to ensure statistical reliability across patient populations.", table_cell_style)
        ],
        [
            Paragraph("Focus Percentile Cutoff", table_cell_bold),
            Paragraph("• Top 10% (P90)<br/>• Top 25% (P75)<br/>• All Spend Percentiles", table_cell_style),
            Paragraph("Limits discovery to the statistical upper tail of expenditure, pinpointing high-impact drug candidates.", table_cell_style)
        ],
    ]

    t3 = Table(sec3_data, colWidths=[120, 130, 254])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), dark_navy),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#ffffff"), bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 8))

    # SECTION 4: End-to-End Workflow Execution
    story.append(Paragraph("4. End-to-End Decision Flow", h1_style))
    
    flow_steps = (
        "<b>Step 1 (Configure):</b> Insurer sets plan scope, business objective preset, and spend floor.<br/>"
        "<b>Step 2 (Simulate):</b> User clicks <i>'Run Health Plan Analysis & Find Opportunities'</i> → backend executes weighted vector scoring.<br/>"
        "<b>Step 3 (Explore):</b> User lands on <i>'Cost & Savings Opportunities'</i> displaying the active parameter summary and ranked drug list.<br/>"
        "<b>Step 4 (Inspect & Review):</b> Clicking <i>'Inspect & Review'</i> opens the <b>Human-in-the-Loop Clinical Review</b> drawer to examine bioequivalent alternatives and save approval decisions directly to the audit log."
    )
    flow_data = [[Paragraph(flow_steps, body_style)]]
    flow_table = Table(flow_data, colWidths=[504])
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('LINELEFT', (0, 0), (0, -1), 3.5, colors.HexColor("#059669")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(flow_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF at: {OUTPUT_PDF}")

if __name__ == "__main__":
    build_pdf()
