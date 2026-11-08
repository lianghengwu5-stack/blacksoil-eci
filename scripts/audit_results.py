"""Recompute source diagnostics and distinguish historical from revised estimates.

This audit does not certify a black-soil-farmland study boundary or causal effects.
"""
from pathlib import Path
import hashlib
import json
import warnings
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
OUT = ROOT / 'artifacts/audit'
KEY = ['profile_id', 'latitude', 'longitude', 'Year', 'References']
INDICATORS = ['SOC (g/kg)', 'SOCD (kg/m2)', 'NDVI', 'MAP', 'AI']
V10_COLUMNS = {'Profile': 'profile_id', 'Latitude': 'latitude', 'Longitude': 'longitude',
               'Upper_depth_cm': 'upper_dept', 'Lower_depth_cm': 'lower_dept',
               'BD_g_cm3': 'BD (g/cm3)', 'SOC_g_kg': 'SOC (g/kg)',
               'SOCD_kg_m_2': 'SOCD (kg/m2)', 'Time': 'Year', 'MAP_mm': 'MAP',
               'Clay_%': 'Clay', 'Sand_%': 'Sand', 'Silt_%': 'Silt'}


def write_csv(frame, name):
    frame.to_csv(OUT / name, index=False, encoding='utf-8-sig')


def region(frame):
    return frame[frame.latitude.between(38, 54) & frame.longitude.between(118, 135)].copy()


def compute_eci(frame, indicators=None):
    indicators = indicators or INDICATORS
    z = frame[indicators].copy().reset_index(drop=True)
    z = z.clip(lower=z.quantile(.01), upper=z.quantile(.99), axis=1)
    span = z.max() - z.min()
    if (span <= 0).any():
        raise ValueError('ECI contains a constant indicator')
    z = (z - z.min()) / span
    p = (z / z.sum()).replace(0, np.nan)
    entropy = -(p * np.log(p)).sum() / np.log(len(z))
    ew = (1 - entropy) / (1 - entropy).sum()
    val, vec = np.linalg.eigh(z.corr())
    order = np.argsort(val)[::-1]
    val, vec = val[order], vec[:, order]
    ratio = val / val.sum()
    k = np.searchsorted(np.cumsum(ratio), .85) + 1
    pw = (np.abs(vec[:, :k] * np.sqrt(val[:k])) * ratio[:k]).sum(axis=1)
    pw = pw / pw.sum()
    weights = pd.DataFrame({'indicator': indicators, 'equal': 1 / len(indicators),
                            'entropy': ew.values, 'pca': pw})
    scores = pd.DataFrame({method: z.to_numpy() @ weights[method].to_numpy() * 100
                           for method in ['equal', 'entropy', 'pca']})
    return scores, weights


def integrate_profile(layers, target=30.):
    """Integrate layer stocks only if [0,target] is covered exactly once.

    SOCD is the carbon stock in each reported layer in kg/m2. Partial layers
    assume uniform density within that layer. Gaps/overlaps are not imputed.
    """
    intervals = []
    for row in layers:
        u, l, stock = map(float, row)
        if not np.isfinite([u, l, stock]).all() or u < 0 or l <= u or stock < 0:
            return np.nan, 'invalid_layer'
        if u < target:
            intervals.append((u, min(l, target), stock / (l - u)))
    intervals.sort()
    cursor, total = 0., 0.
    for u, l, density in intervals:
        if u < cursor - 1e-8:
            return np.nan, 'overlap'
        if u > cursor + 1e-8:
            return np.nan, 'gap'
        total += density * (l - u)
        cursor = l
    if cursor < target - 1e-8:
        return np.nan, 'incomplete_depth'
    return total * 10, 'complete'


def polygon_subset(frame, boundary_name):
    import shapefile
    from pyproj import CRS, Transformer
    from shapely.geometry import shape
    from shapely import union_all, points, covers
    base = RAW / 'source_metadata/boundary' / boundary_name / boundary_name
    reader = shapefile.Reader(str(base), encoding='gb18030')
    geometries = [shape(g.__geo_interface__) for g in reader.shapes()]
    if not all(g.is_valid for g in geometries):
        raise ValueError('Boundary geometry is invalid; explicit repair decision required')
    boundary = union_all(geometries)
    project = Transformer.from_crs('EPSG:4326', CRS.from_wkt(base.with_suffix('.prj').read_text()), always_xy=True)
    valid = frame.latitude.notna() & frame.longitude.notna()
    subset = frame.loc[valid].copy()
    x, y = project.transform(subset.longitude.to_numpy(), subset.latitude.to_numpy())
    subset = subset.loc[covers(boundary, points(x, y))].copy()
    return subset


