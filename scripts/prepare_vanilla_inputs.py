"""D-08: prepare the 12 vanilla-prompt requests. No API calls; never resamples; never reads gold labels.

Input : data/sample_ids.csv, docs/prompt_vanilla.txt, frozen outputs/requests/case_<id>/host.java,
        MM-Assist datasets.zip (only telemetry.hostFunctionTelemetryData lineStart/lineEnd/sourceCode).
Output: outputs/requests_vanilla/case_<id>/{request.json, class_numbered.txt, input_record.json}

{HOST_CLASS_NUMBERED} (D-08): host.java (CRLF->LF), file lines lineStart..lineEnd, first line's leading
indentation removed (PsiClass.text starts at the class start offset), each line prefixed "<file line>. "
(MM-Assist Utils.kt addLineNumbersToCodeSnippet). telemetry sourceCode is a cross-check only.

Usage: python scripts/prepare_vanilla_inputs.py --datasets <path to datasets.zip>
(Run only after D-08 is committed: the commit must precede outputs/requests_vanilla/.)
"""
import argparse, csv, hashlib, json, re, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'docs/prompt_vanilla.txt'
TEMPLATE_SHA256 = '285e18bb72aa8accfd98981fe5607c504e7f562f3e2f28b1687282e2b8863bbb'
DATASETS_SHA256 = '8b2808944db28ba6620f07a71fce38224f32cc100a444bb89573f662e268c3eb'
MODEL = 'gpt-4o-2024-05-13'
OUT = ROOT / 'outputs/requests_vanilla'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_template():
    raw = TEMPLATE.read_bytes()
    # Line endings may be converted on Windows checkouts; the frozen hash is over the LF form.
    lf = raw.replace(b'\r\n', b'\n')
    assert sha(lf) == TEMPLATE_SHA256, 'docs/prompt_vanilla.txt differs from the D-08 registered version'
    template = lf.decode('utf-8')
    roles = list(re.finditer(r'^\[(SYSTEM|USER|ASSISTANT)\]$', template, re.M))
    messages = []
    for i, m in enumerate(roles):
        end = roles[i + 1].start() if i + 1 < len(roles) else len(template)
        messages.append({'role': m[1].lower(), 'content': template[m.end():end].strip('\n')})
    assert [m['role'] for m in messages] == ['system', 'user', 'assistant', 'user']
    assert messages[3]['content'] == '{HOST_CLASS_NUMBERED}'
    return messages, sha(lf)


def numbered_class(host_bytes, start, end):
    lines = host_bytes.decode('utf-8').replace('\r\n', '\n').split('\n')
    segment = lines[start - 1:end]
    segment[0] = segment[0].lstrip(' \t')
    return segment, '\n'.join('%d. %s' % (start + i, l) for i, l in enumerate(segment))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--datasets', required=True, help='path to the MM-Assist datasets.zip (sha256 checked)')
    ap.add_argument('--out', default=str(OUT), help='output folder (default outputs/requests_vanilla; other values for dry tests only)')
    args = ap.parse_args()
    out = Path(args.out)
    archive = Path(args.datasets)
    assert sha(archive.read_bytes()) == DATASETS_SHA256, 'datasets.zip is not the version recorded in docs/artefact_version.txt'
    records = {}
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name.startswith('data/') and '/instance-methods/mm-assist-emm/' in name and name.endswith('_res.json'):
                for r in json.loads(z.read(name)):
                    records[int(r['ref_id'])] = r
    assert len(records) == 117
    messages, template_sha = load_template()
    sample = list(csv.DictReader((ROOT / 'data/sample_ids.csv').open(encoding='utf-8-sig')))
    assert [int(r['case_id']) for r in sample] == [1, 2, 3, 5, 7, 8, 14, 15, 16, 17, 19, 21]
    for row in sample:
        cid = int(row['case_id'])
        rec = records[cid]
        assert rec['extraction_results']['newCommitHash'] == row['commit']
        tel = rec['telemetry']['hostFunctionTelemetryData']
        host_path = ROOT / ('outputs/requests/case_%04d/host.java' % cid)
        host_bytes = host_path.read_bytes()
        frozen_record = json.loads((ROOT / ('outputs/requests/case_%04d/input_record.json' % cid)).read_text(encoding='utf-8'))
        assert sha(host_bytes) == frozen_record['host_sha256'], 'frozen host.java changed'
        segment, numbered = numbered_class(host_bytes, tel['lineStart'], tel['lineEnd'])
        class_text = '\n'.join(segment)
        telemetry_text = tel['sourceCode'].replace('\r\n', '\n')
        request = {'model': MODEL, 'temperature': 0, 'messages': [
            {'role': m['role'], 'content': m['content'].replace('{HOST_CLASS_NUMBERED}', numbered)} for m in messages]}
        body = json.dumps(request, ensure_ascii=False, indent=2)
        folder = out / ('case_%04d' % cid)
        if (folder / 'request.json').exists():
            assert (folder / 'request.json').read_text(encoding='utf-8') == body, 'prepared request differs: %d' % cid
            print(cid, 'already prepared; identical')
            continue
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'class_numbered.txt').write_text(numbered, encoding='utf-8', newline='\n')
        (folder / 'request.json').write_text(body, encoding='utf-8', newline='\n')
        (folder / 'input_record.json').write_text(json.dumps({
            'prepared_at_utc': datetime.now(timezone.utc).isoformat(), 'case_id': cid, 'decision': 'D-08',
            'commit': row['commit'], 'host_class': row['host_class'], 'host_file': row['host_file'],
            'host_source': 'outputs/requests/case_%04d/host.java' % cid, 'host_sha256': sha(host_bytes),
            'line_start': tel['lineStart'], 'line_end': tel['lineEnd'],
            'class_text_sha256': sha(class_text.encode('utf-8')),
            'class_text_equals_telemetry_sourceCode': class_text == telemetry_text,
            'template_path': 'docs/prompt_vanilla.txt', 'template_sha256_lf': template_sha,
            'datasets_zip_sha256': DATASETS_SHA256,
            'request_sha256': sha(body.encode('utf-8')), 'status': 'PREPARED_NOT_SENT', 'api_calls': 0,
            'notes': 'Gold method and gold target are not used to build the request.'},
            ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
        print(cid, 'prepared; class lines %d-%d; telemetry match=%s' % (tel['lineStart'], tel['lineEnd'], class_text == telemetry_text))


if __name__ == '__main__':
    main()
