"""Run the analysis on restored local inputs, preserving historical materials."""
from pathlib import Path
import subprocess
import sys


def main():
    scripts = Path(__file__).resolve().parent
    for name in ['audit_results.py', 'analyze_fixed_depth.py', 'asset_scenarios.py', 'write_audit_report.py']:
        print(f'Running {name}', flush=True)
        subprocess.run([sys.executable, str(scripts / name)], check=True)


if __name__ == '__main__':
    main()
