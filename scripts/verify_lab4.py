"""Verify the saved evidence chain without API calls or external dependencies."""
import csv, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'outputs/runs/20261020T172353_759166Z'
IDS=[1,2,3,5,7,8,14,15,16,17,19,21]
sample=list(csv.DictReader((ROOT/'data/sample_ids.csv').open(encoding='utf-8-sig')))
assert [int(x['case_id']) for x in sample]==IDS
results=list(csv.DictReader((ROOT/'outputs/lab4/results.csv').open(encoding='utf-8-sig')))
assert [int(x['case_id']) for x in results]==IDS
manifest=json.loads((RUN/'run_manifest.json').read_text())
assert hashlib.sha256((RUN/'runner.py').read_bytes()).hexdigest()==manifest['runner_sha256']
usage={k:0 for k in ('prompt_tokens','completion_tokens','total_tokens')}
for row,result in zip(sample,results):
    cid=int(row['case_id']); folder=RUN/('case_%04d'%cid)
    request=json.loads((folder/'request.json').read_text(encoding='utf-8'))
    execution=json.loads((folder/'execution.json').read_text())
    response=json.loads((folder/'response.raw.json').read_text(encoding='utf-8'))
    assert request==json.loads((ROOT/('outputs/requests/case_%04d/request.json'%cid)).read_text(encoding='utf-8'))
    assert hashlib.sha256((folder/'request.json').read_bytes()).hexdigest()==execution['request_sha256']
    assert response['model']==request['model']=='gpt-4o-2024-05-13'
    assert request['temperature']==0 and execution['http_status']==200
    assert response['choices'][0]['finish_reason']=='stop'
    assert execution['status']=='VALID_RESPONSE'
    preparation=ROOT/('outputs/requests/case_%04d'%cid)
    source=preparation/'host.java'
    verification=json.loads((preparation/'source_verification.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==verification['sha256']
    assert row['method'] in request['messages'][-1]['content']
    assert source.read_text(encoding='utf-8') in request['messages'][-1]['content']
    ranking=list(csv.DictReader((ROOT/('outputs/static/%s.csv'%cid)).open(encoding='utf-8-sig')))
    assert ranking==sorted(ranking,key=lambda x:(-int(x['score']),x['candidate_fqn']))
    assert result['static_top1']==(ranking[0]['candidate_fqn'] if ranking else 'NONE')
    candidates={x['candidate_fqn'] for x in ranking}
    assert result['hybrid_top1']==(result['llm_top1'] if result['llm_top1'] in candidates else result['static_top1'])
    assert int(result['llm_recall1'])==int(result['llm_top1']==row['gold_target'])
    assert int(result['static_recall1'])==int(result['static_top1']==row['gold_target'])
    assert int(result['hybrid_recall1'])==int(result['hybrid_top1']==row['gold_target'])
    evidence=(ROOT/('outputs/h_check/%s.txt'%cid)).read_text(encoding='utf-8')
    assert 'Frozen commit: '+row['commit'] in evidence and 'LLM FQN: '+result['llm_top1'] in evidence
    assert 'Source SHA256: '+hashlib.sha256((ROOT/('outputs/h_check/%s_target.java'%cid)).read_bytes()).hexdigest() in evidence
    for key in usage: usage[key]+=response['usage'][key]
summary=json.loads((ROOT/'outputs/lab4/summary.json').read_text())
assert summary['usage']==usage
for key,column in [('llm_recall1','llm_recall1'),('static_recall1','static_recall1'),('hybrid_recall1','hybrid_recall1'),('llm_static_agreement','llm_static_agree')]:
    assert summary[key]==sum(int(x[column]) for x in results)
assert summary['H1']==sum(x['hallucination']=='H1' for x in results)
assert summary['H2']==sum(x['hallucination']=='H2' for x in results)
assert (RUN/'pilot_approved.json').exists() and (RUN/'bounded_run_complete.json').exists()
assert summary['material_signature_mismatch_ids']==[3,5,15,16,19,21]
integrity=json.loads((ROOT/'outputs/lab4/frozen_input_integrity.json').read_text())
assert all(x['matches_M1_PLAN_after_line_ending_normalisation'] for x in integrity[:3])
checksum_file=ROOT/'outputs/lab4/evidence_manifest.sha256'
if checksum_file.exists():
    for line in checksum_file.read_text(encoding='utf-8').splitlines():
        digest,relative=line.split('  ',1)
        assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest, relative
# Inspect only intended submission paths; never scan password stores or ignored caches.
files=[p for directory in ('docs','scripts','data','outputs') for p in (ROOT/directory).rglob('*')
       if p.is_file() and p.suffix not in ('.class','.pyc') and '__pycache__' not in p.parts]
for path in files:
    assert not re.search(rb'sk-(?:proj-)?[A-Za-z0-9_-]{25,}',path.read_bytes()), 'Potential secret in '+str(path)
print('PASS: 12-case input/request/response/model/hash/score/hybrid/metric chain; runner snapshot; no API-key patterns in submission files.')
print('Validity caveats retained: signature discrepancies and gold-package issue; not a clean paper reproduction.')
