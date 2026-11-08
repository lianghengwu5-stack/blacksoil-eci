"""Reassess carbon-stock evidence without using environmental covariates as gates.

Original inputs and the historical five-indicator results are retained. No causal
effect, regional total, annual sequestration rate or revenue is estimated here.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from pyproj import Transformer, Geod
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_results import ROOT, RAW, KEY, V10_COLUMNS, integrate_profile, polygon_subset

OUT = ROOT / 'artifacts/reassessment'


def save(frame, name):
    frame.to_csv(OUT / name, index=False, encoding='utf-8-sig')


def stock_summary(d, label):
    s = d.stock_0_30_tC_ha
    return dict(group=label, n=len(s), median=float(s.median()), mean=float(s.mean()),
                q25=float(s.quantile(.25)), q75=float(s.quantile(.75)),
                minimum=float(s.min()), maximum=float(s.max()))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW / 'source_metadata/SOCS_V10.csv', encoding='gb18030').rename(columns=V10_COLUMNS)
    inside = polygon_subset(raw, 'BlackSoilRegion')
    rows = []
    for key, g in inside.groupby(KEY, dropna=False):
        land = g.CLCD.dropna().unique()
        if len(land) != 1 or land[0] != 'Cropland':
            continue
        layers = g.loc[g.upper_dept < 30].copy()
        stock, status = integrate_profile(layers[['upper_dept', 'lower_dept', 'SOCD (kg/m2)']].to_numpy())
        row = dict(zip(KEY, key))
        row.update(status=status, stock_0_30_tC_ha=stock,
                   stock_method_mix=','.join(sorted(layers.SOCD_methods.dropna().unique())),
                   source_sample_ids=','.join(map(str, layers.Samples.astype(int))))
        # Record covariates, but do not let them determine carbon-stock eligibility.
        for col in ['NDVI', 'MAP', 'AI']:
            vals = g[col].dropna().unique()
            row[col] = vals[0] if len(vals) == 1 else np.nan
        if status == 'complete' and (layers['SOC (g/kg)'].notna() & (layers['SOC (g/kg)'] > 0)).all():
            thick = np.minimum(layers.lower_dept, 30) - layers.upper_dept
            row['SOC_0_30_g_kg_thickness_mean'] = float((layers['SOC (g/kg)'] * thick).sum()/30)
        row['partial_bottom_layer'] = bool((layers.lower_dept > 30).any())
        rows.append(row)
    selection = pd.DataFrame(rows)
    save(selection, 'carbon_profile_selection.csv')
    d = selection.loc[selection.status.eq('complete')].reset_index(drop=True)
    old = pd.read_csv(ROOT / 'artifacts/fixed_depth/fixed_depth_eci_profiles.csv')
    matched = d.merge(old[KEY + ['eci_entropy']], on=KEY, how='left', validate='one_to_one')
    matched['in_historical_eci_sample'] = matched.eci_entropy.notna()
    save(matched, 'carbon_profiles.csv')
    summaries = [stock_summary(d, 'all_carbon_eligible'),
                 stock_summary(d.loc[d.stock_method_mix.eq('direct')], 'source_label_direct_only'),
                 stock_summary(old, 'historical_eci_common_sample')]
    for ref, g in d.groupby('References'):
        summaries.append(stock_summary(g, ref))
    for method, g in d.groupby('stock_method_mix'):
        summaries.append(stock_summary(g, 'method=' + method))
    save(pd.DataFrame(summaries), 'stock_summary.csv')
    save(d.groupby(['References', 'Year', 'stock_method_mix']).size().reset_index(name='n'), 'source_year_method_counts.csv')

    # Equal-area diagnostic grids; not sampling weights and not area estimates.
    x, y = Transformer.from_crs(4326, 6933, always_xy=True).transform(d.longitude, d.latitude)
    grid_stats = []
    for km in [25, 50, 100]:
        g = d.copy()
        g['cell_x'] = np.floor(x/(km*1000)).astype(int)
        g['cell_y'] = np.floor(y/(km*1000)).astype(int)
        cells = g.groupby(['cell_x', 'cell_y']).agg(n=('profile_id','size'),
                    mean_stock=('stock_0_30_tC_ha','mean'), median_stock=('stock_0_30_tC_ha','median')).reset_index()
        save(cells, f'grid_{km}km.csv')
        grid_stats.append(dict(grid_km=km, occupied_cells=len(cells), largest_cell_n=int(cells.n.max()),
                               equal_cell_mean_stock=float(cells.mean_stock.mean())))
    save(pd.DataFrame(grid_stats), 'spatial_grid_sensitivity.csv')
    geod = Geod(ellps='WGS84')
    nn=[]
    for i, p in d.iterrows():
        _, _, dist = geod.inv(np.full(len(d),p.longitude), np.full(len(d),p.latitude),
                             d.longitude.to_numpy(), d.latitude.to_numpy())
        dist[i]=np.inf
        nn.append(float(np.min(dist)/1000))
    d['nearest_profile_km']=nn
    save(d[KEY+['nearest_profile_km']], 'nearest_neighbors.csv')

    rank = old[KEY+['stock_0_30_tC_ha','eci_entropy','NDVI','MAP','AI','SOC_0_30_g_kg_thickness_mean']].copy()
    rank['stock_rank'] = rank.stock_0_30_tC_ha.rank(ascending=False, method='average')
    rank['eci_rank'] = rank.eci_entropy.rank(ascending=False, method='average')
    rank['eci_minus_stock_rank'] = rank.eci_rank - rank.stock_rank
    save(rank.sort_values('eci_minus_stock_rank'), 'historical_eci_rank_changes.csv')
    correlations=[]
    for label, group in [('all_89',old), *list(old.groupby('References'))]:
        for col in ['eci_entropy','SOC_0_30_g_kg_thickness_mean','NDVI','MAP','AI']:
            correlations.append(dict(group=label,n=len(group),variable=col,
                                     spearman_stock=float(spearmanr(group.stock_0_30_tC_ha,group[col]).statistic),
                                     interpretation='descriptive association only; ECI contains stock'))
    save(pd.DataFrame(correlations), 'descriptive_correlations.csv')
    k = int(np.ceil(len(rank)/4))
    # Index tie-breaker is deterministic. Report top-k, not a universal ecological threshold.
    top_stock=set(rank.nlargest(k,'stock_0_30_tC_ha').index)
    top_eci=set(rank.nlargest(k,'eci_entropy').index)
    summary = dict(n_carbon_profiles=len(d),n_historical_eci=len(old),
        n_source_references=int(d.References.nunique()),n_unique_coordinates=len(d[['latitude','longitude']].drop_duplicates()),
        source_counts=d.References.value_counts().to_dict(),year_counts={str(k):int(v) for k,v in d.Year.value_counts().items()},
        method_counts=d.stock_method_mix.value_counts().to_dict(),
        n_partial_bottom_layer=int(d.partial_bottom_layer.sum()),
        latitude_range=[float(d.latitude.min()),float(d.latitude.max())],
        longitude_range=[float(d.longitude.min()),float(d.longitude.max())],
        nearest_neighbor_median_km=float(np.median(nn)),n_nearest_under_5km=int((np.array(nn)<5).sum()),
        stock_summary=summaries,grid_diagnostics=grid_stats,
        eci_vs_stock_rho=float(spearmanr(old.stock_0_30_tC_ha,old.eci_entropy).statistic),
        top_k=k,top_k_overlap=len(top_stock&top_eci),
        median_absolute_rank_change=float(rank.eci_minus_stock_rank.abs().median()),
        maximum_absolute_rank_change=float(rank.eci_minus_stock_rank.abs().max()),
        map_source_range=[float(old.MAP.min()),float(old.MAP.max())],
        decision='Carbon-stock description and evidence-quality assessment. Historical ECI is exploratory only; no environmental attribution model or revenue estimate.')
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))

    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig, axs=plt.subplots(1,2,figsize=(10,4.2))
    for color,(ref,g) in zip(['#256953','#b97b39'],d.groupby('References')):
        axs[0].scatter(g.longitude,g.latitude,s=27,alpha=.8,label=f'{ref} (n={len(g)})',color=color)
        axs[1].hist(g.stock_0_30_tC_ha,bins=np.arange(20,181,20),alpha=.65,label=ref,color=color)
    axs[0].set(xlabel='Longitude',ylabel='Latitude',title='Observed profiles by source')
    axs[0].legend(fontsize=8)
    axs[1].set(xlabel='0–30 cm SOC stock (t C/ha)',ylabel='Number of profiles',title='Sample distribution, not a regional estimate')
    fig.tight_layout();fig.savefig(OUT/'fig01_carbon_samples.png',dpi=190);plt.close(fig)
    fig, ax=plt.subplots(figsize=(6.3,4.3))
    for color,(ref,g) in zip(['#256953','#b97b39'],rank.groupby('References')):
        ax.scatter(g.stock_rank,g.eci_rank,label=ref,s=27,alpha=.8,color=color)
    ax.plot([1,len(rank)],[1,len(rank)],'--',color='#999999',lw=1)
    ax.set(xlabel='SOC stock rank (1 = highest)',ylabel='Historical ECI rank (1 = highest)',
           title='Ranking changes do not demonstrate ecological validity')
    ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'fig02_rank_comparison.png',dpi=190);plt.close(fig)
    inputs=[RAW/'source_metadata/SOCS_V10.csv',ROOT/'artifacts/fixed_depth/fixed_depth_eci_profiles.csv']
    checks=dict(historical_common_n_matches=int(matched.in_historical_eci_sample.sum())==len(old),
                unique_profile_keys=not d.duplicated(KEY).any(),
                historical_stocks_unchanged=bool(np.allclose(old.stock_0_30_tC_ha,
                    old[KEY].merge(d[KEY+['stock_0_30_tC_ha']],on=KEY,validate='one_to_one').stock_0_30_tC_ha,rtol=0,atol=1e-10)),
                nonnegative_stocks=bool((d.stock_0_30_tC_ha>=0).all()))
    assert all(checks.values()),checks
    (OUT/'validation.json').write_text(json.dumps({'checks':checks,'inputs':[
        {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]},indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
