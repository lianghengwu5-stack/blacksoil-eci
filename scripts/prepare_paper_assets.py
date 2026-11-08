from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/paper';OUT.mkdir(parents=True,exist_ok=True)
formulas=[r'$S_i=10\sum_l s_{il}\,\frac{h_{il}}{d_{il}-u_{il}}$']
plt.rcParams['mathtext.fontset']='stix'
for i,formula in enumerate(formulas,1):
 fig=plt.figure(figsize=(7.5,.55));fig.text(.5,.5,formula,ha='center',va='center',fontsize=19)
 fig.savefig(OUT/f'equation_{i}.png',dpi=260,bbox_inches='tight',pad_inches=.06);plt.close(fig)
(OUT/'equations.json').write_text(json.dumps(formulas))
report=json.loads((ROOT/'artifacts/report/tables.json').read_text())
(OUT/'tables.json').write_text(json.dumps({k:report[k] for k in ['carbon_summary','grid_summary']},ensure_ascii=False,indent=2))