def soil_audit(frame, name, crop_value, boundary_name=None):
    ne = polygon_subset(frame, boundary_name) if boundary_name else region(frame)
    top = ne[ne.upper_dept.eq(0)].copy()
    valid = top.dropna(subset=INDICATORS + ['BD (g/cm3)'])
    valid = valid[(valid[INDICATORS + ['BD (g/cm3)']] > 0).all(axis=1)]
    ambiguous = valid.duplicated(KEY, keep=False)
    write_csv(valid.loc[ambiguous, KEY + ['Samples', 'lower_dept']], f'{name}_ambiguous_topsoil.csv')
    unique_top = valid.loc[~ambiguous].copy()
    stats_rows = []
    for label, sub in [('all_landcovers', unique_top),
                        ('cropland', unique_top[unique_top.CLCD.eq(crop_value)])]:
        scores, weights = compute_eci(sub)
        corr = scores.corr('spearman')
        record = {'source_version': name, 'subset': label, 'n': len(sub),
                  'eci_entropy_mean': scores.entropy.mean(), 'eci_entropy_min': scores.entropy.min(),
                  'eci_entropy_max': scores.entropy.max(),
                  'min_weighting_rho': corr.to_numpy()[np.triu_indices(3, 1)].min(),
                  'surface_stock_median_tC_ha': (sub['SOCD (kg/m2)'] * 10).median(),
                  'surface_stock_is_fixed_depth': False}
        stats_rows.append(record)
        write_csv(weights, f'{name}_{label}_weights.csv')
        write_csv(corr.rename_axis('method').reset_index(), f'{name}_{label}_rank_correlation.csv')
        result = sub[KEY + ['Samples', 'CLCD', 'upper_dept', 'lower_dept'] + INDICATORS].reset_index(drop=True)
        write_csv(pd.concat([result, scores.add_prefix('eci_')], axis=1), f'{name}_{label}_scores.csv')
    stocks = []
    for key, group in ne.groupby(KEY, dropna=False):
        relevant = group[group.upper_dept < 30]
        value, status = integrate_profile(relevant[['upper_dept', 'lower_dept', 'SOCD (kg/m2)']].to_numpy())
        land = group.CLCD.dropna().unique()
        if len(land) != 1:
            value, status = np.nan, 'landcover_conflict'
        stocks.append(dict(zip(KEY, key)) | {'CLCD': land[0] if len(land) == 1 else '',
                      'stock_0_30_tC_ha': value, 'coverage_status': status})
    stock = pd.DataFrame(stocks)
    write_csv(stock, f'{name}_strict_depth_profiles.csv')
    write_csv(stock.groupby(['CLCD', 'coverage_status'], dropna=False).size().rename('n').reset_index(),
              f'{name}_depth_exclusions.csv')
    for row in stats_rows:
        sub = stock[stock.coverage_status.eq('complete')]
        if row['subset'] == 'cropland':
            sub = sub[sub.CLCD.eq(crop_value)]
        row.update(stock030_n=len(sub), stock030_median_tC_ha=sub.stock_0_30_tC_ha.median(),
                   stock030_mean_tC_ha=sub.stock_0_30_tC_ha.mean())
    return {'geographic_scope': boundary_name or 'NE_rectangle',
            'regional_layers': len(ne), 'regional_profile_ids': ne.profile_id.nunique(),
            'topsoil_rows_before_validity': len(top), 'topsoil_valid_rows': len(valid),
            'ambiguous_topsoil_rows_excluded': int(ambiguous.sum()),
            'ph_clay_r': frame[['pH', 'Clay']].corr().iloc[0, 1],
            'texture_sum_median': (frame.Sand + frame.Silt + frame.Clay).median(),
            'regional_map_median_as_stored': ne.MAP.median(), 'scenarios': stats_rows}


