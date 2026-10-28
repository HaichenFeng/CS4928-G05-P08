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

## D-08 — Supplementary run with the paper's vanilla prompt (pre-registration, 2026-10-20)

Registered **after** the M2 result was seen and **before** any request of this run is prepared or sent. It tests D-07 threat 1 (and threat 6). It does not replace or re-decide the M2 result in D-07.

### Purpose
D-07 threat 1 explains M2's 0/12 H1+H2 by the target-only prompt, which gives the LLM the method m. This run removes that deviation and the input-format deviation (threat 6): it uses the paper's own vanilla prompt and MM-Assist's own input format.

### Fixed before execution
- **Sample:** the same 12 cases (`data/sample_ids.csv`), same frozen commits. No additions, removals or replacements.
- **Model:** `gpt-4o-2024-05-13`, temperature 0, one run, OpenAI Chat Completions; no other parameters set. Same route as D-05.
- **Prompt:** `docs/prompt_vanilla.txt` (sha256 `285e18bb72aa8accfd98981fe5607c504e7f562f3e2f28b1687282e2b8863bbb`, LF). Rendered verbatim from `MoveMethodRefactoringPrompt.kt` `getPrompt()` @ 8b0898f (sha256 of that file `86b1d57d…`) with Kotlin `trimIndent()` semantics; the system message is from `SuggestRefactoringPrompt.kt` line 24. No wording, typo, trailing space or trailing comma is changed.
- **Input `{HOST_CLASS_NUMBERED}`:** host class text from the frozen `outputs/requests/case_<id>/host.java` (CRLF -> LF), file lines `lineStart`..`lineEnd` from the dataset field `telemetry.hostFunctionTelemetryData`, with the first line's leading indentation removed (`PsiClass.text` starts at the class start offset), and `"<line>. "` prefixed to each line. The dataset's `sourceCode` field is a cross-check only.
  - Cross-check done 2026-10-20: 11/12 identical to `sourceCode` (ref_id 21 differs only by the first-line indent, handled by the rule above). **ref_id 3 differs**: the MM-Assist run saw `selectByIdAndName(Long id, String name)`, the released commit contains `selectByIdAndName() : SFunction<…>` (cf. D-05). The checkout is used, as in M1/M2; reported as a limitation.
- **Requests:** all 12 requests are prepared, saved and hashed into a new directory `outputs/requests_vanilla/` before any API call. Ref_id 1 is the pilot; the pilot is retained.
- **Output:** a new run directory `outputs/runs/<UTC timestamp>_vanilla/`. Nothing under the M2 run directory or `outputs/requests/` is modified.
- **No reruns, no exclusions.** A transport failure with no HTTP response is retried once automatically. An HTTP error response (e.g. 401, 429, 5xx) is not an observation: the run stops, the attempt is archived as `case_<id>.attempt<n>.failed/`, and the same frozen request is resent after the cause is fixed. A response that cannot be parsed is a valid observation with zero recommendations; the run continues.

