"""Check scripts/java_ast.py (tree-sitter) against the M2 JavaParser ASTs (outputs/evaluation/<id>_ast.json).

For each of the 12 gold methods, compares fields, parameters, locals and member accesses as multisets of
(name/kind, whitespace-free type/scope, member, line). Writes outputs/vanilla/ast_equivalence.json.
Exit code 1 if any case differs.
"""
import csv, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import java_ast

ROOT = Path(__file__).resolve().parents[1]


def key_var(v):
    return (v['name'], java_ast.norm(v['type']), v['line'])


def key_acc(a):
    return (a['kind'], java_ast.norm(a['scope']), a['member'], a['line'])


report = []
for row in csv.DictReader((ROOT / 'data/sample_ids.csv').open(encoding='utf-8-sig')):
    cid = int(row['case_id'])
    m2 = json.loads((ROOT / ('outputs/evaluation/%d_ast.json' % cid)).read_text(encoding='utf-8'))
    facts = java_ast.inspect((ROOT / ('outputs/requests/case_%04d/host.java' % cid)).read_bytes(), row['host_class'])
    name = row['method'].split('(', 1)[0].rsplit(' ', 1)[-1]
    methods = [m for m in facts['methods'] if m['name'] == name and m['kind'] == 'method']
    entry = {'case_id': cid, 'method': name, 'unique_method': len(methods) == 1}
    if len(methods) == 1:
        m = methods[0]
        checks = {
            'package': (m2['package'] == facts['package']),
            'imports': (sorted(java_ast.norm(i).removeprefix('import').removesuffix(';').replace('static', 'static ', 1) if java_ast.norm(i).startswith('importstatic') else java_ast.norm(i).removeprefix('import').removesuffix(';') for i in m2['imports']) == sorted(facts['imports'])),
            'fields': Counter(map(key_var, m2['fields'])) == Counter(map(key_var, facts['fields'])),
            'parameters': Counter(map(key_var, m2['parameters'])) == Counter(map(key_var, m['parameters'])),
            'locals': Counter(map(key_var, m2['locals'])) == Counter(map(key_var, m['locals'])),
            'member_accesses': Counter(map(key_acc, m2['member_accesses'])) == Counter(map(key_acc, m['member_accesses'])),
            'method_line': m2['method_line'] == m['line'],
        }
        entry['checks'] = checks
        entry['equal'] = all(checks.values())
        if not entry['equal']:
            entry['diff'] = {k: {'javaparser': m2.get(k), 'tree_sitter': (m if k in m else facts).get(k)} for k, ok in checks.items() if not ok and k not in ('method_line',)}
    else:
        entry['equal'] = False
    report.append(entry)
    print(cid, 'EQUAL' if entry['equal'] else 'DIFF', {k: v for k, v in entry.get('checks', {}).items() if not v})

out = ROOT / 'outputs/vanilla/ast_equivalence.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'parser': 'tree-sitter-java', 'reference': 'outputs/evaluation/*_ast.json (JavaParser 3.26.2, M2)',
                           'all_equal': all(e['equal'] for e in report), 'cases': report}, ensure_ascii=False, indent=2), encoding='utf-8')
sys.exit(0 if all(e['equal'] for e in report) else 1)
