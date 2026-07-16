# Semantic Fusion Experiment Checklist

## Identity

- Active run ID: `semantic_fusion_gain_loss12_20260714_r23`
- Lineage: R21 partial -> R22 complete gate failure -> R23 bounded repair
- Idea: strict-certificate / generic-compatibility fusion
- Stage: phase 1 of 5, fixed 12-case gate

## Planning

- [x] Selected idea summarized and user sequence frozen.
- [x] R12/R20 baseline and comparability contract confirmed.
- [x] Five gains and seven losses recomputed from original trajectories.
- [x] Source dataset and comparator config hashes recorded.
- [x] Code touchpoints, smoke, main run, and fallbacks written.
- [x] Materialize the immutable 12-row dataset without overwriting an existing file.
- [x] Verify row count, unique IDs, hop distribution, source-row equality, and hash.

## Implementation

- [x] Add a pure runtime-only fusion-lane classifier.
- [x] Add strict, generic, and no-fallback unit tests.
- [x] Integrate lane-aware repair and terminal enforcement.
- [x] Log lane, reason, and decisive runtime signals on every trajectory step.
- [x] Prove routing does not inspect sample ID, gold answer, decomposition, or support labels.
- [x] Add stored-trajectory replay/audit tooling.
- [x] Avoid unrelated code changes.

## Pilot / Smoke

- [x] Run focused controller/state/agent tests: 214 passed, 25 subtests.
- [x] Run deterministic replay over all 12 cases.
- [x] Verify strict gains, generic losses, and no-fallback safety expectations.
- [x] Run the full test suite, compileall, and scoped diff check: 617 passed,
  27 subtests; compileall and diff check clean.
- [x] Freeze a unique real-run config only after deterministic gates pass.

## Main Run

- [x] Launch the real 12-case Qwen3-14B gate (R22 completed after R21 partial).
- [x] Monitor durable logs and completed row count.
- [x] Validate 12 unique rows and complete finite metrics.
- [x] Retain 5/5 gains.
- [x] Recover 7/7 losses (R24).
- [x] Keep final unsupported and unsafe transitions at zero.

Blocked launch record (2026-07-14): the sandboxed attempt failed before row 1
with Windows socket permission error. The required network escalation was then
rejected because the run would send MuSiQue questions and retrieved passage
text to the external SiliconFlow API without a fresh explicit data-transfer
approval. The output contains an empty `trajectories.jsonl`, no metrics, and no
lock. Do not interpret this as a methodological failure or advance to phase 2.

R21 partial result after explicit approval: 8/12 rows completed before the
endpoint returned HTTP 403; an identical resume added zero rows and repeated
the 403. R21 retained 4/5 gains and recovered 2/3 completed losses, so the hard
gate failed independently of the endpoint. Failure analysis isolated a false
ordinal surface conflict and a unique-local-date granularity collapse. R22
contains only those two generic invariant repairs and must rerun all 12 rows
under a new output identity.

R22 completed 12/12 with accuracy/F1 `0.6667/0.7500`, five of five gains,
three of seven losses, and final unsupported zero. It fails phase 1. R23 is
limited to binding-to-answer surface handoff plus two candidate/hop conflict-
scope corrections documented in the R22 result report.

R23 deterministic preflight (2026-07-14): focused agent/state/controller
tests pass (`226 passed, 25 subtests`); full suite passes (`632 passed, 27
subtests`); compileall and scoped whitespace checks are clean. Replaying all
12 R22 trajectories produces zero unsafe failure-candidate transitions. Both
Francisco cases have zero canonical conflict after replay; the incomplete case
retains the East Timor president repair target and the later correct Francisco
binding may replace prior support-incomplete state. Frozen R23 config SHA-256:
`56B55143AF28532C75CE685E85A9BB472CB36DEFF11CD81136AB07BCD1533F91`.

R23 completed 12/12 but failed the gate: 5/5 gains, 2/7 losses, final
unsupported zero. The durable result and five failure causes are recorded in
`analysis/semantic_fusion_gain_loss12_results_20260714_r23.md`. R24 is bounded
to post-slot structured handoff stabilization and natural single-hop repair
query rendering; phase 2 remains blocked.

R24 preflight (2026-07-14): focused tests pass (`232 passed, 25 subtests`),
full tests pass (`638 passed, 27 subtests`), and compileall plus scoped diff
checks are clean. R24 differs from R23 only in run/output identity. Frozen
config SHA-256:
`C675691E5016F78508381C9C5806A214DE0DAABAAF6B619A90AF063A89CD8E17`.

R24 completed and passes phase 1: 12/12 normalized-correct, 5/5 gains,
7/7 losses, final unsupported zero, unsafe replay transitions zero. Result:
`analysis/semantic_fusion_gain_loss12_results_20260714_r24.md`.

## Phase 2: Fusion / Generic-Only Stratified45

- [x] Enter only if every phase-1 hard gate passes (authorized by R24).
- [ ] Freeze Fusion stratified45 config.
- [ ] Freeze generic-only stratified45 config with specialized adapters disabled.
- [ ] Run sequentially and compare with R12/R20.

## Phase 3: Evidence Strengthening

- [ ] Run component ladder ablations.
- [ ] Run repeated seeds/replays with uncertainty.
- [ ] Implement or faithfully approximate matched modern baselines.

## Phase 4: Non-Leaking Standard Evaluation

- [ ] Freeze a no-gold runtime data contract.
- [ ] Establish standard MuSiQue dev selection and untouched test evaluation.
- [ ] Audit leakage mechanically before reporting results.

## Phase 5: Scale / Paper Gate

- [ ] Consider 300 samples only after phases 1-4 pass.
- [ ] Consider a paper-facing main experiment only with matched baselines,
  uncertainty, generic-only evidence, and a non-leaking evaluation contract.

## Closeout

- [ ] Record the phase-1 result as supported, refuted, or inconclusive.
- [ ] State the exact next action without skipping a gate.
