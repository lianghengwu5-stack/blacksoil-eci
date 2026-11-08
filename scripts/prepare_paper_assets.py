from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/paper';OUT.mkdir(parents=True,exist_ok=True)
formulas=[r'$S_i=10\sum_l s_{il}\,\frac{h_{il}}{d_{il}-u_{il}}$',
 r'$\mathrm{ECI}_i=100\sum_{j=1}^{5}w_j z_{ij},\qquad \sum_{j=1}^{5}w_j=1$',
 r'$Q=Aq\,\frac{44}{12}(1-b),\qquad C_{\mathrm{MRV}}=Av+F$',
 r'$R=\max(PQ-C_{\mathrm{MRV}},0),\qquad Y=sR-Ac$',
 r'$P^{*}=\frac{Av+F+Ac/s}{Aq(44/12)(1-b)}$']
plt.rcParams['mathtext.fontset']='stix'
for i,formula in enumerate(formulas,1):
 fig=plt.figure(figsize=(7.5,.55));fig.text(.5,.5,formula,ha='center',va='center',fontsize=19)
 fig.savefig(OUT/f'equation_{i}.png',dpi=260,bbox_inches='tight',pad_inches=.06);plt.close(fig)
(OUT/'equations.json').write_text(json.dumps(formulas))
tables={
'paper_parameters':{'caption':'表1 现金流基准假设及108组情景的组合范围','headers':['参数','基准值','组合范围或处理'], 'widths':[2.4,1.7,3.2], 'rows':[
['经营面积A','100 ha','1、10、100、1000 ha'],['年增碳率q','0.3 tC/ha/年','0.1、0.3、0.5 tC/ha/年'],['价格P','100元/tCO₂','50、100、150元/tCO₂'],['缓冲比例b','20%','固定'],['农户分成s','70%','扣核查费后分成'],['作业成本c','100元/ha/年','0、100、300元/ha/年'],['核查变动成本v','20元/ha/年','固定'],['核查固定成本F','1000元/年','固定']]},
'paper_sensitivity':{'caption':'表2 共同样本的ECI权重与排序敏感性','headers':['比较','样本量','Spearman相关'], 'widths':[4,1,2], 'rows':[
['三种赋权的最低相关','89','0.9766'],['删SOC含量，重估熵权','89','0.9740'],['删SOC储量，重估熵权','89','0.9757'],['删NDVI，重估熵权','89','0.9990'],['删MAP，重估熵权','89','0.9764'],['删AI，重估熵权','89','0.9715'],['删Liu et al., 2022来源，重新校准','14','0.8681'],['删Zhang et al., 2022来源，重新校准','75','0.9994']]}}
(OUT/'tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2))