def dl_meta(y, v, conservative_hk=False):
    y, v = np.asarray(y, float), np.asarray(v, float)
    k = len(y)
    if k < 2 or (v <= 0).any():
        raise ValueError('Meta-analysis requires at least two valid estimates')
    w = 1 / v
    fixed = np.sum(w * y) / np.sum(w)
    q = np.sum(w * (y - fixed) ** 2)
    tau = max(0., (q - k + 1) / (w.sum() - (w ** 2).sum() / w.sum()))
    rw = 1 / (v + tau)
    mean = np.sum(rw * y) / rw.sum()
    scale = max(1., np.sum(rw * (y - mean) ** 2) / (k - 1)) if conservative_hk else 1.
    se = np.sqrt(scale / rw.sum())
    critical = stats.t.ppf(.975, k - 1) if conservative_hk else stats.norm.ppf(.975)
    lo, hi = mean - critical * se, mean + critical * se
    return {'k': k, 'lnrr': mean, 'effect_pct': np.expm1(mean) * 100,
            'ci_low_pct': np.expm1(lo) * 100, 'ci_high_pct': np.expm1(hi) * 100,
            'i2_pct': max(0., (q - k + 1) / q) * 100 if q else 0., 'tau2': tau,
            'interval': 'modified_Hartung_Knapp_t' if conservative_hk else 'normal'}


def effect_audit():
    fg = pd.read_csv(RAW / 'figshare_SOC_topsoil.csv')
    fg['row_id'] = np.arange(len(fg)) + 1
    fg['management_code'] = fg.focal_organic_system.str.strip()
    fg = fg[fg.management_code.str.contains('till', case=False, na=False)].copy()
    fg = fg[(fg.control_mean > 0) & (fg.treatment_mean > 0)]
    fg['lnrr'] = np.log(fg.treatment_mean / fg.control_mean)
    fg['variance'] = fg.control_sd**2 / (fg.control_n * fg.control_mean**2) + fg.treatment_sd**2 / (fg.treatment_n * fg.treatment_mean**2)
    write_csv(fg, 'figshare_tillage_coded_rows.csv')
    write_csv(fg.groupby(['study_code', 'management_code']).size().rename('n').reset_index(),
              'figshare_management_composition.csv')
    rows = []
    for name, data in [('all_tillage_containing', fg), ('tillage_only_code', fg[fg.management_code.eq('tillage')])]:
        complete = data.dropna(subset=['variance', 'control_sd', 'treatment_sd', 'control_n', 'treatment_n'])
        complete = complete[(complete.variance > 0) & (complete.control_n >= 2) & (complete.treatment_n >= 2) & (complete.control_sd > 0) & (complete.treatment_sd > 0)]
        common = {'subset': name, 'n_rows': len(data), 'n_studies': data.study_code.nunique(),
                  'complete_rows': len(complete), 'complete_studies': complete.study_code.nunique(),
                  'unweighted_lnrr_effect_pct': np.expm1(data.lnrr.mean()) * 100}
        rows.append(common | {'analysis': 'observation_level_DL_exploratory'} | dl_meta(complete.lnrr, complete.variance))
        # Unknown dependence is made explicit. rho sensitivity is assumed, not estimated.
        for rho in [0., .5, 1.]:
            studies = []
            for study, g in complete.groupby('study_code'):
                y, v = g.lnrr.to_numpy(), g.variance.to_numpy()
                a = (1 / v) / np.sum(1 / v)
                variance = (1 - rho) * np.sum(a*a*v) + rho * np.sum(a*np.sqrt(v))**2
                studies.append({'study_code': study, 'lnrr': np.sum(a*y), 'variance': variance,
                                'n_comparisons': len(g), 'assumed_within_study_rho': rho})
            study_frame = pd.DataFrame(studies)
            write_csv(study_frame, f'figshare_{name}_study_effects_rho_{rho}.csv')
            rows.append(common | {'analysis': 'study_level_DL_modified_HK', 'assumed_rho': rho}
                        | dl_meta(study_frame.lnrr, study_frame.variance, conservative_hk=True))
    result = pd.DataFrame(rows)
    write_csv(result, 'meta_reanalysis.csv')
    return rows


def direction_audit():
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        tr = pd.read_excel(RAW / 'TRACESoils.xlsx', sheet_name='Database')
    candidate = tr[tr.soil_dist1.astype(str).str.contains('till', case=False) |
                   tr.soil_dist2.astype(str).str.contains('till', case=False)].copy()
    write_csv(candidate[['soil_dist1', 'soil_dist2', 'soil_dist_control', 'SOC_accrual_response',
                         'country', 'exp_site', 'reference', 'doi']], 'traces_comparison_audit.csv')
    groups = {'global': candidate, 'china': candidate[candidate.country.eq('China')]}
    groups['northeast_rectangle'] = region(groups['china'])
    rows = []
    for name, data in groups.items():
        counts = data.SOC_accrual_response.fillna('missing').value_counts().to_dict()
        rows.append({'region': name, 'n_total': len(data), 'n_unique_references': data.reference.nunique(), **counts})
    write_csv(pd.DataFrame(rows).fillna(0), 'traces_all_response_categories.csv')
    write_csv(candidate.groupby(['soil_dist1', 'soil_dist_control'], dropna=False).size().rename('n').reset_index(),
              'traces_treatment_control_codes.csv')
    return rows


