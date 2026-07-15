# Semantic Fusion Stratified45 Comparison

## Outcome

Fusion R25 outperforms matched generic-only R26 while both keep final answered unsupported at zero. Phase 2 is complete.

## Metrics

| Run | EM | Answer F1 | Coverage | Selective F1 | Avg calls | Wasted | Final unsupported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| r12 | 0.3333 | 0.3511 | 0.3778 | 0.9294 | 2.3556 | 0.6222 | 0.0000 |
| r20 | 0.2889 | 0.3000 | 0.3333 | 0.9000 | 2.4444 | 0.6667 | 0.0000 |
| generic_r26 | 0.3778 | 0.3778 | 0.4000 | 0.9444 | 2.4000 | 0.6889 | 0.0000 |
| fusion_r25 | 0.4889 | 0.4889 | 0.5111 | 0.9565 | 2.2889 | 0.5778 | 0.0000 |

## Matched Delta

- Answer F1: `+0.1111`
- Coverage: `+0.1111`
- Selective accuracy: `+0.0121`
- Average retrieval calls: `-0.1111`
- Wasted retrieval rate: `-0.1111`

## Paired Correctness

- Fusion-only correct: `6`
- Generic-only correct: `1`
- Both correct: `16`
- Both wrong: `22`

Fusion-only IDs:

- `2hop__132854_417697`
- `2hop__167577_31122`
- `2hop__247353_55227`
- `3hop1__145194_160545_62931`
- `4hop1__161810_583746_457883_650651`
- `4hop1__236903_153080_33897_81096`

Generic-only IDs:

- `3hop1__129499_33897_81096`

## Routing Audit

- R25 lane counts: `{'generic_compatibility': 91, 'no_fallback': 1, 'strict_certificate': 11}`
- R26 lane counts: `{'generic_compatibility': 107, 'no_fallback': 1}`
- R26 recognized certificate-adapter markers: `{}`
- R26 topology-only compatibility markers: `{'final_hop_order_canonicalization': 1}`

## Decision

Phase 2 is complete. Fusion improves matched generic-only Answer F1 and coverage with final unsupported unchanged at zero. Proceed to phase 3 component ablations, repeated runs, and matched modern baselines.
