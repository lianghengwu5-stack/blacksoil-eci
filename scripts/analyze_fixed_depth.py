"""Build a fixed-depth ECI candidate and regenerate traceable result figures."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_results import RAW, ROOT, KEY, V10_COLUMNS, compute_eci, integrate_profile, polygon_subset

OUT = ROOT / 'artifacts/fixed_depth'
INDS = ['SOC_0_30_g_kg_thickness_mean', 'stock_0_30_tC_ha', 'NDVI', 'MAP', 'AI']


def build_profiles():
    d = pd.read_csv(RAW / 'source_metadata/SOCS_V10.csv', encoding='gb18030').rename(columns=V10_COLUMNS)
    for c in ['latitude', 'longitude', 'upper_dept', 'lower_dept', 'SOC (g/kg)', 'SOCD (kg/m2)', 'NDVI', 'MAP', 'AI']:
        d[c] = pd.to_numeric(d[c], errors='coerce').replace(-9999, np.nan)
    d = polygon_subset(d, 'BlackSoilRegion')
    rows = []
    for key, group in d.groupby(KEY, dropna=False):
        g = group[group.upper_dept < 30].copy()
        record = dict(zip(KEY, key))
        cover, status = integrate_profile(g[['upper_dept', 'lower_dept', 'SOCD (kg/m2)']].to_numpy())
        land = group.CLCD.dropna().unique()
        if len(land) != 1 or land[0] != 'Cropland':
            continue
        record.update(stock_0_30_tC_ha=cover, status=status)
        covars = ['NDVI', 'MAP', 'AI']
        if any(group[c].dropna().nunique() != 1 for c in covars):
            record['status'] = 'covariate_conflict_or_missing'
        for c in covars:
            record[c] = group[c].iloc[0]
        if status == 'complete':
            thickness = np.minimum(g.lower_dept, 30) - g.upper_dept
            if (g['SOC (g/kg)'].notna() & (g['SOC (g/kg)'] > 0)).all():
                record['SOC_0_30_g_kg_thickness_mean'] = np.sum(g['SOC (g/kg)'] * thickness) / 30
            else:
                record['status'] = 'missing_or_nonpositive_SOC'
        if any(pd.isna(record.get(c)) or record.get(c, 0) <= 0 for c in covars):
            record['status'] = 'missing_or_nonpositive_covariate'
        record['source_sample_ids'] = ','.join(map(str, g.Samples.astype(int)))
        # Only layers contributing to the 0–30 cm target determine its method.
        record['stock_method_mix'] = ','.join(sorted(g.SOCD_methods.dropna().unique()))
        rows.append(record)
    full = pd.DataFrame(rows)
    full.to_csv(OUT / 'profile_selection.csv', index=False, encoding='utf-8-sig')
    return full[full.status.eq('complete')].reset_index(drop=True)


def soilgrids_layerwise():
    source = ROOT / 'data/external/soilgrids_queries.csv'
    if not source.exists():source = ROOT / 'data/archive/outputs/公开SoilGrids_API原始返回.csv'
    raw = pd.read_csv(source)
    rows = []
    for record in raw.to_dict('records'):
        try:
            payload = json.loads(record['payload'])
            layers = {item['name']: item for item in payload['properties']['layers']}
            stocks = []
            for depth in ['0-5cm', '5-15cm', '15-30cm']:
                soc = next(x for x in layers['soc']['depths'] if x['label'] == depth)
                bd = next(x for x in layers['bdod']['depths'] if x['label'] == depth)
                c = soc['values']['mean'] / layers['soc']['unit_measure']['d_factor']
                b = bd['values']['mean'] / layers['bdod']['unit_measure']['d_factor']
                thickness = soc['range']['bottom_depth'] - soc['range']['top_depth']
                stocks.append(c * b * thickness * .1)
            rows.append({'site': record['site'], 'latitude': record['lat'], 'longitude': record['lon'],
                         'stock_0_30_tC_ha': sum(stocks), 'status': 'complete',
                         'coarse_fragment_adjustment': 'not_available_in_archived_query'})
        except (KeyError, TypeError, ValueError, StopIteration):
            rows.append({'site': record['site'], 'latitude': record['lat'], 'longitude': record['lon'],
                         'stock_0_30_tC_ha': np.nan, 'status': 'incomplete_payload'})
    result = pd.DataFrame(rows)
    inside = polygon_subset(result, 'BlackSoilRegion').index
    result['inside_blacksoil_boundary'] = result.index.isin(inside)
    result.to_csv(OUT / 'soilgrids_layerwise_stock.csv', index=False, encoding='utf-8-sig')
    return result


def sensitivity(d, scores):
    rows = []
    for omitted in INDS:
        s, _ = compute_eci(d, [c for c in INDS if c != omitted])
        rows.append({'analysis': 'leave_one_indicator_out', 'omitted': omitted,
                     'n': len(d), 'spearman_vs_five_indicator_entropy': stats.spearmanr(scores.entropy, s.entropy).statistic})
    # Recalibrate on remaining profiles, then compare ranks on the same survivors.
    for ref, g in d.groupby('References'):
        keep = d.References.ne(ref)
        sub, _ = compute_eci(d.loc[keep], INDS)
        rows.append({'analysis': 'leave_one_source_out_recalibrated', 'omitted': ref,
                     'n': int(keep.sum()), 'spearman_vs_five_indicator_entropy':
                     stats.spearmanr(scores.loc[keep, 'entropy'], sub.entropy).statistic})
    pd.DataFrame(rows).to_csv(OUT / 'sensitivity.csv', index=False, encoding='utf-8-sig')


def figures(d, scores, weights):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.5))
    axs[0].hist(scores.entropy, bins=18, color='#276b4d', edgecolor='white')
    axs[0].set(xlabel='ECI (relative score, 0-100)', ylabel='Number of profiles', title=f'Fixed-depth cropland ECI (n={len(d)})')
    axs[1].hist(d.stock_0_30_tC_ha, bins=18, color='#745037', edgecolor='white')
    axs[1].axvline(d.stock_0_30_tC_ha.median(), color='#b44736', label=f'Median {d.stock_0_30_tC_ha.median():.1f}')
    axs[1].set(xlabel='SOC stock, 0-30 cm (t C/ha)', ylabel='Number of profiles', title='Complete, non-overlapping depth coverage')
    axs[1].legend()
    fig.tight_layout(); fig.savefig(OUT / 'fig01_fixed_depth_distributions.png', dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    w = weights.set_index('indicator').copy()
    w.index = ['SOC concentration', 'SOC stock', 'Vegetation (NDVI)', 'MAP (source values)', 'Aridity index']
    w.plot.barh(ax=ax, color=['#b5b5b5', '#276b4d', '#4878a8'])
    ax.set(xlabel='Indicator weight', title='Weighting sensitivity on the same fixed-depth sample')
    fig.tight_layout(); fig.savefig(OUT / 'fig02_fixed_depth_weights.png', dpi=180); plt.close(fig)
    import shapefile
    from pyproj import CRS, Transformer
    from shapely.geometry import shape
    from shapely.ops import transform
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.3))
    base = RAW / 'source_metadata/boundary/BlackSoilRegion/BlackSoilRegion'
    transformer = Transformer.from_crs(CRS.from_wkt(base.with_suffix('.prj').read_text()), 'EPSG:4326', always_xy=True)
    for shp in shapefile.Reader(str(base)).shapes():
        g = transform(transformer.transform, shape(shp.__geo_interface__))
        polygons = list(g.geoms) if g.geom_type == 'MultiPolygon' else [g]
        for ax in axs:
            for poly in polygons:
                ax.plot(*poly.exterior.xy, lw=.7, color='#777777')
    for ax, values, title, label in zip(axs, [scores.entropy, d.stock_0_30_tC_ha],
                                       ['ECI on sampled cropland profiles', 'SOC stock on sampled cropland profiles'],
                                       ['ECI (0-100)', 'SOC stock (t C/ha)']):
        sc = ax.scatter(d.longitude, d.latitude, c=values, cmap='viridis', s=22, edgecolors='white', linewidths=.3)
        ax.set(xlabel='Longitude', ylabel='Latitude', title=title)
        fig.colorbar(sc, ax=ax, label=label, shrink=.7)
        ax.set_aspect(1 / np.cos(np.deg2rad(47)))
    fig.tight_layout(); fig.savefig(OUT / 'fig03_sample_locations.png', dpi=180); plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = build_profiles()
    scores, weights = compute_eci(d, INDS)
    final = pd.concat([d, scores.add_prefix('eci_')], axis=1)
    final.to_csv(OUT / 'fixed_depth_eci_profiles.csv', index=False, encoding='utf-8-sig')
    weights.to_csv(OUT / 'weights.csv', index=False, encoding='utf-8-sig')
    scores.corr('spearman').to_csv(OUT / 'weighting_rank_correlations.csv', encoding='utf-8-sig')
    sensitivity(d, scores)
    sg = soilgrids_layerwise()
    figures(d, scores, weights)
    summary = {'n_fixed_depth_profiles': len(d), 'n_source_references': d.References.nunique(),
               'stock_median_tC_ha': d.stock_0_30_tC_ha.median(),
               'stock_q25_tC_ha': d.stock_0_30_tC_ha.quantile(.25),
               'stock_q75_tC_ha': d.stock_0_30_tC_ha.quantile(.75),
               'eci_entropy_mean': scores.entropy.mean(), 'eci_entropy_min': scores.entropy.min(),
               'eci_entropy_max': scores.entropy.max(),
               'minimum_weighting_rho': scores.corr('spearman').to_numpy()[np.triu_indices(3, 1)].min(),
               'soilgrids_valid_n': int(sg.status.eq('complete').sum()),
               'soilgrids_stock_min': sg.stock_0_30_tC_ha.min(),
               'soilgrids_stock_max': sg.stock_0_30_tC_ha.max(),
               'MAP_unit_status': 'Source readme says mm; magnitude inconsistent with annual mm, physical interpretation withheld.',
               'interpretation': 'Relative ecological condition index; not management-attributable contribution or carbon credit.'}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
