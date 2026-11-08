"""Portable scientific entry point after the versioned inputs are available."""
from pathlib import Path
import subprocess
import sys


def main():
    here=Path(__file__).resolve().parent
    for name,args in [('fetch_data.py',['--verify-only']),('audit_results.py',[]),
                      ('analyze_fixed_depth.py',[]),('asset_scenarios.py',[])]:
        print('Running',name,flush=True)
        subprocess.run([sys.executable,str(here/name),*args],check=True)


if __name__=='__main__':main()
