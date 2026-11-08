"""Build the first manuscript in the bundled document environment."""
from pathlib import Path
import json,re
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from build_research_report import font,add_table,picture
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'output/docx'

def main():
 source=(ROOT/'docs/论文初稿.md').read_text();lines=source.splitlines()
 tables=json.loads((ROOT/'artifacts/paper/tables.json').read_text())
 formulas=json.loads((ROOT/'artifacts/paper/equations.json').read_text())
 doc=Document();sec=doc.sections[0];sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
 sec.top_margin=sec.bottom_margin=Inches(.78);sec.left_margin=sec.right_margin=Inches(1)
 sec.footer_distance=Inches(.32)
 for el in list(doc.styles.element.iter(qn('w:pBdr'))):el.getparent().remove(el)
 for name in ['Normal','Title','Heading 1','Heading 2','Caption']:
  st=doc.styles[name];st.font.name='Songti SC';st.font.color.rgb=RGBColor(0,0,0)
  rf=st.element.get_or_add_rPr().rFonts;rf.set(qn('w:eastAsia'),'Songti SC')
  for a in list(rf.attrib):
   if a.endswith('Theme'):del rf.attrib[a]
  for el in st.element.iter(qn('w:color')):
   for a in list(el.attrib):
    if 'theme' in a.lower():del el.attrib[a]
  st.paragraph_format.first_line_indent=Pt(0);st.paragraph_format.line_spacing=Pt(20)
  st.paragraph_format.space_after=Pt(7)
 normal=doc.styles['Normal'];normal.font.size=Pt(11);normal.paragraph_format.first_line_indent=Pt(22)
 normal.paragraph_format.line_spacing=Pt(18);normal.paragraph_format.widow_control=True
 for name,size in [('Title',20),('Heading 1',14),('Heading 2',12)]:
  st=doc.styles[name];st.font.size=Pt(size);st.font.bold=True
  st.paragraph_format.line_spacing=Pt(30 if name=='Title' else 23)
  st.paragraph_format.space_before=Pt(12);st.paragraph_format.keep_with_next=True
 doc.styles['Caption'].font.size=Pt(9.5)
 doc.styles['Caption'].paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER
 footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
 field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
 first_heading=next(i for i,l in enumerate(lines) if l.startswith('## '))
 for i,line in enumerate(lines):
  line=line.strip()
  if not line:continue
  if i==0:
   p=doc.add_paragraph(line[2:],style='Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
  elif i<first_heading:
   p=doc.add_paragraph(line);p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Pt(0)
  elif line.startswith('## '):doc.add_paragraph(line[3:],style='Heading 1')
  elif line.startswith('### '):doc.add_paragraph(line[4:],style='Heading 2')
  elif line.startswith('{{EQ:'):
   i=int(line[5:-2]);picture(doc,ROOT/f'artifacts/paper/equation_{i}.png',equation=True,alt=formulas[i-1])
  elif line.startswith('{{TABLE:'):add_table(doc,tables[line[8:-2]])
  elif line.startswith('{{FIG:'):
   path,caption=line[6:-2].split('|',1);picture(doc,ROOT/'artifacts'/path,caption=caption,alt=caption)
  else:
   p=doc.add_paragraph(line)
   if re.match(r'^\[\d+\]',line):
    p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=Pt(14)
    for r in p.runs:font(r,9.5)
 target=OUT/'东北黑土区农田生态状态评价的稳健性与收益约束_论文初稿.docx'
 doc.save(target)
 print(target);print('Han characters',len(re.findall(r'[\u4e00-\u9fff]',source)))

if __name__=='__main__':main()
