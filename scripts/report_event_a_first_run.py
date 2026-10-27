"""Descriptive first-run report; preserves and discloses the frozen empty-output stop."""
import argparse,csv,hashlib,json,os,re,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone
from event_a_rules import rank
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/event_a_gpt6_luna'
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
    tree=(SCREENING/('case_%04d/tree.txt'%cid)).read_text(encoding='utf-8').splitlines()
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


PRIMARY_RUN=ROOT/'outputs/event_a_gpt6_luna/runs/20261027T140405_285837Z'
SUPPLEMENT_RUN=ROOT/'outputs/event_a_supplement_368/runs/20261027T141400_074189Z'
JAVA='F:/IntelliJ IDEA 2024.1.7/jbr/bin/java.exe'
def assess(sample_path,base,run,screening,role):
    global OUT,SCREENING
    OUT=base/'first_run_report';SCREENING=screening;OUT.mkdir(exist_ok=True)
    rows=readcsv(sample_path);results=[];audits=[];usage={}
    frozen_hashes=json.loads((run/'prepared_request_hashes.json').read_text(encoding='utf-8'))
    for row in rows:
        cid=int(row['case_id']);folder=run/('case_%04d'%cid);prepared=base/('requests/case_%04d'%cid)
        req=json.loads((folder/'request.json').read_text(encoding='utf-8'))
        assert req==json.loads((prepared/'request.json').read_text(encoding='utf-8'))
        assert sha((prepared/'request.json').read_bytes())==frozen_hashes[str(cid)]
        assert req['model']=='gpt-6-luna' and req['temperature']==0 and req['reasoning_effort']=='none'
        execution=json.loads((folder/'execution.json').read_text(encoding='utf-8'))
        assert execution['request_sha256']==sha((folder/'request.json').read_bytes())
        raw=json.loads((folder/'response.raw.json').read_text(encoding='utf-8'))
        assert execution['http_status']==200 and raw['model']=='gpt-6-luna' and raw['choices'][0]['finish_reason']=='stop'
        content=raw['choices'][0]['message']['content'].strip()
        if content.startswith('```'):content=re.sub(r'^```(?:json)?\s*|\s*```$','',content).strip()
        data=json.loads(content);assert isinstance(data,list)
        ast=json.loads((prepared/'ast.json').read_text(encoding='utf-8'))
        ranked,static,_,variables=rank(ast,'');candidates={x['candidate_fqn'] for x in ranked}
        if data:
            top=data[0]['target_class'].strip();assert execution['status']=='VALID_RESPONSE'
            assert top==json.loads((folder/'parsed.json').read_text(encoding='utf-8'))['top1'].strip()
            resolved,exists=target_check(row,top,JAVA,False)
            label='H1' if not exists else ('NONE' if resolved in candidates else 'H2')
            fallback=resolved not in candidates;hybrid=static if fallback else resolved
            llm_hit=int(resolved==row['gold_target']);hybrid_hit=int(hybrid==row['gold_target'])
            agree=int(resolved==static)
        else:
            assert cid==363 and execution['status']=='BLOCKED'
            top=resolved='';label='NO_RECOMMENDATION';fallback=None;hybrid=None;hybrid_hit=None
            # Report this convention explicitly as descriptive, rather than changing the frozen parser.
            llm_hit=0;agree=0
        results.append({'case_id':cid,'role':role,'upstream_sha1':row['upstream_sha1'],'commit':row['commit'],
            'host_class':row['host_class'],'method':row['method'],'gold_target':row['gold_target'],
            'raw_top1':top,'resolved_top1':resolved,'static_top1':static,'hybrid_top1':hybrid,
            'recommendation_count':len(data),'output_label':label,'frozen_parser_status':execution['status'],
            'llm_recall1_descriptive_empty_is_miss':llm_hit,'static_recall1':int(static==row['gold_target']),
            'hybrid_recall1_frozen':hybrid_hit,'agreement_descriptive_empty_is_disagreement':agree,
            'fallback_used_frozen':None if fallback is None else int(fallback),
            'fallback_miss_to_hit':None if fallback is None else int(fallback and not llm_hit and hybrid_hit),
            'fallback_hit_to_miss':None if fallback is None else int(fallback and llm_hit and not hybrid_hit),
            'candidate_count':len(ranked),'http_status':200,'returned_model':raw['model'],'request_id':execution.get('request_id')})
        dump(OUT/('static/%s.audit.json'%cid),{'case_id':cid,'host':ast['host'],'actual_method_source':ast['method_source'],
            'ranked_candidates':ranked,'variables':variables,'rule':'Unchanged M2 static ranking'})
        audits.append({'case_id':cid,'frozen_signature':row['method'],'actual_method_declaration':ast['method_source'].split('{',1)[0].strip(),
            'frozen_parameter_types':ast['frozen_parameter_types'],'actual_parameter_types':[p['type'] for p in ast['parameters']],
            'frozen_return_type':row['method'].rsplit(':',1)[-1].strip(),'actual_return_type':ast['actual_return_type'],
            'rule4_selection':ast['rule4_selection'],'signature_sent_unchanged':True})
        for k,v in raw['usage'].items():
            if isinstance(v,int):usage[k]=usage.get(k,0)+v
        print('Verified and coded',cid,label,flush=True)
    writecsv(OUT/'observations.csv',results);dump(OUT/'input_audit.json',audits)
    dump(OUT/'usage.json',usage)
    return results,OUT

