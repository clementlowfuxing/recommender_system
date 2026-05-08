"""
Generate the CDWC Engine — High-Level Architecture & Scoring Flow deck.
Focused on: how the engine computes scores to answer user questions.
Output: presentation_ppt/CDWC_Architecture_Scoring_Flow.pptx
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "presentation_ppt"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "CDWC_Architecture_Scoring_Flow.pptx"

# Palette
DARK_BLUE = RGBColor(0x1E, 0x29, 0x3B)
PRIMARY_BLUE = RGBColor(0x25, 0x63, 0xEB)
LIGHT_BLUE = RGBColor(0xDB, 0xEA, 0xFE)
PALE_BLUE = RGBColor(0xF0, 0xF7, 0xFF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0x64, 0x74, 0x8B)
LIGHT_GRAY = RGBColor(0xF1, 0xF5, 0xF9)
GREEN = RGBColor(0x05, 0x96, 0x69)
PALE_GREEN = RGBColor(0xD1, 0xFA, 0xE5)
RED = RGBColor(0xDC, 0x26, 0x26)
PALE_RED = RGBColor(0xFE, 0xE2, 0xE2)
YELLOW_BG = RGBColor(0xFE, 0xF9, 0xC3)
AMBER = RGBColor(0xCA, 0x8A, 0x04)
PURPLE = RGBColor(0x7C, 0x3A, 0xED)
PALE_PURPLE = RGBColor(0xF3, 0xE8, 0xFF)
TEAL = RGBColor(0x0D, 0x94, 0x88)
PALE_TEAL = RGBColor(0xCC, 0xFB, 0xF1)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)


def add_bg(slide, color=WHITE):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_shape(slide, left, top, width, height, fill_color, line_color=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, left, top, width, height)
    s.fill.solid()
    s.fill.fore_color.rgb = fill_color
    if line_color:
        s.line.color.rgb = line_color
        s.line.width = Pt(1.25)
    else:
        s.line.fill.background()
    return s


def add_text(slide, left, top, width, height, text, size=18, bold=False,
             color=DARK_BLUE, align=PP_ALIGN.LEFT, font="Calibri"):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font
    p.alignment = align
    return tb


def add_bullets(slide, left, top, width, height, items, size=14, color=DARK_BLUE):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.name = "Calibri"
        p.space_after = Pt(4)


def add_labeled_box(slide, x, y, w, h, title, fill, border, desc=None, title_size=13, desc_size=11):
    add_shape(slide, x, y, w, h, fill, border)
    add_text(slide, x + Inches(0.12), y + Inches(0.1), w - Inches(0.24), Inches(0.45),
             title, size=title_size, bold=True, color=DARK_BLUE, align=PP_ALIGN.CENTER)
    if desc:
        add_text(slide, x + Inches(0.12), y + Inches(0.5), w - Inches(0.24), h - Inches(0.55),
                 desc, size=desc_size, color=DARK_BLUE, align=PP_ALIGN.CENTER)


def add_arrow(slide, x1, y1, x2, y2, color=GRAY, weight=Pt(2)):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = color
    c.line.width = weight
    # end arrow
    from pptx.oxml.ns import qn
    from lxml import etree
    ln = c.line._get_or_add_ln()
    tail = etree.SubElement(ln, qn('a:tailEnd'))
    tail.set('type', 'triangle')
    tail.set('w', 'med')
    tail.set('h', 'med')
    return c


def add_header(slide, title, subtitle=None):
    add_text(slide, Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.65),
             title, size=26, bold=True, color=DARK_BLUE)
    if subtitle:
        add_text(slide, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.4),
                 subtitle, size=13, color=GRAY)
    add_shape(slide, Inches(0.5), Inches(1.3), Inches(0.6), Inches(0.05), PRIMARY_BLUE)


# ════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, DARK_BLUE)
add_text(slide, Inches(1), Inches(2.3), Inches(11), Inches(1.2),
         "CDWC Talent Diagnostic Engine",
         size=40, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
add_text(slide, Inches(1), Inches(3.5), Inches(11), Inches(0.8),
         "High-Level Architecture & Scoring Flow",
         size=24, color=RGBColor(0x93, 0xC5, 0xFD), align=PP_ALIGN.CENTER)
add_text(slide, Inches(1), Inches(4.7), Inches(11), Inches(0.6),
         "How the Engine Computes Scores to Answer HOD/GM Questions",
         size=15, color=GRAY, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════
# SLIDE 2 — End-to-End Architecture (the big picture)
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "End-to-End Architecture",
           "From HOD/GM question → to data sources → to scoring → to JSON insights")

# Layer bars (vertical stack of 5 layers)
layers = [
    # (label, color, border, y, h)
    ("① PRESENTATION LAYER   ·   HOD/GM asks a question", PALE_PURPLE, PURPLE),
    ("② CONVERSATION LAYER   ·   NL parser + narrative formatter", PALE_BLUE, PRIMARY_BLUE),
    ("③ API LAYER   ·   FastAPI endpoints route the request", LIGHT_BLUE, PRIMARY_BLUE),
    ("④ ENGINE LAYER   ·   join → scope → score → analyze → insight  (PURE JSON OUT)", PALE_GREEN, GREEN),
    ("⑤ DATA LAYER   ·   DUMMY_SMA_HRIS_sample.json  +  DUMMY_TPCP_Assessment_sample.json", LIGHT_GRAY, GRAY),
]

layer_h = Inches(0.9)
y_start = Inches(1.6)
for i, (lbl, fill, border) in enumerate(layers):
    y = y_start + i * (layer_h + Inches(0.15))
    add_shape(slide, Inches(0.5), y, Inches(12.3), layer_h, fill, border)
    add_text(slide, Inches(0.8), y + Inches(0.25), Inches(11.7), Inches(0.45),
             lbl, size=15, bold=True, color=DARK_BLUE, align=PP_ALIGN.LEFT)

# Vertical connectors (up/down data flow indicators)
for i in range(4):
    y = y_start + (i + 1) * (layer_h + Inches(0.15)) - Inches(0.14)
    add_text(slide, Inches(6.2), y, Inches(1), Inches(0.25),
             "↕", size=14, bold=True, color=GRAY, align=PP_ALIGN.CENTER)

# Side annotation
add_text(slide, Inches(0.5), Inches(6.9), Inches(12.3), Inches(0.4),
         "Engine layer never formats prose. It always emits structured JSON which the conversation layer converts into narrative.",
         size=12, bold=True, color=PRIMARY_BLUE, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════
# SLIDE 3 — Data Layer zoom: the two source files + join
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "Data Layer",
           "Two source files, left-join on dummy_id → unified employee record")

# HRIS box
add_shape(slide, Inches(0.5), Inches(1.75), Inches(5.2), Inches(3.2), LIGHT_BLUE, PRIMARY_BLUE)
add_text(slide, Inches(0.7), Inches(1.9), Inches(4.8), Inches(0.45),
         "DUMMY_SMA_HRIS_sample.json", size=14, bold=True, color=PRIMARY_BLUE)
add_text(slide, Inches(0.7), Inches(2.35), Inches(4.8), Inches(0.4),
         "9,455 employees  (1 row per person)", size=11, color=GRAY)
hris_fields = [
    "• dummy_id, employee_name, superior_name",
    "• skill_group, job_grade, salary_grade",
    "• year_in_sg",
    "• sma_completion_status",
    "• overall_cbs_pct",
    "• technical_cbs_pct",
    "• leadership_cbs_pct",
]
add_bullets(slide, Inches(0.8), Inches(2.8), Inches(4.7), Inches(2), hris_fields, size=12)

# TPCP box
add_shape(slide, Inches(7.6), Inches(1.75), Inches(5.2), Inches(3.2), PALE_PURPLE, PURPLE)
add_text(slide, Inches(7.8), Inches(1.9), Inches(4.8), Inches(0.45),
         "DUMMY_TPCP_Assessment_sample.json", size=14, bold=True, color=PURPLE)
add_text(slide, Inches(7.8), Inches(2.35), Inches(4.8), Inches(0.4),
         "1,018 assessments  (1 row per person)", size=11, color=GRAY)
tpcp_fields = [
    "• dummy_id, employee_name",
    "• business, opu, division, skill_group",
    "• discipline, sub_discipline",
    "• assessment_level, qualified_level, passed_tpcp",
    "• base_pct, key_pct, pacing_pct, emerging_pct, cti_met_pct",
    "• 110+ competency cells  (b1..b25, k1..k15, p1..p10, e1..e10)",
]
add_bullets(slide, Inches(7.8), Inches(2.8), Inches(4.7), Inches(2), tpcp_fields, size=11)

# Join arrows and box
add_arrow(slide, Inches(5.7), Inches(3.3), Inches(6.4), Inches(3.3), PRIMARY_BLUE, Pt(2.5))
add_arrow(slide, Inches(7.6), Inches(3.3), Inches(6.9), Inches(3.3), PURPLE, Pt(2.5))
add_shape(slide, Inches(5.7), Inches(2.9), Inches(1.9), Inches(0.8), YELLOW_BG, AMBER)
add_text(slide, Inches(5.7), Inches(3.0), Inches(1.9), Inches(0.5),
         "LEFT JOIN", size=13, bold=True, color=AMBER, align=PP_ALIGN.CENTER)
add_text(slide, Inches(5.7), Inches(3.35), Inches(1.9), Inches(0.35),
         "on dummy_id", size=10, color=DARK_BLUE, align=PP_ALIGN.CENTER)

# Unified record
add_shape(slide, Inches(1.5), Inches(5.3), Inches(10.3), Inches(1.7), PALE_GREEN, GREEN)
add_text(slide, Inches(1.7), Inches(5.4), Inches(10), Inches(0.4),
         "Unified Employee Record", size=14, bold=True, color=GREEN)
unified_desc = [
    "977 employees with BOTH files (full signal)  ·  8,477 HRIS-only (scored on CBS, zero on TPCP)  ·  41 TPCP-only (edge case)",
    "Each record carries identity + org hierarchy + CBS block + TPCP block + competency cells ready for scoring.",
]
add_bullets(slide, Inches(1.7), Inches(5.85), Inches(10), Inches(1.1), unified_desc, size=12)


# ════════════════════════════════════════════════════════════════════
# SLIDE 4 — The 4-stage pipeline (engine detail)
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "Engine Pipeline — 4 Stages",
           "Every query flows through these stages; outputs are pure JSON")

stages = [
    {"n": "1", "t": "Scope Filter", "c": PALE_RED, "b": RED,
     "d": "Apply mandatory org filter:\nbusiness · opu · division.\nResulting team = candidate pool."},
    {"n": "2", "t": "Per-Person Scoring", "c": LIGHT_BLUE, "b": PRIMARY_BLUE,
     "d": "Compute 6 health scores for\nevery employee in pool.\nAll scores are 0–1."},
    {"n": "3", "t": "Analysis Layer", "c": YELLOW_BG, "b": AMBER,
     "d": "Run 3 parallel analyses:\n• Team aggregate rollup\n• Competency gap matrix\n• Individual drill-down"},
    {"n": "4", "t": "Insight Engine", "c": PALE_GREEN, "b": GREEN,
     "d": "Rule-based triage:\ntraining · exposure · hiring.\nEmit structured JSON."},
]

box_w = Inches(2.9)
box_h = Inches(3.2)
y = Inches(1.7)
start_x = Inches(0.5)
gap = Inches(0.25)

for i, s in enumerate(stages):
    x = start_x + i * (box_w + gap)
    add_shape(slide, x, y, box_w, box_h, s["c"], s["b"])
    # Number badge
    add_shape(slide, x + Inches(0.2), y + Inches(0.2), Inches(0.5), Inches(0.5), s["b"], s["b"], shape=MSO_SHAPE.OVAL)
    add_text(slide, x + Inches(0.2), y + Inches(0.28), Inches(0.5), Inches(0.4),
             s["n"], size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(slide, x + Inches(0.85), y + Inches(0.28), box_w - Inches(1), Inches(0.45),
             s["t"], size=16, bold=True, color=DARK_BLUE)
    add_text(slide, x + Inches(0.25), y + Inches(1), box_w - Inches(0.5), box_h - Inches(1.1),
             s["d"], size=12, color=DARK_BLUE)
    if i < 3:
        add_text(slide, x + box_w, y + Inches(1.4), gap, Inches(0.4),
                 "→", size=22, bold=True, color=GRAY, align=PP_ALIGN.CENTER)

# Question routing below
add_shape(slide, Inches(0.5), Inches(5.2), Inches(12.3), Inches(1.8), PALE_BLUE, PRIMARY_BLUE)
add_text(slide, Inches(0.7), Inches(5.3), Inches(12), Inches(0.4),
         "Which stage answers which question?", size=14, bold=True, color=PRIMARY_BLUE)
route = [
    "• Stage 2 →  'Who has not completed TPCP?'  'Individual scorecards'  'What is their combined score?'",
    "• Stage 3 →  'Team TPCP performance?'  'Which cells are consistently weak?'  'People vs structural?'",
    "• Stage 4 →  'What actions?'  'Training, exposure, hiring?'  'What to close in 6–12 months?'  'Who is promotable?'",
]
add_bullets(slide, Inches(0.8), Inches(5.8), Inches(12), Inches(1.3), route, size=12)


# ════════════════════════════════════════════════════════════════════
# SLIDE 5 — Scoring engine: inputs → 6 health scores → outputs
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "Per-Person Scoring — Inputs to 6 Health Scores",
           "Each employee becomes a 6-dimensional health vector")

# Left column — data inputs (source fields)
add_shape(slide, Inches(0.4), Inches(1.7), Inches(3.2), Inches(5.3), PALE_BLUE, PRIMARY_BLUE)
add_text(slide, Inches(0.6), Inches(1.8), Inches(2.8), Inches(0.4),
         "INPUT FIELDS", size=13, bold=True, color=PRIMARY_BLUE, align=PP_ALIGN.CENTER)
inputs_block = [
    "FROM HRIS:",
    "  • overall_cbs_pct",
    "  • technical_cbs_pct",
    "  • leadership_cbs_pct",
    "  • job_grade",
    "  • year_in_sg",
    "",
    "FROM TPCP:",
    "  • cti_met_pct",
    "  • base_pct",
    "  • key_pct",
    "  • pacing_pct",
    "  • emerging_pct",
    "  • passed_tpcp",
    "  • assessment_level",
    "  • b1..b25, k1..k15,",
    "    p1..p10, e1..e10",
]
add_bullets(slide, Inches(0.6), Inches(2.3), Inches(2.8), Inches(4.7), inputs_block, size=11)

# Middle — 6 score boxes
score_titles = [
    ("1. TPCP Health",       "cti_met_pct, base, key,\npacing, emerging, pass", LIGHT_BLUE, PRIMARY_BLUE),
    ("2. CBS Health",        "technical_cbs +\noverall_cbs +\nleadership_cbs", PALE_PURPLE, PURPLE),
    ("3. Combined Competency","0.55 × TPCP\n+ 0.45 × CBS", PALE_GREEN, GREEN),
    ("4. Grade Fit",         "job_grade ↔\nassessment_level\nalignment", YELLOW_BG, AMBER),
    ("5. Tenure Readiness",  "year_in_sg /\ngrade_threshold", PALE_TEAL, TEAL),
    ("6. Critical Gap Score","1 - (cells ≤ 1 /\ntotal cells)", PALE_RED, RED),
]
col_x = Inches(3.9)
card_w = Inches(3.0)
card_h = Inches(1.6)
for i, (t, d, c, b) in enumerate(score_titles):
    row = i // 2
    col = i % 2
    x = col_x + col * (card_w + Inches(0.2))
    y = Inches(1.7) + row * (card_h + Inches(0.15))
    add_shape(slide, x, y, card_w, card_h, c, b)
    add_text(slide, x + Inches(0.15), y + Inches(0.1), card_w - Inches(0.3), Inches(0.45),
             t, size=13, bold=True, color=DARK_BLUE)
    add_text(slide, x + Inches(0.15), y + Inches(0.55), card_w - Inches(0.3), card_h - Inches(0.65),
             d, size=11, color=DARK_BLUE)

# Right — output vector
right_x = Inches(10.3)
add_shape(slide, right_x, Inches(1.7), Inches(2.6), Inches(5.3), DARK_BLUE, DARK_BLUE)
add_text(slide, right_x + Inches(0.2), Inches(1.85), Inches(2.2), Inches(0.4),
         "OUTPUT", size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
tb = slide.shapes.add_textbox(right_x + Inches(0.2), Inches(2.3), Inches(2.3), Inches(4.5))
tf = tb.text_frame
tf.word_wrap = True
out_text = """{
  "employee_id": 23267,
  "tpcp_health": 0.78,
  "cbs_health": 0.64,
  "combined": 0.72,
  "grade_fit": 1.0,
  "tenure_ready": 0.85,
  "gap_score": 0.88,
  "gap_cells": [
    "k3","p2","e1"
  ]
}"""
p = tf.paragraphs[0]
p.text = out_text
p.font.size = Pt(10)
p.font.name = "Consolas"
p.font.color.rgb = WHITE


# ════════════════════════════════════════════════════════════════════
# SLIDE 6 — Deep dive: how each score is computed
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "How Each Score Is Computed",
           "Every formula is deterministic, traceable, and tunable")

# 2x3 grid of score formulas
score_details = [
    ("1. TPCP Health", LIGHT_BLUE, PRIMARY_BLUE,
     "tpcp_health =\n   0.6 × cti_met_pct\n + 0.4 × avg(base_pct, key_pct,\n            pacing_pct, emerging_pct)\n + 0.1 if passed_tpcp = 'Y'\n (capped at 1.0)",
     "→ 0 if no TPCP record"),
    ("2. CBS Health", PALE_PURPLE, PURPLE,
     "cbs_health =\n   0.5 × technical_cbs_pct\n + 0.3 × overall_cbs_pct\n + 0.2 × leadership_cbs_pct\n (weights rebalance if a\n  dimension is missing)",
     "→ available to all HRIS rows"),
    ("3. Combined Competency", PALE_GREEN, GREEN,
     "combined =\n   0.55 × tpcp_health\n + 0.45 × cbs_health\n\n (if tpcp_health = 0 →\n  combined = cbs_health)",
     "→ primary ranking score"),
    ("4. Grade Fit", YELLOW_BG, AMBER,
     "Expected level by grade:\n  P1–P3 → Staff\n  P4–P6 → Principal\n  P7+   → Custodian\n\nExact=1.0  Over=0.5  Under=0.0",
     "→ flags grade/level misalignment"),
    ("5. Tenure Readiness", PALE_TEAL, TEAL,
     "Grade tenure thresholds:\n  P1–P3 → 3 yrs\n  P4–P6 → 4 yrs\n  P7+   → 5 yrs\n\nscore = min(year_in_sg /\n            threshold, 1.0)",
     "→ gates promotability"),
    ("6. Critical Gap Score", PALE_RED, RED,
     "cells = b1..b25, k1..k15,\n        p1..p10, e1..e10\n\ngap_count = |cells ≤ 1|\n\nscore = 1 − (gap_count /\n             total_cells)",
     "→ also feeds gap matrix"),
]
card_w = Inches(4.1)
card_h = Inches(2.6)
gx = Inches(0.4)
gy = Inches(1.6)
for i, (t, c, b, formula, note) in enumerate(score_details):
    row = i // 3
    col = i % 3
    x = gx + col * (card_w + Inches(0.1))
    y = gy + row * (card_h + Inches(0.15))
    add_shape(slide, x, y, card_w, card_h, c, b)
    add_text(slide, x + Inches(0.15), y + Inches(0.1), card_w - Inches(0.3), Inches(0.4),
             t, size=14, bold=True, color=DARK_BLUE)
    # Formula block
    tb = slide.shapes.add_textbox(x + Inches(0.15), y + Inches(0.55), card_w - Inches(0.3), Inches(1.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = formula
    p.font.size = Pt(10)
    p.font.name = "Consolas"
    p.font.color.rgb = DARK_BLUE
    add_text(slide, x + Inches(0.15), y + card_h - Inches(0.45), card_w - Inches(0.3), Inches(0.35),
             note, size=10, bold=True, color=b)


# ════════════════════════════════════════════════════════════════════
# SLIDE 7 — Worked example (single employee)
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "Worked Example — Single Employee",
           "Tracing one record through the scoring engine")

# Input data panel
add_shape(slide, Inches(0.4), Inches(1.65), Inches(4.0), Inches(5.4), LIGHT_GRAY, GRAY)
add_text(slide, Inches(0.55), Inches(1.75), Inches(3.7), Inches(0.4),
         "INPUT  (from joined record)", size=13, bold=True, color=DARK_BLUE)
tb = slide.shapes.add_textbox(Inches(0.55), Inches(2.2), Inches(3.7), Inches(4.7))
tf = tb.text_frame
tf.word_wrap = True
input_text = """dummy_id            : 23267
job_grade           : P4
year_in_sg          : 4.2

