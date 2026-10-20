# Lab 4 reproduction evidence — G05 / P08

Execution date: 20 October 2026. Frozen plan: `M1_PLAN` (`53c2827dbc8aa579cff9814a541fab4c2dcb5033`).

**Current status: INCONCLUSIVE for the intended paper-level comparison because input/gold validity needs coordinator review. Execution of the 12 frozen requests is complete.** No cases were replaced, dropped or rerun to improve the result.

## Questions and frozen rules

RQ1: reproduce the vanilla LLM Move Method H1+H2 hallucination rate under a target-only prompt on 12 instance-method cases, comparing with `(431+275)/1293 ≈ 54.6%` in paper Table I. The frozen directional rule is REPRODUCED if H1+H2 ≥ 4/12; NOT REPRODUCED if ≤ 3/12. H3 is out of scope because the method is supplied.

RQ2: use the LLM top-1 when it belongs to the static candidate set; otherwise use static top-1. The frozen numerical criterion is Hybrid Recall@1 ≥ LLM-only Recall@1. Evidence of a reduction in hallucinations is a separate claim and requires hallucinations to be present. The ranking-interface design question remains deferred to M4, as frozen in M1.

## Inputs and execution

| Item | Preserved value |
|---|---|
| Corpus | MM-Assist released real-world instance-method corpus, 117 records |
| Upstream commit | `8b0898fbcaf05b6b4596c2c54b3b156d412c77bb` |
| Dataset SHA256 | `8b2808944db28ba6620f07a71fce38224f32cc100a444bb89573f662e268c3eb` |
| Frozen cases | 1, 2, 3, 5, 7, 8, 14, 15, 16, 17, 19, 21 |
| Selection | D-03, unchanged; 11 ruoyi-vue-pro, 1 flink |
| Checkout point | Each case's `extraction_results.newCommitHash`, not the developer's post-refactoring commit |
| Model requested and returned | `gpt-4o-2024-05-13` for all 12 cases |
| Temperature | 0 |
| Endpoint | `https://api.openai.com/v1/chat/completions` |
| Prompt | Frozen `docs/prompt_adapted.txt`, with the case's frozen signature and verbatim host source |
| Response interpretation | First JSON object's `target_class`; exact FQN matching to frozen gold |
| Run | `outputs/runs/20261020T172353_759166Z/` |
| Execution outcome | 12 HTTP 200 responses; all completed with `finish_reason=stop` and valid JSON |
| Usage | 26,446 prompt + 1,114 completion = 27,560 total tokens |

The pilot was ref_id 1. Its request was checked against the earlier prepared request; the fresh source download matched the preserved host hash. It returned valid JSON and was retained as one of the 12 observations. The remaining eleven were enabled only after `pilot_approved.json` was written. No model substitution was required, and no additional sampling took place.

`frozen_input_integrity.json` verifies that the sample CSV and both prompt templates match `M1_PLAN` after line-ending normalisation. The working coding manual already spells its dash, section symbol and union symbol differently from the tag; these are recorded editorial differences, not a change to the empirical coding rules.

The supplied IDE plugin initially returned empty static candidates for the standalone file. Those UI attempts produced no usable vanilla-LLM observations and are not included in these results. The Lab4 run uses the frozen target-only HTTP requests directly. The separate plugin adaptation is not the experimental execution route.

## Observed results

All rates below use the same denominator, 12. Recall@1 is a per-case binary match to the original, unchanged gold FQN.

| Measure | Observed |
|---|---:|
| H1 | 0/12 |
| H2 | 0/12 |
| H1+H2 | **0/12 (0%)** |
| LLM-only Recall@1 | **10/12 (83.3%)** |
| Static Recall@1 | **8/12 (66.7%)** |
| Hybrid Recall@1 | **10/12 (83.3%)** |
| LLM/static top-1 agreement | **9/12 (75.0%)** |
| LLM answer belongs to static candidate set | 12/12 |
| Hybrid fallback used | 0/12 |

