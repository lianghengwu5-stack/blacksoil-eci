"""Copy historical inputs and numerical outputs without changing originals."""
from pathlib import Path
import csv
import hashlib
import shutil
import argparse

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Historical workspace directory')
    source_root = parser.parse_args().source.resolve()
    jobs = []
    for p in sorted((source_root / 'data').rglob('*')):
        if p.is_file() and p.name != '.DS_Store':
            jobs.append((p, ROOT / 'data/raw' / p.relative_to(source_root / 'data')))
    for folder in ['outputs', 'outputs_real']:
        for p in sorted((source_root / folder).glob('*.csv')):
            jobs.append((p, ROOT / 'data/archive' / folder / p.name))
    for name in ['数据源清单_v1.md', '文献与数据核验_v2.md', 'ECI方法学定稿_v1.md']:
        jobs.append((source_root / name, ROOT / 'data/archive' / name))
    rows = []
    for source, dest in jobs:
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'Refusing to overwrite changed file: {dest}')
        if not dest.exists():
            shutil.copy2(source, dest)
        if hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f'Copy checksum mismatch: {dest}')
        rows.append({'relative_path': str(dest.relative_to(ROOT)), 'bytes': dest.stat().st_size,
                     'sha256': digest, 'source_path': str(source), 'license_status': 'pending_source_verification'})
    target = ROOT / 'data/manifest.local.csv'
    with target.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    public_rows = [{k: v for k, v in row.items() if k != 'source_path'} for row in rows]
    with (ROOT / 'data/manifest.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(public_rows[0]))
        writer.writeheader()
        writer.writerows(public_rows)
    print(f'Recovered and verified {len(rows)} files; manifest: {target}')


if __name__ == '__main__':
    main()
