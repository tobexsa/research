# R31 Fixed-12 Failure Analysis Campaign Results

Date: 2026-07-15

## Campaign Outcome

Outcome: stable safety support plus a contradiction of the old online gate
form. R31 confirms that the terminal repair fails closed, but R30/R31 jointly
show that single-run 12/12 is too sensitive to remote verifier/candidate
variation to serve as a deterministic code-regression prerequisite.

## Slice Results

### 1. Integrity and replay — stable support

- 12 rows and 12 unique IDs.
- Final answered unsupported: zero.
- Terminal invariant violations: zero.
- Unsafe typed-state transitions: zero.
- Evidence files are present and hashable.

### 2. R30/R31 identity-only comparison — contradiction

- R30: 10/12, failures `18th` and `Oriole Records`.
- R31: 10/12, failures `Maria Bello` and `Oriole Records`.
- One R30 failure recovered and one previously correct case failed without any
  method/configuration change.
- Oriole failed both times through different causal paths.

This is direct evidence of online stochastic instability, not a reason to
continue retrying until a favorable 12/12 draw appears.

### 3. R31 abstention paths — mixed mechanisms

- `Maria Bello`: adapter binding complete, but the raw verifier switched to an
  unsupported `Salma Hayek` claim and the original controller abstained.
- `Oriole Records`: binding complete and answer surface correct, but the final
  verifier cited unretrieved passage IDs; the terminal guard correctly
  downgraded answer to abstain under the frozen evidence-locality rule.

## Stable, Fragile, And Unresolved Findings

Stable:

- The repaired system avoids final unsupported answers in R29-R31.
- Replay sees no terminal/state invariant violation in R30 or R31.
- Both strict and generic routing activate in the repaired full configuration.

Fragile:

- Raw verifier sufficiency and candidate identity vary across identical online
  executions.
- A correct surface answer can lack a valid local citation certificate.
- Per-sample answer/abstain outcomes are not reproducible enough for a single
  12/12 online run to act as a code oracle.

Unresolved:

- The online probability of certificate completion cannot be estimated
  responsibly from two post-repair runs.
- Whether strict routing adds value on identical certificate streams still
  requires the planned activation-aware counterfactual attribution.

## Claim Update

- Terminal-safety claim: strengthened within the tested targeted boundary.
- Per-run fixed-12 performance-stability claim: refuted.
- Overall Fusion mechanism claim: narrowed; routing contribution must be
  measured on a shared frozen certificate stream before further online runs.

## Recommended Route

Close the paid retry loop. Replace the old single-run oracle with two explicitly
separate contracts:

1. a deterministic frozen-certificate regression gate for code/safety and
   strict-router attribution;
2. a predeclared multi-run online stability contract, to be estimated only
   after the deterministic gate is complete and before any larger experiment.

Do not relax evidence locality, launch R32, start repeats/baselines, or move to
300 cases.
