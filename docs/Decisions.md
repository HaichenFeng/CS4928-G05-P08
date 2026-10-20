## D-03

### Sample selection

Use 12 instance-method Move Method cases from the authors' released datasets.zip.

Source:

- Repository: cuboulder-se-research/move-method-assist
- Version stated in M1: 8b0898f
- Dataset SHA-256: 8b2808944db28ba6620f07a71fce38224f32cc100a444bb89573f662e268c3eb
- Files: data/refminer_data/instance-methods/mm-assist-emm/*_res.json
- Total records: 117

Eligibility:

1. move_method_refactoring.isStatic is false.
2. extraction_results.success is true.
3. The reconstructed newCommitHash is fetchable from GitHub and the host file exists at that commit.

Sort by ref_id ascending and select the first 12 eligible cases. Record exclusions and reasons. Do not select cases based on recommendation quality.

#### Addendum (2026-10-18)

- If fewer than 12 cases are eligible, use all and record this.
- Checkout point: `extraction_results.newCommitHash` (the authors' reconstructed pre-move state), not `sha1` (the developer's post-refactoring commit).
- Screening run 2026-10-18 with `scripts/select_sample.py --check-source`: 12/12 passed rule 3, 0 skipped (`data/screening_log.csv`, `outputs/screening_run.log`).
- Sample: ref_id 1, 2, 3, 5, 7, 8, 14, 15, 16, 17, 19, 21 (`data/sample_ids.csv`).
- Project mix: 11 ruoyi-vue-pro, 1 flink. This is a direct consequence of ref_id ordering; the sample was not altered. Recorded as an external-validity threat.

## D-04

### LLM configuration, prompt and hallucination coding

Supersedes the 2026-10-17 draft of D-04 (see git history). Frozen on: 2026-10-18 (tag M1_PLAN, commit 39b6642).

- Model: gpt-4o-2024-05-13, temperature 0. If unavailable: record the replacement, the reason and the data-contamination risk here BEFORE any run, and confirm the change with the coordinator.
- Prompt source: the paper prints only a paraphrase (Sec. II, Sec. IV-B: host class source given, LLM asked which methods to move and where). The full vanilla prompt is taken from the replication package, `MoveMethodRefactoringPrompt.kt` `getPrompt()` @ 8b0898f (Sec. VIII states the prompts are released there).
  - Original: `docs/prompt_original.txt`
  - Adapted: `docs/prompt_adapted.txt`
- Top-1 = the first object's `target_class` in the JSON response. The raw request and response are saved per case.
- The prompt never includes the gold target or the authors' existing recommendations.

Deviations from the paper:

1. **Target-only prompt.** The method m is given to the LLM and only the target class is asked (the vanilla prompt asks for method + target). Consequence: H3 cannot occur; LLM-only Recall@1 may exceed the paper's RecallC, which is conditional on the LLM first finding m.
2. **H2 operationalisation.** H2 = the class exists but is not a field type of H or a parameter type of m. IDE precondition checks (Def. III.3: movability, reference access) are not run, so H2 may be undercounted.
3. **RQ1 comparison figure.** RQ1 is compared against H1+H2 = (431+275)/1293 ~ 55% (Table I), not ~80% (which includes H3). Amendment 2026-10-18, made before any execution. AI-assisted: suggested by an AI assistant and checked by the group against Table I.

No LLM calls were executed before this entry was frozen.

## D-05 — Lab4 execution and post-execution validity audit (2026-10-20)

This is a dated execution record, not a retrospective rewrite of D-03/D-04.

- Executed the frozen target-only requests directly through OpenAI Chat Completions using `gpt-4o-2024-05-13`, temperature 0. No replacement model. The exploratory IDE plugin attempts returned empty candidates and are not empirical LLM observations.
- Run: `outputs/runs/20261020T172353_759166Z/`. Ref_id 1 was the pilot; its request matched the previously prepared request. It was retained in the 12-case run. All twelve returned HTTP 200 and valid complete JSON. No valid observations were rerun or excluded.
- After execution, checked reconstructed declarations against frozen signatures. Material differences were found in ref_ids 3, 5, 15, 16, 19, 21; all twelve source methods also use private visibility while frozen signatures say public. Static coding uses the uniquely named method's actual source parameters/body. Original prompts and labels remain unchanged.
- Ref_id 14 gold names `service.impl.AiChatModalService`, while the checked source and existing interface use `service.AiChatModalService`. Keep the frozen exact-match gold and record the discrepancy. Do not relabel it as a hit.
- Observed H1/H2 = 0/12, LLM/static/hybrid Recall@1 = 10/12, 8/12, 10/12. Frozen arithmetic: RQ1 NOT REPRODUCED; RQ2 non-decrease rule satisfied. No hallucination reduction was demonstrated, because no hallucinations or hybrid fallbacks occurred.
- Overall intended paper-level interpretation: INCONCLUSIVE pending coordinator review of input/oracle validity. The bounded API execution and as-frozen calculations are complete. See `outputs/lab4/LAB4_REPORT.md`.
- No corrective method/sample/model change has been implemented. Any coordinator-approved correction must be recorded prospectively before a distinct new run, preserving this run and M1 unchanged. No Event/held-out material used. The M4 ranking-interface decision remains deferred.
- GenAI helped write support scripts and this audit. The group must review the source-based coding and interpretation; assistant-generated prose is not raw experimental evidence.
