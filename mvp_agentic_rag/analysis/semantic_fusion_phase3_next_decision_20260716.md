# Post-Phase-3 Route Decision

Date: 2026-07-16
Decision: `go_to_non_leaking_standard_musique_evaluation`

## Evidence

- Four-run online stability protocol decision:
  `pass_to_matched_modern_baselines`.
- Adapter-minus-generic correct-certificate delta is positive in both blocks:
  `+0.0889`, `+0.0889`.
- Adapter-minus-generic Answer F1 delta is positive in both blocks:
  `+0.0714`, `+0.0829`.
- Aggregate F1/coverage deltas: `+0.0772 / +0.0556`.
- Four-run answer-without-certificate and safety totals: `0 / 0`.
- Matched primary comparator F1/coverage: `0.1511 / 0.2667` versus incumbent
  mean `0.4285 / 0.4556`.

## Decision Boundary

Proceed to phase 4 only. Phase 4 must:

1. identify the canonical MuSiQue source and standard split files;
2. freeze development selection before any test evaluation;
3. construct runtime records without gold answer, decomposition, support
   labels, or sample-specific routing fields;
4. make gold available only to the offline evaluator after trajectories are
   immutable;
5. audit train/dev/test ID and context overlap and config source paths;
6. keep the promoted strict-off adapter incumbent and generic comparator fixed.

Do not authorize 300 samples or paper main experiments until the non-leaking
standard dev/test contract is frozen and produces a valid result.
