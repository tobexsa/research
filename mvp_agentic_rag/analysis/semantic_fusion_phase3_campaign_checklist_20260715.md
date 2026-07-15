# Semantic Fusion Phase-3 Campaign Checklist

## Identity And Launch

- Campaign id: `semantic_fusion_phase3_20260715`.
- Parent runs: R25 Fusion and R26 generic-only.
- [x] Claim and fixed user order are explicit.
- [x] Phase-3 `PLAN.md` and `CHECKLIST.md` surfaces exist.
- [x] Slices are prioritized by decision value.
- [x] R25/R26 outputs and comparison are complete.

## Component Ablations

- [x] Define the full 2x2 factor matrix.
- [x] Create R27 adapter-only config (`strict=off`, `adapters=on`).
- [x] Create R28 strict-only config (`strict=on`, `adapters=off`).
- [x] Prove both configs preserve every other R25 setting.
- [x] Record config and dataset hashes.
- [x] Run focused and full tests plus compileall.
- [x] Run R27 serially to 45 unique rows.
- [x] Audit R27 metrics, markers, state replay, and unsupported=0.
- [x] Run R28 serially only after R27 passes audit.
- [x] Audit R28 metrics, markers, state replay, and unsupported=0: rejected;
  unsupported was `0.0500` and strict-lane activation was zero.
- [ ] Write and verify the aggregate 2x2 comparison.

Frozen evidence:

- R27 config:
  `14F20854C5F4C89E27CAAF8D044BD1307AB80BE15C3E1E8E1B33BAA5CE192D95`.
- R28 config:
  `2B00BD5963951D6519A9ACD788013ACBE12A5AB4268DD63F8D448610A45D5959`.
- Dataset:
  `2B4A0DFAD40AC8B120FF59862FCBF216C5AD419EC7E2783E35534281653D63A5`.
- Focused tests: 276 passed and 27 subtests passed.
- Full tests: 640 passed and 27 subtests passed with a project-local
  `--basetemp`; compileall and config assertions passed.
- R27 result:
  `analysis/semantic_adapter_only_stratified45_results_20260715_r27.md`.
- R27 completed at EM/F1 `0.4444`, coverage `0.4667`, final unsupported 0,
  strict-lane steps 0, recognized adapter marker applications 20, and unsafe
  replay transitions 0.
- R28 result:
  `analysis/semantic_strict_only_stratified45_results_20260715_r28.md`.
- R28 completed 45 unique rows but is rejected: EM `0.3778`, Answer F1
  `0.3889`, coverage `0.4444`, final unsupported `0.0500`, strict-lane steps
  0, adapter markers 0, and structural replay unsafe transitions 0.
- Hard stop active: do not start repeats or baselines until the generic
  terminal unsupported-answer failure and zero strict activation are resolved.
- [x] Record post-R28 route decision:
  `analysis/semantic_fusion_phase3_r28_next_decision_20260715.md`.
- [ ] Implement general terminal fail-closed and dependency-closure guards.
- [ ] Add terminal replay invariants and deterministic regression tests.
- [ ] Pass offending-case probe and repaired 12-case gate.
- [ ] Complete activation-aware shared-certificate component attribution.

## Independent Repeated Runs

- [ ] Freeze fresh Fusion and generic-only repeat configs after ablations.
- [ ] Record why these are independent repeats rather than seeded repeats.
- [ ] Produce at least three total observations per main variant when feasible.
- [ ] Report mean, sample standard deviation, range, paired deltas, and
  per-example stability.
- [ ] Confirm unsupported=0 and safety replay for every repeat.

## Matched Modern Baselines

- [ ] Read and freeze benchmark/split/preprocessing/evaluator/metric contract.
- [ ] Inventory local or attachable candidate baselines before downloading.
- [ ] Select a primary comparator and label fallback/infrastructure comparators.
- [ ] Store each route under `baselines/local/` or `baselines/imported/`.
- [ ] Run a bounded smoke before each substantial reproduction.
- [ ] Verify completion, source identity, metrics, deviations, feasibility, and
  downstream trust class.
- [ ] Reject direct comparison to published numbers from unmatched protocols.
- [ ] Publish a self-contained matched-baseline verification report.

## Aggregation And Closeout

- [ ] Classify stable support, contradiction, or unresolved ambiguity.
- [ ] Summarize highest-impact findings first without hiding null results.
- [ ] Write the phase-3 campaign report and explicit next-route decision.
- [ ] Enter non-leaking standard MuSiQue dev/test only after all phase-3 gates.
- [ ] Keep 300-sample and paper experiments deferred until the final phase.
