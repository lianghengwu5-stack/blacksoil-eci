"""Archive public repository metadata and versioned SOC files with checksums."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'data/raw/source_metadata'
URLS = {
    'zenodo_15851730.json': 'https://zenodo.org/api/records/15851730',
    'zenodo_17304024.json': 'https://zenodo.org/api/records/17304024',
    'zenodo_13468926.json': 'https://zenodo.org/api/records/13468926',
    'figshare_11983959.json': 'https://api.figshare.com/v2/articles/11983959',
    'SOCS_V10.csv': 'https://zenodo.org/records/17304024/files/SOCS_V10.csv?download=1',
    'SOCS_V10_Readme.txt': 'https://zenodo.org/records/17304024/files/SOCS_V10_Readme.txt?download=1',
}


def fetch(item):
    name, url = item
    try:
        r = requests.get(url, timeout=90)
        r.raise_for_status()
        if name.endswith('.json'):
            r.json()
        (DEST / name).write_bytes(r.content)
        return {'file': name, 'url': url, 'status': 'downloaded',
                'bytes': len(r.content), 'sha256': hashlib.sha256(r.content).hexdigest()}
    except Exception as exc:
        return {'file': name, 'url': url, 'status': 'failed', 'error': str(exc)}


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, URLS.items()))
    (DEST / 'fetch_manifest.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
    for result in results:
        print(result['file'], result['status'], flush=True)


if __name__ == '__main__':
    main()
