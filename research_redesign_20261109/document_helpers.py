from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
WIDTH=6.5
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