| ref_id | LLM correct | Static correct | Hybrid correct | LLM/static agree | H1/H2 |
|---:|---:|---:|---:|---:|---|
| 1 | 1 | 1 | 1 | 1 | None |
| 2 | 1 | 1 | 1 | 1 | None |
| 3 | 1 | 0 | 1 | 0 | None |
| 5 | 1 | 1 | 1 | 1 | None |
| 7 | 1 | 1 | 1 | 1 | None |
| 8 | 1 | 1 | 1 | 1 | None |
| 14 | 0 | 0 | 0 | 0 | None |
| 15 | 1 | 1 | 1 | 1 | None |
| 16 | 1 | 0 | 1 | 0 | None |
| 17 | 1 | 1 | 1 | 1 | None |
| 19 | 1 | 1 | 1 | 1 | None |
| 21 | 0 | 0 | 0 | 1 | None |

Full FQNs, commits, model names and request IDs are in [results.csv](results.csv). Machine-readable totals are in [summary.json](summary.json).

### Applying the predeclared numerical rules

- RQ1 arithmetic: **NOT REPRODUCED**, since 0/12 ≤ 3/12. The expected 5–8 hallucinations were not observed. This arithmetic is reported without changing the threshold.
- RQ2 non-decrease criterion: **SUPPORTED as an equality**, since 10/12 ≥ 10/12. Every LLM answer was already in the static candidate set, so hybrid returned exactly the same answers. **No hallucination-reduction benefit was demonstrated.**
- The expected LLM Recall@1 range of 5–8/12 and agreement below 6/12 were also not observed.

These are computations on the as-frozen inputs. They do not remove the validity concerns below or establish a clean contradiction of the paper.

## Input and oracle audit: discovered after execution

The frozen requests were sent unchanged. JavaParser then selected the uniquely named method in each frozen host source for static coding. All twelve source methods are `private` although the frozen corpus signatures say `public`. Additional material discrepancies occur in six cases:

| ref_id | Frozen signature information | Actual reconstructed source |
|---:|---|---|
| 3 | `selectByIdAndName(Long id, String name)` returning `CrmBusinessStatusTypeDO` | No parameters; returns `SFunction<CrmBusinessStatusTypeDO,Object>`; body is a method reference |
| 5 | `selectCountByCategoryId(Long categoryId)` returning `Long` | Returns `CrmProductDO` |
| 15 | `selectByStatusAndPlatform(AiImageStatusEnum, AiPlatformEnum)` | No parameters |
| 16 | `updateConversationLastMessage(KeFuMessageDO)` | Also takes a `KeFuConversationDO conversation` parameter |
| 19 | `getSpuMap(Collection<Long> ids)` | Takes `Set<Long> spuIds` |
| 21 | `getWindowSize()` returning `Optional<Duration>` | Returns `void` and updates a field using `currentPattern.getWindowTime()` |

The parser did not pick another overload: each selected host contains only one method of the given name. These mismatches were not repaired, and neither prompts nor gold labels were rewritten after observing outputs. Static candidates and scores use the actual named method's declarations/body, following the coding manual's source-based rule. This limitation is particularly relevant where the supplied signature has a different parameter set.

For ref_id 14, the frozen gold is `cn.iocoder.yudao.module.ai.service.impl.AiChatModalService`. The checked-out host instead imports the existing interface `cn.iocoder.yudao.module.ai.service.AiChatModalService`; this is also the LLM answer and a static candidate. The tree has `service/AiChatModalService.java` and `service/impl/AiChatModalServiceImpl.java`, and the declaration search in the gold package found no `AiChatModalService` declaration. The run still scores it as incorrect under exact frozen FQN matching. The gold was **not** normalised to improve Recall@1.

For ref_id 21, gold `org.apache.flink.cep.pattern.Quantifier.Times` is a real nested class in `Quantifier.java`; lack of a `Times.java` file must not be interpreted as nonexistence. The LLM's `org.apache.flink.cep.pattern.Pattern` also exists and belongs to the actual static candidate set, so its gold mismatch is not H1/H2.

See [input_audit.json](input_audit.json) and [additional_validity_checks.txt](additional_validity_checks.txt). These concerns prevent an unqualified paper-level reproduction judgment. The conservative overall checkpoint status is **INCONCLUSIVE pending coordinator review**, while the bounded API execution and as-frozen calculations are complete.

