# CS4928-G05-P08

## RQ1

Reproduce vanilla LLM MoveMethod hallucination rates (H1/H2/H3) on a small sample from the paper's released corpus, comparing against the ~80% reported

## RQ2

Can a simple hybrid rule reduce hallucinated recommendations without lowering Recall@1, and is a common ranking interface justified over keeping the logic inline?

## Bounded sample / case IDs

12 instance-method Move Method cases from the MM-Assist real-world corpus. Source: datasets.zip (repo cuboulder-se-research/move-method-assist @ 8b0898f, sha256 8b2808…c3eb), instance-methods/mm-assist-emm/*_res.json (117 entries). Eligibility (D-03): isStatic = false; authors' reconstruction succeeded; newCommitHash fetchable from GitHub and host file present at that commit. Order: ref_id ascending; first 12 eligible.

## Method / metric or decision rule

Unit of analysis: one (host class H, method m) case; n = 12. Each case gets three top-1 target-class recommendations: (1) LLM-only: GPT-4o (gpt-4o-2024-05-13, or substitute recorded in D-04), temperature 0, paper's vanilla prompt adapted to ask for the target class only (deviation D-04). (2) Static coupling ranking: candidates = field types of H + parameter types of m (excluding JDK/primitive types and H); score = references in m's body to members of the candidate; ties broken alphabetically; no candidates = "NONE"

## Expected result before execution

Reference: paper Table III (Vanilla-LLM RecallC@1 = 67% small / 44% large classes, real-world instance methods) and Table I (vanilla LLM: H1 ≈ 33%, H2 ≈ 21%). E1: LLM-only Recall@1 ≈ 5–8/12, with at least 1 H1 or H2 recommendation. E2: Hybrid has 0 H1/H2 by construction; the test is whether Hybrid Recall@1 ≥ LLM-only. E3: LLM and static top-1 agree on fewer than 6/12 cases. Reproduced: LLM-only Recall@1 ≤ 8/12 AND ≥ 1 hallucination (LLM alone unreliable). Non-reproduction: LLM-only Recall@1 > 8/12 AND 0 hallucinations. Otherwise: partial reproduction, reported as observed.
