"""Author the editable research report from the evidence-linked Markdown master.

Run with the bundled document runtime. Equations and analysis tables are prepared
separately by prepare_report_assets.py in the scientific environment.
"""
from pathlib import Path
import json
import re
from PIL import Image
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'output/revision_20261109'
WIDTH=6.27


def font(run,size=None,bold=None):
    run.font.name='Songti SC'
    rpr=run._element.get_or_add_rPr()
    rf=rpr.rFonts
    if rf is None:rf=OxmlElement('w:rFonts');rpr.insert(0,rf)
    for attr in ['ascii','hAnsi','eastAsia','cs']:rf.set(qn('w:'+attr),'Songti SC')
    run.font.color.rgb=RGBColor(0,0,0)
    if size:run.font.size=Pt(size)
    if bold is not None:run.bold=bold


def add_table(doc,item):
    cap=doc.add_paragraph(item['caption'],style='Caption');cap.paragraph_format.keep_with_next=True
    table=doc.add_table(rows=1,cols=len(item['headers']))
    table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
    widths=[w/sum(item['widths'])*WIDTH for w in item['widths']]
    for col,width in zip(table.columns,widths):col.width=Inches(width)
    for j,(cell,text) in enumerate(zip(table.rows[0].cells,item['headers'])):
        cell.text=text;cell.width=Inches(widths[j])
    repeat=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in item['rows']:
        for j,(cell,text) in enumerate(zip(table.add_row().cells,row)):
            cell.text=str(text);cell.width=Inches(widths[j])
    props=table._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for tag in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+tag);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    props.append(borders)
    for i,row in enumerate(table.rows):
        cant=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(cant)
        for j,cell in enumerate(row.cells):
            cell.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
            tcpr=cell._tc.get_or_add_tcPr();margin=OxmlElement('w:tcMar')
            for side,value in [('top',90),('bottom',90),('left',85),('right',85)]:
                e=OxmlElement('w:'+side);e.set(qn('w:w'),str(value));e.set(qn('w:type'),'dxa');margin.append(e)
            tcpr.append(margin)
            if i==0:
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E9EEF0');tcpr.append(shade)
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next=(i < len(table.rows)-1)
                p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=Pt(13.5);p.paragraph_format.space_after=Pt(1)
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:font(run,9.5,i==0)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)


