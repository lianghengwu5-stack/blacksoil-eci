"""Export a repository candidate without local raw inputs or historical files."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT.parent/'output/github/blacksoil-eci'


def main():
    STAGE.mkdir(parents=True,exist_ok=True)
    for directory in ['scripts','tests','docs','artifacts']:
        source=ROOT/directory
        shutil.copytree(source,STAGE/directory,dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__','legacy_run','logs','*.pyc'))
    for name in ['README.md','CITATION.cff','requirements.txt','requirements-lock.txt','.gitignore']:
        shutil.copy2(ROOT/name,STAGE/name)
    (STAGE/'data').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'data/manifest.csv',STAGE/'data/manifest.csv')
    shutil.copytree(ROOT/'data/external',STAGE/'data/external',dirs_exist_ok=True)
    reports=STAGE/'reports';reports.mkdir(exist_ok=True)
    for kind in ['pdf','docx']:
        for p in (ROOT.parent/'output'/kind).glob('*研究报告_初稿.'+kind):
            shutil.copy2(p,reports/p.name)
    forbidden=[p for p in STAGE.rglob('*') if p.is_file() and
               any(part in ['raw','archive','.venv','legacy_run','logs','__pycache__'] for part in p.relative_to(STAGE).parts)]
    assert not forbidden,forbidden
    files=[p for p in sorted(STAGE.rglob('*')) if p.is_file() and '.git' not in p.parts and p.name!='release_manifest.json']
    manifest=[{'path':str(p.relative_to(STAGE)),'bytes':p.stat().st_size,
               'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    (STAGE/'release_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    target=STAGE.parent/'blacksoil-eci_private_repository.zip'
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as out:
        for p in sorted(STAGE.rglob('*')):
            if p.is_file() and '.git' not in p.parts:out.write(p,str(Path('blacksoil-eci')/p.relative_to(STAGE)))
    print(json.dumps({'stage':str(STAGE),'archive':str(target),'files':len(manifest)+1,
                      'archive_bytes':target.stat().st_size},ensure_ascii=False))


if __name__=='__main__':main()
