# CS4928-G05-P08

Group G05 | Project P08: Move Method Refactoring with LLM + Static Evidence. The study is Bellur et al., ICSME 2025 (MM-Assist).

## Lab4 execution update — 2026-10-20

The 12 frozen target-only requests completed using **gpt-4o-2024-05-13**, temperature 0. H1+H2 = **0/12**; LLM/static/hybrid Recall@1 = **10/12, 8/12, 10/12**; LLM-static agreement = **9/12**.

The frozen arithmetic gives RQ1 **NOT REPRODUCED** and satisfies RQ2's non-decrease rule by equality. It does **not** demonstrate hallucination reduction. Overall paper-level interpretation is **INCONCLUSIVE pending coordinator review** because six frozen signatures differ materially from reconstructed source and ref_id 14 has a gold-package discrepancy. Inputs, gold labels and the decision rule were not changed; no result-driven reruns were performed.

**M2 status (D-07, supersedes the "pending coordinator review" wording above):** the as-frozen run is the final M2 result. RQ1 NOT REPRODUCED (H1+H2 0/12); RQ2 non-decrease rule supported by equality, with no hallucination reduction demonstrated. The signature, gold (ref_id 14), prompt and sample issues are recorded as threats to validity in D-07. A supplementary run with the paper's original vanilla prompt is registered in D-08; it does not replace this result.

**Prompt version (D-06):** the run used the `M1_PLAN` version of `docs/prompt_adapted.txt` (verified by `template_sha256` in each `input_record.json`). A 2026-10-19 revision was merged only after the run and was never used; it is kept as `docs/prompt_adapted_rev2026-10-19_UNUSED.txt`.

- [Lab4 report and evidence chain](outputs/lab4/LAB4_REPORT.md)
- [Per-case results](outputs/lab4/results.csv) · [Machine-readable totals](outputs/lab4/summary.json)
- [Input/gold audit](outputs/lab4/input_audit.json) · [Coordinator checkpoint](outputs/lab4/COORDINATOR_CHECKPOINT.md)
- Raw requests/responses: `outputs/runs/20261020T172353_759166Z/`
- Verify without API credits: `python scripts/evaluate_lab4.py --offline`, then `python scripts/verify_lab4.py`.

The original frozen M1 text and its pre-execution amendments are retained below.

The RQ, method and expected-result sections below are the same as the shared workbook (Student Tracker, G05 row). Amendments are appended with their dates; the original text is kept.

## RQ1

Reproduce vanilla LLM MoveMethod hallucination rates (H1/H2/H3) on a small sample from the paper's released corpus, comparing against the ~80% reported.

> **[Amendment 2026-10-18, before any execution]** Under our target-only prompt H3 cannot occur (m is given to the LLM, D-04), so RQ1 is measured on H1+H2. The comparable paper figure is (431+275)/1293 ~ 55% (Table I). The ~80% includes H3 and is not directly comparable. AI-assisted: suggested by an AI assistant, checked by the group against paper Table I and D-04.

## RQ2

Can a simple hybrid rule reduce hallucinated recommendations without lowering Recall@1, and is a common ranking interface justified over keeping the logic inline?

> **[Amendment 2026-10-18, before any execution]** The design part (common ranking interface vs inline logic) is answered in M4. Its alternatives and decision criteria will be frozen at PRE_EVENT_B.

## Bounded sample / case IDs

- **Unit:** 12 instance-method Move Method cases from the MM-Assist real-world corpus.
- **Source:** datasets.zip (repo cuboulder-se-research/move-method-assist @ 8b0898f, sha256 8b2808...c3eb), `instance-methods/mm-assist-emm/*_res.json` (117 entries).
- **Eligibility (D-03):**
  - isStatic = false;
  - the authors' reconstruction succeeded;
  - newCommitHash is fetchable from GitHub and the host file is present at that commit.