From HRIS
  overall_cbs_pct   : 0.65
  technical_cbs_pct : 0.70
  leadership_cbs_pct: 0.55

From TPCP
  assessment_level  : Principal
  passed_tpcp       : Y
  cti_met_pct       : 0.83
  base_pct          : 0.75
  key_pct           : 0.70
  pacing_pct        : 0.60
  emerging_pct      : 0.80
  b,k,p,e cells ≤ 1 : 3 of 60"""
p = tf.paragraphs[0]
p.text = input_text
p.font.size = Pt(10.5)
p.font.name = "Consolas"
p.font.color.rgb = DARK_BLUE

# Arrow
add_text(slide, Inches(4.45), Inches(4.0), Inches(0.5), Inches(0.6),
         "→", size=32, bold=True, color=GRAY, align=PP_ALIGN.CENTER)

# Computation panel
add_shape(slide, Inches(5.0), Inches(1.65), Inches(4.5), Inches(5.4), PALE_BLUE, PRIMARY_BLUE)
add_text(slide, Inches(5.15), Inches(1.75), Inches(4.2), Inches(0.4),
         "COMPUTATION", size=13, bold=True, color=PRIMARY_BLUE)
tb = slide.shapes.add_textbox(Inches(5.15), Inches(2.2), Inches(4.2), Inches(4.7))
tf = tb.text_frame
tf.word_wrap = True
calc_text = """tpcp_avg = mean(0.75, 0.70,
                0.60, 0.80) = 0.7125
