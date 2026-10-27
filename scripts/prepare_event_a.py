"""Screen and prepare Event A only; no LLM calls and no gold-label output."""
import argparse, csv, hashlib, json, os, re, shutil, subprocess, zipfile
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'Codex-MM-Assist/mm-assist/replication-package/artifacts/datasets.zip'
EXPECTED='8b2808944db28ba6620f07a71fce38224f32cc100a444bb89573f662e268c3eb'
OUT=ROOT/'outputs/event_a'
GIT=shutil.which('git')
ENV={k:v for k,v in os.environ.items() if k not in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE')}
ENV['GIT_TERMINAL_PROMPT']='0'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def git(repo,*args,timeout=240):
    cmd=[GIT,'--git-dir='+str(repo),*args]
    return cmd,subprocess.run(cmd,env=ENV,capture_output=True,timeout=timeout)
def csvout(p,rows,cols):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(rows)
def frozen_messages(template):
    roles=list(re.finditer(r'^\[(SYSTEM|USER|ASSISTANT)\]\s*$',template,re.M));messages=[]
    for i,match in enumerate(roles):
        content=template[match.end():roles[i+1].start() if i+1<len(roles) else len(template)]
        content=re.sub(r'\n# Top-1.*','',content,flags=re.S).strip()
        messages.append({'role':match[1].lower(),'content':content})
    return messages
def render(messages,row,source):
    return {'model':'gpt-4o-2024-05-13','temperature':0,'messages':[
        {'role':m['role'],'content':m['content'].replace('{METHOD_SIGNATURE}',row['method']).replace('{HOST_CLASS_SOURCE}',source)} for m in messages]}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--tracker-recorded',action='store_true',required=True)
    ap.add_argument('--java',required=True,help='Java 17+ runtime; same JavaParser version as M2')
    args=ap.parse_args()
    if (ROOT/'data/event_a_sample_ids.csv').exists():raise SystemExit('Sample already exists. Preserve it; do not resample.')
    assert sha(ARCHIVE.read_bytes())==EXPECTED,'Dataset archive changed'
    m2=list(csv.DictReader((ROOT/'data/sample_ids.csv').open(encoding='utf-8-sig')));used={r['project'] for r in m2}
    template=(ROOT/'docs/prompt_adapted.txt').read_text(encoding='utf-8');messages=frozen_messages(template)
    for row in m2:
        folder=ROOT/('outputs/requests/case_%04d'%int(row['case_id']))
        source=(folder/'host.java').read_bytes().decode('utf-8')
        assert render(messages,row,source)==json.loads((folder/'request.json').read_text(encoding='utf-8')),'M2 prompt rendering differs'
    cases=[];desc=re.compile(r'in class (?P<host>\S+) & moved to class (?P<target>\S+)$')
    with zipfile.ZipFile(ARCHIVE) as z:
        for name in z.namelist():
            if not name.startswith('data/') or '/instance-methods/mm-assist-emm/' not in name or not name.endswith('_res.json'):continue
            for r in json.loads(z.read(name)):
                project=r['repository'].rstrip('/').removesuffix('.git').split('/')[-1]
                mm=r['move_method_refactoring'];ex=r.get('extraction_results',{});match=desc.search(mm['description'])
                extracted=next(x for x in mm['rightSideLocations'] if x['description']=='extracted method declaration')
                cases.append({'case_id':int(r['ref_id']),'project':project,'repo_url':r['repository'],
                    'upstream_sha1':r['sha1'],'commit':ex.get('newCommitHash',''),'host_class':match['host'],
                    'host_file':mm['leftSideLocations'][0]['filePath'],'method':extracted['codeElement'],'gold_target':match['target'],
                    'eligible12':not mm['isStatic'] and str(ex.get('success')).lower()=='true' and 'telemetry' in r})
    minima={}
    for c in cases:minima[c['project']]=min(minima.get(c['project'],c['case_id']),c['case_id'])
    order=sorted((p for p in minima if p not in used),key=lambda p:minima[p])
    assert order[0]=='elasticsearch','Unused-project order differs from registration'
    OUT.mkdir(parents=True,exist_ok=True)
    dump(OUT/'preparation_manifest.json',{'started_utc':datetime.now(timezone.utc).isoformat(),
        'tracker_recorded_confirmed_by_group':True,'dataset_sha256':EXPECTED,
        'prompt_sha256':sha((ROOT/'docs/prompt_adapted.txt').read_bytes()),'m2_request_rendering_equivalence':len(m2),
        'project_order':order,'preregistration_sha256':sha((ROOT/'docs/Decisions.md').read_bytes()),
        'api_calls':0,'gold_labels_used_for_selection':False})
    deps=ROOT/'Codex-MM-Assist/work/dependencies'
    cp=os.pathsep.join(str(deps/x) for x in ['javaparser-core-3.26.2.jar','gson-2.10.1.jar'])
    sample=[];log=[]
    for project in order:
        for c in sorted((x for x in cases if x['project']==project and x['eligible12']),key=lambda c:c['case_id']):
            if len(sample)==6:break
            cid=c['case_id'];folder=OUT/('screening/case_%04d'%cid);folder.mkdir(parents=True,exist_ok=True)
            repo=ROOT/'repos'/project
            if not repo.exists():
                subprocess.run([GIT,'init','--bare',str(repo)],env=ENV,check=True,capture_output=True)
                git(repo,'remote','add','origin',c['repo_url'])[1].check_returncode()
            cmd,fetched=git(repo,'fetch','--depth=1','--filter=blob:none','origin',c['commit'])
            evidence='$ '+' '.join(cmd)+'\n'+fetched.stdout.decode(errors='replace')+fetched.stderr.decode(errors='replace')
            (folder/'fetch.txt').write_text(evidence,encoding='utf-8')
            if fetched.returncode:
                reason=fetched.stderr.decode(errors='replace')
                if not any(s in reason.lower() for s in ('not our ref','unadvertised object',"couldn't find remote ref")):
                    raise RuntimeError('Fetch infrastructure failure; do not skip case '+str(cid))
                ok=False;why='frozen commit unavailable'
            else:
                _,tree=git(repo,'ls-tree','-r','--name-only',c['commit']);tree.check_returncode();(folder/'tree.txt').write_bytes(tree.stdout)
                _,present=git(repo,'cat-file','-e',c['commit']+':'+c['host_file'])
                if present.returncode:ok=False;why='host file absent'
                else:
                    _,source=git(repo,'show',c['commit']+':'+c['host_file']);source.check_returncode()
                    (folder/'host.java').write_bytes(source.stdout)
                    run=subprocess.run([args.java,'-cp',cp,str(ROOT/'scripts/InspectEventACase.java'),str(folder/'host.java'),c['host_class'],c['method'],str(folder/'ast.json')],capture_output=True)
                    (folder/'method_check.txt').write_bytes(run.stdout+run.stderr)
                    if run.returncode:
                        if b'Rule4 method selection:' not in run.stderr:raise RuntimeError('Parser/tool failure; do not skip case '+str(cid))
                        ok=False;why='rule4: no unique method match'
                    else:ok=True;why='rules1-4 passed'
            log.append({'case_id':cid,'project':project,'commit':c['commit'],'included':ok,'reason':why})
            csvout(ROOT/'data/event_a_screening_log.csv',log,['case_id','project','commit','included','reason'])
            print(cid,project,ok,why,flush=True)
            if ok:sample.append(c)
        if len(sample)==6:break
    if len(sample)!=6:raise RuntimeError('Fewer than six eligible cases; stop before requests')
    csvout(ROOT/'data/event_a_sample_ids.csv',sample,['case_id','project','commit','upstream_sha1','host_class','host_file','method','gold_target'])
    for c in sample:
        cid=c['case_id'];src=OUT/('screening/case_%04d'%cid);dest=OUT/('requests/case_%04d'%cid);dest.mkdir(parents=True)
        source_bytes=(src/'host.java').read_bytes();request=render(messages,c,source_bytes.decode('utf-8'))
        (dest/'host.java').write_bytes(source_bytes);dump(dest/'request.json',request)
        dump(dest/'input_record.json',{'prepared_at_utc':datetime.now(timezone.utc).isoformat(),'case_id':cid,
            'repository':c['repo_url'],'commit':c['commit'],'host_file':c['host_file'],'host_class':c['host_class'],
            'method_signature_from_frozen_sample':c['method'],'host_sha256':sha(source_bytes),
            'template_path':'docs/prompt_adapted.txt','template_sha256':sha((ROOT/'docs/prompt_adapted.txt').read_bytes()),
            'request_sha256':sha((dest/'request.json').read_bytes()),'status':'PREPARED_NOT_SENT','api_calls':0})
        shutil.copyfile(src/'ast.json',dest/'ast.json')
    print('Prepared six requests. No LLM calls. Gold labels were not printed or scored.')
if __name__=='__main__':main()