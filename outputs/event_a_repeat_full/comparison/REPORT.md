# Event A first result and exploratory stability repeat

The first GPT-6 Luna run produced six complete HTTP-200 responses: three correct target classes, two incorrect out-of-candidate targets (H2), and one empty recommendation list. A complete repeat with byte-identical requests produced the same target or empty-list outcome in all six cases. The separate reserve case 368 was correct. No result replaces the first observations.

## Execution and model deviation

Primary cases: 66, 93, 94, 278, 279, 363 from elasticsearch; exact frozen commits are in data/event_a_sample_ids.csv. M2 used gpt-4o-2024-05-13. That snapshot was shut down on 23 October 2026, between M2's 20 October run and Event A. The failed 404 attempt was preserved; Event A uses gpt-6-luna, temperature=0 and reasoning_effort=none. The prompt/source/signatures were retained unchanged. Project and model both changed, so differences cannot be attributed to project transfer alone.

Primary evidence: outputs/event_a_gpt6_luna/runs/20261027T140405_285837Z/.
Repeat evidence: outputs/event_a_repeat_full/runs/20261027T142152_834187Z/.
Supplement evidence: outputs/event_a_supplement_368/runs/20261027T141400_074189Z/.

## Per-case primary result and repeat

| Case | First target | Repeat target | Exact-gold hit | Label | Static hit |
|---|---|---|---:|---|---:|
| 66 | IndexShardSnapshotStatus | Same | 1 | Valid | 1 |
| 93 | EsPhysicalOperationProviders | Same | 1 | Valid | 0 |
| 94 | EnrichPolicyResolver | Same | 1 | Valid | 0 |
| 278 | BooleanLookup | Same | 0 | H2 | 0 |
| 279 | BytesRefLookup | Same | 0 | H2 | 0 |
| 363 | Empty list [] | Empty list [] | 0* | No recommendation | 0 |

*For descriptive Recall@1, no recommended target is counted as a miss. This convention is disclosed after observing the empty response; it does not change the frozen parser or claim a pre-registered empty-output policy. Each nonempty target's actual declaration was checked in its frozen commit. H2 means the class exists but is outside the operational candidate set. No recommendation is not classified as H1 or H2.

All six target/empty outcomes agree across runs; the rationale wording differs for the five nonempty answers. This is limited repeatability evidence for these six fixed requests and two full runs, not a guarantee of deterministic generation.

## Metrics and comparison with M2

| Metric | M2 primary | Event A first run | Full repeat |
|---|---:|---:|---:|
| LLM Recall@1, with disclosed empty-is-miss convention | 10/12 (83.3%) | 3/6 (50.0%) | 3/6 (50.0%) |
| Static Recall@1 | 8/12 (66.7%) | 1/6 (16.7%) | 1/6 (16.7%) |
| LLM-static agreement, empty counted as disagreement | 9/12 (75.0%) | 1/6 (16.7%) | 1/6 (16.7%) |
| H1 + H2, case denominator | 0/12 | 2/6 | 2/6 |
| Empty recommendations | 0/12 | 1/6 | 1/6 |
| Fully specified frozen hybrid Recall@1 | 10/12 | Undefined for 363 | Undefined for 363 |

For the five nonempty cases, the frozen hybrid rule yields three hits. Fallback occurs on 278 and 279: both change from an incorrect LLM target to an incorrect static target. There is no observed miss-to-hit or hit-to-miss change on those cases. The plan did not specify an absent LLM top-1, so a six-case frozen hybrid point estimate is not claimed. With 363 unresolved, the arithmetic bound is 3-4 hits out of 6. Two explicitly post-hoc conventions, counting no hybrid output as a miss or using the static fallback on an empty LLM response, both give 3/6. They are sensitivity descriptions, not replacements for the frozen result. The repeat runner records [] and continues; this operational change does not repair the first protocol retrospectively.

Predictions: LLM 3-5/6 and static no higher than LLM are met descriptively; the H1+H2 prediction of at most 1/6 and agreement prediction of 3-5/6 are not met. The full frozen hybrid non-decrease prediction cannot be scored without an empty-output convention; both disclosed post-hoc conventions give equality.

## Developer-commit sensitivity

Cases 278/279 share one developer commit and form a single unit. There are five units: {66}, {93}, {94}, {278,279}, {363}. Weighted descriptive LLM Recall@1 is 3/5, static 1/5 and agreement 1/5. H1+H2 is 1/5 (20%), compared with 2/6 (33.3%) when cases are counted separately.

Thus the case-level hallucination challenge threshold is reached, but the cluster-weighted threshold (>25%) is not. As pre-registered, the conclusion depends on the paired cases and is weak. The two H2 observations must not be treated as independent confirmation. Model replacement adds a further confound.

For M2, clustering 7/8 gives eleven units. The existing results are recounted separately below; the original M2 result remains unchanged.

## Separate supplementary case 368

The next pre-listed reserve, 368, was registered after primary responses and run once. It recommended AggregateFunction, matching the exact gold and lying in C: LLM 1/1, static 0/1, hybrid 1/1, no H1/H2 and no fallback. It is an additional observation, not a replacement for 363, and does not change the primary denominator, predictions or thresholds. No seven-case primary score is reported.

## Design implication

The candidate-set check rejects two operational H2 targets, but its static fallback does not recover either correct gold target. It therefore supplies a constraint check without demonstrating improved exact-gold accuracy here. These observations do not justify adding a common ranking interface as an accuracy improvement. A concrete maintainability issue is the need for an explicit no-recommendation result distinct from transport errors and malformed output: [] is valid JSON, yet the frozen parser stopped the run. Any revised handling should be registered for future runs while preserving these first observations.

## Limitations

Further limitations include one project, small n, dependent generated-code cases, unchanged dataset/source signature differences (notably 279), narrow H2 operationalisation, unknown cause of the empty response, model change and possible exposure to released source. Repeated [] is evidence of recurrence, not an explanation of why it occurred.

## Tracker result text

Event A (gpt-6-luna replacement): first six cases yielded LLM Recall@1 3/6 (empty recommendation counted as a miss descriptively), static 1/6, LLM-static agreement 1/6, H1=0, H2=2 and one empty list (363). The frozen hybrid metric is undefined for the empty-output case; among the other five cases there are three hits, and the two H2 fallbacks do not improve accuracy. Two explicitly post-hoc empty-output conventions both give hybrid 3/6. The H1+H2 challenge is pair-sensitive: 2/6 by case versus 1/5 by developer-commit cluster. Separate supplement 368 is an LLM/hybrid hit. An exploratory full repeat reproduced all six target/empty outcomes. Model change limits comparison with M2. Evidence: first_run_report/, event_a_supplement_368/first_run_report/ and event_a_repeat_full/comparison/.

M2 developer-commit recount: 11 units; llm_recall1 = 9.0/11, static_recall1 = 7.0/11, hybrid_recall1 = 9.0/11, llm_static_agree = 8.0/11.
