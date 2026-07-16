# Shared-Certificate Terminal Replay

- Source: `runs\layer1_siliconflow_qwen3_14b_nonleaking_musique_dev_pilot12_adapter_20260716_s1\trajectories.jsonl`
- Rows / unique: `12 / 12`
- Repeat count: `3`
- Deterministic replay: `true`
- Strict eligible: `0`
- Strict-on/off action changes: `0`
- Strict-on terminal invariant violations: `0`
- Strict-off terminal invariant violations: `0`
- Gate pass: `true`

| Sample | Eligible | Strict-on lane/action | Strict-off lane/action | Changed | Input digest |
|---|---:|---|---|---:|---|
| `q_004732875d5a7b72a7d952f3` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `593A636D4D00...` |
| `q_00972b0c4d999c38b5c98630` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `69E9944733B3...` |
| `q_00b7b7947d662df65733c4d0` | false | generic_compatibility / answer | generic_compatibility / answer | false | `9CE343DBC27B...` |
| `q_00ba96c23347b8d74456e3af` | false | generic_compatibility / answer | generic_compatibility / answer | false | `547C7EC70E4D...` |
| `q_00e8f0ec574cb8a98efccc93` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `92A4720E4BB5...` |
| `q_012bbeb36621cbf087ae953a` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `38C080F4C27C...` |
| `q_012f7cf9909b0d1e09510ea3` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `10409E6CCA4E...` |
| `q_018b8a368316855e9294e73a` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `61E9F3AD177A...` |
| `q_00355d33c009072dab282e74` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `C60E1D64F4FE...` |
| `q_00545634562beb8d5262611e` | false | no_fallback / abstain | no_fallback / abstain | false | `A88CAEF243D3...` |
| `q_0056b70f2e6a2356f20bfa03` | false | generic_compatibility / answer | generic_compatibility / answer | false | `370DD75927E3...` |
| `q_0136b0ef9fb6b898da2cb2f3` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `5FDEA5DF3E62...` |

## Contract

Frozen runtime state, verifier, binding, proposal, budget, repair metadata, and retrieved evidence IDs only; no gold fields.

The replay reports sample IDs for audit only. It does not read gold
answers, decompositions, or gold support to select a lane or action.
