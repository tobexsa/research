# Shared-Certificate Terminal Replay

- Source: `runs\layer1_siliconflow_qwen3_14b_nonleaking_musique_dev_pilot12_generic_20260716_s1\trajectories.jsonl`
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
| `q_004732875d5a7b72a7d952f3` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `0E70C77E1CCD...` |
| `q_00972b0c4d999c38b5c98630` | false | no_fallback / abstain | no_fallback / abstain | false | `46B7F2CFAEA3...` |
| `q_00b7b7947d662df65733c4d0` | false | generic_compatibility / answer | generic_compatibility / answer | false | `CC608E695E27...` |
| `q_00ba96c23347b8d74456e3af` | false | generic_compatibility / answer | generic_compatibility / answer | false | `3F364EDA4D17...` |
| `q_00e8f0ec574cb8a98efccc93` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `61BCFB85E99D...` |
| `q_012bbeb36621cbf087ae953a` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `8D42204F3F7A...` |
| `q_012f7cf9909b0d1e09510ea3` | false | no_fallback / abstain | no_fallback / abstain | false | `875A52B26497...` |
| `q_018b8a368316855e9294e73a` | false | no_fallback / abstain | no_fallback / abstain | false | `9D1DFA734E28...` |
| `q_00355d33c009072dab282e74` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `BA06A2A73D5C...` |
| `q_00545634562beb8d5262611e` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `4A0D3A757D63...` |
| `q_0056b70f2e6a2356f20bfa03` | false | generic_compatibility / answer | generic_compatibility / answer | false | `2BE9D896FA77...` |
| `q_0136b0ef9fb6b898da2cb2f3` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `A0A32C0D4D8E...` |

## Contract

Frozen runtime state, verifier, binding, proposal, budget, repair metadata, and retrieved evidence IDs only; no gold fields.

The replay reports sample IDs for audit only. It does not read gold
answers, decompositions, or gold support to select a lane or action.
