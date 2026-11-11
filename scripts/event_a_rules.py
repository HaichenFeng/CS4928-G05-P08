"""Unchanged M2 candidate/score rules, extracted without running M2 evaluation."""

import re

CONTAINERS={'Map','List','Set','Collection','Optional','Iterable','Queue','Deque','SortedMap','SortedSet'}

JDK={'String','Long','Integer','Double','Float','Boolean','Byte','Short','Character','Object','Void','Number','Duration'}

PRIMITIVES={'boolean','byte','short','int','long','float','double','char','void'}

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

def rank(ast,top1):
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
    return ranked,static,hybrid,variables

# --- Event B (D-13): single shared definition of the hybrid rule -------------
# The frozen scripts and rank() above keep their own inline copies unchanged,
# because they produced the tagged M2/Event A evidence. New callers use this.
EMPTY_POLICIES=('miss','static_fallback')

def hybrid_top1(llm_top1,candidates,static_top1,empty_policy):
    """D-03 hybrid rule: keep the LLM top-1 if it is a statically valid
    candidate, otherwise fall back to the static top-1.
    empty_policy decides the case the frozen rule left unspecified
    (the LLM returned an empty list, e.g. case 363):
      'miss'            -> None (no hybrid recommendation, scored as a miss)
      'static_fallback' -> static_top1"""
    if empty_policy not in EMPTY_POLICIES:
        raise ValueError('unknown empty_policy: %r'%(empty_policy,))
    if not llm_top1:
        return None if empty_policy=='miss' else static_top1
    return llm_top1 if llm_top1 in candidates else static_top1
