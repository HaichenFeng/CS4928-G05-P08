"""Screen and prepare only the prospectively fixed supplementary case 368. No API call."""
import argparse,json,zipfile,re,subprocess,os,shutil
from pathlib import Path
from datetime import datetime,timezone
from prepare_event_a import ROOT,ARCHIVE,EXPECTED,sha,dump,git,ENV,GIT,csvout,frozen_messages,render
OUT=ROOT/'outputs/event_a_supplement_368'
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--java',required=True);args=ap.parse_args()
    plan=ROOT/'docs/event_a_supplement_368.md';assert plan.exists()
    if OUT.exists():raise SystemExit('Supplement evidence exists; preserve it and review before another attempt.')
    assert sha(ARCHIVE.read_bytes())==EXPECTED
    OUT.mkdir(parents=True)
    primary=ROOT/'outputs/event_a_gpt6_luna'
    originals={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in primary.rglob('*') if p.is_file()}
    dump(OUT/'primary_evidence_hashes.json',originals)
    dump(OUT/'plan_manifest.json',{'registered_plan_sha256':sha(plan.read_bytes()),'started_utc':datetime.now(timezone.utc).isoformat(),
        'case_id':368,'role':'POST_PRIMARY_SUPPLEMENT_NOT_REPLACEMENT','api_calls':0,'gold_used_for_selection':False})
    record=None
    with zipfile.ZipFile(ARCHIVE) as z:
        for name in z.namelist():
            if not name.startswith('data/') or '/instance-methods/mm-assist-emm/' not in name or not name.endswith('_res.json'):continue
            for row in json.loads(z.read(name)):
                if int(row['ref_id'])==368:
                    assert record is None,'Duplicate ref_id';record=row
    assert record is not None
    mm=record['move_method_refactoring'];ex=record.get('extraction_results',{})
    project=record['repository'].rstrip('/').removesuffix('.git').split('/')[-1]
    assert project=='elasticsearch'
    eligible=not mm['isStatic'] and str(ex.get('success')).lower()=='true' and 'telemetry' in record
    if not eligible:
        dump(OUT/'screening.json',{'case_id':368,'included':False,'reason':'rules1/2 failed'});raise SystemExit('368 ineligible. Stop; no next reserve.')
    match=re.search(r'in class (?P<host>\S+) & moved to class (?P<target>\S+)$',mm['description'])
    method=next(x for x in mm['rightSideLocations'] if x['description']=='extracted method declaration')['codeElement']
    c={'case_id':368,'project':project,'commit':ex['newCommitHash'],'upstream_sha1':record['sha1'],
       'host_class':match['host'],'host_file':mm['leftSideLocations'][0]['filePath'],'method':method,'gold_target':match['target']}
    folder=OUT/'screening/case_0368';folder.mkdir(parents=True)
    repo=ROOT/'repos'/project
    cmd,fetch=git(repo,'fetch','--depth=1','--filter=blob:none','origin',c['commit'])
    (folder/'fetch.txt').write_text('$ '+' '.join(cmd)+'\n'+fetch.stdout.decode(errors='replace')+fetch.stderr.decode(errors='replace'),encoding='utf-8')
    if fetch.returncode:
        dump(OUT/'screening.json',{'case_id':368,'included':False,'reason':'fetch failed; inspect evidence, no replacement selected'});fetch.check_returncode()
    _,tree=git(repo,'ls-tree','-r','--name-only',c['commit']);tree.check_returncode();(folder/'tree.txt').write_bytes(tree.stdout)
    _,source=git(repo,'show',c['commit']+':'+c['host_file']);source.check_returncode();(folder/'host.java').write_bytes(source.stdout)
    deps=ROOT/'Codex-MM-Assist/work/dependencies'
    cp=os.pathsep.join(str(deps/x) for x in ['javaparser-core-3.26.2.jar','gson-2.10.1.jar'])
    parsed=subprocess.run([args.java,'-cp',cp,str(ROOT/'scripts/InspectEventACase.java'),str(folder/'host.java'),c['host_class'],c['method'],str(folder/'ast.json')],capture_output=True)
    (folder/'method_check.txt').write_bytes(parsed.stdout+parsed.stderr)
    if parsed.returncode:
        dump(OUT/'screening.json',{'case_id':368,'included':False,'reason':'method check failed; inspect evidence, no next reserve'});parsed.check_returncode()
    dump(OUT/'screening.json',{'case_id':368,'project':project,'commit':c['commit'],'included':True,'reason':'rules1-4 passed'})
    csvout(ROOT/'data/event_a_supplement_368.csv',[c],list(c))
    messages=frozen_messages((ROOT/'docs/prompt_adapted.txt').read_text(encoding='utf-8'))
    request=render(messages,c,source.stdout.decode('utf-8'));request['model']='gpt-6-luna';request['reasoning_effort']='none'
    dest=OUT/'requests/case_0368';dest.mkdir(parents=True)
    dump(dest/'request.json',request);(dest/'host.java').write_bytes(source.stdout);shutil.copyfile(folder/'ast.json',dest/'ast.json')
    dump(dest/'input_record.json',{'case_id':368,'repository':record['repository'],'commit':c['commit'],'host_file':c['host_file'],
        'host_class':c['host_class'],'method_signature_from_frozen_sample':method,'host_sha256':sha(source.stdout),
        'request_sha256':sha((dest/'request.json').read_bytes()),'template_sha256':sha((ROOT/'docs/prompt_adapted.txt').read_bytes()),
        'model':'gpt-6-luna','temperature':0,'reasoning_effort':'none','status':'PREPARED_NOT_SENT','api_calls':0,
        'role':'POST_PRIMARY_SUPPLEMENT_NOT_REPLACEMENT'})
    assert all(sha((ROOT/p).read_bytes())==h for p,h in originals.items()),'Primary evidence changed'
    print('368 eligible; independent request prepared. Primary six and all evidence unchanged. No API calls; no gold labels printed.')
if __name__=='__main__':main()