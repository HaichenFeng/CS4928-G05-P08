# Event A supplementary reserve plan for case 368

Registered: 2026-10-27, after the six primary responses and before screening, preparing or requesting case 368. This is a post-primary supplementary plan, not part of the original pre-registration. The group explicitly requested this additional case in chat.

## Trigger and purpose

Primary ref_id 363 returned HTTP 200, finish_reason=stop and content=[]: a complete JSON response with no recommendation. The unchanged M2 parser rejected the empty list because it requires a nonempty list containing target_class. The execution record says BLOCKED. This is not a network failure, truncated response, H1/H2 target, or justification for discarding an observation. The original six requests/responses remain the primary evidence. Why the model returned [] is unknown.

Use the next reserve already named in D-11, ref_id 368, to obtain one additional observation. It must be reported separately and must not replace 363, alter the original six-case denominator, or be used to claim that the original protocol completed without the empty-output problem.

## Case selection and eligibility

- Fixed additional case: ref_id 368, elasticsearch, from the same SHA256-verified MM-Assist datasets.zip @ 8b0898f.
- Use its extraction_results.newCommitHash and original dataset method signature.
- Apply D-03 eligibility and D-11 rule4 before any LLM request. Save commit fetch, tree, host source and unique-method matching evidence.
- If 368 fails eligibility, record the failure and stop. Do not automatically select another reserve.
- Do not use gold targets or author recommendations for selection or input construction. No correctness-dependent resampling.

## Fixed method and execution

- gpt-6-luna; Chat Completions; temperature=0; reasoning_effort=none.
- Identical frozen M2 prompt messages, rendered with the complete host .java source and the unchanged dataset signature; no line numbers, cropping, extra examples or instruction to force a nonempty answer.
- Same JavaParser facts, static candidate set/ranking, exact-FQN matching and hybrid rule as the current Event A plan. No change to primary scripts, files, inputs, outputs or thresholds.
- One request for 368; retain the first response. A transport/HTTP failure is preserved and reported, not silently rerun. An empty/unparseable/incomplete response is also retained, with no automatic second attempt or further reserve.
- If an empty recommendation occurs, label it NO_RECOMMENDATION; do not invent a target or classify it as H1/H2. The frozen hybrid rule's treatment of an absent top-1 remains unspecified. Do not retrofit a fallback as a primary result.

## Prediction and reporting

No supplementary correctness prediction is claimed: this plan follows knowledge of the primary empty response. The original numerical predictions remain unchanged and apply to the original six cases only. Report 368 individually as a post-primary supplementary observation. Its result must not change whether the original Section 5 challenge thresholds were met. Any seven-case aggregation is exploratory only, with 363 retained and the aggregation convention explicitly disclosed.

Primary status: six HTTP-200 responses exist, five with a top-1 recommendation and one empty list. The original parser's stop at 363 and the missing pre-specified empty-output scoring convention must be disclosed in the final report. No successful six-case hybrid evaluation is claimed by adding a seventh observation.

## Evidence locations

- Plan: docs/event_a_supplement_368.md
- Additional sample: data/event_a_supplement_368.csv (independent of data/event_a_sample_ids.csv)
- Screening, requests, raw response and supplementary results: outputs/event_a_supplement_368/
- Primary evidence remains outputs/event_a_gpt6_luna/runs/20261027T140405_285837Z/
- Runner: scripts/run_event_a_368.py (GUI; exactly one case)

The assistant does not commit or push. Tracker entry is maintained by the group.

## Tracker addendum

Supplementary reserve plan (registered after the primary responses): case 363 returned a complete empty recommendation list ([]), which the frozen parser could not process. We retain all six primary cases and responses. We will additionally run the next pre-listed reserve, ref_id 368, once with the same gpt-6-luna prompt and settings, and report it separately. It does not replace 363 or change the original n=6 predictions, thresholds or conclusions. Evidence: docs/event_a_supplement_368.md and outputs/event_a_supplement_368/.