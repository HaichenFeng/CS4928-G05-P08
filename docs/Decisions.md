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

## D-06 — Prompt version used in the Lab4 run (record correction, 2026-10-20)

This corrects the record only. No request, response, score or decision rule is changed, and no run is repeated.

- **Version used.** All 12 requests in `outputs/runs/20261020T172353_759166Z/` were rendered from `docs/prompt_adapted.txt` as frozen at tag `M1_PLAN` (commit 39b6642, unchanged in 5cf9f03).
  - Evidence: every `outputs/requests/case_*/input_record.json` records `template_sha256 = ef3ed569ee78d943a559319e2661354a9feab91c54be2a56731c7b92a982fbe1`. This equals the sha256 of `M1_PLAN:docs/prompt_adapted.txt` checked out with CRLF line endings (Windows). The 2026-10-19 revision (1f8cf01) hashes to `818270187dabdc67…` (LF) / `e3b9adb3fecb0255…` (CRLF) and matches no request.
  - Check: `git show M1_PLAN:docs/prompt_adapted.txt | sed 's/$/\r/' | sha256sum`
- **Why HEAD differed.** The revision 1f8cf01 (2026-10-19, "before any LLM call") was committed on a separate branch. The run branch (eb33a96) was based on 5cf9f03 and did not contain it. The revision entered `main` only through merge d11a925, after the run. It was never used.
- **Correction.** `docs/prompt_adapted.txt` is restored to the M1_PLAN content, so `scripts/prepare_frozen_inputs.py` regenerates the requests actually sent. The unused revision is kept as `docs/prompt_adapted_rev2026-10-19_UNUSED.txt`.
- **Differences between the used (M1_PLAN) prompt and `docs/prompt_original.txt`, beyond D-04 deviation 1:**
  1. Few-shot method signature written as `public calculateDiscount(): double`; the original has `public calculateDiscount(double amount): double`. Not documented in M1_PLAN.
  2. Trailing comma after the few-shot `rationale` field removed; the original keeps it. Not documented in M1_PLAN.
  3. The method to move is named in the first user message, before the few-shot example, as well as after the host class. This is a placement choice within D-04 deviation 1 (the method is given to the LLM).
- **Expected impact.** Items 1-2 only touch the few-shot example. Item 3 gives the same information as the revision, earlier in the prompt. None changes what the LLM is told about the host class or the method. The effect on H1/H2 and Recall@1 is expected to be small but is not measured; recorded as a threat to validity.
- **No re-run.** The as-frozen result stands. Any further run is a distinct new run and must be registered in this log before execution (see D-08); it does not replace this run.

## D-07 — M2 result finalised as-frozen (2026-10-20)

Group decision. This supersedes the "INCONCLUSIVE pending coordinator review" status in D-05 and `outputs/lab4/`; the earlier text is kept unchanged.

- **M2 result (final, primary):** the as-frozen 12-case run is the bounded reproduction result and the primary answer to RQ1. No coordinator review was sought or awaited. No correction run replaces it; a supplementary run that tests threat 1 is registered separately in D-08 and does not change this result.
  - RQ1: H1+H2 = 0/12 (paper comparison figure ~55%). Pre-registered rule (<= 3/12): **NOT REPRODUCED**.
  - RQ2: Hybrid Recall@1 10/12 = LLM-only 10/12 (static 8/12). Non-decrease rule **SUPPORTED by equality**. No hallucination reduction was demonstrated, because no hallucinations occurred and the hybrid fallback was never used.
  - LLM-static top-1 agreement: 9/12 (E3 expected < 6/12; not met).
- **Reason:** the brief accepts non-reproduction as a result when the method and evidence are sound. The validity issues below concern how the result is interpreted, not whether the frozen procedure was followed.
- **Threats to validity (carried into the final synthesis):**
  1. Target-only prompt (D-04 deviation 1): the LLM is given m, which removes H3 and makes H1/H2 and Recall@1 not directly comparable with the paper's vanilla setting. This is the most likely reason the hallucination rate is far below the paper's.
  2. Sample: 11/12 cases from ruoyi-vue-pro (D-03), mostly Service -> Mapper moves with an obvious field-type target.
  3. Frozen signatures differ materially from reconstructed source in ref_ids 3, 5, 15, 16, 19, 21 (D-05); all 12 differ in visibility.
  4. Ref_id 14 gold package (`service.impl`) differs from the existing interface (`service`); scored as a miss as frozen. With a corrected gold, LLM-only Recall@1 would be 11/12.
  5. H2 coded without IDE precondition checks (D-04 deviation 2); prompt deviations recorded in D-06; n = 12, one run at temperature 0.
  6. Input format, found 2026-10-20 after execution: MM-Assist passes the LLM only the host class text (`PsiClass.text`, without package/imports) with `<file line>. ` prefixed to every line (`ApplySuggestRefactoringIntention.kt` lines 79-108, `Utils.kt` `addLineNumbersToCodeSnippet`, @ 8b0898f). M2 sent the whole .java file without line numbers. Not documented in D-04.
- **Next:** run the supplementary analysis registered in D-08, then tag `M2_REPRO` and `PRE_EVENT_A`. Event A is read only after the tags are pushed.
