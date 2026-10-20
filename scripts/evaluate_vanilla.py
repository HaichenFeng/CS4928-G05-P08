"""D-08: code every vanilla-prompt recommendation (H1 / H3 / H2 / Valid) and compute the registered metrics.
No LLM calls. Responses are re-parsed from response.raw.json with scripts/vanilla_parse.py.

Usage:
  python scripts/evaluate_vanilla.py --run outputs/runs/<UTC>_vanilla            # fetches target sources, caches evidence
  python scripts/evaluate_vanilla.py --run outputs/runs/<UTC>_vanilla --offline  # replays from the cached evidence only

Outputs (outputs/vanilla/): recommendations.csv, cases.csv, summary.json, h_check/<case>/<FQN>.java + .txt
Rules: docs/Decisions.md D-08. Static candidate set: same functions as scripts/evaluate_lab4.py (M2).
"""
import argparse, csv, hashlib, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import java_ast  # noqa: E402
from vanilla_parse import parse_raw  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/vanilla'
REQUESTS = ROOT / 'outputs/requests_vanilla'
MODEL = 'gpt-4o-2024-05-13'
IDS = [1, 2, 3, 5, 7, 8, 14, 15, 16, 17, 19, 21]

# --- identical to scripts/evaluate_lab4.py (M2 static candidate rule, docs/coding_manual.md) ---
CONTAINERS = {'Map', 'List', 'Set', 'Collection', 'Optional', 'Iterable', 'Queue', 'Deque', 'SortedMap', 'SortedSet'}
JDK = {'String', 'Long', 'Integer', 'Double', 'Float', 'Boolean', 'Byte', 'Short', 'Character', 'Object', 'Void', 'Number', 'Duration'}
PRIMITIVES = {'boolean', 'byte', 'short', 'int', 'long', 'float', 'double', 'char', 'void'}


def split_args(text):
    pieces = []; depth = 0; start = 0
    for i, c in enumerate(text):
        if c == '<': depth += 1
        if c == '>': depth -= 1
        if c == ',' and depth == 0: pieces.append(text[start:i]); start = i + 1
    pieces.append(text[start:]); return pieces


def concrete_types(text):
    text = re.sub(r'\s+', '', text).replace('[]', '')
    raw = text.split('<')[0]
    if raw.split('.')[-1] in CONTAINERS and '<' in text:
        return [t for a in split_args(text[text.index('<') + 1:-1]) for t in concrete_types(a)]
    return [] if raw in PRIMITIVES or raw in JDK or raw in ('T', 'K', 'V', 'E', '?') else [raw]


def resolve(name, facts):
    if '.' in name and name[0].islower(): return name
    for value in facts['imports']:
        if not value.startswith('static ') and value.split('.')[-1] == name: return value
    return facts['package'] + '.' + name
# --- end of M2 functions ---


