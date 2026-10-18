# Step 1: MM-Assist real-world dataset - format record

- Accessed: 2026-10-05
- Repository: https://github.com/cuboulder-se-research/move-method-assist
- Repository HEAD: `8b0898fbcaf05b6b4596c2c54b3b156d412c77bb` (2026-01-30)
- Dataset file: `replication-package/artifacts/datasets.zip`
  - sha256: `8b2808944db28ba6620f07a71fce38224f32cc100a444bb89573f662e268c3eb`
  - Last changed in commit `131502c` (2025-07-30)
- Full version record: `docs/artefact_version.txt`.
- The datasets.zip download link on the landing page is the same file as the one in the repository.

## 1. Where the real-world dataset is

| Subset | Path (inside datasets.zip) | Format | Records |
|---|---|---|---|
| Instance methods (MM-Assist results + oracle) | `data/refminer_data/instance-methods/mm-assist-emm/<project>_res.json` | JSON array, one file per project, 11 files | 117 |
| Instance-method baselines | `instance-methods/feTruth/*.json`, `instance-methods/jmove/*.txt` | JSON / TSV | - |
| Instance-method ID map | `instance-methods/ref_id_map.json` | `{RefactoringMiner description: ref_id}` | 912 (raw mined refactorings, unfiltered) |
| Static methods | `static-methods/mm-assist/*.jsonl`, `static-methods/feTruth-*/` | JSONL / JSON+TSV | 83 (out of scope) |

Records per project: kafka 41, graal 17, ruoyi-vue-pro 11, elasticsearch 9, flink 8, spring-boot 8, dbeaver 5, ghidra 5, selenium 5, redisson 4, spring-framework 4.

## 2. Record structure (`mm-assist-emm/*_res.json`)

```
{
  "repository": "https://github.com/dbeaver/dbeaver.git",
  "sha1": "8c8725f1...",            # developer's real refactoring commit (post-refactoring state)
  "url": "...",
  "ref_id": 887,                    # unique integer ID, range 1-905
  "move_method_refactoring": {
    "type": "Extract And Move Method",        # all 117 records have this type
    "description": "Extract And Move Method public createSchemaImpl(...) : OracleSchema extracted from ... in class <HOST_FQN> & moved to class <TARGET_FQN>",
    "leftSideLocations":  [{filePath, startLine, endLine, codeElementType, description, codeElement}, ...],
    "rightSideLocations": [... {"description": "extracted method declaration", "codeElement": "<method signature>"} ...],
    "isStatic": false
  },
  "extraction_results": {
    "success": true,
    "newCommitHash": "67832724...",           # authors' reconstructed pre-move state
    "newBranchName": "extract-<m>-<src>-<parent7>"
  },
  "telemetry": {                              # MM-Assist run log (missing in 3 records)
    "hostFunctionTelemetryData": {"sourceCode": "<full host class source>", "filePath", "methodCount", ...},
    "candidatesTelemetryData", "iterationData", "methodCompatibilityScores",
    "llmMethodPriority", "targetClassMap"
  }
}
```

## 3. Identifier fields

| Needed | Source |
|---|---|
| Case ID | `ref_id` |
| Project name | last segment of `repository`, without `.git` |
| Commit | `extraction_results.newCommitHash` is the checkout point for this study; `sha1` is kept for provenance only |
| Host class | X in `in class X &` within `description` (FQN; inner classes written as `Outer.Inner`) |
| Host file path | `leftSideLocations[0].filePath` (relative to repository root) |
| Method name / signature | `codeElement` of the `rightSideLocations` entry whose `description == "extracted method declaration"` |
| Gold target class | Y in `moved to class Y` within `description` (FQN) |
| Instance / static | `move_method_refactoring.isStatic`; all 117 records in this subset are `false` |

All 117 records parse successfully with these regular expressions (0 failures).

## 4. Findings that affect later steps

1. **All cases are "Extract And Move Method", not plain Move Method.**
   - In the real commit, the developer extracted code and moved it in one step. The paper's authors started from the parent of the developer's commit, put the extracted method back into the host class, and committed that state as `newCommitHash`. This gives the pre-move state.
   - The checkout point is therefore `newCommitHash`, not `sha1`.
   - Verified for one redisson case: the reconstructed commit (author Abhiram98, message "match developer changes") can be fetched from GitHub with `git fetch origin <newCommitHash>` and contains the extracted method.
   - Rule (3) in D-03: `newCommitHash` is fetchable and the host file exists at that commit.
   - One elasticsearch `newCommitHash` tested on 2026-10-09 returned `not our ref`, i.e. some reconstructed commits are no longer available. Such cases fail rule (3) and are skipped and logged.
2. **3 records have `extraction_results.success = false` and no telemetry.**
   - D-03 lists reconstruction success as an explicit eligibility condition.
   - After rules (1) and (2), 114 records are eligible.
3. **One record stores `success` as the string `"true"`.** The selection script normalises this.
4. **`ref_id` is unique.**
   - The ordering "case ID, then file path, then chronological ID" is therefore decided by `ref_id` alone; the later keys never apply.
   - The dataset has no commit dates; these would have to come from git.
5. **At least 2 records have a host class that is an inner class of the target** (e.g. `OracleDataSource.SchemaCache` -> `OracleDataSource`).
   - The outer class is neither a field type nor a parameter type, so under the coding manual it would be coded as H2 or NONE.
   - Not encountered in the 12-case sample.
6. **`telemetry.hostFunctionTelemetryData.sourceCode` contains the full host class source.**
   - Useful to cross-check the checked-out file.
   - Prompt input is always read from the checkout.

## 5. Selection script

`scripts/select_sample.py`:

- **Dry run:** applies rules (1) and (2) only and writes nothing.
- **With `--check-source`:** applies rule (3) case by case, skips failures and takes the next case, and writes `data/sample_ids.csv` and `data/screening_log.csv`.
- Run with `--check-source` only after D-03 is committed.
