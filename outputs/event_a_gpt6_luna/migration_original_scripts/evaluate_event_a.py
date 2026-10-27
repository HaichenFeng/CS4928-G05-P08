"""Evaluate preserved Event A responses with the unchanged M2 static/hybrid rules."""
import argparse,csv,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone
from event_a_rules import rank
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/event_a'
ENV={k:v for k,v in os.environ.items() if k not in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE')}
ENV['GIT_TERMINAL_PROMPT']='0'
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def readcsv(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
def writecsv(p,rows):
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def git(row,*args):
    cmd=[shutil.which('git'),'--git-dir='+str(ROOT/'repos'/row['project']),*args]
    result=subprocess.run(cmd,capture_output=True,env=ENV,timeout=240)
    if result.returncode not in (0,1):raise RuntimeError(result.stderr.decode(errors='replace'))
    return cmd,result

def target_check(row,target,java,offline):
    """Verify actual declarations, including nested/non-public classes. Never infer from filename alone."""
    cid=int(row['case_id']);dest=OUT/('h_check/%s'%cid);dest.mkdir(parents=True,exist_ok=True)
    cache=dest/'resolution.json'
    if offline:
        old=json.loads(cache.read_text(encoding='utf-8'))
        assert old['target']==target and old['commit']==row['commit']
        for item in old['sources']:
            assert sha((dest/item['saved_name']).read_bytes())==item['sha256']
        return old['resolved'],old['exists']
    tree=(OUT/('screening/case_%04d/tree.txt'%cid)).read_text(encoding='utf-8').splitlines()
    names=target.split('.');simple=names[-1];qualified='.' in target and target[0].islower()
    # A nested target's outer class normally supplies a filename. Also search declarations
    # if that route cannot establish an exact FQN or unique simple-name match.
    filename_names=[n for n in names if n and n[0].isupper()]
    paths=[p for p in tree if p.endswith('.java') and Path(p).stem in filename_names]
    deps=ROOT/'Codex-MM-Assist/work/dependencies'
    cp=os.pathsep.join(str(deps/x) for x in ['javaparser-core-3.26.2.jar','gson-2.10.1.jar'])
    sources=[];found=set();visited=set();commands=[]
    def inspect(paths):
        for path in paths:
            if path in visited:continue
            visited.add(path);cmd,res=git(row,'show',row['commit']+':'+path)
            if res.returncode:raise RuntimeError('Cannot load target source '+path)
            saved='source_%03d.java'%len(sources);file=dest/saved;file.write_bytes(res.stdout)
            index=dest/(saved+'.types.json')
            run=subprocess.run([java,'-cp',cp,str(ROOT/'scripts/IndexEventAClass.java'),str(file),str(index)],capture_output=True)
            if run.returncode:raise RuntimeError(run.stderr.decode(errors='replace'))
            classes=json.loads(index.read_text(encoding='utf-8'));found.update(classes)
            sources.append({'path':path,'saved_name':saved,'sha256':sha(res.stdout),'declared_types':classes})
            commands.append('$ '+' '.join(cmd)+'\n')
    inspect(paths)
    exact=target in found
    # For simple names, global declaration search is necessary to establish uniqueness.
    if not exact:
        pattern=r'(class|interface|enum|record)[[:space:]]+'+re.escape(simple)+r'([[:space:]]|<|\{|\()'
        cmd,res=git(row,'grep','-l','-E',pattern,row['commit'],'--','*.java')
        commands.append('$ '+' '.join(cmd)+'\n'+res.stdout.decode(errors='replace')+res.stderr.decode(errors='replace'))
        prefix=row['commit']+':'
        more=[line.removeprefix(prefix) for line in res.stdout.decode('utf-8').splitlines()]
        inspect(more)
    if qualified:matches=[target] if target in found else []
    elif '.' in target:matches=[f for f in found if f.endswith('.'+target)]
    else:matches=[f for f in found if f.rsplit('.',1)[-1]==target]
    matches=sorted(set(matches))
    if len(matches)>1:raise RuntimeError('Ambiguous LLM simple target; manual coding required, do not guess: '+target)
    resolved=matches[0] if matches else target
    result={'target':target,'commit':row['commit'],'resolved':resolved,'exists':bool(matches),'sources':sources,'checked_paths':sorted(visited)}
    dump(cache,result)
    (OUT/('h_check/%s.txt'%cid)).write_text('Frozen commit: '+row['commit']+'\nLLM target: '+target+'\nResolved: '+resolved+'\nExists: '+str(bool(matches))+'\n'+'\n'.join(commands),encoding='utf-8')
    return resolved,bool(matches)

METRICS=['llm_recall1','static_recall1','hybrid_recall1','llm_static_agree','h1_h2','fallback_used','fallback_miss_to_hit','fallback_hit_to_miss']
def metrics(rows,clustered=False):
    groups={}
    for row in rows:
        key=row['upstream_sha1'] if clustered else row['case_id'];groups.setdefault(key,[]).append(row)
    sums={k:sum(sum(float(r[k]) for r in g)/len(g) for g in groups.values()) for k in METRICS}
    return {'units':len(groups),'numerators':sums,'rates':{k:v/len(groups) for k,v in sums.items()},
        'groups':[[int(r['case_id']) for r in g] for g in groups.values()]}
def conclusions(m):
    r=m['rates']
    return {'challenges_a':r['h1_h2']>0.25,'challenges_b':r['hybrid_recall1']<r['llm_recall1'],
        'strengthens_b':r['fallback_used']>0 and r['hybrid_recall1']>r['llm_recall1'],
        'uninformative_b':r['fallback_used']==0}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--java',required=True);ap.add_argument('--offline',action='store_true');args=ap.parse_args()
    run=args.run.resolve();assert run.is_relative_to(OUT/'runs'),'Use an Event A run'
    sample=readcsv(ROOT/'data/event_a_sample_ids.csv');assert len(sample)==6
    assert (run/'sample_ids.csv').read_bytes()==(ROOT/'data/event_a_sample_ids.csv').read_bytes()
    (OUT/'static').mkdir(exist_ok=True);results=[];audits=[];usage={}
    for row in sample:
        cid=int(row['case_id']);case=run/('case_%04d'%cid);prepared=OUT/('requests/case_%04d'%cid)
        request=json.loads((case/'request.json').read_text(encoding='utf-8'))
        assert request==json.loads((prepared/'request.json').read_text(encoding='utf-8'))
        assert request['model']=='gpt-4o-2024-05-13' and request['temperature']==0
        record=json.loads((case/'execution.json').read_text(encoding='utf-8'));raw=json.loads((case/'response.raw.json').read_text(encoding='utf-8'))
        assert record['http_status']==200 and record['status']=='VALID_RESPONSE'
        assert record['request_sha256']==sha((case/'request.json').read_bytes())
        assert raw['model']==request['model'] and raw['choices'][0]['finish_reason']=='stop'
        content=raw['choices'][0]['message']['content'].strip()
        if content.startswith('```'):content=re.sub(r'^```(?:json)?\s*|\s*```$','',content).strip()
        top1=json.loads(content)[0]['target_class'].strip()
        assert top1==json.loads((case/'parsed.json').read_text(encoding='utf-8'))['top1'].strip()
        for k,v in raw.get('usage',{}).items():
            if isinstance(v,int):usage[k]=usage.get(k,0)+v
        ast=json.loads((prepared/'ast.json').read_text(encoding='utf-8'))
        ranked,static,_,variables=rank(ast,top1)
        resolved,exists=target_check(row,top1,args.java,args.offline)
        candidates={c['candidate_fqn'] for c in ranked}
        hallucination='H1' if not exists else ('NONE' if resolved in candidates else 'H2')
        fallback=resolved not in candidates;hybrid=static if fallback else resolved
        llm_hit=int(resolved==row['gold_target']);hybrid_hit=int(hybrid==row['gold_target'])
        results.append({'case_id':cid,'project':row['project'],'commit':row['commit'],'upstream_sha1':row['upstream_sha1'],
            'gold_target':row['gold_target'],'llm_raw_top1':top1,'llm_top1':resolved,'static_top1':static,'hybrid_top1':hybrid,
            'hallucination':hallucination,'llm_recall1':llm_hit,'static_recall1':int(static==row['gold_target']),
            'hybrid_recall1':hybrid_hit,'llm_static_agree':int(resolved==static),'h1_h2':int(hallucination!='NONE'),
            'candidate_count':len(candidates),'fallback_used':int(fallback),
            'fallback_miss_to_hit':int(fallback and not llm_hit and hybrid_hit),
            'fallback_hit_to_miss':int(fallback and llm_hit and not hybrid_hit),
            'http_status':200,'returned_model':raw['model'],'request_id':record.get('request_id')})
        with (OUT/('static/%s.csv'%cid)).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=['candidate_fqn','source','occurrences','score']);w.writeheader()
            for c in ranked:w.writerow({k:(';'.join(str(a['line'])+':'+a['scope']+'.'+a['member'] for a in c['occurrences']) if k=='occurrences' else c[k]) for k in w.fieldnames})
        dump(OUT/('static/%s.audit.json'%cid),{'case_id':cid,'host':ast['host'],'actual_method_source':ast['method_source'],'variables':variables,'ranked_candidates':ranked})
        frozen_types=ast['frozen_parameter_types'];actual_types=[re.sub(r'\s+','',p['type']) for p in ast['parameters']]
        frozen_return=row['method'].rsplit(':',1)[-1].strip();actual_return=ast['actual_return_type']
        audits.append({'case_id':cid,'frozen_signature':row['method'],'actual_declaration':ast['method_source'].split('{',1)[0].strip(),
            'frozen_parameter_types':frozen_types,'actual_parameter_types':actual_types,'parameter_types_match':frozen_types==actual_types,
            'frozen_return_type':frozen_return,'actual_return_type':actual_return,'return_type_matches':re.sub(r'\s+','',frozen_return)==re.sub(r'\s+','',actual_return),
            'rule4_selection':ast['rule4_selection'],'note':'Dataset signature sent unchanged; actual source used for static coding.'})
    primary=metrics(results);sensitivity=metrics(results,True)
    m2sample={r['case_id']:r for r in readcsv(ROOT/'data/sample_ids.csv')};m2=[]
    for row in readcsv(ROOT/'outputs/lab4/results.csv'):
        row['upstream_sha1']=m2sample[row['case_id']]['upstream_sha1'];row['h1_h2']=int(row['hallucination']!='NONE')
        # M2 had zero fallbacks; verify against its preserved candidate audit before recounting.
        audit=json.loads((ROOT/('outputs/static/%s.audit.json'%row['case_id'])).read_text(encoding='utf-8'))
        fallback=row['llm_top1'] not in {c['candidate_fqn'] for c in audit['ranked_candidates']}
        row['fallback_used']=int(fallback);row['fallback_miss_to_hit']=int(fallback and row['llm_recall1']=='0' and row['hybrid_recall1']=='1')
        row['fallback_hit_to_miss']=int(fallback and row['llm_recall1']=='1' and row['hybrid_recall1']=='0');m2.append(row)
    pcon=conclusions(primary);scon=conclusions(sensitivity)
    summary={'evaluated_utc':datetime.now(timezone.utc).isoformat(),'n':6,'run':str(run.relative_to(ROOT)),
        'model':'gpt-4o-2024-05-13','temperature':0,'usage':usage,
        'H1':sum(r['hallucination']=='H1' for r in results),'H2':sum(r['hallucination']=='H2' for r in results),
        'primary':primary,'developer_commit_sensitivity':sensitivity,'primary_conclusions':pcon,'sensitivity_conclusions':scon,
        'conclusion_robustness':{k:'robust to developer-commit clustering' if pcon[k]==scon[k] else 'depends on the paired cases; weak' for k in pcon},
        'm2_primary_recount':metrics(m2),'m2_developer_commit_recount':metrics(m2,True),
        'predictions_met':{'P1':3<=primary['numerators']['llm_recall1']<=5,'P2':primary['numerators']['h1_h2']<=1,
            'P3_static':primary['numerators']['static_recall1']<=primary['numerators']['llm_recall1'],
            'P3_agreement':3<=primary['numerators']['llm_static_agree']<=5,'P4':not pcon['challenges_b']}}
    writecsv(OUT/'results.csv',results);dump(OUT/'summary.json',summary);dump(OUT/'input_audit.json',audits)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()