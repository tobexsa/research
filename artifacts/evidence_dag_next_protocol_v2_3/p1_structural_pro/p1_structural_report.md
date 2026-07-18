# V2.3 P1 Structural Diagnostic Report

New API calls: **362** (Route A 60, C2P 52, C4A 250).

| Slice | Primary result | Invalid |
|---|---:|---:|
| Route A direct topology | 0/60 (0.0%) | 50/60 |
| C1 attached hop | 24/60 (40.0%) | 8/60 |
| C2O attached shape, 3/4-hop only | 7/50 (14.0%) | 31/50 |
| C2P end-to-end topology | 7/60 (11.7%) | 18/60 |
| C4A pair relation | 85/250 (34.0%) | 23/250 |
| C4A exact graph | 1/60 (1.7%) | 58/60 inconsistent |

Route A macro-F1: 0.0000; prediction entropy: 1.8464 bits.
C2P macro-F1: 0.0751; mean calls/question: 1.8667.
C4A mean edge F1: 0.0250.

Invalid and transport-failed outputs remain in every planned denominator. C1/C2O are attached from the verified V1 baseline; no Confirmation or Internal Holdout sample was queried.