tpcp_health = 0.6 × 0.83
            + 0.4 × 0.7125
            + 0.1 (passed)
            = 0.49 + 0.285 + 0.1
            = 0.87  (capped 1.0)

cbs_health = 0.5 × 0.70
           + 0.3 × 0.65
           + 0.2 × 0.55
           = 0.35+0.195+0.11 = 0.65

combined = 0.55 × 0.87
         + 0.45 × 0.65
         = 0.48 + 0.29 = 0.77

grade_fit  : P4 → Principal ✓  = 1.0
tenure     : 4.2/4.0 capped   = 1.0
gap_score  : 1 − 3/60         = 0.95"""
p = tf.paragraphs[0]
p.text = calc_text
p.font.size = Pt(10)
p.font.name = "Consolas"
p.font.color.rgb = DARK_BLUE

# Arrow
add_text(slide, Inches(9.55), Inches(4.0), Inches(0.5), Inches(0.6),
         "→", size=32, bold=True, color=GRAY, align=PP_ALIGN.CENTER)

# Output panel
add_shape(slide, Inches(10.1), Inches(1.65), Inches(2.8), Inches(5.4), DARK_BLUE, DARK_BLUE)
add_text(slide, Inches(10.25), Inches(1.75), Inches(2.5), Inches(0.4),
         "OUTPUT (JSON)", size=13, bold=True, color=WHITE)
tb = slide.shapes.add_textbox(Inches(10.25), Inches(2.2), Inches(2.5), Inches(4.7))
tf = tb.text_frame
tf.word_wrap = True
out = """{
  "tpcp_health": 0.87,
  "cbs_health": 0.65,
  "combined": 0.77,
  "grade_fit": 1.0,
  "tenure_ready": 1.0,
  "gap_score": 0.95,
  "promotable": true,
  "gap_count": 3
}"""
p = tf.paragraphs[0]
p.text = out
p.font.size = Pt(11)
p.font.name = "Consolas"
p.font.color.rgb = WHITE


# ════════════════════════════════════════════════════════════════════
# SLIDE 8 — Aggregation: per-person scores → team insights
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "From Per-Person Scores to Team Insights",
           "Stage 3 runs 3 analyses in parallel over the scored population")

# Center input source
add_shape(slide, Inches(5.1), Inches(1.7), Inches(3.2), Inches(1.1), DARK_BLUE, DARK_BLUE)
add_text(slide, Inches(5.2), Inches(1.8), Inches(3), Inches(0.5),
         "Scored Population", size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
add_text(slide, Inches(5.2), Inches(2.25), Inches(3), Inches(0.4),
         "N employees × 6 scores each",
         size=11, color=RGBColor(0x93, 0xC5, 0xFD), align=PP_ALIGN.CENTER)

# 3 branch arrows
add_arrow(slide, Inches(6.7), Inches(2.8), Inches(2.3), Inches(3.5), GRAY, Pt(2))
add_arrow(slide, Inches(6.7), Inches(2.8), Inches(6.7), Inches(3.5), GRAY, Pt(2))
add_arrow(slide, Inches(6.7), Inches(2.8), Inches(11.1), Inches(3.5), GRAY, Pt(2))

# Three analysis boxes
branches = [
    {
        "title": "A. Team Rollup", "x": Inches(0.6), "color": PALE_PURPLE, "border": PURPLE,
        "body": [
            "• pass rate, level distribution",
            "• avg combined / TPCP / CBS",
            "• not_assessed count",
            "• grade-level headcounts",
            "",
            "ANSWERS:",
            "• How did my team perform?",
            "• Who has not completed TPCP?",
            "• Enough Staff/Principal?",
            "• Overall SMA strength?",
        ],
    },
    {
        "title": "B. Gap Matrix", "x": Inches(5.05), "color": YELLOW_BG, "border": AMBER,
        "body": [
            "For each cell (b1..e10):",
            "  fail_rate = |score ≤ 1| / N",
            "",
            "Classify each cell:",
            "  ≥ 60%  → STRUCTURAL",
            "  20–60% → MIXED",
            "  < 20%  → PEOPLE",
            "",
            "ANSWERS:",
            "• Which cells are weak?",
            "• Repeat gaps across people?",
            "• People vs structural?",
        ],
    },
    {
        "title": "C. Individual Drill-Down", "x": Inches(9.45), "color": LIGHT_BLUE, "border": PRIMARY_BLUE,
        "body": [
            "• flag low combined (< 0.5)",
            "• flag promotable (≥ 0.75 +",
            "   tenure + pass + ≤3 gaps)",
            "• list gap cells per person",
            "",
            "ANSWERS:",
            "• Critical gap individuals?",
            "• Who is promotable?",
            "• Gaps before promotion?",
            "• Move to critical role?",
        ],
    },
]
box_w = Inches(3.85)
box_h = Inches(3.7)
for br in branches:
    x = br["x"]
    y = Inches(3.4)
    add_shape(slide, x, y, box_w, box_h, br["color"], br["border"])
    add_text(slide, x + Inches(0.15), y + Inches(0.15), box_w - Inches(0.3), Inches(0.45),
             br["title"], size=15, bold=True, color=DARK_BLUE, align=PP_ALIGN.CENTER)
    add_bullets(slide, x + Inches(0.2), y + Inches(0.7), box_w - Inches(0.4), box_h - Inches(0.8),
                br["body"], size=11)


# ════════════════════════════════════════════════════════════════════
# SLIDE 9 — Insight Engine: scores → actions
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "Insight Engine — From Scores to Actions",
           "Stage 4 turns numbers into 'what to do' via rule-based triage")

# Input on left
add_shape(slide, Inches(0.4), Inches(1.7), Inches(3.2), Inches(5.3), LIGHT_GRAY, GRAY)
add_text(slide, Inches(0.55), Inches(1.8), Inches(3), Inches(0.4),
         "INPUT TO TRIAGE", size=13, bold=True, color=DARK_BLUE)
in_items = [
    "From Team Rollup:",
    "  • level distribution",
    "  • pass rate, avg scores",
    "",
    "From Gap Matrix:",
    "  • per-cell failure rate",
    "  • structural / mixed / people",
    "",
    "From Individual Drill-Down:",
    "  • flagged low performers",
    "  • promotable candidates",
    "  • personal gap lists",
]
add_bullets(slide, Inches(0.55), Inches(2.3), Inches(3), Inches(4.6), in_items, size=11)

# Decision tree in middle
add_shape(slide, Inches(4.0), Inches(1.7), Inches(5.0), Inches(5.3), PALE_BLUE, PRIMARY_BLUE)
add_text(slide, Inches(4.15), Inches(1.8), Inches(4.7), Inches(0.4),
         "DECISION RULES", size=13, bold=True, color=PRIMARY_BLUE)
rules_text = """IF cell.fail_rate ≥ 60%
   AND cell ∈ (Base, Key)
   → action = TRAINING (priority: high)

