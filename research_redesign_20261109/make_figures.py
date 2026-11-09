"""Publication figures from reported treatment means; no synthetic observations."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
ROOT=Path(__file__).resolve().parent
R=json.loads((ROOT/'results/results.json').read_text())
A=json.loads((ROOT/'results/agsy2024_results.json').read_text())
font_manager.fontManager.addfont('/System/Library/Fonts/Supplemental/Songti.ttc')
plt.rcParams.update({'font.family':'Songti SC','font.size':11,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','savefig.facecolor':'white'})
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
GREEN='#236447';BLUE='#346c9b';ORANGE='#b86c2e';GREY='#727e83'
def save(fig,name):
 fig.savefig(OUT/(name+'.png'),dpi=240,bbox_inches='tight')
 fig.savefig(OUT/(name+'.svg'),bbox_inches='tight');plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(10.2,4.2),gridspec_kw={'width_ratios':[1,1.2]})
for j,(ax,study,lab) in enumerate(zip(axs,['liang2021','chen2021'],['公主岭','海伦'])):
 rs=[x for x in R['index'] if x['study']==study]
 labels=[x['treatment']+'/'+x['control'] for x in rs]
 for k,(field,marker,color,label) in enumerate([('carbon_concentration_response','o',GREEN,'有机碳浓度响应'),('aggregate_response','s',BLUE,'水稳性团聚体响应'),('index','D',ORANGE,'综合指数')]):
  ax.scatter([x[field] for x in rs],[i+(k-1)*.19 for i in range(len(rs))],marker=marker,c=color,s=45,label=label)
 ax.set_yticks(range(len(rs)),labels);ax.invert_yaxis();ax.axvline(100,color=GREY,lw=1,ls='--');ax.set_xlabel('相对响应  对照 = 100');ax.set_title(lab+'  0-30 cm',loc='left');ax.grid(axis='x',alpha=.18)
axs[0].legend(loc='center left',fontsize=9)
fig.tight_layout(w_pad=2);save(fig,'01_soil_components')

fig,axs=plt.subplots(1,2,figsize=(10.2,4))
ss=[x for x in R['sensitivity'] if x['study']=='liang2021' and x['treatment']=='SM']
for depth,col in zip([10,20,30,40],[GREEN,BLUE,ORANGE,GREY]):
 rs=[x for x in ss if x['depth_cm']==depth]
 axs[0].plot([x['carbon_weight'] for x in rs],[x['index'] for x in rs],marker='o',label=f'0-{depth} cm',color=col)
axs[0].set(xlabel='有机碳功能权重',ylabel='综合指数  对照 = 100',title='公主岭覆盖免耕的权重与深度敏感性');axs[0].legend(fontsize=9);axs[0].grid(alpha=.15)
r=next(x for x in R['index'] if x['study']=='liang2021' and x['treatment']=='SM')
for field,color,label in [('soc_ratio',GREEN,'有机碳浓度'),('mwd_ratio',BLUE,'水稳性团聚体')]:
 axs[1].plot([100*(x[field]-1) for x in r['layers']],range(len(r['layers'])),marker='o',color=color,label=label)
axs[1].set_yticks(range(len(r['layers'])),[f'{x["depth_cm"][0]}-{x["depth_cm"][1]} cm' for x in r['layers']]);axs[1].invert_yaxis();axs[1].axvline(0,color=GREY,ls='--');axs[1].set_xlabel('相对对照变化 %');axs[1].set_title('综合改善仍可能包含局部下降',loc='left');axs[1].legend(fontsize=9);axs[1].grid(alpha=.15)
fig.tight_layout(w_pad=2);save(fig,'02_depth_weight_sensitivity')

fig,axs=plt.subplots(1,2,figsize=(10.2,4))
for ax,pair,title in zip(axs,[('NT','CT'),('NT','MP')],['整套措施比较  NT 对 CT','同样还田下比较耕作  NT 对 MP']):
 rs=[x for x in A['contrasts'] if (x['treatment'],x['control'])==pair]
 for i,x in enumerate(rs):
  ax.bar(i-.14,x['margin_delta_table6_yuan_mu'],width=.28,color=GREEN,label='表6毛利差' if i==0 else None)
  ax.bar(i+.14,x['margin_delta_table5_yuan_mu'],width=.28,color=BLUE,alpha=.7,label='表5收支复算' if i==0 else None)
  ax.text(i-.14,x['margin_delta_table6_yuan_mu']+1.4,f'{x["margin_delta_table6_yuan_mu"]:.2f}',ha='center',fontsize=10)
  if i==0:ax.text(i+.14,x['margin_delta_table5_yuan_mu']+1.4,f'{x["margin_delta_table5_yuan_mu"]:.2f}',ha='center',fontsize=10)
 ax.set_xticks(range(2),['2020','2021']);ax.set_ylim(0,100);ax.set_ylabel('材料毛利差  元/亩/年');ax.set_title(title,loc='left');ax.grid(axis='y',alpha=.15)
axs[1].legend(fontsize=9);fig.tight_layout(w_pad=2);save(fig,'03_margin_controls')

fig,axs=plt.subplots(1,2,figsize=(10.2,4))
rs=[x for x in A['contrasts'] if x['treatment']=='NT' and x['control']=='CT']
axs[0].bar(['2020','2021'],[x['avoided_input_ghg_kgCO2e_ha']/15 for x in rs],color=GREY,label='投入端柴油减少')
axs[0].bar(['2020','2021'],[x['avoided_soil_nonCO2_ghg_kgCO2e_ha']/15 for x in rs],bottom=[x['avoided_input_ghg_kgCO2e_ha']/15 for x in rs],color=GREEN,label='生长季土壤 CH$_4$ 与 N$_2$O')
for i,x in enumerate(rs):axs[0].text(i,x['avoided_total_kgCO2e_mu']+1,f'{x["avoided_total_kgCO2e_mu"]:.2f}',ha='center')
axs[0].set_ylim(0,70);axs[0].set_ylabel('减少排放  kg CO$_2$e/亩');axs[0].set_title('长春减排的来源  NT 对 CT',loc='left');axs[0].legend(fontsize=9)
soil=[x for x in A['soil_contrasts'] if x['metric']=='SOC']
axs[1].bar([x['treatment']+'/'+x['control'] for x in soil],[x['response_pct'] for x in soil],color=[GREEN,ORANGE,BLUE])
for i,x in enumerate(soil):axs[1].text(i,x['response_pct']+.45,f'{x["response_pct"]:.2f}%\n'+('显著' if x['source_letters_differ'] else '不显著'),ha='center',fontsize=10)
axs[1].set_ylim(0,17);axs[1].set_ylabel('有机碳浓度变化 %');axs[1].set_title('2020年 0-20 cm 浓度的不同对照',loc='left')
for ax in axs:ax.grid(axis='y',alpha=.15)
fig.tight_layout(w_pad=2);save(fig,'04_climate_and_soc')
# Formula PNGs are static display equations, separate from observations.
formulas={
'eq_index':r'I_H=100\exp\left\{\sum_l\frac{h_l}{H}\left[\alpha\ln\frac{C_{T,l}}{C_{C,l}}+(1-\alpha)\ln\frac{A_{T,l}}{A_{C,l}}\right]\right\}',
'eq_carbon':r'q=\frac{(S_{T,1}-S_{T,0})-(S_{C,1}-S_{C,0})}{\Delta t}\times\frac{44}{12}\times\frac{1}{15},\qquad V=qP',
'eq_subsidy':r'S_{\mathrm{gap}}=\max\{0,\ U-\Delta M\}',
'eq_margin':r'\Delta M=(G_T-K_T)-(G_C-K_C)'
}
for name,latex in formulas.items():
 fig=plt.figure(figsize=(10.2,1.15));fig.text(.01,.45,'$'+latex+'$',fontsize=19);fig.savefig(OUT/(name+'.png'),dpi=260,bbox_inches='tight',pad_inches=.04);plt.close(fig)
(OUT/'equations.json').write_text(json.dumps(formulas,indent=2))
print('4 figures PNG/SVG and 4 display equations generated from computed results')