def candidate_set(facts, method):
    cands = set()
    for var in facts['fields'] + (method['parameters'] if method else []):
        for name in concrete_types(var['type']):
            fqn = resolve(name, facts)
            if fqn.startswith(('java.', 'javax.')) or fqn == facts['host']:
                continue
            cands.add(fqn)
    return cands


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Project:
    """Class existence at the frozen commit: tree listing (outputs/source_checks/<id>_tree.txt) + declaration in source."""

    def __init__(self, cid, row, offline):
        self.cid, self.row, self.offline = cid, row, offline
        self.paths = (ROOT / ('outputs/source_checks/%d_tree.txt' % cid)).read_text(encoding='utf-8').splitlines()
        self.repo = json.loads((ROOT / ('outputs/requests/case_%04d/input_record.json' % cid)).read_text(encoding='utf-8'))['repository']
        self.by_fqn = {}
        for p in self.paths:
            if p.endswith('.java') and '/java/' in p:  # Maven layout: FQN = path after the last /java/
                self.by_fqn.setdefault(p.rsplit('/java/', 1)[1][:-5].replace('/', '.'), []).append(p)
        self.packages = {f.rsplit('.', 1)[0] for f in self.by_fqn}
        self.cache = {}

    def source(self, fqn):
        """Fetch (or replay) the top-level file for fqn; record evidence. Returns (bytes, path) or (None, None)."""
        paths = self.by_fqn.get(fqn, [])
        if not paths:
            return None, None
        path = sorted(paths)[0]
        if path in self.cache:
            return self.cache[path], path
        folder = OUT / 'h_check' / str(self.cid)
        target, evidence = folder / (fqn + '.java'), folder / (fqn + '.txt')
        if self.offline:
            data = target.read_bytes()
            assert ('Source SHA256: ' + sha(data)) in evidence.read_text(encoding='utf-8'), 'cached evidence mismatch: ' + fqn
        else:
            url = 'https://raw.githubusercontent.com/%s/%s/%s' % (self.repo.removesuffix('.git').removeprefix('https://github.com/'), self.row['commit'], path)
            with urlopen(url, timeout=90) as r:
                data = r.read()
            folder.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            evidence.write_text('Frozen commit: %s\nFQN: %s\nTree path: %s\nURL: %s\nSource SHA256: %s\nFetched UTC: %s\n'
                                % (self.row['commit'], fqn, path, url, sha(data), datetime.now(timezone.utc).isoformat()), encoding='utf-8')
        self.cache[path] = data
        return data, path

    def exists(self, fqn):
        """True if fqn is a top-level or nested type declared in the project at the frozen commit."""
        parts = fqn.split('.')
        for i in range(len(parts), 0, -1):
            top = '.'.join(parts[:i])
            if top in self.by_fqn:
                data, _ = self.source(top)
                try:
                    root = java_ast.PARSER.parse(data).root_node
                    pkg = next((c for c in root.children if c.type == 'package_declaration'), None)
                    package = java_ast.norm(java_ast.text(pkg)).removeprefix('package').removesuffix(';') if pkg is not None else ''
                    return fqn in java_ast.find_types(root, package)
                except Exception:
                    return False
        return False

    def simple_matches(self, simple):
        return sorted(f for f in self.by_fqn if f.rsplit('.', 1)[-1] == simple)


def clean_target(t):
    t = (t or '').strip().strip('`').removeprefix('class ').strip()
    t = re.sub(r'<.*>$', '', t).removesuffix('.java').strip()
    return t


def resolve_target(raw, facts, project, cands):
    """D-08 step 1. Returns (fqn or None, how). how in fqn/import/nested/package/wildcard/unique/candidate/external/ambiguous/unresolved."""
    t = clean_target(raw)
    if not t or not re.fullmatch(r'[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)*', t):
        return None, 'unresolved'
    if t.startswith(('java.', 'javax.')):
        return t, 'external'
    first, _, rest = t.partition('.')
    if t[0].islower():  # fully qualified
        if project.exists(t):
            return t, 'fqn'
        if t in facts['imports']:
            return t, 'external'
        return t, 'unresolved'
    suffix = ('.' + rest) if rest else ''
    for imp in facts['imports']:
        if not imp.startswith('static ') and imp.split('.')[-1] == first:
            fqn = imp + suffix
            if imp.rsplit('.', 1)[0] in project.packages:
                return fqn, 'import' if project.exists(fqn) else 'unresolved'
            return fqn, 'external'
    nested = [f for f in facts['types_in_file'] if f.endswith('.' + t)]
    if len(nested) == 1:
        return nested[0], 'nested'
    if project.exists(facts['package'] + '.' + t):
        return facts['package'] + '.' + t, 'package'
    for imp in facts['imports']:
        if imp.endswith('.*') and not imp.startswith('static ') and project.exists(imp[:-2] + '.' + t):
            return imp[:-2] + '.' + t, 'wildcard'
    if t in JDK or first in ('String', 'Object', 'List', 'Map', 'Set', 'Optional', 'Collection'):
        return 'java.lang.' + t if t in JDK else 'java.util.' + t, 'external'
    matches = [m + suffix for m in project.simple_matches(first)]
    matches = [m for m in matches if not rest or project.exists(m)]
    if len(matches) == 1:
        return matches[0], 'unique'
    if len(matches) > 1:
        inset = [m for m in matches if m in cands]
        if len(inset) == 1:
            return inset[0], 'candidate'
        return None, 'ambiguous'
    return None, 'unresolved'


