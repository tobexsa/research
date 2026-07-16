# R21 Partial Failure Analysis Campaign

## 1. Objective

- Campaign ID: `semantic_fusion_r21_partial_failure_20260714`.
- Parent run: `semantic_fusion_gain_loss12_20260714_r21`.
- Claim under test: the first Fusion implementation can retain all five R20
  gains and recover all seven R12 losses through runtime-only lane selection.
- Required outcome: identify the smallest code-level causes of the observed
  gate failure before any R22 retry; do not authorize stratified45.

## 2. Boundary And Comparability

- Fixed: R12/R20 trajectories, the first eight durable R21 trajectories,
  evaluator, gate membership, corpus, and configuration.
- May vary: analysis code only.
- Non-comparable evidence: four R21 samples are missing because SiliconFlow
  began returning HTTP 403; no 8-row metric is a full gate metric.

## 3. Slice Plan

| Slice | Type | Question | Observable | Decision value |
| --- | --- | --- | --- | --- |
| S1 | error analysis | Why did `18th` regress despite generic routing? | state events and object identity | identify reducer defect |
| S2 | error analysis | Why did exact date regress to bare year? | answer/binding/evidence granularity | identify candidate-granularity defect |
| S3 | environment | Is the 403 methodological? | completed rows, retry position, endpoint exception | separate endpoint from method |

## 4. Assets

- R12, R20, and partial R21 trajectory JSONL files.
- Fixed gain/loss-12 dataset and MuSiQue corpus.
- Repository evaluator and state diagnostics.
- No new service call or dataset is required.

## 5. Execution And Reporting

- Run one automated analysis script over the fixed artifacts.
- Stable support: one repeated, code-local mechanism explains each failure.
- Contradiction: lane routing itself cannot distinguish the cases.
- Ambiguity: evidence is insufficient because of missing R21 rows or stochastic
  output and no code-local cause can be isolated.
- Output: JSON plus Markdown aggregate report, then an explicit R22/no-R22
  decision. Phase 2 stays blocked regardless of this campaign outcome.

## 6. Checklist

- `analysis/semantic_fusion_r21_failure_campaign_checklist_20260714.md`

## 7. Revision Log

| Time | Change | Reason |
| --- | --- | --- |
| 2026-07-14 | Campaign created after partial R21 | two hard-gate failures and repeated external 403 require separation |