def picture(doc,path,caption=None,equation=False,alt=None):
    with Image.open(path) as image:w,h=image.size
    width=min(WIDTH,w/260) if equation else WIDTH
    if not equation:width=min(width,5.6 if h/w>.8 else WIDTH)
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Pt(0)
    p.paragraph_format.line_spacing=1.0
    p.paragraph_format.space_after=Pt(4);p.paragraph_format.keep_with_next=bool(caption)
    run=p.add_run();shape=run.add_picture(str(path),width=Inches(width))
    if alt:shape._inline.docPr.set('descr',alt)
    if caption:
        p=doc.add_paragraph(caption,style='Caption')
        p.paragraph_format.keep_with_next=False


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    text=(ROOT/'docs/研究报告.md').read_text().replace('\u2212','-')
    lines=text.splitlines();tables=json.loads((ROOT/'artifacts/report/tables.json').read_text())
    equations=json.loads((ROOT/'artifacts/report/equations.json').read_text())
    pages_file=ROOT/'artifacts/report/toc_pages.json'
    toc_pages=json.loads(pages_file.read_text()) if pages_file.exists() else {}
    doc=Document();sec=doc.sections[0]
    sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
    sec.top_margin=sec.bottom_margin=Inches(.85);sec.left_margin=sec.right_margin=Inches(1)
    sec.footer_distance=Inches(.35)
    for grid in sec._sectPr.findall(qn('w:docGrid')):sec._sectPr.remove(grid)
    for element in list(doc.styles.element.iter(qn('w:pBdr'))):element.getparent().remove(element)
    for element in doc.styles.element.iter(qn('w:rFonts')):
        for key in list(element.attrib):
            if key.endswith('Theme'):del element.attrib[key]
    for element in doc.styles.element.iter(qn('w:color')):
        for key in list(element.attrib):
            if 'theme' in key.lower():del element.attrib[key]
    for name in ['Normal','Title','Heading 1','Heading 2','Caption']:
        st=doc.styles[name];st.font.name='Songti SC';st.font.color.rgb=RGBColor(0,0,0)
        st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Songti SC')
    normal=doc.styles['Normal'];normal.font.size=Pt(12)
    normal.paragraph_format.line_spacing=Pt(20);normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.first_line_indent=Pt(24)
    normal.paragraph_format.widow_control=True
    for name,size in [('Heading 1',16),('Heading 2',13),('Title',24)]:
        st=doc.styles[name];st.font.size=Pt(size);st.font.bold=True
        st.paragraph_format.first_line_indent=Pt(0);st.paragraph_format.space_before=Pt(12);st.paragraph_format.space_after=Pt(10)
        st.paragraph_format.keep_with_next=True
        st.paragraph_format.line_spacing=Pt(32 if name=='Title' else 25 if name=='Heading 1' else 21)
    cap=doc.styles['Caption'];cap.font.size=Pt(10);cap.paragraph_format.first_line_indent=Pt(0)
    cap.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER;cap.paragraph_format.space_after=Pt(9)
    cap.paragraph_format.line_spacing=Pt(15)
    footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    footer.paragraph_format.first_line_indent=Pt(0)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE')
    fr=OxmlElement('w:r');rp=OxmlElement('w:rPr');sz=OxmlElement('w:sz');sz.set(qn('w:val'),'18');rp.append(sz);fr.append(rp)
    ft=OxmlElement('w:t');ft.text='1';fr.append(ft);field.append(fr);footer._p.append(field)
    sec.different_first_page_header_footer=True
    # The cover uses only verified project metadata; there are no invented IDs.
    p=doc.add_paragraph();p.paragraph_format.space_after=Pt(70)
    p=doc.add_paragraph(lines[0][2:].replace('与资产化','\n与资产化'),style='Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after=Pt(85)
    first_heading=next(i for i,line in enumerate(lines) if line.startswith('## '))
    for line in lines[1:first_heading]:
        if line.strip():
            p=doc.add_paragraph(line);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Pt(0)
            p.paragraph_format.space_after=Pt(14)
    doc.add_page_break()
    p=doc.add_paragraph('内容',style='Heading 1')
    headings=[line[3:] for line in lines if line.startswith('## ')]
    for heading in headings:
        p=doc.add_paragraph();p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=Pt(18);p.paragraph_format.space_after=Pt(7)
        tabs=p.paragraph_format.tab_stops
        from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
        tabs.add_tab_stop(Inches(WIDTH-.05),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
        p.add_run(heading+'\t'+str(toc_pages.get(heading,'')))
    doc.add_page_break()
    equation_index=0;first=True
    for line in lines[first_heading:]:
        line=line.strip()
        if not line:continue
        if line.startswith('## '):
            p=doc.add_paragraph(line[3:],style='Heading 1')
            if line[3:].startswith(('一 研究','参考文献','附录')):p.paragraph_format.page_break_before=True
            first=False
        elif line.startswith('### '):
            doc.add_paragraph(re.sub(r'^\d+\.\d+\s+','',line[4:]),style='Heading 2')
        elif line.startswith('$$'):
            eq=equations[equation_index];equation_index+=1
            picture(doc,ROOT/'artifacts/report'/eq['path'],equation=True,alt=eq['latex'])
        elif line.startswith('{{TABLE:'):
            add_table(doc,tables[line[len('{{TABLE:'):-2]])
        elif line.startswith('{{FIG:'):
            path,caption=line[len('{{FIG:'):-2].split('|',1)
            picture(doc,ROOT/'artifacts'/path,caption=caption,alt=caption)
        else:
            p=doc.add_paragraph(line)
            if re.match(r'^\[\d+\]',line):
                p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=Pt(15)
                for run in p.runs:font(run,10.5)
    settings=doc.settings.element
    update=OxmlElement('w:updateFields');update.set(qn('w:val'),'true');settings.append(update)
    target=OUT/'研究报告_修订稿.docx'
    doc.save(target)
    print(target)
    print('Body Chinese characters:',len(re.findall(r'[\u4e00-\u9fff]',text)))


if __name__=='__main__':main()
