# Event A model replacement before valid execution

Date: 2026-10-27. Selected by the group in chat: gpt-6-luna.

## Reason and preserved evidence

The first Event A request, ref_id 66, returned HTTP 404 model_not_found: gpt-4o-2024-05-13 has been deprecated. The original attempt is preserved at outputs/event_a/runs/20261027T134156_153205Z/case_0066/. It yielded no valid empirical observation and is not scored as a hallucination or a miss. The original six prepared requests and all screening evidence remain unchanged under outputs/event_a/.

OpenAI's deprecations page lists shutdown on 2026-10-23. This is after M2 on 2026-10-20 and before Event A on 2026-10-27. M2's saved raw response records gpt-4o-2024-05-13 and HTTP 200; it remains the primary historical result.

Sources:
- https://developers.openai.com/api/docs/deprecations
- https://developers.openai.com/api/docs/models/gpt-6-luna
- https://developers.openai.com/api/docs/guides/latest-model

## Replacement protocol

- Model: gpt-6-luna (the exact user-selected ID; record the returned model in every response).
- Endpoint: https://api.openai.com/v1/chat/completions, unchanged.
- temperature: 0, unchanged.
- reasoning_effort: none, explicitly set so that temperature remains supported and the migration does not silently adopt the new model's default reasoning effort.
- All six source files, prompt messages, dataset method signatures, sample IDs, static candidate/scoring rules, gold labels, metrics and challenge thresholds are unchanged. No Event A valid answer was examined before this replacement.
- New requests and runs use outputs/event_a_gpt6_luna/; old evidence is not overwritten.
- Retain the first valid response for each case; no outcome-based reruns, substitutions or prompt tuning.
- The pilot review checks request integrity and transport/parsing, not correctness. It is retained in the six cases.
- The numerical predictions already recorded in the Tracker are retained, rather than revised after observing a result. Add the replacement disclosure to the Tracker before the replacement run.

## Comparability and registration status

This is a documented model deviation from M2. Differences from M2 can reflect both the held-out project and model change, so they cannot be attributed solely to transfer across projects. The newer model's knowledge cutoff and possible exposure to released source are additional limitations. This is a continuation with a registered replacement, not a successful run of the original exact-model protocol.

D-04 asks for coordinator confirmation of a replacement model. The group has selected the replacement in chat; coordinator confirmation has not been evidenced to the assistant. The group manages that course requirement and all Git commits/pushes. No confirmation, commit or push is claimed here.

## Tracker addendum to enter before execution

Model update before valid Event A execution: gpt-4o-2024-05-13 was shut down on 23 October 2026; the first Event A attempt returned HTTP 404 and produced no scored observation. We will use gpt-6-luna with reasoning_effort=none and temperature=0. The six cases, exact prompt messages, static/hybrid rules, predictions and thresholds remain unchanged. Original failed evidence is preserved; replacement evidence will be under outputs/event_a_gpt6_luna/. Model change is a confound in the comparison with M2.

## IntelliJ setting

The new option is openai-gpt-6-luna in the existing LLM settings dropdown. It maps to gpt-6-luna and uses reasoning_effort=none. The plugin's existing temperature setting is passed through. An adapter is needed because the bundled langchain4j-open-ai 0.33.0 SDK predates reasoning_effort. Other model routes are unchanged. This IDE setting does not control the independent Python Event A runner.

Build: Codex-MM-Assist/build-gpt6-luna.py. Package version: 0.2.2-openai-gpt6luna.1. Built against IntelliJ IDEA 2024.1.7, Java 17. No dependencies upgraded. Install the ZIP via Settings > Plugins > gear > Install Plugin from Disk, then restart IntelliJ. The currently installed plugin is not automatically replaced.

Offline validation: compiled plugin and verified archive contents; adapter checks cover model/temperature/reasoning, message preservation, usage parsing, and rejection of truncated or wrong-model responses. All six migrated requests were compared with their original counterparts; their messages and source bytes are identical. No GPT-6 Luna API request has been sent by this migration.