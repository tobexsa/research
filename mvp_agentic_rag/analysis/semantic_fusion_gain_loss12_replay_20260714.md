# Semantic Fusion Gain/Loss-12 Replay Audit

This is a structural replay of stored R20 states, not a fused outcome run.

| Group | Sample | Hop | R12 | R20 | R20 lane trace |
| --- | --- | ---: | --- | --- | --- |
| gain | `2hop__136179_13529` | 2 | abstain | June 1982 | strict_certificate |
| gain | `2hop__167577_31122` | 2 | abstain | 18th | generic_compatibility -> generic_compatibility |
| gain | `3hop1__136129_87694_124169` | 3 | abstain | 1952 | strict_certificate -> strict_certificate |
| gain | `4hop1__161810_583746_457883_650651` | 4 | abstain | NBC | strict_certificate -> strict_certificate |
| gain | `4hop1__236903_153080_33897_81096` | 4 | abstain | Mario Andretti | strict_certificate -> strict_certificate -> strict_certificate |
| loss | `2hop__142699_67465` | 2 | March 11, 2011. | 2011 | generic_compatibility |
| loss | `2hop__194469_83289` | 2 | Matt Bennett | abstain | generic_compatibility -> generic_compatibility -> generic_compatibility |
| loss | `2hop__23459_35124` | 2 | 450 | abstain | generic_compatibility -> generic_compatibility -> generic_compatibility |
| loss | `2hop__247353_55227` | 2 | Maria Bello | abstain | generic_compatibility -> generic_compatibility -> generic_compatibility |
| loss | `3hop1__103881_443779_52195` | 3 | Francisco Guterres | abstain | no_fallback |
| loss | `3hop1__140786_2053_5289` | 3 | Oriole Records | abstain | generic_compatibility -> generic_compatibility -> generic_compatibility |
| loss | `3hop1__144439_443779_52195` | 3 | Francisco Guterres | abstain | generic_compatibility -> generic_compatibility -> generic_compatibility |

## Interpretation

- The router consumes only canonical runtime state.
- Stored R20 replay can validate certificate/no-fallback separation,
  but cannot simulate the R12-compatible verifier outputs that the live
  Fusion run will produce before strict-certificate escalation.
- The real 12-case gate remains the decisive phase-1 result.