def param_types(signature):
    if not signature or '(' not in signature:
        return None
    inner = signature.split('(', 1)[1].rsplit(')', 1)[0].strip()
    if not inner:
        return []
    out = []
    for piece in split_args(inner):
        toks = piece.replace('final ', '').strip().split()
        out.append(java_ast.norm(' '.join(toks[:-1])) if len(toks) > 1 else java_ast.norm(piece))
    return out


def pick_method(facts, name, signature):
    """D-08: methods of H named method_name; overloads by parameter types, then count, else first declared."""
    name = (name or '').split('(')[0].strip()
    ms = [m for m in facts['methods'] if m['name'] == name and m['kind'] == 'method']
    if not ms:
        ctor = [m for m in facts['methods'] if m['name'] == name and m['kind'] == 'constructor']
        return (ctor[0], 'constructor') if ctor else (None, 'missing')
    if len(ms) == 1:
        return ms[0], 'unique'
    want = param_types(signature)
    if want is not None:
        exact = [m for m in ms if [java_ast.norm(p['type']) for p in m['parameters']] == want]
        if len(exact) == 1:
            return exact[0], 'overload_types'
        count = [m for m in ms if len(m['parameters']) == len(want)]
        if len(count) == 1:
            return count[0], 'overload_count'
    return ms[0], 'overload_first_declared'