## Static coding and checks

Candidates are direct declared field types of H plus actual parameter types of the named method; generic containers contribute their element types. Primitive/JDK types, type variables (which are not concrete classes), and H are excluded. Imported names or the same package determine FQNs. Zero-score candidates remain in the set. Scores count each member-access expression through a field, parameter or local of the candidate's own type once. Calling a container's member does not count as accessing its element type. Ties use ascending FQN.

JavaParser 3.26.2 extracted fields, parameters, locals, source line numbers and member-access expressions. The twelve target methods were inspected; their scored accesses require no inference of chained return types. Each returned target was checked in the exact frozen Git commit by path, package declaration and class/interface declaration. No API/network failure was coded as a hallucination.

Examples worth checking: ref_id 3 has two zero-score Mapper candidates, so alphabetical tie-breaking selects `CrmBusinessStatusMapper`; ref_id 16 accesses `KeFuMessageDO` twice versus the conversation service once; ref_id 21 accesses `Pattern` once. Per-case tables are `outputs/static/<ref_id>.csv`, with the detailed traces in adjacent `.audit.json` files.

## Evidence chain and coordinator checkpoint

Trace one reported result: case 1 contributes one LLM hit in `results.csv`. Its first response object names `CrmCustomerPoolConfigMapper` in `outputs/runs/20261020T172353_759166Z/case_0001/response.raw.json`. The adjacent request and execution record identify the model, timestamp, request hash, HTTP status and request ID. The prepared `outputs/requests/case_0001/` directory links that request to the source hash, frozen commit, host path and prompt-template hash. `outputs/h_check/1.txt` verifies the target exists, and `outputs/static/1.csv` shows its single scoped access at source line 42.

| Lab4 requirement | Evidence |
|---|---|
| Frozen M1 | Tag `M1_PLAN`; README amendments; `docs/Decisions.md`; `data/sample_ids.csv` |
| Executable route/environment | `scripts/run_frozen_lab.py`, `scripts/prepare_frozen_inputs.py`, `scripts/evaluate_lab4.py`, `scripts/InspectCases.java`; environment record |
| Genuine raw output | Twelve request/response/execution triplets under the run directory |
| Derived results | `outputs/static/`, `outputs/h_check/`, `outputs/lab4/results.csv` and `summary.json` |
| Deviations/issues | D-05 and the input/oracle audit; original M1 and all raw evidence retained |
| Current status | Execution complete; intended paper-level interpretation INCONCLUSIVE pending validity review |
| Held-out boundary | No Event/held-out material used; only released corpus and frozen selected source commits |

Before M2, show the coordinator the signature mismatches and ref_id 14 gold-package discrepancy. Agree whether the current as-frozen run is interpretable or a prospective, separately documented correction is needed. Retain this run under its existing ID. Any authorised correction must be recorded before a new run; do not silently replace these outputs. Do not claim that the common ranking interface has been justified; its M4 decision remains outstanding.

## Reproducing the calculations without spending API credits

From the repository root, with Python 3.9+:

```text
python scripts/evaluate_lab4.py --offline
python scripts/verify_lab4.py
```

Offline evaluation uses the committed AST traces, source/tree evidence and genuine raw responses. It validates source hashes and does not call OpenAI. To refresh source evidence, run `python scripts/cache_frozen_commits.py`, then `python scripts/evaluate_lab4.py` (requires Git and network). To regenerate ASTs, compile/run `scripts/InspectCases.java` with Java 17, JavaParser 3.26.2 and Gson 2.10.1; pass the repository root as its sole argument. Obtain dependencies into an ignored local cache, not into the evidence directories.

Running `scripts/run_frozen_lab.py` again creates a **new paid run**, not a reproduction of the saved calculation. It is not needed to inspect this report.

GenAI assisted with support scripts, input audit and this report. Reported counts come from the saved API responses, checked source declarations and deterministic evaluation; an assistant explanation is not treated as empirical evidence. Group review of the coding and coordinator interpretation is still required.
