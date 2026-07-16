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
- [x] Replace the invalid raw 2x2 causal reading with shared-certificate
  activation-aware attribution and verify it on all relevant streams.

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
- [x] Implement general terminal fail-closed and dependency-closure guards.
- [x] Add terminal replay invariants and deterministic regression tests.
- [x] Pass offending-case probe and repaired deterministic/online safety gates.
- [x] Complete activation-aware shared-certificate component attribution.

## Independent Repeated Runs

- [x] Freeze fresh adapter-only incumbent and generic-only repeat configs after
  attribution.
- [x] Record why these are independent repeats rather than seeded repeats.
- [x] Produce exactly two fresh observations per variant under the later frozen
  no-extra-draw protocol; historical R25/R26 are non-primary.
- [x] Report mean, sample standard deviation, range, paired deltas, and
  per-example stability.
- [x] Confirm unsupported=0 and safety replay for every repeat.

## Matched Modern Baselines

- [x] Read and freeze benchmark/split/preprocessing/evaluator/metric contract.
- [x] Inventory local and paper-linked candidate baselines before downloading.
- [x] Select a primary comparator and label infrastructure comparators.
- [x] Store the route under `baselines/local/`.
- [x] Run a bounded deterministic smoke before reproduction.
- [x] Verify completion, source identity, metrics, deviations, feasibility, and
  downstream trust class.
- [x] Reject direct comparison to published numbers from unmatched protocols.
- [x] Publish a self-contained matched-baseline verification report locally.

## Aggregation And Closeout

- [x] Classify as stable support with narrowed strict-router attribution.
- [x] Summarize highest-impact findings first without hiding null results.
- [x] Write the phase-3 campaign report and explicit next-route decision.
- [x] Authorize non-leaking standard MuSiQue dev/test only after all phase-3
  gates; phase 4 is next and not yet executed.
- [x] Keep 300-sample and paper experiments deferred until the final phase.
