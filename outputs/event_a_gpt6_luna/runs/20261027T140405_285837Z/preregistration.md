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
