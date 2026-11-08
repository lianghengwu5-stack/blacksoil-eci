"""Fetch versioned public inputs or verify existing copies by SHA-256."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import requests

ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
    {'id':'soc_v9','path':'China_SOC_profiles_2010_2024.csv',
     'url':'https://zenodo.org/records/15851730/files/China_profile_dataset_20250710.csv?download=1',
     'sha256':'65a8a291605c3d5b8f2e38d1b007aa4c9a33ddc2ebde9743277159e2d7c3516b',
     'citation':'https://doi.org/10.5281/zenodo.15851730'},
    {'id':'soc_v10','path':'source_metadata/SOCS_V10.csv',
     'url':'https://zenodo.org/records/17304024/files/SOCS_V10.csv?download=1',
     'sha256':'3cb6a1a1d8f89413e49d88b7fff467abd7cf147bf7bba6f20eebc9d131bf9a00',
     'citation':'https://doi.org/10.5281/zenodo.17304024'},
    {'id':'traces','path':'TRACESoils.xlsx',
     'url':'https://zenodo.org/records/13468926/files/TRACESoils_GlobalDatasetSOCaccrual.xlsx?download=1',
     'sha256':'9b9a8dfb36fe6f32c8b99dc7a5b662a216db06d2e121d57772d9f44678382c5c',
     'citation':'https://doi.org/10.5281/zenodo.13468926'},
    {'id':'figshare','path':'figshare_SOC_topsoil.csv','url':'https://ndownloader.figshare.com/files/25642934',
     'sha256':'6e632e48e9e1d0ca26b9e1900851576c6e9df4bb7a27ee4ede3f4ffd92f793b5',
     'citation':'https://doi.org/10.6084/m9.figshare.11983959.v4'},
    {'id':'kbs','path':'cordova/Cordova_et_al._Soil_C_Dryad_v2.xlsx',
     'url':'https://datadryad.org/downloads/file_stream/3918003',
     'sha256':'7a4ffdcd6d0619be1831b113907c4c39d3728097ee18f1e2362e7610c1907596',
     'citation':'https://doi.org/10.5061/dryad.1rn8pk0x1'},
    {'id':'boundary','path':'source_metadata/BlackSoilRegionChina.rar',
     'url':'https://www.geodoi.ac.cn/WebCn/down.aspx?fileID=5828&size=728888',
     'sha256':'384ab8613589e60a654435ebf311af7f69d910532440c10c76067d8f953f1ace',
     'citation':'https://doi.org/10.3974/geodb.2021.06.08.V1'},
]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def one(source,dest,verify_only):
    target=dest/source['path']
    if target.exists():
        if digest(target)==source['sha256']:return {'id':source['id'],'status':'verified_existing'}
        return {'id':source['id'],'status':'checksum_mismatch','path':source['path']}
    if verify_only:return {'id':source['id'],'status':'missing','path':source['path']}
    try:
        response=requests.get(source['url'],timeout=60)
        response.raise_for_status()
        if hashlib.sha256(response.content).hexdigest()!=source['sha256']:
            return {'id':source['id'],'status':'download_checksum_mismatch','path':source['path']}
        target.parent.mkdir(parents=True,exist_ok=True)
        temp=target.with_suffix(target.suffix+'.partial');temp.write_bytes(response.content);temp.replace(target)
        return {'id':source['id'],'status':'downloaded_verified'}
    except requests.RequestException as exc:
        return {'id':source['id'],'status':'manual_download_required','path':source['path'],
                'source_page':source['citation'],'error':str(exc).split('\n')[0][:200]}


def extract_boundary(dest):
    archive=dest/'source_metadata/BlackSoilRegionChina.rar'
    base=dest/'source_metadata/boundary'
    if (base/'BlackSoilRegion/BlackSoilRegion.shp').exists() and (base/'TypicalBlackSoilRegion/TypicalBlackSoilRegion.shp').exists():return
    tar=shutil.which('bsdtar') or shutil.which('tar')
    if not tar:raise RuntimeError('Install libarchive bsdtar or manually unpack the boundary archive into data/raw/source_metadata/boundary.')
    listing=subprocess.check_output([tar,'-tf',str(archive)],text=True).splitlines()
    if any(Path(n).is_absolute() or '..' in Path(n).parts or Path(n).parts[0] not in ['BlackSoilRegion','TypicalBlackSoilRegion'] for n in listing):
        raise RuntimeError('Unexpected archive members; refusing extraction')
    base.mkdir(parents=True,exist_ok=True)
    subprocess.run([tar,'-xf',str(archive),'-C',str(base)],check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only',action='store_true')
    parser.add_argument('--data-dir',type=Path,default=ROOT/'data/raw')
    parser.add_argument('--only',choices=[s['id'] for s in SOURCES],nargs='+')
    args=parser.parse_args();sources=[s for s in SOURCES if not args.only or s['id'] in args.only]
    args.data_dir.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        result=list(pool.map(lambda s:one(s,args.data_dir,args.verify_only),sources))
    for row in result:print(json.dumps(row,ensure_ascii=False),flush=True)
    (args.data_dir/'fetch_status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    if any(r['status'] not in ['verified_existing','downloaded_verified'] for r in result):
        raise SystemExit('Some inputs need attention. Download from the cited source into the stated path, then verify again. Existing changed files are never overwritten.')
    if any(s['id']=='boundary' for s in sources):extract_boundary(args.data_dir)


if __name__=='__main__':main()
