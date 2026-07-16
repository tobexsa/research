# Post-R31 Fixed-12 Decision

Date: 2026-07-15

## Decision Question

Can the old requirement “one online fixed-12 execution must score 12/12” remain
the prerequisite for activation-aware attribution after R30 and the single
authorized R31 retry?

## Verdict And Action

- Verdict: `bad` for the old single-execution 12/12 gate; `good` for the
  repaired terminal-safety boundary tested by R29-R31; `neutral` for the wider
  Fusion mechanism claim.
- Action: `iterate` by replacing the online single-draw oracle with a
  deterministic frozen-certificate regression gate, then perform the already
  planned activation-aware shared-certificate attribution.
- Stop condition now active: no more identity-only paid retries.

## Decisive Evidence

- R30 and R31 are identity-matched and both score 10/12 with final unsupported
  zero.
- Their failure sets differ: `18th` recovers while `Maria Bello` regresses.
- `Oriole Records` fails twice through different mechanisms.
- R31 replay has zero terminal invariant violations and zero unsafe structural
  transitions.
- R31 has 8 strict steps, so the failure is not caused by an empty strict
  treatment cell.

Evidence:

- `analysis/semantic_terminal_safety_gain_loss12_results_20260715_r31.md`
- `analysis/semantic_terminal_safety_r31_state_replay_20260715.json`
- `analysis/semantic_terminal_safety_r31_failure_campaign_results_20260715.md`

## Selected Next Direction

Objective: make the fixed-12 prerequisite deterministic and mechanism-aware
without weakening the terminal safety contract.

Key steps:

1. Freeze gold-free terminal/controller inputs from existing valid and invalid
   trajectories. Expected outcomes may live in the test/evaluation layer but
   must never enter routing logic.
2. Build a deterministic regression gate that repeatedly replays identical
   certificate streams through terminal authorization and asserts identical
   actions, local-evidence enforcement, ancestor closure, and zero violations.
3. Include positive complete/local certificate controls and negative R28-style
   abstain/unclear/non-local controls.
4. On the same frozen adapter-on certificate stream, replay strict acceptance
   enabled and disabled. Report eligibility, actual action changes, and safety
   deltas instead of treating a configured switch as delivered treatment.
5. Only after the deterministic gate is clean, predeclare a separate online
   stability protocol. It must report distributions and per-case stability;
   it may not redefine success after observing favorable draws.

Success criteria:

- byte-identical input streams yield identical replay results across repeated
  executions;
- every accepted answer has a complete, conflict-free, local certificate;
- every unsafe R28-style state abstains;
- strict-router attribution uses nonzero eligible cases and identical
  certificate inputs for the on/off comparison;
- no gold/sample-specific branch appears in runtime code.

Abandonment/narrowing criteria:

- strict routing changes no action on any eligible shared certificate;
- its only changes are safety regressions;
- adapter-only explains the stable benefit and strict adds no reproducible
  value.

In that case, retain adapters as the incumbent and narrow or remove the strict
router claim.

## Rejected Alternatives

- Launch R32: rejected because it would optimize for a favorable stochastic
  draw and violate the frozen retry stop condition.
- Relax non-local evidence blocking: rejected because it would reopen the
  exact terminal safety class repaired after R28.
- Declare Phase C passed from final unsupported alone: rejected because the
  fixed-12 performance boundary is still unresolved.
- Start online repeats, modern baselines, non-leaking dev/test, or 300 cases:
  rejected because the deterministic mechanism gate is not yet complete.

## Stage Boundary

The next stage remains Phase D-style offline activation-aware attribution and
deterministic gate construction. The user-approved global order remains
unchanged; no larger-sample or paper experiment is authorized.
