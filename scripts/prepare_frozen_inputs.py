"""Prepare the already-frozen sample; never resample or include oracle fields in prompts."""
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re
import zipfile
from urllib.request import urlopen
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'Codex-MM-Assist/mm-assist/replication-package/artifacts/datasets.zip'
EXPECTED = '8b2808944db28ba6620f07a71fce38224f32cc100a444bb89573f662e268c3eb'
def sha(data): return hashlib.sha256(data).hexdigest()
assert sha(ARCHIVE.read_bytes()) == EXPECTED
sample = list(csv.DictReader((ROOT/'data/sample_ids.csv').open(encoding='utf-8-sig')))
assert [int(x['case_id']) for x in sample] == [1,2,3,5,7,8,14,15,16,17,19,21]
records = {}
with zipfile.ZipFile(ARCHIVE) as z:
    for name in z.namelist():
        if name.startswith('data/') and '/instance-methods/mm-assist-emm/' in name and name.endswith('_res.json'):
            for record in json.loads(z.read(name)):
                records[int(record['ref_id'])] = record
assert len(records) == 117
template = (ROOT/'docs/prompt_adapted.txt').read_text(encoding='utf-8')
roles = list(re.finditer(r'^\[(SYSTEM|USER|ASSISTANT)\]\s*$', template, re.M))
messages = []
for i, match in enumerate(roles):
    content = template[match.end():roles[i+1].start() if i+1<len(roles) else len(template)]
    content = re.sub(r'\n# Top-1.*', '', content, flags=re.S).strip()
    messages.append({'role':match[1].lower(),'content':content})

def prepare(row):
    case_id = int(row['case_id'])
    record = records[case_id]
    assert record['extraction_results']['newCommitHash'] == row['commit']
    assert not record['move_method_refactoring']['isStatic']
    assert str(record['extraction_results']['success']).lower() == 'true'
    repo = record['repository'].removesuffix('.git').removeprefix('https://github.com/')
    url = 'https://raw.githubusercontent.com/' + repo + '/' + row['commit'] + '/' + row['host_file']
    with urlopen(url, timeout=90) as response:
        source_bytes = response.read()
    source = source_bytes.decode('utf-8')
    request = {'model':'gpt-4o-2024-05-13','temperature':0,'messages':[
        {'role':m['role'], 'content':m['content'].replace('{METHOD_SIGNATURE}',row['method']).replace('{HOST_CLASS_SOURCE}',source)}
        for m in messages]}
    folder = ROOT / ('outputs/requests/case_%04d' % case_id)
    folder.mkdir(parents=True, exist_ok=True)
    if (folder/'request.json').exists():
        old = json.loads((folder/'request.json').read_text(encoding='utf-8'))
        assert old == request, 'Prepared request differs from preserved request: %s' % case_id
        assert (folder/'host.java').read_bytes() == source_bytes, 'Host changed'
    else:
        (folder/'host.java').write_bytes(source_bytes)
        (folder/'request.json').write_text(json.dumps(request,ensure_ascii=False,indent=2),encoding='utf-8')
        (folder/'input_record.json').write_text(json.dumps({
            'prepared_at_utc':datetime.now(timezone.utc).isoformat(), 'case_id':case_id,
            'repository':record['repository'],'commit':row['commit'],'host_file':row['host_file'],
            'host_class':row['host_class'],'method_signature_from_frozen_sample':row['method'],
            'host_sha256':sha(source_bytes),'template_path':'docs/prompt_adapted.txt',
            'template_sha256':sha((ROOT/'docs/prompt_adapted.txt').read_bytes()),
            'request_sha256':sha((folder/'request.json').read_bytes()),'source_url':url,
            'status':'PREPARED_NOT_SENT','api_calls':0,
            'notes':'Gold target and author recommendations excluded from request; frozen template unchanged.'
        },ensure_ascii=False,indent=2),encoding='utf-8')
    # Separate verification preserves earlier preparation manifests unchanged.
    (folder/'source_verification.json').write_text(json.dumps({
        'verified_at_utc':datetime.now(timezone.utc).isoformat(),'source_url':url,
        'sha256':sha(source_bytes),'matches_preserved_source':True,
        'request_sha256':sha((folder/'request.json').read_bytes())},indent=2),encoding='utf-8')
    return '%s prepared; source=%s' % (case_id, sha(source_bytes))

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(prepare, sample):
            print(result, flush=True)
