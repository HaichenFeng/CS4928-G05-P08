"""Evaluate preserved responses against the frozen manual. No LLM calls or resampling.

JavaParser ASTs supply direct host fields, actual method parameters and scoped
member accesses. These twelve methods require no inferred chained return types.
All class-existence claims are checked in their frozen Git commit.
"""
import csv, hashlib, json, os, re, subprocess, shutil, sys
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'outputs/runs/20261020T172353_759166Z'
GIT=shutil.which('git') or 'C:/Users/jl/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
OFFLINE='--offline' in sys.argv
ENV={k:v for k,v in os.environ.items() if k not in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE')}
ENV.update(TEMP=str(ROOT/'Codex-MM-Assist/temp'),TMP=str(ROOT/'Codex-MM-Assist/temp'),GIT_TERMINAL_PROMPT='0')
CONTAINERS={'Map','List','Set','Collection','Optional','Iterable','Queue','Deque','SortedMap','SortedSet'}
JDK={'String','Long','Integer','Double','Float','Boolean','Byte','Short','Character','Object','Void','Number','Duration'}
PRIMITIVES={'boolean','byte','short','int','long','float','double','char','void'}
def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def git(project,*args):
    command=[GIT,'--git-dir='+str(ROOT/'repos'/project),*args]
    result=subprocess.run(command,env=ENV,capture_output=True,timeout=180)
    return command,result
def split_args(text):
    pieces=[]; depth=0; start=0
    for i,c in enumerate(text):
        if c=='<': depth+=1
        if c=='>': depth-=1
        if c==',' and depth==0: pieces.append(text[start:i]); start=i+1
    pieces.append(text[start:]); return pieces
def concrete_types(text):
    text=re.sub(r'\s+','',text).replace('[]','')
    raw=text.split('<')[0]
    if raw.split('.')[-1] in CONTAINERS and '<' in text:
        return [t for a in split_args(text[text.index('<')+1:-1]) for t in concrete_types(a)]
    return [] if raw in PRIMITIVES or raw in JDK or raw in ('T','K','V','E','?') else [raw]
def resolve(name,ast):
    if '.' in name and name[0].islower(): return name
    for line in ast['imports']:
        value=line.strip().removeprefix('import ').removesuffix(';').strip()
        if not value.startswith('static ') and value.split('.')[-1]==name: return value
    return ast['package']+'.'+name
def fqn_path(tree,fqn):
    suffix='/'+fqn.replace('.','/')+'.java'
    return [p for p in tree if p.endswith(suffix)]

sample=list(csv.DictReader((ROOT/'data/sample_ids.csv').open(encoding='utf-8-sig')))
results=[]; audits=[]; tokens={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0}
for row in sample:
    cid=int(row['case_id']); ast=json.loads((ROOT/('outputs/evaluation/%s_ast.json'%cid)).read_text())
    case=RUN/('case_%04d'%cid)
    request=json.loads((case/'request.json').read_text(encoding='utf-8'))
    expected=json.loads((ROOT/('outputs/requests/case_%04d/request.json'%cid)).read_text(encoding='utf-8'))
    raw=json.loads((case/'response.raw.json').read_text(encoding='utf-8'))
    execution=json.loads((case/'execution.json').read_text())
    assert request==expected and request['model']=='gpt-4o-2024-05-13' and request['temperature']==0
    assert raw['model']==request['model'] and execution['http_status']==200
    assert hashlib.sha256((case/'request.json').read_bytes()).hexdigest()==execution['request_sha256']
    choice=raw['choices'][0]; assert choice['finish_reason']=='stop'
    content=choice['message']['content'].strip()
    if content.startswith('```'): content=re.sub(r'^```(?:json)?\s*|\s*```$','',content).strip()
    top1=json.loads(content)[0]['target_class'].strip()
    assert top1==json.loads((case/'parsed.json').read_text())['top1']
    for key in tokens: tokens[key]+=raw['usage'][key]
    candidates={}; variables={}
    for origin,vars in [('field',ast['fields']),('param',ast['parameters'])]:
        for var in vars:
            for name in concrete_types(var['type']):
                fqn=resolve(name,ast)
                if fqn.startswith(('java.','javax.')) or fqn==ast['host']: continue
                candidate=candidates.setdefault(fqn,{'candidate_fqn':fqn,'source':set(),'declarations':[],'occurrences':[],'score':0})
                candidate['source'].add(origin)
                candidate['declarations'].append({'origin':origin,**var})
            # Only a variable whose own declared type is T accesses T's members;
            # calling a container's member does not count as access to its element.
            if var['type'].split('<')[0].split('.')[-1] not in CONTAINERS:
                types=concrete_types(var['type'])
                if len(types)==1: variables[var['name']]=resolve(types[0],ast)
    for var in ast['locals']:
        types=concrete_types(var['type'])
        if var['type'].split('<')[0].split('.')[-1] not in CONTAINERS and len(types)==1:
            variables[var['name']]=resolve(types[0],ast)
    for access in ast['member_accesses']:
        scope=access['scope'].removeprefix('this.')
        fqn=variables.get(scope)
        if fqn in candidates:
            candidates[fqn]['occurrences'].append(access)
            candidates[fqn]['score']+=1
    ranked=sorted(candidates.values(),key=lambda c:(-c['score'],c['candidate_fqn']))
    for candidate in ranked: candidate['source']=';'.join(sorted(candidate['source']))
    static=ranked[0]['candidate_fqn'] if ranked else 'NONE'
    hybrid=top1 if top1 in candidates else static
    tree=(ROOT/('outputs/source_checks/%s_tree.txt'%cid)).read_text(encoding='utf-8').splitlines()
    paths=fqn_path(tree,top1)
    assert paths, 'Need full inner/non-public search before assigning H1: '+top1
    path=paths[0]
    evidence=ROOT/('outputs/h_check/%s.txt'%cid); evidence.parent.mkdir(exist_ok=True)
    if OFFLINE:
        source_bytes=(evidence.parent/('%s_target.java'%cid)).read_bytes()
        saved_evidence=evidence.read_text(encoding='utf-8')
        assert 'Frozen commit: '+row['commit'] in saved_evidence
        assert 'LLM FQN: '+top1 in saved_evidence
        assert 'Source SHA256: '+hashlib.sha256(source_bytes).hexdigest() in saved_evidence
    else:
        command,shown=git(row['project'],'show',row['commit']+':'+path)
        assert shown.returncode==0
        source_bytes=shown.stdout
    source=source_bytes.decode('utf-8')
    package=re.search(r'\bpackage\s+([\w.]+)\s*;',source).group(1)
    name=top1.rsplit('.',1)[1]
    assert package==top1.rsplit('.',1)[0]
    assert re.search(r'\b(class|interface|enum|record)\s+'+re.escape(name)+r'\b',source)
    if not OFFLINE:
        cmdtree,listed=git(row['project'],'ls-tree','-r','--name-only',row['commit'],'--',path)
        cmdgrep,grepped=git(row['project'],'grep','-n','-E',r'(class|interface|enum|record)[[:space:]]+'+name+r'([[:space:]]|<|\{)',row['commit'],'--',path)
        assert grepped.returncode==0
        evidence.write_text('Frozen commit: '+row['commit']+'\nLLM FQN: '+top1+'\n'+
            '$ '+' '.join(cmdtree)+'\n'+listed.stdout.decode('utf-8')+
            '\n$ '+' '.join(cmdgrep)+'\n'+grepped.stdout.decode('utf-8')+
            '\nSource package verified: '+package+'\nSource SHA256: '+hashlib.sha256(source_bytes).hexdigest()+
            '\nExists: true\nIn static candidate set: '+str(top1 in candidates)+'\n',encoding='utf-8')
        (evidence.parent/('%s_target.java'%cid)).write_bytes(source_bytes)
    h='NONE' if top1 in candidates else 'H2'
    out=ROOT/('outputs/static/%s.csv'%cid); out.parent.mkdir(exist_ok=True)
    with out.open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=['candidate_fqn','source','occurrences','score'])
        writer.writeheader()
        for candidate in ranked:
            writer.writerow({k:(';'.join(str(a['line'])+':'+a['scope']+'.'+a['member'] for a in candidate['occurrences']) if k=='occurrences' else candidate[k]) for k in writer.fieldnames})
    dump(ROOT/('outputs/static/%s.audit.json'%cid),{'case_id':cid,'host':ast['host'],
        'actual_method_source':ast['method_source'],'variables':variables,'ranked_candidates':ranked,
        'rule':'docs/coding_manual.md; direct host fields + actual named-method parameters; generic element types; count each AST member-access occurrence once; score-desc/FQN-asc'})
    results.append({'case_id':cid,'project':row['project'],'commit':row['commit'],'gold_target':row['gold_target'],
        'llm_top1':top1,'static_top1':static,'hybrid_top1':hybrid,'hallucination':h,
        'llm_recall1':int(top1==row['gold_target']),'static_recall1':int(static==row['gold_target']),
        'hybrid_recall1':int(hybrid==row['gold_target']),'llm_static_agree':int(top1==static),
        'candidate_count':len(candidates),'http_status':execution['http_status'],
        'returned_model':raw['model'],'request_id':execution['request_id']})
    declaration=ast['method_source'].split('{',1)[0].strip()
    expected_params=row['method'].split('(',1)[1].split(')',1)[0]
    expected_count=len(split_args(expected_params)) if expected_params else 0
    frozen_types=[p.strip().split(' ',1)[1].replace(' ','') for p in split_args(expected_params)] if expected_params else []
    actual_types=[p['type'].replace(' ','') for p in ast['parameters']]
    method_name=row['method'].split('(',1)[0].rsplit(' ',1)[-1]
    actual_return=declaration.split(method_name+'(',1)[0].removeprefix('private ').removeprefix('public ').strip().replace(' ','')
    frozen_return=row['method'].rsplit(':',1)[1].strip().replace(' ','')
    audits.append({'case_id':cid,'frozen_signature':row['method'],'actual_declaration':declaration,
        'frozen_parameter_count':expected_count,'actual_parameter_count':len(ast['parameters']),
        'frozen_parameter_types':frozen_types,'actual_parameter_types':actual_types,
        'parameter_types_match':frozen_types==actual_types,
        'frozen_return_type':frozen_return,'actual_return_type':actual_return,
        'return_type_matches':frozen_return==actual_return,
        'material_signature_mismatch':frozen_types!=actual_types or frozen_return!=actual_return,
        'gold_path_matches':fqn_path(tree,row['gold_target']),
        'note':'Actual named method selected uniquely by JavaParser; signatures preserved verbatim in the LLM request, never corrected after execution.'})

