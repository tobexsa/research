# Shared-Certificate Terminal Replay

- Source: `runs\layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_terminal_safety_20260715_r31\trajectories.jsonl`
- Rows / unique: `12 / 12`
- Repeat count: `3`
- Deterministic replay: `true`
- Strict eligible: `4`
- Strict-on/off action changes: `0`
- Strict-on terminal invariant violations: `0`
- Strict-off terminal invariant violations: `0`
- Gate pass: `true`

| Sample | Eligible | Strict-on lane/action | Strict-off lane/action | Changed | Input digest |
|---|---:|---|---|---:|---|
| `2hop__136179_13529` | true | strict_certificate / answer | generic_compatibility / answer | false | `DD80275BC5E5...` |
| `2hop__167577_31122` | false | generic_compatibility / answer | generic_compatibility / answer | false | `2EFA9846B3BB...` |
| `3hop1__136129_87694_124169` | true | strict_certificate / answer | generic_compatibility / answer | false | `2A9045919BE7...` |
| `4hop1__161810_583746_457883_650651` | true | strict_certificate / answer | generic_compatibility / answer | false | `6A976A3A0A3B...` |
| `4hop1__236903_153080_33897_81096` | true | strict_certificate / answer | generic_compatibility / answer | false | `3CDA366F6927...` |
| `2hop__142699_67465` | false | generic_compatibility / answer | generic_compatibility / answer | false | `241181CE421F...` |
| `2hop__194469_83289` | false | generic_compatibility / answer | generic_compatibility / answer | false | `56B8057395B2...` |
| `2hop__23459_35124` | false | generic_compatibility / answer | generic_compatibility / answer | false | `845ED3EEC871...` |
| `2hop__247353_55227` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `6349B9E15FF8...` |
| `3hop1__103881_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `B55824F5EFED...` |
| `3hop1__140786_2053_5289` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `4FF378031E5F...` |
| `3hop1__144439_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `CF860C577A67...` |

## Contract

Frozen runtime state, verifier, binding, proposal, budget, repair metadata, and retrieved evidence IDs only; no gold fields.

The replay reports sample IDs for audit only. It does not read gold
answers, decompositions, or gold support to select a lane or action.
