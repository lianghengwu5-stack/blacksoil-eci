from pathlib import Path
import json,os
from decimal import Decimal,ROUND_HALF_UP
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle,Patch
from matplotlib.lines import Line2D
P=Path(__file__).resolve().parent
d={k:v['data'] for k,v in json.loads((P/'data/source_snapshot.json').read_text()).items()};a=json.loads((P/'data/analysis_results.json').read_text())
font=os.environ.get('GUOCHUANG_FONT','/System/Library/Fonts/Supplemental/Songti.ttc');font_manager.fontManager.addfont(font)
plt.rcParams.update({'font.family':font_manager.FontProperties(fname=font).get_name(),'font.size':12,'axes.titlesize':13,'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,'legend.frameon':False,'svg.fonttype':'path','savefig.facecolor':'white'})
G='#218477';B='#376F9E';O='#B87742';D='#6C7881';R='#B84D4B';colors=[D,G,O,B]
def save(fig,stem):
 for ext in ['png','svg']:fig.savefig(P/'figures'/f'{stem}.{ext}',dpi=300,bbox_inches='tight')
 plt.close(fig)
def head(fig,text,sub=''):
 fig.text(.035,.965,text,fontsize=18,weight='bold',va='top')
 if sub:fig.text(.035,.90,sub,fontsize=10.5,color=D,va='top')
def foot(fig,text):fig.text(.035,.025,text,fontsize=9.5,color=D,va='bottom')
def grid(ax):ax.grid(axis='y',lw=.5,color='#DCE2E3');ax.set_axisbelow(True)

fig,ax=plt.subplots(figsize=(10.5,4.4));ax.axis('off');ax.set(xlim=(0,10),ylim=(0,4));head(fig,'将生态评价连接到措施选择与农户参与')
columns=[(.1,'管理措施','还田频率与用量\n耕作和覆盖组合','长期试验'),(2.65,'生态与生产','土层与生育阶段\n地力短板和产量','水分观测及土壤调查'),(5.2,'经营表现','粮食收入与投入\n作业和组织成本','合作社及田间账户'),(7.75,'选择与支持','保护目标与现实备选\n采用条件和参与补差','目标规则及政策情景')]
for x,title,txt,source in columns:
 ax.text(x,2.95,title,fontsize=15,weight='bold',color=G);ax.plot([x,x+2],[2.67,2.67],lw=2,color=G)
 ax.text(x,2.1,txt,fontsize=12,linespacing=1.8,va='center');ax.text(x,1.15,source,fontsize=10.5,color=D)
 if x<7:ax.annotate('',(x+2.45,2.2),(x+2.1,2.2),arrowprops={'arrowstyle':'->','color':D,'lw':1.5})
ax.text(.1,.35,'区域主案例：梨树县     外部比较：东北多地点、不同作物与年度     评价输出：分项表现、短板、收益和补差',fontsize=10.5,color=D)
fig.subplots_adjust(top=.85,bottom=.08,left=.04,right=.98);save(fig,'F1_研究框架')

rr=d['yang']['records'];fig,axs=plt.subplots(1,2,figsize=(10.8,5.5));head(fig,'同量还田条件下比较实施频率与土层响应','梨树长期试验  |  2017年  |  4处理×4区组')
for indices,color,label in [([0,1],G,'低用量  年均2.5 t/ha'),([2,3],B,'高用量  年均5.0 t/ha')]:
 y=[rr[i]['yield_kg_ha_figure']/1000 for i in indices];axs[0].plot([0,1],y,'-o',color=color,lw=2,ms=7,label=label)
 for j,i in enumerate(indices):axs[0].annotate(f"{y[j]:.2f} {rr[i]['yield_letters']}",(j,y[j]),xytext=(-7,9 if i!=3 else -20),textcoords='offset points',fontsize=11)
axs[0].set(xticks=[0,1],xticklabels=['间隔还田 LF','每年还田 HF'],ylabel='玉米产量（t/ha）',ylim=(8.7,11.55),xlim=(-.25,1.25),title='A  连续实施的产量表现');axs[0].legend(loc='lower right',fontsize=9);grid(axs[0])
for r,c in zip(rr,colors):axs[1].errorbar(r['SOC_g_kg_layers'],[2.5,7.5,15],xerr=r['SOC_SE_layers'],fmt='-o',lw=1.4,capsize=3,color=c,label=r['treatment'])
axs[1].set(ylim=(18,-1),yticks=[2.5,7.5,15],yticklabels=['0—5','5—10','10—20'],xlabel='有机碳浓度（g/kg）',ylabel='土层（cm）',title='B  表层与下层的响应差异');axs[1].legend(ncol=2,fontsize=9)
fig.subplots_adjust(top=.77,bottom=.19,wspace=.36,left=.09,right=.98)
foot(fig,'Yang等（2022）表1与图1。左图为图形恢复均值及原显著性字母；右图为均值±SE。33/67为年均还田量比例。')
save(fig,'F2_还田频率与土层')

v=np.array([r['stages'] for r in a['water']]);fig,ax=plt.subplots(figsize=(10.4,5.5));head(fig,'水分适宜度的薄弱阶段随年份变化','梨树县 2014—2016年  |  0—40 cm按层厚加权  |  橙框标示该处理当年的最低阶段')
im=ax.imshow(v,vmin=0,vmax=100,cmap='YlGnBu',aspect='auto');ax.set_xticks(range(4),['播种—拔节','拔节—抽穗','抽穗—乳熟','乳熟—成熟']);ax.set_yticks(range(6),[f"{r['year']} {r['rain_type']}  "+('免耕覆盖' if r['treatment']=='NT' else '常规垄作') for r in a['water']]);ax.tick_params(length=0,pad=8)
for i in range(6):
 for j in range(4):ax.text(j,i,str(Decimal(str(v[i,j])).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP)),ha='center',va='center',color='white' if v[i,j]>65 else '#173C46',fontsize=13)
 ax.add_patch(Rectangle((np.argmin(v[i])-.48,i-.47),.96,.94,fill=False,edgecolor=O,lw=2.3))
for y in [1.5,3.5]:ax.axhline(y,color='white',lw=5)
for sp in ax.spines.values():sp.set_visible(False)
cb=fig.colorbar(im,ax=ax,fraction=.04,pad=.035);cb.set_label('阶段水分适宜度（%）');cb.outline.set_visible(False)
fig.subplots_adjust(top=.79,bottom=.18,left=.24,right=.91);foot(fig,'刘淑珍等（2020）表3重算。土层权重为0.125、0.125、0.25、0.50；6个处理年度均来自同一试验。');save(fig,'F3_水分阶段诊断')

bench=d['benchmark'];fig,axs=plt.subplots(1,2,figsize=(10.8,5.5));head(fig,'精简地力指标的解释度与监测规模比较','梨树62样点研究的公开拟合结果  |  R²为样本内统计量')
for k,c,label in [('TDS',D,'全部指标'),('IDS',O,'重要指标'),('MDS',G,'最小指标集')]:axs[0].plot(bench['depths_cm'],bench[k+'_R2'],'-o',label=label,color=c)
axs[0].set(xlabel='累计采样深度（cm）',ylabel='产量解释度 R²',ylim=(.25,.62),xticks=bench['depths_cm'],title='A  深度与指标组合');axs[0].legend(fontsize=9,loc='lower right');grid(axs[0])
for n,r2,label,c,offset in [(1,.654**2,'黑土层厚度',D,(8,-18)),(6,.56,'六项精简指数',G,(8,-3)),(29,.43,'0—30 cm全指标',B,(-110,14))]:
 axs[1].scatter(n,r2,s=95,color=c);axs[1].annotate(f'{label}\nR²={r2:.2f}',(n,r2),textcoords='offset points',xytext=offset,fontsize=10)
axs[1].set(xlabel='指标与土层组合的字段数',ylabel='产量解释度 R²',xlim=(-2,34),ylim=(.25,.62),xticks=[1,6,15,29],title='B  以简单指标为基准');grid(axs[1])
fig.subplots_adjust(top=.77,bottom=.2,left=.08,right=.97,wspace=.29);foot(fig,'Fang等（2023）表2、3、6及图3；黑土层厚度R²由r²换算。字段数用于表示监测规模，不等同于实际费用。');save(fig,'F4_指数基准与复杂度')

fig,axs=plt.subplots(1,2,figsize=(10.8,5.4),gridspec_kw={'width_ratios':[.9,1.25]});head(fig,'梨树经营增益中超过一半来自节本','2020年  |  元/亩/年  |  传统垄作与合作社秸秆覆盖条带旋耕模式')
groups=['CRT','SRTS'];x=np.arange(2);rev=[a['farm_totals'][g]['revenue'] for g in groups];cost=[a['farm_totals'][g]['cost'] for g in groups];bal=[a['farm_totals'][g]['balance'] for g in groups]
axs[0].bar(x,bal,color=[D,G],width=.48,label='经营结余');axs[0].bar(x,cost,bottom=bal,color='#CFD8DB',width=.48,label='已列成本')
for i in range(2):axs[0].text(i,bal[i]/2,f'{bal[i]:.2f}',ha='center',color='white',fontsize=11);axs[0].text(i,bal[i]+cost[i]/2,f'{cost[i]:.2f}',ha='center',fontsize=10)
axs[0].set(xticks=x,xticklabels=['传统模式','合作社模式'],ylabel='收入及分配（元/亩）',ylim=(0,2050),title='A  经营账户');axs[0].legend(fontsize=9,loc='upper left');grid(axs[0])
cum=0
for i,(label,value) in enumerate(a['components']):
 axs[1].bar(i,value,bottom=cum,color=O if i==0 else G,width=.62);axs[1].text(i,cum+value+4,f'+{value:.2f}',ha='center',fontsize=10);cum+=value
 if i<3:axs[1].plot([i+.31,i+.69],[cum,cum],color=D,lw=.8,ls=':')
axs[1].bar(4,cum,color=B,width=.62);axs[1].text(4,cum+4,f'{cum:.2f}',ha='center',fontsize=11)
axs[1].set(xticks=range(5),xticklabels=['粮食\n增收','机械\n节本','农资\n节本','人工\n节本','结余\n增量'],ylabel='增益贡献（元/亩）',ylim=(0,210),title='B  经营增益分解');grid(axs[1])
fig.subplots_adjust(top=.76,bottom=.20,left=.09,right=.98,wspace=.34);foot(fig,'Liao等（2022）表4复算；23合作社与23位相邻非成员农户。经营结余按原文列示成本计算，未含土地和补贴。');save(fig,'F5_梨树经营收益分解')

ec=d['economics']['changchun'];fig,ax=plt.subplots(figsize=(10.3,4.9));head(fig,'长春试验显示节本可以覆盖粮食收入的下降','同一研究内的两年三措施比较  |  按研究当年价格折算为元/亩/年')
for i,r in enumerate(ec):
 y=r['revenue_change'];c=r['cost_saving'];net=r['balance_change'];ax.barh(i,y,color=O,height=.48);ax.barh(i,c,left=max(y,0),color=G,height=.48);ax.plot(net,i,'D',color='#1F3840',ms=7);ax.annotate(f'{net:+.2f}',(net,i),xytext=(7,-15),textcoords='offset points',fontsize=11)
ax.set_yticks(range(4),[f"{r['year']}  NT − {r['reference']}" for r in ec]);ax.set_ylim(3.8,-.6);ax.set_xlim(-27,102);ax.axvline(0,color=D,lw=.8);ax.set_xlabel('相对参照的变化（元/亩/年）');ax.grid(axis='x',color='#DCE2E3',lw=.5);ax.set_axisbelow(True)
fig.legend(handles=[Patch(color=O,label='粮食收入变化'),Patch(color=G,label='成本节约'),Line2D([0],[0],marker='D',color='none',markerfacecolor='#1F3840',label='结余增量')],ncol=3,loc='upper left',bbox_to_anchor=(.18,.85),fontsize=10)
fig.subplots_adjust(top=.70,bottom=.23,left=.18,right=.97);foot(fig,'Zhang等（2024）表5重算。NT：免耕还田；CT：翻耕移除秸秆；MP：翻耕还田。');save(fig,'F6_长春收益机制比较')

fig,axs=plt.subplots(1,2,figsize=(10.8,5.4));head(fig,'综合评价需要同时保留目标偏好与分项短板')
ys=np.array([r['yield_kg_ha_figure'] for r in rr]);cs=np.array([r['SOC_Mg_ha_figure'] for r in rr]);weights=np.linspace(0,1,501)
for i,r in enumerate(rr):axs[0].plot(weights,100*(cs[i]/cs[0])**weights*(ys[i]/ys[0])**(1-weights),label=r['treatment'],color=colors[i],lw=1.8)
for sw in a['weight_switches']:axs[0].axvline(np.mean(sw['interval']),color=D,ls=':',lw=1)
axs[0].set(xlabel='碳储量权重 w',ylabel='聚合分值（LF33＝100）',title='A  偏好改变最高分措施');axs[0].legend(ncol=2,fontsize=9);grid(axs[0])
rows=d['rules']['rows'][4:];xx=np.arange(8)
axs[1].plot(xx,[r['geometric_score'] for r in rows],'-s',color=O,label='几何平均分');axs[1].plot(xx,[r['min_score'] for r in rows],'-o',color=B,label='最低分项分');axs[1].axhline(100,color=D,ls='--',lw=1);axs[1].set(xticks=xx,xticklabels=['ST\n30','ST\n60','ST\n150','ST\n360','SST\n30','SST\n60','SST\n150','SST\n360'],ylim=(85,130),ylabel='对照归一为100的分值',title='B  总分改善与局部短板可并存');axs[1].tick_params(axis='x',labelsize=8);axs[1].legend(fontsize=9,loc='upper right');grid(axs[1])
fig.subplots_adjust(top=.79,bottom=.22,left=.08,right=.98,wspace=.31);foot(fig,'A：梨树四处理均值的权重检验。B：Zhang等（2020）微区数据，数字为培养天数；100为不下降示例目标。');save(fig,'F7_聚合与短板检验')

fig,axs=plt.subplots(1,2,figsize=(10.8,5.5));head(fig,'采用边界连接产量变化与转型成本','以梨树2020年粮价2.30元/kg和节本96.60元/亩为参照  |  坐标为敏感性参数')
x=np.linspace(-100,80,181);y=np.linspace(0,320,161);X,Y=np.meshgrid(x,y);gap=np.maximum(0,Y-96.6-2.3*X)
im=axs[0].pcolormesh(X,Y,gap,cmap='YlGnBu',shading='auto',vmin=0,vmax=450);axs[0].contour(X,Y,96.6+2.3*X-Y,levels=[0],colors=[O],linewidths=1.6);axs[0].plot(33.333,0,'o',color=R,ms=7,clip_on=False);axs[0].annotate('观测账户锚点',(33.333,0),xytext=(-55,12),textcoords='offset points',fontsize=9)
axs[0].set(xlabel='相对参照的产量差（kg/亩）',ylabel='额外净增成本 K（元/亩）',title='A  收入补差需求');fig.colorbar(im,ax=axs[0],fraction=.05,pad=.025,label='元/亩')
for support,c in [(0,D),(80,B),(105,G)]:axs[1].plot(x,96.6+2.3*x+support,color=c,label=f'增量支持 {support} 元/亩',lw=2)
axs[1].set(xlabel='相对参照的产量差（kg/亩）',ylabel='可承担额外成本上限（元/亩）',title='B  支持情景下的采用边界',ylim=(-80,420));axs[1].axhline(0,color=D,lw=.7);axs[1].legend(fontsize=9);grid(axs[1])
fig.subplots_adjust(top=.77,bottom=.21,left=.09,right=.97,wspace=.43);foot(fig,'补差＝max(0，K−2.30ΔY−96.60)。80/105元为2026年吉林省政策条件上限参照，实际金额由当地方案确定。');save(fig,'F8_采用和补偿边界')

fig,axs=plt.subplots(1,3,figsize=(10.8,4.8),sharex=True,sharey=True);head(fig,'土壤指标改善与产量响应的联合比较')
for ax,key,title in zip(axs,['Li2024','Yan2020','You2017'],['李瑞平等2024\n有机质 SOM','闫雷等2020\n有机碳 SOC','You等2017\n棕壤参照 SOC']):
 rows=[r for r in d['pairs'] if r['study']==key]
 for year,c in zip(sorted({r['year'] for r in rows}),[G,O,B]):
  z=[r for r in rows if r['year']==year];ax.scatter([r['soil_pct'] for r in z],[r['yield_pct'] for r in z],color=c,s=45,label=str(year))
 ax.axhline(0,lw=.8,color=D);ax.axvline(0,lw=.8,color=D);ax.set(xlim=(-3,29),ylim=(-20,55),title=title,xlabel='0—20 cm浓度变化（%）');ax.legend(fontsize=8);grid(ax)
axs[0].set_ylabel('产量变化（%）');fig.subplots_adjust(top=.76,bottom=.19,left=.08,right=.98,wspace=.16);foot(fig,'21个同年处理—对照比较来自3个试验。SOC与SOM分别展示，保留共同对照与年度关联。');save(fig,'S1_土壤产量联合响应')

fig,ax=plt.subplots(figsize=(10.2,5.5));head(fig,'现实备选措施影响增产判断','同一免耕处理分别相对旋耕与深翻  |  2023年六地点')
for i,r in enumerate(d['baseline']):
 x1,x2=r['vs_RT_pct'],r['vs_DP_pct'];ax.plot([x1,x2],[i,i],color='#BAC8CD',lw=3);ax.scatter(x1,i,color=B,s=65);ax.scatter(x2,i,color=O,s=65,marker='s');ax.annotate(f'{x1:+.1f}%',(x1,i),xytext=(0,9),textcoords='offset points',ha='center',fontsize=10,color=B);ax.annotate(f'{x2:+.1f}%',(x2,i),xytext=(0,-17),textcoords='offset points',ha='center',fontsize=10,color=O)
ax.set(yticks=range(6),yticklabels=[r['site'] for r in d['baseline']],ylim=(5.6,-.7),xlabel='免耕相对产量变化（%）',xlim=(-17,16));ax.axvline(0,color=D,lw=1)
fig.legend(handles=[Line2D([0],[0],marker='o',color=B,label='相对旋耕'),Line2D([0],[0],marker='s',color=O,label='相对深翻')],loc='upper right',bbox_to_anchor=(.95,.90),ncol=2,fontsize=10)
fig.subplots_adjust(top=.75,bottom=.17,left=.12,right=.96);foot(fig,'Jiang等（2025）图5数字化提取。白城、赤峰和公主岭更换对照后，产量差方向改变。');save(fig,'S2_对照敏感性')

fig,axs=plt.subplots(1,2,figsize=(10.8,5.2));head(fig,'作物与现实备选共同影响经济选择')
for crop,c,label in [('maize',B,'玉米'),('soybean',G,'大豆')]:
 rows=[r for r in d['economics']['dehui'] if r['crop']==crop];axs[0].plot([r['year'] for r in rows],[r['NT_minus_RT'] for r in rows],'-o',color=c,label=f"{label}  均值{a['dehui_means'][crop]:+.1f}")
axs[0].set(xlabel='年份',ylabel='免耕相对垄作的结余变化（元/亩）',title='A  德惠轮作体系',xticks=[2002,2003,2004,2005,2006]);axs[0].legend(fontsize=9);axs[0].axhline(0,color=D,lw=.8);grid(axs[0])
for r in d['frontier']['options']:
 c=D if r['dominated'] else G;axs[1].scatter(r['modeled_GHG'],r['balance'],s=90,color=c);axs[1].annotate(r['treatment'],(r['modeled_GHG'],r['balance']),xytext=(7,6),textcoords='offset points')
axs[1].set(xlabel='模型排放（kg CO₂e/亩）',ylabel='经营结余（美元/亩）',title='B  桦川收益与排放前沿',xlim=(223,238),ylim=(237,269));grid(axs[1]);fig.subplots_adjust(top=.78,bottom=.21,left=.09,right=.97,wspace=.34);foot(fig,'张晓平等（2008）表6；Han等（2026）表3。两地分别沿用历史价格和原币种，ST为条带耕作、NT为免耕。');save(fig,'S3_年度与备选比较')

fig,axs=plt.subplots(1,2,figsize=(10.8,4.8));head(fig,'统一土层后的区域碳储量描述与来源结构')
for source,c in [('Liu et al., 2022',G),('Zhang et al., 2022',O)]:
 rows=[r for r in d['profiles'] if r['References']==source];axs[0].scatter([float(r['longitude']) for r in rows],[float(r['latitude']) for r in rows],s=24,color=c,label=f'{source}  n={len(rows)}',alpha=.8)
axs[0].set(xlabel='经度（°E）',ylabel='纬度（°N）',title='A  90个剖面的观测位置');axs[0].legend(fontsize=8)
stocks=np.array([float(r['stock_0_30_tC_ha']) for r in d['profiles']]);axs[1].hist(stocks,bins=np.arange(20,171,15),color=G,edgecolor='white');axs[1].axvline(np.median(stocks),color=O,lw=2,ls='--',label=f'中位数 {np.median(stocks):.2f}');axs[1].set(xlabel='0—30 cm碳储量（t C/ha）',ylabel='剖面数',title='B  储量分布');axs[1].legend(fontsize=10);grid(axs[1]);fig.subplots_adjust(top=.78,bottom=.2,left=.08,right=.98,wspace=.28);foot(fig,'中国SOC剖面库V10经黑土区边界与耕地筛选；来源标签沿原数据库。区域储量描述用于研究基础。');save(fig,'S4_前期碳核算')
assert len(list((P/'figures').glob('*.png')))==12
print('Exported 8 main figures and 4 supplementary figures, PNG and portable SVG.')
