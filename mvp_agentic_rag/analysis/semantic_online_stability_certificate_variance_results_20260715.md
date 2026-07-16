# Online Stability Certificate-Completion Variance

Date: 2026-07-15
Protocol: `semantic_adapter_generic_online_stability_v1_20260715`
Status: `primary_complete`

## Question

Holding the dataset, model, retrieval, evaluator, strict-off terminal policy,
and run order fixed, do deterministic adapters create a repeat-stable increase
in correct terminal certificates relative to generic-only processing?

## Result

Yes on the frozen two-block criterion. Terminal-correct-certificate rate is
higher for adapter-only in both independent paired blocks by exactly `+0.0889`
(`+4/45`) each time.

| Block | Adapter | Generic | Adapter - Generic |
|---|---:|---:|---:|
| A1 vs G1 | 20/45 (0.4444) | 16/45 (0.3556) | +4/45 (+0.0889) |
| A2 vs G2 | 21/45 (0.4667) | 17/45 (0.3778) | +4/45 (+0.0889) |

Across the two repeats:

| Measure | Adapter-only mean ± sample SD | Generic-only mean ± sample SD | Mean delta |
|---|---:|---:|---:|
| Terminal-complete certificate rate | 0.5444 ± 0.0157 | 0.5000 ± 0.0157 | +0.0444 |
| Terminal-correct certificate rate | 0.4556 ± 0.0157 | 0.3667 ± 0.0157 | +0.0889 |
| Answer F1 | 0.4285 ± 0.0162 | 0.3514 ± 0.0081 | +0.0772 |
| Coverage | 0.4556 ± 0.0157 | 0.4000 ± 0.0000 | +0.0556 |

The predeclared primary mechanism measure is terminal-correct certificates,
not raw completion. Raw terminal completion also increases on average, but its
paired magnitude varies (`+1/45` in block 1 and `+3/45` in block 2). Correct
certificate gain is the repeat-stable result.

## Per-Case Completion Stability

Terminal-complete certificate frequency across each variant's two repeats:

| Frequency | Adapter-only cases | Generic-only cases |
|---|---:|---:|
| 0/2 repeats | 20 | 21 |
| 1/2 repeats | 1 | 3 |
| 2/2 repeats | 24 | 21 |

Thus adapter-only has more always-complete cases and fewer one-off completion
cases. Some per-case online variance remains, so the claim is a stable
aggregate advantage under the frozen protocol, not per-case determinism.

## Mechanism Boundary

- Adapter marker applications were `19` in A1 and `20` in A2, versus `0` in
  both generic runs.
- Shared-certificate replay found strict eligibility only in adapter streams
  (`5` rows in each), but strict on/off changed `0` terminal actions.
- Therefore the supported attribution is: deterministic adapters improve
  certificate construction/eligibility. The result does not support an
  independent strict-terminal-acceptance benefit.

## Performance Coupling

The certificate gain is accompanied by a positive Answer F1 delta in both
blocks:

- Block 1: `+0.0714`.
- Block 2: `+0.0829`.
- Aggregate: `+0.0772`.

Coverage is also positive in both blocks (`+0.0444`, `+0.0667`) and in the
aggregate (`+0.0556`). This satisfies the frozen rule that certificate gains
must not be separated from stable downstream F1 improvement.

## Verdict

`stable_support`: deterministic adapters create a repeat-stable improvement in
correct terminal certificate production and downstream Answer F1 on the
frozen stratified45 protocol. The evidence supports promotion to matched
modern baselines, not yet to non-leaking dev/test or a 300-sample main claim.

Primary evidence:

- `analysis/semantic_online_stability_primary_aggregate_20260715.json`
  (`7FB49D753A0E1C8DF8F8322D4AB2E7E480AE26DEC13FCE28248B0E72F13F7296`)
- `analysis/semantic_online_stability_primary_aggregate_20260715.md`
  (`88C982A4F6F183AFA118A514D51FDB26306D596BD7141FCE0491A4535C0C8605`)
