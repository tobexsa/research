# Phase-3 Decision After Shared-Certificate Attribution

Date: 2026-07-15

## Decision Question

Does strict terminal routing have enough isolated evidence to remain a claimed
contributor alongside deterministic adapters?

## Verdict And Action

- Verdict: `good` for deterministic adapters and the shared terminal
  fail-closed guard; `bad` for a standalone strict terminal-acceptance benefit;
  `neutral` for an upstream strict-protocol interaction.
- Action: `iterate` with adapter-only plus shared fail-closed terminal safety as
  the incumbent. Downgrade strict terminal routing from the current component
  claim and keep it experimental until a nonzero, safe, shared-input action or
  upstream-protocol effect is demonstrated.

## Decisive Evidence

- R27 adapter-only improves Answer F1 and coverage over R26 generic-only by
  `+0.0667`, with final unsupported zero.
- R25 and R27 each have the same five strict-eligible frozen terminal samples.
- Strict on/off changes zero terminal actions on both streams and on R31.
- R26 and R28 have zero eligibility without adapters.
- All counterfactual accepted actions pass terminal safety invariants.

Evidence:

- `analysis/semantic_shared_certificate_attribution_results_20260715.md`
- `analysis/semantic_adapter_only_stratified45_results_20260715_r27.md`
- `analysis/semantic_strict_only_stratified45_results_20260715_r28.md`

## Claim Boundary

Supported claim:

> Deterministic adapters improve certificate completion relative to generic-only,
> while the shared terminal guard prevents uncertified final answers in the
> tested post-repair boundary.

Unsupported claim:

> Strict terminal acceptance independently produces the remaining full-Fusion
> gain.

The `R25 - R27 = +0.0444` difference is not assigned to strict routing because
the streams came from separate online calls and the matched terminal
counterfactual has zero action deltas.

## Next Direction

1. Freeze the incumbent as `adapter-only + shared terminal fail-closed` for the
   next comparison contract.
2. Do not delete strict code yet; retain its logs as an experimental boundary
   and require activation-aware reporting anywhere it is enabled.
3. Before any new paid run, predeclare an online stability protocol that
   separates certificate-completion variance from terminal-policy behavior.
4. Only a nonzero safe effect on shared inputs may restore strict routing to
   the component claim.
5. Independent repeats and matched modern baselines remain after that online
   stability contract; non-leaking dev/test and 300 cases remain later in the
   user-approved order.

## Rejected Alternatives

- Attribute R25-R27 directly to strict routing: rejected because the shared
  terminal treatment effect is zero and the online streams are independently
  sampled.
- Treat R28 as a zero-valued strict ablation: rejected because eligibility is
  zero, so no strict treatment was delivered.
- Relax the terminal guard to recover gold-matching uncertified answers:
  rejected because this would trade away the repaired R28 safety invariant.
- Start 45-case repeats immediately: rejected until the separate online
  stability contract is fixed; the old single-draw 12/12 gate was refuted.
- Jump to baselines, dev/test, or 300: rejected by the approved ordering.

## Reopen Criteria For Strict Routing

Strict routing may return to the incumbent only if a predeclared experiment
shows all of the following:

- nonzero strict eligibility;
- identical evidence/certificate inputs or a separately isolated upstream
  protocol intervention;
- nonzero beneficial action or metric delta;
- zero final unsupported and zero terminal invariant violations;
- reproducibility across independent runs rather than one favorable draw.