def kbs_audit():
    d = pd.read_excel(RAW / 'cordova/Cordova_et_al._Soil_C_Dryad_v2.xlsx', sheet_name='Table 4')
    d['soc'] = pd.to_numeric(d['SOC_stock_Mg C/ha'], errors='coerce')
    d = d[d.year.isin([2001, 2013])]
    cells = d.groupby(['year', 'system']).soc.agg(['count', 'mean', 'std']).reset_index()
    write_csv(cells, 'kbs_cells_2001_2013.csv')
    paired = d.pivot(index=['system', 'replicate'], columns='year', values='soc').dropna()
    paired['change_tC_ha'] = paired[2013] - paired[2001]
    write_csv(paired.reset_index(), 'kbs_matched_replicate_changes.csv')
    a = paired.loc['Late successional', 'change_tC_ha']
    b = paired.loc['Conventional', 'change_tC_ha']
    t = stats.ttest_ind(a, b, equal_var=False)
    return {'matched_late_successional_n': len(a), 'matched_conventional_n': len(b),
            'matched_change_difference_tC_ha': a.mean() - b.mean(), 'welch_p': t.pvalue,
            'interpretation': 'External system contrast, not a pre-intervention conservation-tillage DiD.'}


def legacy_comparison():
    rows = []
    for f in sorted((ROOT / 'data/archive/outputs_real').glob('*.csv')):
        new = ROOT / 'artifacts/legacy_run/outputs_real' / f.name
        status = 'missing_recomputed_file'
        if new.exists():
            try:
                pd.testing.assert_frame_equal(pd.read_csv(f), pd.read_csv(new), check_exact=False, rtol=1e-10, atol=1e-10)
                status = 'match_within_1e-10'
            except AssertionError:
                status = 'difference'
        rows.append({'file': f.name, 'status': status})
    write_csv(pd.DataFrame(rows), 'legacy_csv_comparison.csv')
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    v9 = pd.read_csv(RAW / 'China_SOC_profiles_2010_2024.csv')
    v9.columns = v9.columns.str.strip()
    for c in v9.columns.difference(['References', 'SOCD__meth']):
        v9[c] = pd.to_numeric(v9[c], errors='coerce').replace(-9999, np.nan)
    v10 = pd.read_csv(RAW / 'source_metadata/SOCS_V10.csv', encoding='gb18030').rename(columns=V10_COLUMNS)
    for c in v10.columns.difference(['References', 'SOCD_methods', 'Depth_cm', 'CLCD']):
        v10[c] = pd.to_numeric(v10[c], errors='coerce').replace(-9999, np.nan)
    summary = {'legacy_csv_comparison': legacy_comparison(),
               'soil_v9': soil_audit(v9, 'v9', 1),
               'soil_v10': soil_audit(v10, 'v10', 'Cropland'),
               'soil_v10_blacksoil': soil_audit(v10, 'v10_blacksoil', 'Cropland', 'BlackSoilRegion'),
               'soil_v10_typical': soil_audit(v10, 'v10_typical', 'Cropland', 'TypicalBlackSoilRegion'),
               'meta': effect_audit(), 'traces': direction_audit(), 'kbs': kbs_audit()}
    summary['v10_national_profile_count_in_file'] = int(v10.profile_id.nunique())
    summary['v10_national_layer_count'] = len(v10)
    summary['source_checksums'] = {str(f.relative_to(RAW)): hashlib.sha256(f.read_bytes()).hexdigest()
                                   for f in [RAW / 'China_SOC_profiles_2010_2024.csv', RAW / 'source_metadata/SOCS_V10.csv']}
    def serial(value):
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(type(value).__name__)
    (OUT / 'summary.json').write_text(json.dumps(summary, default=serial, ensure_ascii=False, indent=2))
    soils = [k for k in summary if k.startswith('soil_v')]
    write_csv(pd.DataFrame([r for k in soils for r in summary[k]['scenarios']]), 'soil_scenarios.csv')
    print(json.dumps({k: summary[k] for k in soils + ['kbs']}, default=serial, ensure_ascii=False, indent=2))
    print('Audit tables saved:', OUT)


if __name__ == '__main__':
    main()
