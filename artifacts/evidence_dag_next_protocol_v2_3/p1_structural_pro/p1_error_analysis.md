# P1 Failure Analysis

| Variant | N | Length | Valid | Exact | Valid but wrong | Repetition | P50 ms | P90 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `c2p_shape` | 52 | 10 | 42 | 7 | 35 | 0 | 769.0 | 2043.2 |
| `c4a_pair` | 250 | 23 | 227 | 85 | 142 | 0 | 597.4 | 1204.5 |
| `route_a` | 60 | 50 | 10 | 0 | 10 | 0 | 3211.9 | 4289.2 |

Overall completion tokens: **13145**; prompt tokens: **58527**.

`finish=length` and repetition are reported independently from valid-but-wrong classifications. This separates decoder looping from semantic classification failure.
