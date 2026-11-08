"""Create report tables and equation images from the reproducible outputs."""
from pathlib import Path
import json
import re
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/report'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ROOT / 'artifacts/fixed_depth/fixed_depth_eci_profiles.csv')
    tables = {}
    labels = {'stock_0_30_tC_ha':'SOC储量 tC/ha', 'SOC_0_30_g_kg_thickness_mean':'SOC含量 g/kg',
              'NDVI':'NDVI', 'MAP':'MAP源值 单位待核', 'AI':'AI', 'eci_entropy':'ECI熵权得分'}
    rows = []
    for col, label in labels.items():
        s = d[col]
        rows.append([label] + [f'{v:.2f}' for v in [s.mean(), s.median(), s.quantile(.25), s.quantile(.75), s.min(), s.max()]])
    tables['descriptive'] = {'caption':'表1 共同样本描述统计 n=89', 'headers':['指标','均值','中位数','Q1','Q3','最小','最大'],
                              'rows':rows,'widths':[1.9,.74,.74,.74,.74,.74,.74]}
    w = pd.read_csv(ROOT / 'artifacts/fixed_depth/weights.csv')
    tables['weights'] = {'caption':'表2 三种赋权的指标权重','headers':['指标','等权','熵权','PCA'],
                         'rows':[[labels[r.indicator],f'{r.equal:.3f}',f'{r.entropy:.3f}',f'{r.pca:.3f}'] for r in w.itertuples()],
                         'widths':[3.5,.9,.9,.9]}
    sen = pd.read_csv(ROOT / 'artifacts/fixed_depth/sensitivity.csv')
    rows = []
    for r in sen.itertuples():
        label = '删除指标 '+labels[r.omitted] if r.analysis=='leave_one_indicator_out' else '删除来源 '+r.omitted
        rows.append([label,str(r.n),f'{r.spearman_vs_five_indicator_entropy:.3f}'])
    tables['sensitivity'] = {'caption':'表3 指标与来源删除的排序敏感性','headers':['删除内容','剩余样本','秩相关'],
                             'rows':rows,'widths':[4.2,1,1]}
    meta = pd.read_csv(ROOT / 'artifacts/audit/meta_reanalysis.csv')
    rows=[]
    for r in meta.itertuples():
        scope = '含耕作组合' if r.subset=='all_tillage_containing' else '仅tillage编码'
        method = '观测级DL' if r.analysis=='observation_level_DL_exploratory' else f'研究级修正HK rho={r.assumed_rho:g}'
        rows.append([scope,method,str(r.k),f'{r.effect_pct:.2f}',f'{r.ci_low_pct:.2f}至{r.ci_high_pct:.2f}'])
    tables['meta']={'caption':'表4 探索性Meta与依赖敏感性 变化单位为百分比','headers':['范围','合并方法','单元数','估计 %','95%区间 %'],
                    'rows':rows,'widths':[1.25,2.15,.65,.8,1.45]}
    tables['assumptions']={'caption':'表5 收益模型的假设参数 全部用于情景分析','headers':['参数','取值','含义'],
        'rows':[['面积A','1、10、100、1000 ha','经营聚合规模假设'],['年增碳率q','0.1、0.3、0.5 tC/ha/年','独立假设，不从ECI推导'],
                ['价格P','50、100、150元/tCO₂','假设价格，不是预测'],['新增作业成本c','0、100、300元/ha/年','相对基线的成本假设'],
                ['缓冲扣减b','20%','非指定方法学固定值'],['农户分成s','70%','未实际签署的分成假设'],
                ['变动核查成本v','20元/ha/年','假设成本'],['固定核查成本F','1000元/年','假设成本']], 'widths':[1.5,2.15,2.65]}
    a=pd.read_csv(ROOT / 'artifacts/asset_scenarios/cashflow_scenarios.csv')
    a=a[a.area_ha.eq(100)&a.assumed_farm_cost_yuan_ha_yr.eq(100)]
    tables['cashflow_grid']={'caption':'表6 100公顷情景下农户净收益 元/ha/年','headers':['年增碳 tC/ha','价格50','价格100','价格150'],
        'rows':[[f'{q:.1f}']+[f'{a[a.assumed_gain_tC_ha_yr.eq(q)&a.assumed_price_yuan_tCO2.eq(p)].iloc[0].farmer_net_yuan_ha_yr:.2f}' for p in [50,100,150]] for q in [.1,.3,.5]],
        'widths':[2,1.4,1.4,1.4]}
    cards=pd.read_csv(ROOT / 'artifacts/asset_scenarios/sample_state_cards.csv')
    tables['cards']={'caption':'表7 实际公开样点的状态卡 非权属证明或核证资产','headers':['样点ID','纬度 N','经度 E','年份','ECI','SOC tC/ha'],
        'rows':[[str(r.profile_id),f'{r.latitude:.4f}',f'{r.longitude:.4f}',str(r.Year),f'{r.eci_entropy:.2f}',f'{r.stock_0_30_tC_ha:.2f}'] for r in cards.itertuples()],
        'widths':[.9,1.2,1.2,.8,1,1.1]}
    (OUT/'tables.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2))
    source=(ROOT/'docs/研究报告.md').read_text()
    equations=re.findall(r'^\$\$(.*?)\$\$$',source,re.MULTILINE)
    manifest=[]
    plt.rcParams.update({'mathtext.fontset':'stix','font.family':'STIXGeneral'})
    for i,latex in enumerate(equations,1):
        fig=plt.figure(figsize=(10,1.2));fig.text(.02,.4,'$'+latex+'$',fontsize=17)
        path=OUT/f'equation_{i:02}.png'
        fig.savefig(path,dpi=260,bbox_inches='tight',pad_inches=.08,transparent=False,facecolor='white');plt.close(fig)
        manifest.append({'index':i,'latex':latex,'path':path.name})
    (OUT/'equations.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print('Prepared',len(tables),'tables and',len(equations),'equations')


if __name__=='__main__':main()
