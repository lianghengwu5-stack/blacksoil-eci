"""Fetch the two CC0 Dryad files used in the optional coverage audit."""
from pathlib import Path
import argparse,hashlib,json
import requests
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'data/raw/revision_20261109/dryad_cvdncjt89'
FILES=[('Measurement_data.csv','2362934','71a32d6b7798960f2e0510b45a05a10c0170a56720f3ec5c016c14afd12e362a'),
       ('README.md','2362937','14f8ca879ac54395cdb0e01a55cbc59f61631dda13a9ccfb77eace8841c3c58e')]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
 TARGET.mkdir(parents=True,exist_ok=True);manifest=[]
 for name,file_id,expected in FILES:
  p=TARGET/name;url='https://datadryad.org/downloads/file_stream/'+file_id
  if not p.exists():
   if args.verify_only:raise FileNotFoundError(p)
   try:
    response=requests.get(url,timeout=(15,45));response.raise_for_status();body=response.content
    if hashlib.sha256(body).hexdigest()!=expected:raise ValueError('Unexpected file hash')
    p.write_bytes(body)
   except (requests.RequestException,ValueError) as exc:
    raise SystemExit(f'{name}: download not verified. Use the official dataset https://doi.org/10.5061/dryad.cvdncjt89 and save to {p}. Then rerun --verify-only. Reason: {type(exc).__name__}') from exc
  actual=hashlib.sha256(p.read_bytes()).hexdigest()
  if actual!=expected:raise ValueError(f'Hash mismatch: {p}')
  manifest.append(dict(path=str(p.relative_to(ROOT)),url=url,sha256=actual,bytes=p.stat().st_size))
 (TARGET/'download_manifest.json').write_text(json.dumps(manifest,indent=2))
 print(f'Verified {len(manifest)} Dryad files')
if __name__=='__main__':main()