- **Order:** ref_id ascending; the first 12 eligible are taken. Failures are skipped and logged.
- **ref_ids:** 1, 2, 3, 5, 7, 8, 14, 15, 16, 17, 19, 21
- **Skipped during screening:** 0 (all 12 passed rule 3; screening run 2026-10-18).
- **Project mix:** 11 ruoyi-vue-pro, 1 flink. This is a direct consequence of ref_id ordering; the sample was not altered (external-validity threat).
- **Evidence:** `data/sample_ids.csv`, `data/screening_log.csv`, `outputs/screening_run.log`, `docs/Decisions.md` (D-03).

## Method / metric or decision rule

**Unit of analysis:** one (host class H, method m) case; n = 12. Each case gets three top-1 target-class recommendations:

1. **LLM-only:** GPT-4o (gpt-4o-2024-05-13, or a substitute recorded in D-04), temperature 0. The paper's vanilla prompt is adapted to ask for the target class only (deviation D-04; `docs/prompt_original.txt`, `docs/prompt_adapted.txt`).
2. **Static coupling ranking:** candidates are the field types of H plus the parameter types of m, excluding JDK/primitive types and H. Score = references in m's body to members of the candidate. Ties are broken alphabetically. No candidates = "NONE". See `docs/coding_manual.md`.
3. **Hybrid:** use the LLM answer if it is in the static candidate set; otherwise use the static top-1.

**Metrics:**

- Recall@1 per method (exact FQN match with the gold target).
- LLM-static top-1 agreement (x/12).
- Hallucinations: H1 = the class does not exist at the commit; H2 = the class exists but is not in the static candidate set.

**Decision rule:** directional comparison with the paper (see Expected result).

> **[Amendment 2026-10-18, before any execution]** RQ1 measure: hallucination rate = (number of cases where the LLM-only answer is H1 or H2) / 12. H3 is not applicable because m is given to the LLM (D-04).

## Expected result before execution

**Reference:** paper Table III (Vanilla-LLM RecallC@1 = 67% for small classes, 44% for large classes; real-world instance methods) and Table I (vanilla LLM: H1 ~ 33%, H2 ~ 21%).

- **E1:** LLM-only Recall@1 ~ 5-8/12, with at least 1 H1 or H2 recommendation.
- **E2:** Hybrid has 0 H1/H2 by construction; the test is whether Hybrid Recall@1 >= LLM-only.
- **E3:** LLM and static top-1 agree on fewer than 6/12 cases.

**Reproduced:** LLM-only Recall@1 <= 8/12 AND >= 1 hallucination.
**Non-reproduction:** LLM-only Recall@1 > 8/12 AND 0 hallucinations.
**Otherwise:** partial reproduction, reported as observed.

**Known deviation:** the LLM is given m, so LLM-only may score higher than the paper.

> **[Amendment 2026-10-18, before any execution: no LLM calls, no sampling run yet]**
>
> - Added **E0 (RQ1):** LLM-only H1+H2 in ~ 5-8 of 12 cases.
> - The following replaces the earlier Reproduced / Non-reproduction rule:
>   - **RQ1 reproduced:** H1+H2 >= 4/12.
>   - **RQ1 non-reproduction:** H1+H2 <= 3/12 (~4% probability if the true rate were 55%).
>   - **RQ2 supported:** Hybrid Recall@1 >= LLM-only Recall@1; not supported otherwise.
> - E1 (without its hallucination clause), E2 and E3 are unchanged.
> - **Reason:** the original rule judged RQ1 by Recall@1, which did not match RQ1's hallucination-rate question.

## Repository layout

| Path | Contents |
|---|---|
| `docs/` | decision log (D-03, D-04), artefact version, dataset format, prompts, static coding manual |
| `data/` | frozen sample and screening log |
| `scripts/` | sample selection script |
| `outputs/` | raw run logs and outputs |

**Reproduce sample selection:** `python scripts/select_sample.py --data <unzipped datasets.zip>/data --check-source`
