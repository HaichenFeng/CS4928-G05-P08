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

## D-04

### LLM configuration and prompt adaptation

Planned model: gpt-4o-2024-05-13.
Temperature: 0.

As stated in M1, adapt the paper's vanilla prompt to request only the target class. This narrows the task to target-class recommendation and may limit comparison with the paper's original hallucination categories.

The exact prompt has not yet been finalised. Save and freeze its full text before LLM execution, without including the gold answer or authors' existing recommendations.

No substitute model has been selected. If the planned model is unavailable, record the replacement, reason and likely impact before running, and confirm the change with the coordinator.

No LLM calls have been executed for this reproduction.
