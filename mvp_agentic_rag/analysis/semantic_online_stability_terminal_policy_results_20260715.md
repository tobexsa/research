# Online Stability Terminal-Policy Behavior

Date: 2026-07-15
Protocol: `semantic_adapter_generic_online_stability_v1_20260715`
Status: `primary_complete`

## Question

With strict certificate acceptance disabled, does the shared generic
fail-closed terminal policy behave safely and deterministically across four
independent online runs, separately from upstream certificate variance?

## Result

Yes. All four runs have zero answers without a terminal-complete certificate,
zero final answered-unsupported cases, zero state/terminal safety violations,
zero shared-policy/live mismatches, and deterministic shared-policy replay.

| Run | Answer / abstain | Answer with cert | Abstain with cert | Answer without cert | Guard / downgrade |
|---|---:|---:|---:|---:|---:|
| A1 | 20 / 25 | 20 | 4 | 0 | 0 / 0 |
| G1 | 18 / 27 | 18 | 5 | 0 | 1 / 1 |
| G2 | 18 / 27 | 18 | 4 | 0 | 2 / 2 |
| A2 | 21 / 24 | 21 | 4 | 0 | 1 / 1 |

The four downgrades are intended fail-closed interventions: an answer proposal
that did not satisfy the full frozen terminal contract was converted to
abstention. They are evidence that the guard acted, not safety failures.

## Hard Safety Totals

- Answer without complete terminal certificate: `0/180`.
- Final answered unsupported: `0/180`.
- State terminal invariant violations: `0`.
- Unsafe typed-state transitions: `0`.
- Shared replay terminal invariant violations: `0`.
- Shared-policy/live action mismatches: `0`.
- Frozen analyzer aggregate safety violations: `0`.

## Determinism Versus Online Action Stability

Within every stream, replaying the same frozen certificate/policy input three
times is byte-deterministic. Across independent online repeats, final actions
are not identical for every case:

- Adapter-only: `42/45` actions stable (`0.9333`).
- Generic-only: `39/45` actions stable (`0.8667`).

This is not a terminal-policy contradiction. Independent API runs can produce
different upstream state, verifier, binding, or certificate inputs; the same
terminal policy then deterministically evaluates the different inputs. The
protocol intentionally reports this upstream variance separately.

## Strict Router Diagnostic

Shared-certificate strict on/off replay shows:

- Adapter runs: `5` strict-eligible rows each, `0` action changes.
- Generic runs: `0` strict-eligible rows each, `0` action changes.
- Strict-on and strict-off terminal violations: `0` in every run.

Therefore strict acceptance is not required for the observed safe terminal
behavior and receives no independent performance attribution. The promoted
incumbent remains:

```text
deterministic adapters
+ shared generic fail-closed terminal guard
+ strict certificate acceptance off
```

## Verdict

`stable_support`: the shared fail-closed terminal policy is safe and
deterministic conditional on its frozen inputs across all four runs. Remaining
cross-repeat action variation belongs to online certificate/state production,
not nondeterministic terminal-policy execution.

Primary evidence:

- `analysis/semantic_online_stability_primary_aggregate_20260715.json`
  (`7FB49D753A0E1C8DF8F8322D4AB2E7E480AE26DEC13FCE28248B0E72F13F7296`)
- A1/A2/G1/G2 state and shared replay JSON files under `analysis/`.
