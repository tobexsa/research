# Claim Risk v1.3.5 Answer Safety Guard Runtime Checklist

## Preflight

- [x] Confirm current branch is `main`.
- [x] Confirm answer safety guard commit is present: `34a2d69`.
- [x] Confirm v1.3.4 baseline metrics are available.
- [x] Confirm dataset, corpus, index, and embedding model paths exist.
- [x] Confirm `.env` contains `SILICONFLOW_API_KEY`.
- [x] Run full test suite before launch.
- [x] Confirm v1.3.5 run directory does not contain prior trajectories.

## Runtime

- [x] Launch v1.3.5 full stratified45 runtime.
- [x] Preserve stdout/stderr logs.
- [x] Monitor progress at 15 completed samples.
- [x] Monitor progress at 30 completed samples.
- [x] Monitor progress at 45 completed samples.
- [x] Confirm `trajectories.jsonl`, `metrics.json`, and `run_summary.md` are produced.

## Export And Evaluation

- [x] Export v1.3.5 predictions from trajectories.
- [x] Confirm export coverage: `prediction_count=120`, `unmatched_count=0`.
- [x] Evaluate predictions against `test_v4_strict.jsonl`.
- [x] Confirm `prediction_schema_issue_count=0`.
- [x] Generate or update error attribution.
- [x] Generate or update repair miss analysis.

## Decision

- [x] Compare unsafe answer rate against v1.3.4 runtime and offline replay.
- [x] Compare oracle action accuracy, macro F1, repair recall, missed repair rate, and over-abstain rate.
- [x] Identify whether remaining unsafe answers are true final-answer bugs or diagnostic-state drift.
- [x] Decide next engineering route.
