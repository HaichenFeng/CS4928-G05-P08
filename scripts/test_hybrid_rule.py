"""Event B (D-13) equivalence check for event_a_rules.hybrid_top1.

Recomputes the hybrid top-1 for every saved case (M2/Lab4 12 cases, Event A
primary 6 cases, Event A supplement case 368) from the preserved static audit
files and saved LLM top-1, and compares it with the hybrid_top1 that the
frozen scripts wrote. Read-only: no frozen script or output is changed.

Run from the repository root:  python scripts/test_hybrid_rule.py
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from event_a_rules import hybrid_top1  # noqa: E402

SOURCES = [
    # (label, results file, top-1 column, static audit directory)
    ('M2', 'outputs/lab4/results.csv', 'llm_top1', 'outputs/static'),
    ('EventA', 'outputs/event_a_gpt6_luna/first_run_report/observations.csv',
     'resolved_top1', 'outputs/event_a_gpt6_luna/first_run_report/static'),
    ('EventA-368', 'outputs/event_a_supplement_368/first_run_report/observations.csv',
     'resolved_top1', 'outputs/event_a_supplement_368/first_run_report/static'),
]


def candidates_for(audit_dir, case_id):
    audit = json.loads((ROOT / audit_dir / ('%s.audit.json' % case_id)).read_text(encoding='utf-8'))
    return {c['candidate_fqn'] for c in audit['ranked_candidates']}


def main():
    failures, rows = [], []
    for label, results, top_col, audit_dir in SOURCES:
        with open(ROOT / results, encoding='utf-8') as f:
            for r in csv.DictReader(f):
                cid, top, static = r['case_id'], r[top_col], r['static_top1']
                saved = r['hybrid_top1'] or None  # frozen report wrote None as ''
                cands = candidates_for(audit_dir, cid)
                miss = hybrid_top1(top, cands, static, 'miss')
                fallback = hybrid_top1(top, cands, static, 'static_fallback')
                if top:
                    # Non-empty: both policies must reproduce the frozen value exactly.
                    ok = miss == saved and fallback == saved
                else:
                    # Empty: frozen report recorded no hybrid value; policy is now explicit.
                    ok = saved is None and miss is None and fallback == static
                rows.append((label, cid, 'empty' if not top else 'llm', saved, miss, fallback, ok))
                if not ok:
                    failures.append((label, cid))

    # Unknown policy must be rejected, not silently defaulted.
    try:
        hybrid_top1('', set(), 'X', 'default')
        failures.append(('policy', 'unknown policy accepted'))
    except ValueError:
        pass

    for row in rows:
        print('%-10s case %-4s %-5s saved=%s | miss=%s | static_fallback=%s | %s' % (
            row[0], row[1], row[2], row[3], row[4], row[5], 'OK' if row[6] else 'FAIL'))
    print('cases checked: %d' % len(rows))
    if failures:
        print('FAIL: %s' % failures)
        sys.exit(1)
    print('PASS: hybrid_top1 reproduces every saved hybrid value for non-empty LLM output; '
          'empty output (363) is resolved only by the explicit policy.')


if __name__ == '__main__':
    main()
