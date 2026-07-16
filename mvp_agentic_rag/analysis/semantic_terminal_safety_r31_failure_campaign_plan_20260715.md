# R31 Fixed-12 Failure Analysis Campaign Plan

Date: 2026-07-15

## 1. Objective

- Campaign id: `semantic_terminal_safety_r31_failure_analysis_20260715`.
- Parent run: R31 fixed-12 identity-only retry.
- Main claim under test: whether the repaired online fixed-12 gate is stable
  enough to remain a per-execution 12/12 prerequisite, and whether R31's two
  abstentions are safety-repair regressions or upstream certificate/verifier
  instability.
- User requirement: solve the R28 terminal-safety problem without skipping the
  fixed-12 gate or moving to 300 samples.
- Required outcome: a no-more-paid-retries decision backed by per-case,
  cross-run, routing, certificate, and replay evidence.
- This is not writing-facing; no paper outline or experiment matrix applies.

## 2. Boundary And Comparability

- References: R24 pre-repair 12/12, R30 post-repair 10/12, and R31
  identity-only post-repair 10/12.
- Fixed conditions for R30 versus R31: code, data, model, retriever, budgets,
  prompts, evaluator, and metrics; only run identity/output path differ.
- No new API calls, code changes, evaluator changes, or dataset changes are
  allowed in this campaign.
- Historical R24 is a pre-repair reference and therefore supports per-case
  diagnosis, not a same-code stochastic repeat estimate.

## 3. Slice Plan

| Slice id | Class | Type | Question | Observable | Priority |
|---|---|---|---|---|---:|
| `r31_integrity_replay` | claim-carrying | error analysis | Is R31 complete and safe? | rows, unique IDs, final unsupported, terminal/state invariants, hashes | 1 |
| `r30_r31_failure_shift` | claim-carrying | robustness/error analysis | Does an identity-only retry reproduce the same successes and failures? | paired case actions and failure-set overlap | 2 |
| `r31_abstention_path` | auxiliary | case study | Which layer caused each R31 abstention? | verifier, binding, controller original action, terminal downgrade reasons, evidence locality | 3 |

All slices are offline and use existing trajectories only.

## 4. Assets And Dependencies

- R24, R30, and R31 trajectories and metrics.
- R30 result report and frozen R31 run contract.
- `scripts/replay_typed_hop_state.py` and the repaired terminal invariant audit.
- No external service or new baseline is required.
- The runtime lacks artifact/memory and managed `bash_exec`; repository-local
  reports and replay JSON are the explicit fallback.

## 5. Execution Strategy

- Run the replay/integrity slice first.
- Compare R30/R31 failure sets without altering evaluation logic.
- Inspect only the two R31 failure trajectories and their R24/R30 counterparts.
- Stop once the evidence distinguishes upstream abstention, guard downgrade,
  and unsafe answer behavior.

## 6. Reporting And Decision Contract

- Stable support: both post-repair runs have zero final unsupported and zero
  replay violations.
- Contradiction to the old gate: R31 remains below 12/12 despite an identity-only
  retry, or the failed IDs/actions change between R30 and R31.
- Safety regression: a locally supported, complete, verifier-sufficient answer
  is downgraded without a frozen block reason.
- Expected closeout: either retain per-run 12/12, or replace it with a
  deterministic certificate-stream regression gate plus a separately named
  online stability contract. No outcome authorizes 300 cases.

## 7. Checklist

- `analysis/semantic_terminal_safety_r31_failure_campaign_checklist_20260715.md`

## 8. Revision Log

| Date | Change | Reason | Impact |
|---|---|---|---|
| 2026-07-15 | Initial offline campaign charter | R31 completed at 10/12 after the one authorized retry | Paid retry loop is closed; diagnosis only |
