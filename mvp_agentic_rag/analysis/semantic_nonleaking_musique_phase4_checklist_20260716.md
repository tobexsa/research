# Phase-4 Non-Leaking MuSiQue Checklist

## Source Audit

- [x] Official train/dev/test files located.
- [x] Row counts, schema, hashes, and split ID overlap audited.
- [x] Official test confirmed unlabeled.
- [x] Existing runtime gold/support data flow audited.

## Implementation

- [x] Build opaque runtime samples, label sidecars, submission maps, and corpus.
- [x] Add candidate-scoped non-oracle retriever.
- [x] Add novelty-based non-leaking EvidenceLedger mode.
- [x] Keep verifier-cited evidence separate from gold support.
- [x] Add blind trajectories plus offline dev label join.
- [x] Add test predictions-only path.

## Deterministic Gates

- [x] Unit tests prove runtime sample/corpus field allowlists.
- [x] Unit tests prove official/source IDs cannot reach trajectories.
- [x] Unit tests prove support labels do not affect retrieval gain.
- [x] Unit tests prove label join is exact and evaluator-only.
- [x] Unit tests prove unlabeled test cannot emit EM/F1.
- [x] Focused and full regression tests pass: 35 focused; 659 full plus 27
  subtests; compileall pass.

## Data Freeze And Runs

- [x] Build and hash complete standard dev/test runtime assets.
- [x] Run bounded deterministic runner/evaluator integration smoke.
- [x] Freeze real dev pilot config and budget.
- [x] Run and audit dev pilot: both 12/12 complete, leakage-valid, and terminal-safe.
- [x] Decide full standard dev execution without reading test labels: do not
  start while adapter activation remains 0/12; route choice is pending.
- [ ] Generate blind official-test predictions only after dev freeze.

## Route

- [x] Publish pilot metrics and leakage status, explicitly not as standard dev
  metrics.
- [ ] Publish complete 2,417-case dev metrics and blind test submission status.
- [x] Keep 300-sample and paper main experiments blocked until phase 4 closes.

## Post-Pilot Gate

- [x] Record adapter marker activation: `0/12`.
- [x] Record strict-certificate eligibility: `0/12` in both flows.
- [x] Record paired terminal choice: identical answer/abstain choice on 12/12.
- [x] Record projected two-flow full-dev runtime: approximately 140-190 hours.
- [x] Keep full dev unlaunched because the mechanism-identifiability gate did
  not pass.
- [ ] User selects one route: activation failure analysis/new pilot,
  non-leaking dev45 activation probe, or full dev now.
