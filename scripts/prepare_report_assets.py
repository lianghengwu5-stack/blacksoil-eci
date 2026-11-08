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
    carbon=pd.read_csv(ROOT/'artifacts/reassessment/stock_summary.csv')
    group_names={'all_carbon_eligible':'全部碳样本','source_label_direct_only':'目标层全为direct','Liu et al., 2022':'Liu来源','Zhang et al., 2022':'Zhang来源'}
    rows=[]
    for r in carbon.itertuples():
        if r.group in group_names:rows.append([group_names[r.group],str(r.n),f'{r.median:.2f}',f'{r.mean:.2f}',f'{r.q25:.2f}—{r.q75:.2f}'])
    tables['carbon_summary']={'caption':'表1 碳储量描述统计 单位tC/ha','headers':['范围','剖面数','中位数','均值','四分位区间'],'rows':rows,'widths':[1.8,.7,.9,.9,1.7]}
    grid=pd.read_csv(ROOT/'artifacts/reassessment/spatial_grid_sensitivity.csv')
    tables['grid_summary']={'caption':'表2 已采样网格等权敏感性 非区域面积加权估计','headers':['网格边长 km','占用网格数','单格最多剖面','网格等权均值 tC/ha'],'rows':[[str(r.grid_km),str(r.occupied_cells),str(r.largest_cell_n),f'{r.equal_cell_mean_stock:.2f}'] for r in grid.itertuples()],'widths':[1.4,1.2,1.4,2]}
    tables['meta']['caption']='表3 探索性Meta与依赖敏感性 变化单位为百分比'
    tables['weights']['caption']='表A1 历史候选ECI三种赋权的指标权重'
    tables['sensitivity']['caption']='表A2 历史候选ECI指标与来源删除的排序敏感性'
    tables.pop('descriptive',None)
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