def summarize(rows,cluster=False):
    groups={}
    for r in rows:groups.setdefault(r['upstream_sha1'] if cluster else str(r['case_id']),[]).append(r)
    def value(key):return sum(sum(float(r[key]) for r in g)/len(g) for g in groups.values())
    n=len(groups);llm=value('llm_recall1_descriptive_empty_is_miss');static=value('static_recall1')
    agree=value('agreement_descriptive_empty_is_disagreement')
    halluc=sum(sum(r['output_label'] in ('H1','H2') for r in g)/len(g) for g in groups.values())
    low=sum(sum(float(r['hybrid_recall1_frozen'] or 0) for r in g)/len(g) for g in groups.values())
    missing=sum(sum(r['hybrid_recall1_frozen'] is None for r in g)/len(g) for g in groups.values())
    # These are explicitly post-hoc sensitivity conventions, never substituted for frozen primary output.
    static_empty=sum(sum(float(r['hybrid_recall1_frozen'] if r['hybrid_recall1_frozen'] is not None else r['static_recall1']) for r in g)/len(g) for g in groups.values())
    return {'units':n,'groups':[[r['case_id'] for r in g] for g in groups.values()],
        'llm_hits_descriptive_empty_is_miss':llm,'llm_rate_descriptive':llm/n,'static_hits':static,'static_rate':static/n,
        'agreement_descriptive':agree,'agreement_rate_descriptive':agree/n,'H1_H2_weighted_count':halluc,'H1_H2_rate':halluc/n,
        'challenges_a_using_registered_rate_threshold':halluc/n>0.25,'frozen_hybrid_metric_defined':missing==0,
        'frozen_hybrid_known_hits':low,'frozen_hybrid_unresolved_weight':missing,'hybrid_rate_bounds':[low/n,(low+missing)/n],
        'posthoc_empty_as_no_output_hybrid_hits':low,'posthoc_empty_use_static_hybrid_hits':static_empty,
        'no_recommendation_ids':[r['case_id'] for r in rows if r['recommendation_count']==0]}

def main():
    primary,pdest=assess(ROOT/'data/event_a_sample_ids.csv',ROOT/'outputs/event_a_gpt6_luna',PRIMARY_RUN,ROOT/'outputs/event_a/screening','PRIMARY_FIRST_RUN')
    supplement,sdest=assess(ROOT/'data/event_a_supplement_368.csv',ROOT/'outputs/event_a_supplement_368',SUPPLEMENT_RUN,ROOT/'outputs/event_a_supplement_368/screening','POST_PRIMARY_SUPPLEMENT_NOT_REPLACEMENT')
    p=summarize(primary);c=summarize(primary,True);supp=summarize(supplement)
    summary={'primary':p,'primary_commit_clusters':c,'supplement_368_separate':supp,
        'primary_H1':sum(r['output_label']=='H1' for r in primary),'primary_H2':sum(r['output_label']=='H2' for r in primary),
        'first_run_status':'Six HTTP-200 responses; frozen parser stops on 363 empty list. Hybrid empty-output policy unspecified.',
        'challenges_a_robust_to_pair':p['challenges_a_using_registered_rate_threshold']==c['challenges_a_using_registered_rate_threshold'],
        'model_confounded_with_project_change':True,'no_new_llm_calls':True,'no_case_replacement':True}
    dump(pdest/'summary.json',summary);dump(sdest/'summary.json',{'supplement_only':supp,'primary_denominator_unchanged':True})
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
