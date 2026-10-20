"""Fetch only frozen commit trees initially; blobs are loaded on demand."""
import csv, json, os, subprocess, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GIT=shutil.which('git') or 'C:/Users/jl/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
env={k:v for k,v in os.environ.items() if k not in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE')}
env.update(TEMP=str(ROOT/'Codex-MM-Assist/temp'),TMP=str(ROOT/'Codex-MM-Assist/temp'),GIT_TERMINAL_PROMPT='0')
sample=list(csv.DictReader((ROOT/'data/sample_ids.csv').open(encoding='utf-8-sig')))
for row in sample:
    project=row['project']; repo=ROOT/'repos'/project
    meta=json.loads((ROOT/('outputs/requests/case_%04d/input_record.json'%int(row['case_id']))).read_text(encoding='utf-8'))
    if not repo.exists():
        repo.mkdir(parents=True)
        subprocess.run([GIT,'init','--bare',str(repo)],env=env,check=True,capture_output=True)
        subprocess.run([GIT,'--git-dir='+str(repo),'remote','add','origin',meta['repository']],env=env,check=True)
    command=[GIT,'--git-dir='+str(repo),'fetch','--depth=1','--filter=blob:none','origin',row['commit']]
    result=subprocess.run(command,env=env,capture_output=True,timeout=240)
    evidence=ROOT/'outputs/source_checks'; evidence.mkdir(exist_ok=True)
    text='$ '+' '.join(command)+'\n'+result.stdout.decode(errors='replace')+result.stderr.decode(errors='replace')
    if result.returncode:
        (evidence/(row['case_id']+'_fetch.txt')).write_text(text,encoding='utf-8')
        raise RuntimeError('Commit fetch failed '+row['case_id'])
    command=[GIT,'--git-dir='+str(repo),'ls-tree','-r','--name-only',row['commit']]
    tree=subprocess.run(command,env=env,capture_output=True,check=True).stdout
    (evidence/(row['case_id']+'_tree.txt')).write_bytes(tree)
    (evidence/(row['case_id']+'_fetch.txt')).write_text(text,encoding='utf-8')
    print('Cached tree',row['case_id'],project,len(tree.splitlines()),flush=True)