def h3_reason(method, how):
    if method is None:
        return 'method_not_in_host'
    if how == 'constructor' or method['kind'] == 'constructor':
        return 'constructor'
    if 'Override' in method['annotations']:
        return 'override'
    if 'Test' in method['annotations']:
        return 'test'
    if method['accessor']:
        return method['accessor']
    if not method['has_body'] or method['statement_count'] == 0:
        return 'empty_body'
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    ap.add_argument('--offline', action='store_true')
    args = ap.parse_args()
    run = Path(args.run) if Path(args.run).is_absolute() else ROOT / args.run
    sample = list(csv.DictReader((ROOT / 'data/sample_ids.csv').open(encoding='utf-8-sig')))
    assert [int(r['case_id']) for r in sample] == IDS
    recs_out, cases_out, usage = [], [], {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    for row in sample:
        cid = int(row['case_id'])
        case = run / ('case_%04d' % cid)
        execution = json.loads((case / 'execution.json').read_text(encoding='utf-8'))
        assert execution['status'].startswith('VALID_RESPONSE'), 'case %d has no valid observation' % cid
        prepared = json.loads((REQUESTS / ('case_%04d/request.json' % cid)).read_text(encoding='utf-8'))
        sent = json.loads((case / 'request.json').read_text(encoding='utf-8'))
        assert sent == prepared and sha((case / 'request.json').read_bytes()) == execution['request_sha256']
        raw = json.loads((case / 'response.raw.json').read_text(encoding='utf-8'))
        assert raw['model'] == MODEL, 'returned model differs: ' + raw['model']
        parsed = parse_raw(raw)
        assert parsed['recommendations'] == json.loads((case / 'parsed.json').read_text(encoding='utf-8'))['recommendations']
        for k in usage:
            usage[k] += (raw.get('usage') or {}).get(k, 0)
        facts = java_ast.inspect((ROOT / ('outputs/requests/case_%04d/host.java' % cid)).read_bytes(), row['host_class'])
        project = Project(cid, row, args.offline)
        gold_method = row['method'].split('(', 1)[0].rsplit(' ', 1)[-1]
        labels = []
        for rec in parsed['recommendations']:
            method, how_m = pick_method(facts, rec['method_name'], rec['method_signature'])
            cands = candidate_set(facts, method if how_m != 'constructor' else None)
            fqn, how_t = resolve_target(rec['target_class'], facts, project, cands)
            reason = h3_reason(method, how_m)
            if fqn is None and how_t == 'unresolved':
                label = 'H1'
            elif how_t == 'unresolved':
                label = 'H1'
            elif reason:
                label = 'H3'
            elif how_t in ('external', 'ambiguous') or fqn not in cands:
                label = 'H2'
            else:
                label = 'Valid'
            labels.append(label)
            recs_out.append({'case_id': cid, 'rank': rec['rank'], 'method_name': rec['method_name'], 'method_signature': rec['method_signature'],
                             'target_class': rec['target_class'], 'resolved_target': fqn or '', 'target_resolution': how_t,
                             'method_resolution': how_m, 'method_line': method['line'] if method else '',
                             'h3_reason': reason or '', 'in_candidate_set': int(bool(fqn) and fqn in cands),
                             'candidate_set': ';'.join(sorted(cands)), 'label': label,
                             'gold_method': int((rec['method_name'] or '').split('(')[0].strip() == gold_method),
                             'gold_pair': int((rec['method_name'] or '').split('(')[0].strip() == gold_method and fqn == row['gold_target'])})
        mine = [r for r in recs_out if r['case_id'] == cid]

        def hit(k, key):
            return int(any(r[key] for r in mine if r['rank'] <= k))
        cases_out.append({'case_id': cid, 'project': row['project'], 'gold_method': gold_method, 'gold_target': row['gold_target'],
                          'parse_status': parsed['parse_status'], 'finish_reason': parsed['finish_reason'], 'recommendations': len(mine),
                          'H1': labels.count('H1'), 'H2': labels.count('H2'), 'H3': labels.count('H3'), 'Valid': labels.count('Valid'),
                          'top1_label': labels[0] if labels else 'NO_RECOMMENDATION',
                          'top1_method': mine[0]['method_name'] if mine else '', 'top1_target': (mine[0]['resolved_target'] or mine[0]['target_class']) if mine else '',
                          'recallM_at1': hit(1, 'gold_method'), 'recallM_at3': hit(3, 'gold_method'),
                          'recallMC_at1': hit(1, 'gold_pair'), 'recallMC_at3': hit(3, 'gold_pair'),
                          'request_id': execution.get('request_id')})
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in (('recommendations.csv', recs_out), ('cases.csv', cases_out)):
        with (OUT / name).open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['case_id'])
            w.writeheader(); w.writerows(rows)
    R = len(recs_out)
    count = {h: sum(r['label'] == h for r in recs_out) for h in ('H1', 'H2', 'H3', 'Valid')}
    rate = (count['H1'] + count['H2'] + count['H3']) / R if R else 0.0
    top1_h12 = sum(c['top1_label'] in ('H1', 'H2') for c in cases_out)
    rm = {k: sum(c['recallM_at%d' % k] for c in cases_out) for k in (1, 3)}
    rmc = {k: sum(c['recallMC_at%d' % k] for c in cases_out) for k in (1, 3)}
    if rate >= 0.5 or top1_h12 >= 4:
        decision = 'SUPPORTED'
    elif rate <= 0.2 and top1_h12 <= 1:
        decision = 'NOT SUPPORTED'
    else:
        decision = 'PARTIAL'
    summary = {'evaluated_utc': datetime.now(timezone.utc).isoformat(), 'decision_record': 'D-08',
               'run': run.relative_to(ROOT).as_posix() if run.is_relative_to(ROOT) else str(run), 'model': MODEL, 'temperature': 0,
               'n_cases': len(cases_out), 'usage': usage, 'R': R, **count,
               'rates': {h: (count[h] / R if R else None) for h in ('H1', 'H2', 'H3', 'Valid')},
               'hallucination_rate_H1_H2_H3': rate if R else None, 'R_is_zero': R == 0,
               'paper_table1_realworld': {'R': 1293, 'H1': 431, 'H2': 275, 'H3': 320, 'rate': 1026 / 1293},
               'top1_H1_H2_cases': top1_h12, 'M2_top1_H1_H2_cases': 0,
               'recallM': {'@1': rm[1], '@3': rm[3]}, 'recallMC': {'@1': rmc[1], '@3': rmc[3]},
               'recallC': {'@1': (rmc[1] / rm[1]) if rm[1] else None, '@3': (rmc[3] / rm[3]) if rm[3] else None},
               'threat1_decision': decision,
               'rule': 'SUPPORTED if rate>=0.5 or top1 H1+H2>=4/12; NOT SUPPORTED if rate<=0.2 and top1 H1+H2<=1/12; else PARTIAL',
               'parse_status': {c['case_id']: c['parse_status'] for c in cases_out}}
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ('R', 'H1', 'H2', 'H3', 'Valid', 'hallucination_rate_H1_H2_H3', 'top1_H1_H2_cases', 'recallM', 'recallMC', 'threat1_decision')}, indent=2))


if __name__ == '__main__':
    main()
