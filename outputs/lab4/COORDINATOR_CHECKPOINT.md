# G05 / P08 — Week 6 Lab4 coordinator checkpoint

**Status to show:** frozen 12-case execution complete; **INCONCLUSIVE for paper-level interpretation pending input/gold validity review**.

| Checkpoint | Where to look |
|---|---|
| Frozen contract | `M1_PLAN` tag; original README and D-03/D-04 |
| Sample | `data/sample_ids.csv`; same 12 IDs, 0 replacements |
| Model/route | `scripts/run_frozen_lab.py`; saved runner snapshot in the run directory |
| Raw evidence | `outputs/runs/20261020T172353_759166Z/case_0001/response.raw.json` and the other eleven cases |
| Trace one number | Case 1 hit → first `target_class` in raw response → saved request → input manifest → frozen commit and source hash |
| Static evidence | `outputs/static/<id>.csv` and `.audit.json`; JavaParser ASTs in `outputs/evaluation/` |
| H1/H2 evidence | `outputs/h_check/<id>.txt` and target source at the frozen commit |
| Decision record | D-05, appended after execution without rewriting M1 |
| Held-out material | None used |

Observed: H1+H2 **0/12**; LLM/static/hybrid Recall@1 **10/12, 8/12, 10/12**; agreement **9/12**. The numerical RQ1 rule says NOT REPRODUCED. The RQ2 non-decrease rule is satisfied by equality; hallucination reduction was not demonstrated because baseline H1/H2 was zero and fallback was never used.

## Issue to resolve before M2

Please inspect `input_audit.json`: six frozen signatures differ materially from the actual reconstructed declarations (3, 5, 15, 16, 19, 21). Ref_id 14's frozen gold package also differs from the existing imported service interface. All original requests and gold labels were retained for scoring. No post-result correction or rerun was made.

Ask the coordinator whether this as-frozen run is interpretable as the bounded result, or whether a separate prospectively documented correction is required. If correction is authorised, record exactly which input/oracle/method aspects change, why, and the expected interpretation consequences **before** starting a distinct run. Keep the present run intact. Do not enlarge the sample or consume Event material to rescue the outcome.

The common ranking-interface design comparison is deferred to M4; Lab4 does not settle it.

## Suggested tracker update

> Completed the frozen 12-case target-only GPT-4o-2024-05-13 run at temperature 0. All 12 responses are preserved and traceable. H1+H2 = 0/12; LLM/static/hybrid Recall@1 = 10/12, 8/12, 10/12; agreement = 9/12. Arithmetic: RQ1 not reproduced; RQ2 non-decrease criterion met, with no observed hallucination-reduction benefit. Overall paper-level interpretation inconclusive pending coordinator review of reconstructed-signature discrepancies and a gold-package issue. No sample/model/prompt/gold changes or result-driven reruns. Next before M2: review validity audit with coordinator and document any authorised correction prospectively.

Tracker text is prepared locally only; nothing has been submitted or sent.