### Parsing
Strip a surrounding ``` fence; `json.loads`; if that fails, remove trailing commas before `}` or `]` (the few-shot answer itself has one) and `json.loads` again. A JSON list is the recommendation list; its rank is its list position. Anything that still does not parse, or is not a list, gives zero recommendations. Use `method_name` (text before any `(`) and `target_class`; `method_signature` is used only to pick between overloads.

### Coding each recommendation (exactly one label, in this order)
1. **Resolve the target** (generic arguments and a `.java` suffix are dropped; `Outer.Inner` is allowed).
   - FQN (first segment lowercase): exists in the project -> that class; equal to an import of H -> external; otherwise unresolved.
   - Simple name, in this order: H's imports (if the imported package is a project package the class must exist, else unresolved; otherwise external); types nested in H's file; H's package; H's wildcard imports; common JDK names (`String`, `Object`, `List`, `Map`, `Set`, `Optional`, `Collection`, boxed types) -> external; a unique project class of that simple name; several -> the one in the static candidate set (step 4) if exactly one is, otherwise "ambiguous".
   - Project classes: `.java` files in `outputs/source_checks/<id>_tree.txt` (the frozen commit's tree), FQN = path after the last `/java/` (Maven layout); a nested type must be declared in its outer file. Each looked-up file is fetched at the frozen commit and saved with its sha256 in `outputs/vanilla/h_check/`.
   - `java.*`, `javax.*` and library classes ("external") exist but are never in the candidate set.
2. **H1** — the target is unresolved (does not exist at the frozen commit).
   **Method lookup** for steps 3-4: methods of H with that name; if several overloads, the one whose parameter types equal those in `method_signature`, else the one with the same parameter count, else the first declared. A name that only matches a constructor is a constructor.
3. **H3** — the method is invalid to move: no method named `method_name` in H; or a constructor; or annotated `@Override` or `@Test`; or a getter/setter (body is a single `return <field>;` or `<field> = <param>;`); or an empty/comments-only body. (Paper Sec. III-B sanity checks; same filters as the plugin, `ApplyMoveMethodInteractiveIntention.kt` lines 106-107.)
4. **H2** — the target exists but is not in the static candidate set of that method: field types of H ∪ parameter types of the method, per `docs/coding_manual.md` (and D-04 deviation 2: no IDE precondition run). "Ambiguous" targets are H2.
5. Otherwise **Valid**.

### Metrics
- Per recommendation (paper Table I comparison): R, and H1/R, H2/R, H3/R, (H1+H2+H3)/R. Paper real-world: R = 1293, H1 33%, H2 21%, H3 25%, total ~80%.
- Per case, top-1 only (M2 comparison): number of cases whose rank-1 recommendation is H1 or H2, out of 12 (M2: 0/12).
- RecallM@k: the gold method name is among the top-k `method_name`s (name match; each host has one method of that name, D-05).
- RecallMC@k: a top-k recommendation has the gold method name **and** a resolved target equal to the frozen gold FQN (exact, as in M2; ref_id 14 kept as frozen).
- RecallC@k = RecallMC@k / RecallM@k (paper definition). k = 1 and 3.

### Expected result and decision rule (written before execution)
- **Expectation:** (H1+H2+H3)/R between 40% and 80%; top-1 H1+H2 in 2-6 of 12 cases; RecallM@1 4-7/12 (11 of 12 hosts have fewer than 15 methods, the paper's "small class" group, Vanilla-LLM RecallM@1 52%); RecallMC@1 2-6/12.
- **Threat 1 supported:** (H1+H2+H3)/R >= 50%, or top-1 H1+H2 >= 4/12.
- **Threat 1 not supported:** (H1+H2+H3)/R <= 20% and top-1 H1+H2 <= 1/12. The low M2 rate then is not explained by the target-only prompt.
- **Otherwise:** partial; reported as observed.
- Whatever the outcome, the RQ1 decision in D-07 (NOT REPRODUCED under the pre-registered M1 method) is unchanged. This run is reported as a supplementary sensitivity analysis in M2.

### Implementation (committed with this entry, before execution)
- `scripts/prepare_vanilla_inputs.py --datasets <datasets.zip>` -> `outputs/requests_vanilla/` (checks the prompt and datasets.zip hashes; no API call).
- `scripts/run_vanilla_lab.py` (GUI, key in memory; adapted from `run_frozen_lab.py`; ref_id 1 pilot, then `pilot_approved.json` gate) -> `outputs/runs/<UTC>_vanilla/`; the runner and parser are copied into the run folder.
- `scripts/vanilla_parse.py` (parsing rule above), `scripts/evaluate_vanilla.py --run <run> [--offline]` (coding and metrics) -> `outputs/vanilla/`.
- Java facts come from `scripts/java_ast.py` (tree-sitter 0.26.0, tree-sitter-java 0.23.5), because JavaParser (used in M2) cannot be downloaded in the analysis environment. Equivalence check `scripts/check_ast_equivalence.py`: for all 12 gold methods, fields, parameters, locals, member accesses, imports and method line equal the M2 JavaParser ASTs (`outputs/vanilla/ast_equivalence.json`). The static candidate rule (`concrete_types`, `resolve`) is copied unchanged from `evaluate_lab4.py`.
- Dry tests before execution used a scratch copy of the requests and a fabricated response set, never the API; no file under `outputs/requests_vanilla/` or `outputs/runs/` was created by them.
- Known property of the coding (from the gold labels, not from any response): when the gold target is neither a field type of H nor a parameter type of m (e.g. ref_id 21, `Quantifier.Times`), a correct recommendation is coded H2. Recall is computed independently of the label.

### Known deviations from the paper
One run at temperature 0 (the paper averages 5 runs at each of temperatures 0, 0.5, 1 for RecallX, and uses temperature 0 for Table I); 12 cases instead of 210; H2 without IDE preconditions; host input from the released reconstruction commit (ref_id 3 differs from what MM-Assist saw).

### Status
Registered 2026-10-20; binding from the commit that adds this entry. That commit must be pushed before `outputs/requests_vanilla/` is created and before the run directory exists. AI-assisted: drafted by an AI assistant; prompt source, input format and the ref_id 3 discrepancy were checked against the upstream repository and dataset. Accepted by the group for execution on 2026-10-20.

## D-09 — Result of the D-08 supplementary run (2026-10-20)

Records the outcome of the run registered in D-08. Nothing in D-08 (prompt, sample, coding rules, thresholds) was changed after execution. The M2 result in D-07 is unchanged.

### Timeline
D-08 was committed (17ec648) before the run but pushed after it, contrary to its "push first" rule; the scripts and prompt used are byte-identical to that commit. This is the only vanilla run and it is reported in full.

### Execution
- 12/12 HTTP 200, model `gpt-4o-2024-05-13`, all `finish_reason = stop`, all 12 responses plain JSON (the trailing-comma rule was never needed). No API errors, no retries, no exclusions. Pilot ref_id 1 retained.
- Independent check (2026-10-20): requests re-prepared from the frozen inputs in a second environment are byte-identical; offline re-evaluation (`evaluate_vanilla.py --offline`) reproduces `recommendations.csv` and `cases.csv` byte-for-byte.

### Results (`outputs/vanilla/summary.json`, `cases.csv`, `recommendations.csv`)
- Recommendations R = 34 (1-10 per case, mean 2.8). Labels: H1 5, H2 0, H3 3, Valid 26.
- Hallucination rate (H1+H2+H3)/R = 8/34 = 23.5% (paper Table I real-world: 1026/1293 = 79.4%). H1+H2 = 5/34 = 14.7%.
- Top-1 H1/H2: 2/12 cases (ref_ids 3, 16); M2: 0/12.
- RecallM@1 5/12, @3 9/12; RecallMC@1 4/12, @3 7/12; RecallC@1 4/5, @3 7/9.
- **Pre-registered decision (D-08): PARTIAL** (rate between 20% and 50%; top-1 H1+H2 between 1 and 4). D-07 threat 1 is partly supported.

### Coding audit (no rule changed)
- All 5 H1 targets are absent from the frozen trees: `CrmBusinessStatusTypeValidator` (ref_id 3, ranks 1-3), `UserValidationService` and `WebSocketSenderService` (ref_id 16; the existing class is `WebSocketSenderApi`, imported by the host). All 3 H3 are `@Override` methods (ref_ids 15, 17).
- Ref_id 3 ranks 1 and 2 are identical; counted as two recommendations per D-08. Deduplicated: R = 33, rate 7/33 = 21.2%, decision unchanged.
- Ref_id 14: top-1 has the gold method and target `cn.iocoder.yudao.module.ai.service.AiChatModalService`, scored as a miss against the frozen gold `...service.impl.AiChatModalService` (D-07 threat 4). With a corrected gold, RecallMC@1 would be 5/12.

### Post-hoc comparison with M2 (not pre-registered; exploratory)
- Top-1 fully correct (method and target): M2 10/12 (method given) vs vanilla 4/12. Paired exact McNemar: 6 cases correct only in M2, 0 only in vanilla, p = 0.031.
- Hallucinations: M2 0/12 vs vanilla 8/34 per recommendation (Fisher p = 0.09); top-1 H1/H2 0/12 vs 2/12 (p = 0.48). Not significant at n = 12. *[Corrected in D-10: the first comparison mixes units and is withdrawn.]*
- Both runs are far below the paper (binomial p < 0.001). *[Qualified in D-10: the vanilla p-value assumes independent recommendations.]*

### Interpretation
- The target-only prompt mainly inflated accuracy: giving the LLM the method raised top-1 accuracy from 4/12 to 10/12. Its effect on hallucinations is in the expected direction but small and not significant here.
- Even with the paper's own prompt and input format, the hallucination rate (23.5%) does not reproduce Table I (79%). The non-reproduction in D-07 is therefore not explained by our prompt adaptation alone. Remaining candidate explanations: sample (D-07 threat 2: mostly Service -> Mapper moves in small classes, 11/12 with fewer than 15 methods), the narrow H2 rule (H2 = 0 in both runs vs 21% in the paper; D-04 deviation 2), fewer recommendations per class (2.8 vs about 6), and a single run at temperature 0.
- M2 remains the primary, pre-registered RQ1 result (D-07: NOT REPRODUCED). This run is the closest operational replication of the paper's vanilla setting and is reported as a supplementary sensitivity analysis.

## D-10 — Record corrections before tagging M2_REPRO (2026-10-20)

Record and housekeeping changes only. No request, response, score, threshold, sample or decision changes, and nothing is re-run. The M2 result (D-07) and the D-08 decision (D-09: PARTIAL) are unchanged.

1. **D-09 statistics (exploratory part only).**
   - The Fisher test "M2 0/12 vs vanilla 8/34" compares a per-case count (top-1 of 12 cases) with a per-recommendation count (34 recommendations). The units differ, so this comparison is withdrawn. The like-for-like comparison is top-1 H1/H2 0/12 vs 2/12 (Fisher p = 0.48), as already reported.
   - "Both runs are far below the paper (binomial p < 0.001)": for M2 (one top-1 per case, 0/12 vs 55%) the test is valid (p = 6.9e-5). For the vanilla run (8/34 vs 79.4%) the binomial test treats the 34 recommendations as independent, but they are clustered within 12 cases (e.g. ref_id 3 contributes three H1). Its p-value is therefore too small and is indicative only. The direction (far below the paper) is unchanged.
   - D-09 text is kept; a pointer to this entry is added to the two bullets.
2. **Non-English text in group scripts.** The GUI labels and status messages of `scripts/run_frozen_lab.py` and `scripts/run_vanilla_lab.py` were partly in Chinese (group rule: all group-written material in English). They are translated. Only Tk label/status strings change; request construction, parsing, file layout and the API call are untouched.
   - The runner snapshots inside the run folders (`outputs/runs/*/runner.py`) are **not** changed, because `run_manifest.json` records their sha256. They remain the exact code that was executed. From this commit on, `scripts/run_*_lab.py` differ from those snapshots only in these strings (the D-09 statement "byte-identical to 17ec648" refers to the code as executed).
3. **Stale status in Lab4 files.** `outputs/lab4/LAB4_REPORT.md` and `COORDINATOR_CHECKPOINT.md` still say "INCONCLUSIVE pending coordinator review". A one-line "superseded by D-07" note is added at the top of each; the rest is kept as the Lab4 record. Neither file is listed in `evidence_manifest.sha256`.
4. **Reproducibility notes.** Added `requirements.txt` (tree-sitter versions from D-08). README now states that an offline re-evaluation on another OS rewrites `outputs/lab4/` and `outputs/static/` with only line-ending, path-separator and `evaluated_utc` differences (checked on Linux 2026-10-20: `git diff --ignore-cr-at-eol` shows only `evaluated_utc` and `run` path), and the repository layout table is updated.

AI-assisted: these issues were found in a repository review by an AI assistant and checked by the group before committing.


## D-11 — Event A pre-registration: held-out sample, frozen decision rule, prediction (pre-execution registration, 2026-10-27)

Written after reading the Event A brief and before any held-out request, static coding or gold lookup. Base: tag `PRE_EVENT_A`. Commit this entry (and fill in the tracker prediction) before running `select_sample.py --check-source` on the held-out set.

### 1. Held-out material

- **Source:** same artefact as M2: datasets.zip @ cuboulder-se-research/move-method-assist `8b0898f`, sha256 `8b2808…c3eb` (re-verified), file `data/refminer_data/instance-methods/mm-assist-emm/elastic_res.json`.
- **Project rule (fixed before looking at any outcome):** take the first project, ordered by its smallest `ref_id`, that does not appear in the M2 sample. M2 used ruoyi-vue-pro (min ref_id 1) and flink (min 21), so the held-out project is **elasticsearch** (min ref_id 66; 9 records).
- **Eligibility:** D-03 rules (1)-(3) unchanged, plus rule (4) below. All 9 elasticsearch records pass rules (1) and (2) (dry run).
    - (4) The method m can be located in the host file at `newCommitHash`: a unique method with that name, or, if overloaded, a unique match on parameter count and types from the dataset signature. Added because D-05 found signature mismatches in M2; it is checked during screening, before any LLM call, and reasons for failure are logged.
- **Order and size:** ref_id ascending; first 6 eligible. Failures are skipped and logged in `data/event_a_screening_log.csv`.
    - Expected sample if all pass: **66, 93, 94, 278, 279, 363**. Reserves in order: 368, 373, 376.
    - If fewer than 6 elasticsearch records are eligible, top up from the next unused project in the same order (graal, min ref_id 433) and record this.
- **Window/version:** each case is checked out at its `extraction_results.newCommitHash` (authors' reconstructed pre-move state), as in M2.
- **Known before execution (not outcome information):** the elasticsearch host classes are larger than in M2 (telemetry `methodCount` 15-46 for the expected six vs 2-14 for ruoyi-vue-pro). Gold targets have not been read.
- **Non-independent pair 278/279 (group decision: keep both).**
    - Both records come from the same developer commit (`sha1` 04d3b99) and move the same `lookup(IntBlock, ByteSizeValue)` method out of two sibling classes (`BooleanVectorBlock`, `BytesRefVectorBlock`). Both host files are under `generated-src/`, i.e. generated from a shared template.
    - Both are kept, because the order rule selects them and M2 kept the same situation (ref_ids 7 and 8 share developer commit 29f1eb2). Adding a de-duplication rule only for Event A would change the frozen sampling rule.
    - The pair is handled by the pre-registered sensitivity analysis in Section 3, not by removing a case. No case is removed or replaced after execution for this reason.
    - The dataset signature for 279 gives the return type `ReleasableIterator<BooleanBlock>` although the host is the BytesRef class (probably copied from 278). Rule (4) only checks that m can be located (by name, and by parameter types if overloaded); it does not compare return types. As in D-05, any signature difference is recorded in the input audit and is not a reason to exclude the case. The frozen signature is sent to the LLM unchanged.

### 2. Frozen method (no retuning)

Identical to M2 (D-03, D-04, `docs/coding_manual.md`, all at `PRE_EVENT_A`):

- **LLM-only:** `gpt-4o-2024-05-13`, temperature 0, `docs/prompt_adapted.txt` as at `M1_PLAN` (template sha256 `ef3ed569…` with CRLF; check with `input_record.json`), whole .java file without line numbers, one request per case, top-1 = first `target_class`.
- **Static coupling ranking:** coding manual rules 1-5 unchanged (C = field types of H ∪ parameter types of m; score = member accesses in m's body; ties alphabetical; empty C = `NONE`). Static coding uses the actual source of m, as in D-05.
- **Decision rule (hybrid), written down before execution:**
    1. If the LLM top-1 resolves to a class in C, output the LLM top-1.
    2. Otherwise (LLM class is H1 or H2), output the static top-1.
    3. If C is empty, the output is `NONE` and counts as a miss.

  This is the M2 hybrid rule unchanged; step 3 only states how M2's existing `NONE` rule applies to the hybrid output.
- **Coding:** H1/H2 as in the coding manual (H1 check saved to `outputs/event_a/h_check/<ref_id>.txt`); gold = exact FQN match; a simple name is resolved only if unique in the project. Inner-class hosts are coded as written (dataset_format.md finding 5: an outer-class target that is not in C counts as H2) — not changed for Event A.
- **Outputs:** `outputs/event_a/` (requests, raw responses, `results.csv`, `summary.json`), using the same scripts. The only script changes allowed are input/output paths (sample file, output folder, case-ID list) so that M2 files are not overwritten; selection uses `scripts/select_sample.py --project elasticsearch --n 6 --rule4 --sample-out data/event_a_sample_ids.csv --log-out data/event_a_screening_log.csv`. Request construction, parsing, static coding and scoring are not changed. The first run is frozen; any later method change is a separately registered run and does not replace it.

### 3. Metrics (same as M2, n = 6)

LLM / static / hybrid Recall@1; H1+H2 count for LLM-only; LLM-static top-1 agreement; plus the number of cases where the hybrid fallback (step 2) was used and whether it turned a miss into a hit or a hit into a miss.

**Primary result:** all metrics over the 6 cases, each case counted once. The prediction (Section 4) and the challenge thresholds (Section 5) apply to the primary result.

**Pre-registered sensitivity analysis (developer-commit clusters):**

- Cases that share a developer commit (`sha1`) form one cluster. In the expected sample this is only {278, 279}, giving 5 units. If screening replaces a case, the same rule is applied to the final sample.
- Each cluster's value for a metric is the mean of its cases (0, 0.5 or 1 for a two-case cluster). Each metric is reported as the sum over units / 5.
- The sensitivity result is reported next to the primary result and does not replace it.
- **Reading rule:** if a Section 5 conclusion (challenges / does not challenge M2) is the same under both counts, it is reported as robust to the pair. If it changes, the conclusion is reported as depending on the 278/279 pair and therefore weak.
- For comparability, the same clustering is also reported for M2 (7 and 8 as one cluster, 11 units) in the Event A comparison. This is a post-M2 re-count of existing results, not a change to the M2 result (D-07).

### 4. Prediction (enter in the tracker before execution)

Basis: paper Table III (vanilla LLM RecallC@1 44% for large classes) and Table I (H1+H2 ~ 55%), adjusted upward for our target-only prompt (M2: 10/12; D-09 exploratory comparison: fully correct top-1 4/12 with the vanilla prompt vs 10/12 with the target-only prompt).

- **P1:** LLM-only Recall@1 = 3-5/6 (below M2's 10/12 = 83% because classes are larger and targets less obvious than Service -> Mapper).
- **P2:** LLM-only H1+H2 = 0-1/6.
- **P3:** static Recall@1 <= LLM-only Recall@1; LLM-static agreement 3-5/6.
- **P4:** hybrid Recall@1 >= LLM-only Recall@1 (RQ2 non-decrease rule).

### 5. Outcomes that would challenge the M2 conclusion

M2 concluded: (a) under a target-only prompt, hallucinations are rare (RQ1 NOT REPRODUCED, 0/12); (b) the hybrid rule does not lower Recall@1 (supported by equality, fallback never used).

- **Challenges (a):** LLM-only H1+H2 >= 2/6. The threshold matches M2's non-reproduction cut-off (<= 3/12 = 25%; here <= 1/6 ~ 17%). If the true rate were the paper's 55%, P(<= 1/6) ~ 7%. A result >= 2/6 would mean the M2 0/12 is mainly a sample effect (D-07 threat 2).
- **Challenges (b):** hybrid Recall@1 < LLM-only Recall@1, i.e. the static fallback replaces a correct LLM answer.
- **Strengthens (b) beyond M2:** fallback used at least once and hybrid Recall@1 > LLM-only Recall@1 (first observed evidence of hallucination reduction).
- **Not informative for (b):** fallback never used again (same as M2); report it as such.

### 6. Comparison and design implication (after execution)

- Report transfers / does not transfer for each of (a), (b), Recall@1 and agreement against M2, with the per-case table as the main evidence.
- Design implication to evaluate with the evidence (no pattern assumed in advance): whether the static candidate set C is a useful precondition check on LLM output, i.e. whether the "where does m's data come from" coupling evidence (Feature Envy) changes any decision. Whether a common ranking interface is justified stays with M4/PRE_EVENT_B; a fallback that is never used is an argument against adding the abstraction now.

### 7. Threats specific to Event A

n = 6, one run; 278/279 not independent (handled by the Section 3 sensitivity analysis); 278/279 hosts are generated code, so the developer's real change was probably in the generator template, which neither the LLM nor the static ranking sees; one project only; possibly unavailable `newCommitHash` for some elasticsearch records (seen for one record on 2026-10-09); larger classes may hit the context limit (record any truncation; do not trim the input).

### 8. Execution readiness record (2026-10-27)

This registration was saved before Event A source screening, static coding, reference-target lookup or LLM requests in this session. The shared tracker has not yet been completed, as confirmed by the group. Screening and execution are pending that entry. No Event A outcome is claimed.

Implementation audit: the existing M2 selector does not yet implement --project, --rule4, --sample-out or --log-out. Event A support must be implemented and checked before selection; the command in Section 2 describes the intended interface, not an already available capability. Event A support must use separate paths and preserve the M2 files. Method-location screening is a prospective eligibility addition, not a change to ranking, prompting or scoring.

Historical tags: M2_REPRO and PRE_EVENT_A were absent locally at the start of this session. Any tags added now identify the existing pre-event commit; they do not establish that tagging or pushing happened before the Event A brief was read. The brief and the supplied D-11 draft had already been read. This timing limitation must be disclosed.

Prediction clarification: P1 is a range of 3-5 correct cases out of 6 (50%-83.3%); its upper endpoint equals M2's 10/12, rather than being strictly below it.

Sensitivity implementation clarification: cluster-weighted rates use the actual number of developer-commit clusters in the final sample. The expected denominator is 5. To apply Section 5 to weighted counts, use the underlying H1+H2 rate threshold (>25% challenges (a)); compare hybrid and LLM weighted Recall@1 directly for (b). Weighted fallback incidence and directional effects are descriptive rates; preserve the primary integer case counts separately.

AI assistance: an assistant helped prepare this registration and implementation audit. Group review and tracker entry remain pending. No API calls have been made for Event A.
### 9. Readiness update before source screening (2026-10-27)

The group confirmed in chat that the shared Tracker prediction and sample plan have been entered. Git commits and pushes are managed by the group; the assistant will not create them. The assistant-created commit and tags were revoked at the group's request. The baseline is identified by commit 1b2eb41, without claiming a currently existing PRE_EVENT_A tag.

Implementation interface: scripts/prepare_event_a.py --tracker-recorded --java <Java17+> implements the registered project order, six-case selection, rule4 and separate Event A evidence paths. It replaces the not-yet-implemented selector command shown in Section 2. It does not change prompting, ranking or scoring. Rule4 is a prospective eligibility difference from M2 and is reported as such. Parser-tool failures and network infrastructure errors stop execution; they are not grounds for silently replacing a case. JavaParser facts were checked to be exactly equal to the preserved AST facts for all twelve M2 cases before screening. scripts/run_event_a.py retains the M2 model, temperature, request construction and parser, and uses the final six-case list and independent paths.

The first pilot is retained in the six observations. The remaining requests require a pilot review confirming input integrity and transport/parsing only; no rule or input is tuned to pilot correctness. No valid response is rerun. HTTP/transport failures stop the run and are preserved; incomplete/unparseable responses stop for reporting and are not silently replaced. The group must record any subsequent action prospectively.

Terminal entry point added before any Event A API request: scripts/run_event_a_terminal.py. The group requested terminal input because the GUI field was unusable. It inherits Runner.execute and parse_result from scripts/run_event_a.py; only secret entry and progress display differ. It preserves the pilot integrity gate, all six frozen requests, model and decision rules. No key is saved or passed on the command line.

## D-12 — Event A result, prediction check and comparison with M2 (2026-10-28)

Result record for the run pre-registered in D-11. Nothing is re-run and no request, response, label, rule or threshold is changed.

### 1. Timeline and registration evidence

| UTC, 2026-10-27 | Event | Evidence |
|---|---|---|
| 13:35 | Event A preparation and screening started (6/6 pass rules 1-4) | `outputs/event_a/preparation_manifest.json`, `data/event_a_screening_log.csv` |
| 13:41 | gpt-4o-2024-05-13, case 66: HTTP 401 (API key) | `outputs/event_a/runs/20261027T134143_156443Z_terminal/` |
| 13:41, 13:44 | gpt-4o-2024-05-13, case 66: HTTP 404 `model_not_found` (two attempts) | `outputs/event_a/runs/20261027T134156_153205Z/`, `…134412_021954Z/` |
| 14:04 | gpt-6-luna primary run, pilot 66 then 93, 94, 278, 279, 363 | `outputs/event_a_gpt6_luna/runs/20261027T140405_285837Z/` |
| 14:14 | Supplementary case 368 (registered after the primary responses) | `outputs/event_a_supplement_368/` |
| 14:21 | Exploratory full repeat (registered after the primary responses) | `outputs/event_a_repeat_full/` |
| 16:25 | Everything above committed and pushed in one commit `68f634d` | git |

**Disclosure.** D-11 asked for the entry to be committed before screening. This did not happen: the registration, screening, all runs and the first report were committed together after execution. Git therefore does not show that D-11 preceded execution. The available evidence is:

- every run folder contains `preregistration.md`, which is identical (whitespace-normalised) to D-11 as committed;
- `pilot_approved.json` records that the pilot gate checked integrity only (`gold_or_correctness_used_for_gate: false`);
- D-11 §9 records the group's confirmation that the Tracker prediction and sample plan were entered before source screening. The Tracker entry time itself is not recorded in this repository.

No numerical prediction was changed after any response was seen.

### 2. Deviations from D-11 (all disclosed before or at execution unless stated)

1. **Model.** `gpt-4o-2024-05-13` was shut down by OpenAI on 2026-10-23 (deprecation announced 2026-04-22), between M2 (2026-10-20) and Event A. The failed attempts are preserved and not scored. Replacement: `gpt-6-luna`, temperature 0, `reasoning_effort: none`; prompt messages and source bytes unchanged (`outputs/event_a_gpt6_luna/migration_check.json`).
   - The replacement was selected by the group (`docs/event_a_model_change.md`).
2. **Empty recommendation (363).** The model returned a complete HTTP-200 response with an empty list `[]`. D-11 did not register this outcome; the unchanged parser stopped (`BLOCKED`). 363 is retained and not classified as H1/H2. For Recall@1 and agreement it is counted as a miss / disagreement; this convention was chosen after seeing the response.
3. **Hybrid for 363.** D-11 step 2 reads "Otherwise … output the static top-1". Read literally, an empty LLM answer falls under "Otherwise" and the hybrid outputs the static top-1 (`IndexVersion`, a miss). The parenthesis "(LLM class is H1 or H2)" shows this case was not anticipated. Both readings (static fallback, or no output) give the same hybrid result, 3/6, so no conclusion depends on the choice.
4. **Prompt hash.** D-11 cites the M1_PLAN template hash with CRLF line endings (`ef3ed569…`). The Event A requests record `fbe97552…`, which is the same M1_PLAN file with LF line endings (`git show M1_PLAN:docs/prompt_adapted.txt | sha256sum`). Content is unchanged.
5. **Implementation.** Screening used `scripts/prepare_event_a.py` (JavaParser) instead of the `select_sample.py` options named in D-11 §2 (recorded in D-11 §9). Selection order, rule 4 and the final sample are as registered.
6. **Signatures.** As in M2 (D-05), dataset signatures differ from the reconstructed source in 5/6 cases (66, 93, 94, 279, 363; `first_run_report/input_audit.json`). They were sent unchanged.

### 3. Primary result (6 cases, first gpt-6-luna response)

| Case | Gold target | LLM top-1 | LLM | Label | Static top-1 (score) | Static | Hybrid | Fallback |
|---|---|---|---:|---|---|---:|---:|---|
| 66 | IndexShardSnapshotStatus | same | 1 | valid | IndexShardSnapshotStatus (5) | 1 | 1 | no |
| 93 | EsPhysicalOperationProviders | same | 1 | valid | LocalExecutionPlannerContext (2) | 0 | 1 | no |
| 94 | EnrichPolicyResolver | same | 1 | valid | EnrichResolution (1) | 0 | 1 | no |
| 278 | BooleanVector | BooleanLookup | 0 | H2 | ByteSizeValue (0) | 0 | 0 | miss→miss |
| 279 | BytesRefVector | BytesRefLookup | 0 | H2 | ByteSizeValue (0) | 0 | 0 | miss→miss |
| 363 | DenseVectorFieldMapper.ElementType | `[]` | 0 | no recommendation | IndexVersion (0) | 0 | 0 | see §2.3 |

| Metric | M2 (12 cases) | Event A (6 cases) | Event A, commit clusters (5 units) | M2, commit clusters (11 units) |
|---|---:|---:|---:|---:|
| LLM Recall@1 | 10/12 (83%) | 3/6 (50%) | 3/5 (60%) | 9/11 |
| Static Recall@1 | 8/12 (67%) | 1/6 (17%) | 1/5 (20%) | 7/11 |
| Hybrid Recall@1 | 10/12 (83%) | 3/6 (50%) | 3/5 (60%) | 9/11 |
| LLM-static agreement | 9/12 (75%) | 1/6 (17%) | 1/5 (20%) | 8/11 |
| H1+H2 (LLM-only) | 0/12 | 2/6 (33%) — H1 0, H2 2 | 1/5 (20%) | 0/11 |
| Fallback used | 0/12 | 2/6 (both miss→miss) | — | — |
| No recommendation | 0/12 | 1/6 | — | — |

Evidence: `outputs/event_a_gpt6_luna/first_run_report/` (`observations.csv`, `summary.json`, `static/`, `h_check/`, `input_audit.json`).

### 4. Prediction check (D-11 §4)

| | Prediction | Observed | Verdict |
|---|---|---|---|
| P1 | LLM Recall@1 3-5/6 | 3/6 | met (lower bound) |
| P2 | H1+H2 0-1/6 | 2/6 | **not met** |
| P3 | static <= LLM; agreement 3-5/6 | 1/6 <= 3/6; agreement 1/6 | first part met; agreement **not met** |
| P4 | hybrid >= LLM | 3/6 = 3/6 | met, by equality (either §2.3 reading) |

### 5. Does the M2 conclusion transfer? (D-11 §5)

- **(a) Hallucinations are rare under the target-only prompt — weakened, not cleanly overturned.** By case, H1+H2 = 2/6 reaches the challenge threshold (>= 2/6). By developer-commit cluster it is 1/5 = 20%, below the registered 25% threshold. Under the pre-registered reading rule the challenge therefore **depends on the 278/279 pair and is weak**. Both H2 answers name the generated `…Lookup` class that implements the `lookup` operation, which exists in the project but is not a field or parameter type of the host (narrow H2 rule, D-04 deviation 2).
- **(b) The hybrid rule does not lower Recall@1 — transfers, with no benefit.** Hybrid = LLM = 3/6. Unlike M2, the fallback was used (278, 279): the candidate-set check rejected both H2 answers, but the static replacement was also wrong. Neither the challenge (hybrid < LLM) nor the strengthening condition (hybrid > LLM) is met.
- **Recall@1 — lower, cause not separable.** LLM-only drops from 83% to 50%. Because the project and the model changed together (§2.1), this cannot be attributed to project transfer.
- **LLM-static agreement and static accuracy — do not transfer.** Agreement falls from 75% to 17% and static Recall@1 from 67% to 17%. In 3/6 cases (278, 279, 363) every static candidate scores 0, so the static top-1 is decided only by the alphabetical tie-break. This does not depend on the LLM, so the model change does not explain it.

**Strongest evidence:** the per-case table in §3, in particular the zero-score static rankings in `first_run_report/static/{278,279,363}.audit.json` and the cluster-weighted H1+H2 of 1/5.

### 6. Supplementary and exploratory runs (reported separately; not part of the primary result)

- **Case 368** (next reserve, registered after the primary responses because of 363): LLM hit (`AggregateFunction`, in C), static miss (`Expression`, score 2), hybrid hit, no fallback. Does not replace 363 or change the denominator. `docs/event_a_supplement_368.md`, `outputs/event_a_supplement_368/`.
- **Full repeat** (byte-identical requests, registered after the primary responses): the same target or empty outcome in 6/6 cases, including `[]` for 363; rationale text differs in 5/6. Limited repeatability evidence only; not pooled. `docs/event_a_repeat_full.md`, `outputs/event_a_repeat_full/comparison/`.

### 7. Post-hoc observation (not pre-registered; descriptive only)

In the authors' reconstructed source the extracted method sometimes takes the gold target as a parameter. This holds for 66 (`IndexShardSnapshotStatus`), 93 (`EsPhysicalOperationProviders`) and 368 (`AggregateFunction`), i.e. 3 of the 4 Event A LLM hits, and for 0/12 M2 cases (where the gold was typically a field type of a Service class). The frozen signature sent to the LLM does not contain these parameters, but the full host file does. This may make some held-out cases easier for the LLM and is a further difference between the two samples. It is not tested here.

### 8. Design / refactoring implication

The two parts of the hybrid behave differently on this project:

- As a **precondition check** (is the LLM's class a field or parameter type of H?), the static candidate set C did its job: it flagged both H2 answers, in line with Def. III.3 of the paper.
- As a **ranking**, the coupling score failed: in 278, 279 and 363 the method body accesses no member of any candidate (278/279 only delegate: `return getBooleanLookup(positions, targetBlockSize);`). With no Feature Envy signal, the "best" static target is chosen alphabetically, i.e. arbitrarily, and the fallback cannot recover the correct target.

Implication: a Move Method decision for a delegating method cannot be justified by coupling evidence from the method body alone. The static evidence should be used to reject candidates, not to choose one, when all scores are zero. This is evidence for keeping the check inline as a filter rather than introducing a common ranking interface now; that design question remains with M4 (PRE_EVENT_B). Separately, the runner needs an explicit "no recommendation" outcome distinct from transport errors and malformed output; this is recorded for future runs and does not change the first observations.

### 9. Threats specific to this result

n = 6, one project; 278/279 not independent and generated code (the real change was probably in the template); model change and possible contamination; no-recommendation convention chosen after execution; signature mismatches in 5/6 cases; narrow H2 rule; one primary run (plus one exploratory repeat).

### 10. Tracker entry (Event A result / decision)

> Event A (elasticsearch, 6 cases; gpt-4o-2024-05-13 shut down 23 Oct, replaced by gpt-6-luna, disclosed before the valid run): LLM Recall@1 3/6, static 1/6, hybrid 3/6, agreement 1/6, H1+H2 2/6 (1/5 by developer-commit cluster), one empty recommendation (363). M2's "hallucinations are rare" is weakened but the challenge depends on the non-independent pair 278/279; the hybrid non-decrease result transfers (equality, fallback used twice without benefit); the Recall@1 drop cannot be separated from the model change. Evidence: D-12, tag EVENT_A, outputs/event_a_gpt6_luna/first_run_report/.