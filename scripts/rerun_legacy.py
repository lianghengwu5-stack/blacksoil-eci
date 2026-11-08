"""Reproduce unchanged historical scripts in an isolated copy."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent


def main():
    work = ROOT / 'artifacts/legacy_run'
    work.mkdir(parents=True, exist_ok=True)
    data = work / 'data'
    if not data.exists():
        data.symlink_to(ROOT / 'data/raw', target_is_directory=True)
    names = ['eci_real.py', 'tillage_effect.py', 'did_real.py', 'harden.py',
             'enrich_figures.py', 'enrich2.py', 'gpp_integrate.py', 'eci_pipeline.py']
    results = []
    for name in names:
        source = PROJECT / '中期评审/05_代码' / name
        shutil.copy2(source, work / name)
        run = subprocess.run([sys.executable, str(work / name)], capture_output=True,
                             text=True, timeout=180)
        (work / (name + '.log')).write_text(run.stdout + '\nSTDERR\n' + run.stderr)
        results.append({'script': name, 'returncode': run.returncode})
        print(name, run.returncode, flush=True)
    (work / 'run_status.json').write_text(json.dumps(results, indent=2))
    if any(r['returncode'] for r in results):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
