"""Portable scientific entry point after the versioned inputs are available."""
from pathlib import Path
import subprocess
import sys
import argparse


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--include-illustrative-scenarios',action='store_true',
                        help='Reproduce withdrawn hypothetical cash flows for archival inspection only.')
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    jobs=[('fetch_data.py',['--verify-only']),('audit_results.py',[]),
          ('analyze_fixed_depth.py',[]),('reassess_evidence.py',[])]
    if args.include_illustrative_scenarios: jobs.append(('asset_scenarios.py',[]))
    for name,args in jobs:
        print('Running',name,flush=True)
        subprocess.run([sys.executable,str(here/name),*args],check=True)


if __name__=='__main__':main()
