"""Create a reading PDF from the phase-one evidence record."""
from pathlib import Path
from xml.sax.saxutils import escape
import re
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(__file__).resolve().parents[1]


def main():
    pdfmetrics.registerFont(TTFont('STSong-Light', '/System/Library/Fonts/Supplemental/Songti.ttc', subfontIndex=6))
    styles = {
        'title': ParagraphStyle('Title', fontName='STSong-Light', fontSize=20, leading=28, spaceAfter=18),
        'heading': ParagraphStyle('Heading', fontName='STSong-Light', fontSize=13, leading=20, spaceBefore=15, spaceAfter=7, keepWithNext=True),
        'body': ParagraphStyle('Body', fontName='STSong-Light', fontSize=10.5, leading=18, spaceAfter=8, wordWrap='CJK'),
        'table': ParagraphStyle('Table', fontName='STSong-Light', fontSize=8, leading=12, wordWrap='CJK'),
        'caption': ParagraphStyle('Caption', fontName='STSong-Light', fontSize=9, leading=14, alignment=TA_CENTER, spaceAfter=12),
    }
    def para(text, kind='body'):
        return Paragraph(escape(text.replace('\u2212', '-')), styles[kind])
    source = (ROOT / 'docs/第一阶段数据与结果核查.md').read_text()
    lines = source.splitlines()
    flow, i = [], 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = lines[i].strip().strip('|').split('|')
                if not all(re.fullmatch(r'\s*:?-+:?\s*', c) for c in cells):
                    # Make scope labels readable rather than exposing internal identifiers.
                    cells = [c.replace('all_landcovers', '全土地').replace('cropland', '农田').replace('v10_blacksoil', 'V10黑土区').replace('v10_typical', 'V10典型区') for c in cells]
                    rows.append([para(c, 'table') for c in cells])
                i += 1
            table = Table(rows, colWidths=[147, 75, 78, 80, 80], repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9eef0')),
                ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#d9d9d9')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
            flow.extend([table, Spacer(1, 10)])
            continue
        if line.startswith('# '):
            flow.append(para(line[2:], 'title'))
        elif line.startswith('## '):
            flow.append(para(line[3:], 'heading'))
        else:
            flow.append(para(line.removeprefix('- ')))
        i += 1
    flow += [PageBreak(), para('固定深度分析图件', 'heading')]
    for name, caption in [
        ('fig01_fixed_depth_distributions.png', '图1 共同样本ECI与0—30厘米SOC储量分布，n=89'),
        ('fig02_fixed_depth_weights.png', '图2 同一样本内的等权、熵权与PCA权重'),
        ('fig03_sample_locations.png', '图3 黑土区矢量边界与有效农田剖面点位')]:
        from PIL import Image as PILImage
        p = ROOT / 'artifacts/fixed_depth' / name
        with PILImage.open(p) as im:
            w, h = im.size
        flow += [Image(str(p), width=460, height=460*h/w), para(caption, 'caption'), Spacer(1, 10)]
    dest = ROOT.parent / 'output/pdf/第一阶段数据与结果核查.pdf'
    dest.parent.mkdir(parents=True, exist_ok=True)
    def footer(canvas, doc):
        canvas.setFont('STSong-Light', 9)
        canvas.drawCentredString(A4[0]/2, 28, str(doc.page))
    doc = SimpleDocTemplate(str(dest), pagesize=A4, leftMargin=50, rightMargin=50,
                            topMargin=48, bottomMargin=47, title='第一阶段数据与结果核查', author='黑土ECI项目组')
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(dest)


if __name__ == '__main__':
    main()