IF cell.fail_rate 20–60%
   AND cell ∈ (Pacing, Emerging)
   → action = EXPOSURE (targeted)

IF level_distribution.principals /
   team_size < benchmark
   AND no internal upgrade path
   → action = HIRING

IF individual.combined ≥ 0.75
   AND tenure_ready ≥ 1.0
   AND passed_tpcp = 'Y'
   AND gap_count ≤ 3
   → promotable = true

IF individual.combined 0.65–0.74
   → close_in_6m: list gaps at level 2"""
tb = slide.shapes.add_textbox(Inches(4.15), Inches(2.3), Inches(4.7), Inches(4.6))
tf = tb.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = rules_text
p.font.size = Pt(10.5)
p.font.name = "Consolas"
p.font.color.rgb = DARK_BLUE

# Output on right
add_shape(slide, Inches(9.4), Inches(1.7), Inches(3.5), Inches(5.3), DARK_BLUE, DARK_BLUE)
add_text(slide, Inches(9.55), Inches(1.8), Inches(3.2), Inches(0.4),
         "JSON OUTPUT", size=13, bold=True, color=WHITE)
tb = slide.shapes.add_textbox(Inches(9.55), Inches(2.3), Inches(3.2), Inches(4.6))
tf = tb.text_frame
tf.word_wrap = True
out_text = """{
  "actions": [
    {
      "type": "training",
      "priority": "high",
      "cell": "k3",
      "fail_rate": 0.68,
      "horizon_months": 6,
      "affects": 18
    },
    {
      "type": "exposure",
      "priority": "medium",
      "cell": "p2",
      "horizon_months": 9,
      "affects": 4
    }
  ],
  "promotable_count": 3,
  "critical_gap_count": 5
}"""
p = tf.paragraphs[0]
p.text = out_text
p.font.size = Pt(10)
p.font.name = "Consolas"
p.font.color.rgb = WHITE


# ════════════════════════════════════════════════════════════════════
# SLIDE 10 — Full request trace: user question → JSON response
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "Full Request Trace",
           "One user question walked through every layer")

# 7 vertical steps
steps = [
    ("HOD asks",
     '"Which of my principals in PCSB-DR Drilling\nstill have critical gaps?"',
     PALE_PURPLE, PURPLE),
    ("Chat parser extracts",
     "business=Upstream, opu=PCSB-DR, division=Drilling,\nquestion_type=critical_gaps, filter=assessment_level:Principal",
     PALE_BLUE, PRIMARY_BLUE),
    ("API routes",
     "POST /team/analyze  →  RecommendationEngine.run()",
     LIGHT_BLUE, PRIMARY_BLUE),
    ("Engine — scope filter",
     "HRIS⋈TPCP left-join; keep rows where business/opu/division match\n→ 47 candidates",
     PALE_RED, RED),
    ("Engine — per-person scoring",
     "Compute 6 health scores for each of 47 employees",
     LIGHT_BLUE, PRIMARY_BLUE),
    ("Engine — analysis",
     "Filter: assessment_level=Principal AND combined < 0.6\n→ 5 flagged individuals with gap lists",
     YELLOW_BG, AMBER),
    ("Engine returns JSON; conversation layer narrates",
     '{"flagged":[...]} → "5 of your 12 principals fall below 0.6. Top gaps: k3, p2, e1."',
     PALE_GREEN, GREEN),
]

y = Inches(1.5)
step_h = Inches(0.75)
for i, (t, d, c, b) in enumerate(steps):
    yi = y + i * (step_h + Inches(0.08))
    # Step number
    add_shape(slide, Inches(0.5), yi, Inches(0.7), step_h, b, b, shape=MSO_SHAPE.OVAL)
    add_text(slide, Inches(0.5), yi + Inches(0.2), Inches(0.7), Inches(0.4),
             str(i + 1), size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    # Step content
    add_shape(slide, Inches(1.4), yi, Inches(11.4), step_h, c, b)
    add_text(slide, Inches(1.6), yi + Inches(0.08), Inches(3.5), Inches(0.3),
             t, size=12, bold=True, color=DARK_BLUE)
    add_text(slide, Inches(1.6), yi + Inches(0.38), Inches(11), Inches(0.38),
             d, size=11, color=DARK_BLUE, font="Consolas")


# ════════════════════════════════════════════════════════════════════
# SLIDE 11 — Summary
# ════════════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide, WHITE)
add_header(slide, "Summary — Architecture & Scoring Flow")

summary = [
    "• 5-layer architecture: Presentation → Conversation → API → Engine → Data",
    "• Engine consumes 2 files (HRIS + TPCP), left-joined on dummy_id",
    "• Engine pipeline: scope filter → per-person scoring → analysis → insight triage",
    "• 6 health scores per employee — all deterministic, all in 0–1 range",
    "• 3 parallel analyses answer different question types (team / gaps / individuals)",
    "• Insight engine applies explicit rules to emit structured actions",
    "• Engine emits PURE JSON; conversation layer handles the narrative framing",
    "• Every output is traceable back to raw HRIS and TPCP fields",
]
add_bullets(slide, Inches(0.8), Inches(1.8), Inches(11.8), Inches(5.2), summary, size=16)

add_shape(slide, Inches(0.6), Inches(6.5), Inches(12.2), Inches(0.7), PALE_BLUE, PRIMARY_BLUE)
add_text(slide, Inches(0.8), Inches(6.6), Inches(11.8), Inches(0.5),
         "Rule-based · Deterministic · Explainable · No labeled data needed · Conversation-ready JSON",
         size=13, bold=True, color=PRIMARY_BLUE, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════
# SAVE
# ════════════════════════════════════════════════════════════════════
prs.save(str(OUTPUT_FILE))
print(f"Presentation saved to: {OUTPUT_FILE}")
print(f"Total slides: {len(prs.slides)}")
