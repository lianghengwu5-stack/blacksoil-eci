"""Audit additional public records; do not assume a measurement unit or pairing."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from pyproj import Geod
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from audit_results import ROOT,RAW,polygon_subset


def main():
    out=ROOT/'artifacts/reassessment';out.mkdir(parents=True,exist_ok=True)
    folder=RAW/'revision_20261109/dryad_cvdncjt89'
    p=folder/'Measurement_data.csv'
    expected='71a32d6b7798960f2e0510b45a05a10c0170a56720f3ec5c016c14afd12e362a'
    assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
    d=pd.read_csv(p)
    assert list(d.columns)==['longitude','latitude','SOC']
    d.insert(0,'source_row',np.arange(2,len(d)+2))
    d['inside_blacksoil_boundary']=d.index.isin(polygon_subset(d,'BlackSoilRegion').index)
    d['duplicate_coordinates']=d.duplicated(['longitude','latitude'],keep=False)
    d['duplicate_full_record']=d.duplicated(['longitude','latitude','SOC'],keep=False)
    d.to_csv(out/'external_sample_inventory.csv',index=False,encoding='utf-8-sig')
    main=pd.read_csv(out/'carbon_profiles.csv')
    geod=Geod(ellps='WGS84');rows=[]
    for r in main.itertuples():
        _,_,dist=geod.inv(np.full(len(d),r.longitude),np.full(len(d),r.latitude),d.longitude.to_numpy(),d.latitude.to_numpy())
        j=int(np.argmin(dist))
        rows.append(dict(profile_id=r.profile_id,nearest_external_source_row=int(d.iloc[j].source_row),
                         distance_km=float(dist[j]/1000),same_site_verified=False))
    pd.DataFrame(rows).to_csv(out/'external_nearest_points.csv',index=False,encoding='utf-8-sig')
    summary=dict(source_doi='10.5061/dryad.cvdncjt89',n_records=len(d),
        n_unique_coordinates=len(d[['longitude','latitude']].drop_duplicates()),
        n_records_in_boundary=int(d.inside_blacksoil_boundary.sum()),
        n_records_outside_boundary=int((~d.inside_blacksoil_boundary).sum()),
        n_records_with_duplicate_coordinates=int(d.duplicate_coordinates.sum()),
        n_records_with_duplicate_full_records=int(d.duplicate_full_record.sum()),
        missing=d.isna().sum().to_dict(),fields=list(d.columns),
        n_main_profiles_with_external_point_within_1km=sum(r['distance_km']<1 for r in rows),
        n_main_profiles_with_external_point_within_5km=sum(r['distance_km']<5 for r in rows),
        source_protocol='README describes cropland sampling 5–10 km intervals, at least 200 m from roads; dichromate heating method. Article abstract states 0–20 cm.',
        missing_for_stock_or_causal_analysis=['per-point sampling date','bulk density','coarse fragments','management treatment','control assignment'],
        unit_status='CSV and README do not state the SOC unit explicitly; no concentration conversion or pooled value comparison performed.',
        independence_status='Different published source; no cross-source record lineage to prove independence. Spatial proximity is not pairing.',
        use='Spatial coverage audit only; not added to the 0–30 cm stock denominator.')
    (out/'external_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    fig,ax=plt.subplots(figsize=(7,5))
    ax.scatter(d.longitude,d.latitude,s=6,alpha=.4,color='#9EB8AC',label='Additional published points (n=2140)')
    ax.scatter(main.longitude,main.latitude,s=27,color='#A05D34',label='Stock profiles (n=90)')
    ax.set(xlabel='Longitude',ylabel='Latitude',title='Different sampling coverage; no temporal pairing established')
    ax.legend(fontsize=8);fig.tight_layout();fig.savefig(out/'fig03_external_coverage.png',dpi=190);plt.close(fig)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