dest=ROOT/'outputs/lab4'; dest.mkdir(exist_ok=True)
with (dest/'results.csv').open('w',newline='',encoding='utf-8') as file:
    writer=csv.DictWriter(file,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
hall=sum(x['hallucination']!='NONE' for x in results)
summary={'evaluated_utc':datetime.now(timezone.utc).isoformat(),'n':len(results),'run':str(RUN.relative_to(ROOT)),
    'model':'gpt-4o-2024-05-13','temperature':0,'successful_responses':len(results),'usage':tokens,
    'H1':sum(x['hallucination']=='H1' for x in results),'H2':sum(x['hallucination']=='H2' for x in results),
    'H1_H2_rate':hall/len(results),'llm_recall1':sum(x['llm_recall1'] for x in results),
    'static_recall1':sum(x['static_recall1'] for x in results),'hybrid_recall1':sum(x['hybrid_recall1'] for x in results),
    'llm_static_agreement':sum(x['llm_static_agree'] for x in results),
    'RQ1_arithmetic_rule':'REPRODUCED' if hall>=4 else 'NOT REPRODUCED',
    'RQ2_non_decrease_rule':'SUPPORTED' if sum(x['hybrid_recall1'] for x in results)>=sum(x['llm_recall1'] for x in results) else 'NOT SUPPORTED',
    'hallucination_reduction_observed':False,'interpretation_status':'INCONCLUSIVE for intended paper reproduction pending input/gold validity review; as-frozen execution complete'}
summary['material_signature_mismatch_ids']=[x['case_id'] for x in audits if x['material_signature_mismatch']]
dump(dest/'summary.json',summary);dump(dest/'input_audit.json',audits)
print(json.dumps(summary,indent=2))
for x in results: print(x['case_id'],x['hallucination'],x['llm_recall1'],x['static_recall1'],x['hybrid_recall1'],x['llm_static_agree'])
