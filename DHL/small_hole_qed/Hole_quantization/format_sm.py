# -*- coding: utf-8 -*-
"""Post-process Supplemental_Material.docx: fonts and paragraph formatting only.
Do NOT touch OMML math elements — pandoc generates them correctly."""
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn

INPUT  = r'z:\tmp\Supplemental_Material.docx'
OUTPUT = r'z:\321\DHL\Self_Learning\DHL\small_hole_qed\Hole_quantization\Supplemental_Material_v3.docx'

doc = Document(INPUT)

# ── Default style: 小四 = 12pt, Times New Roman + 宋体 ──
style = doc.styles['Normal']
style.font.name = 'Times New Roman'
style.font.size = Pt(12)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
pf = style.paragraph_format
pf.space_after = Pt(4)
pf.line_spacing = 1.25

# ── Heading styles: 黑体 ──
for lvl, (sz, east) in enumerate([(14, '黑体'), (13, '黑体'), (12, '黑体')], 1):
    hs = doc.styles[f'Heading {lvl}']
    hs.font.name = 'Times New Roman'
    hs.font.size = Pt(sz)
    hs.font.bold = True
    hs.font.color.rgb = None
    hs.element.rPr.rFonts.set(qn('w:eastAsia'), east)
    hs.paragraph_format.space_before = Pt(14)
    hs.paragraph_format.space_after = Pt(4)

# ── Body paragraphs: indent, font ──
for p in doc.paragraphs:
    if p.style.name.startswith('Heading'):
        continue
    if not p.text.strip():
        continue
    # Equation paragraph: mostly math, short text → center
    from docx.oxml.ns import qn as _qn
    has_math = p._element.findall('.//' + _qn('m:oMath'))
    plain_text = p.text or ''
    if has_math and len(plain_text.strip()) < 40:
        p.alignment = 1  # CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        continue
    # Body text
    p.paragraph_format.first_line_indent = Cm(0.74)
    for run in p.runs:
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

# ── DO NOT touch m:rPr / m:sty — leave pandoc's OMML intact ──

doc.save(OUTPUT)
print(f'Saved to: {OUTPUT}')
