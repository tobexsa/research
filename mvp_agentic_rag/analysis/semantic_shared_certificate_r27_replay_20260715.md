# Shared-Certificate Terminal Replay

- Source: `runs\layer1_siliconflow_qwen3_14b_semantic_adapter_only_stratified45_20260715_r27\trajectories.jsonl`
- Rows / unique: `45 / 45`
- Repeat count: `3`
- Deterministic replay: `true`
- Strict eligible: `5`
- Strict-on/off action changes: `0`
- Strict-on terminal invariant violations: `0`
- Strict-off terminal invariant violations: `0`
- Gate pass: `true`

| Sample | Eligible | Strict-on lane/action | Strict-off lane/action | Changed | Input digest |
|---|---:|---|---|---:|---|
| `2hop__10620_49084` | false | generic_compatibility / answer | generic_compatibility / answer | false | `B9B53BFF08F0...` |
| `2hop__129721_40482` | false | generic_compatibility / answer | generic_compatibility / answer | false | `5F99A3B49DB3...` |
| `2hop__131951_643670` | false | generic_compatibility / answer | generic_compatibility / answer | false | `185216809098...` |
| `2hop__132854_417697` | false | generic_compatibility / answer | generic_compatibility / answer | false | `4E46266BE351...` |
| `2hop__136179_13529` | true | strict_certificate / answer | generic_compatibility / answer | false | `E6F11A7813C7...` |
| `2hop__142699_67465` | false | generic_compatibility / answer | generic_compatibility / answer | false | `0789476A1EC7...` |
| `2hop__151750_141308` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `E5ECFB191793...` |
| `2hop__153573_44085` | false | generic_compatibility / answer | generic_compatibility / answer | false | `440E86FEC936...` |
| `2hop__167577_31122` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `39CB05F3E0F5...` |
| `2hop__194469_83289` | false | generic_compatibility / answer | generic_compatibility / answer | false | `970DFAA89B43...` |
| `2hop__20268_42014` | false | generic_compatibility / answer | generic_compatibility / answer | false | `663322ECDA6B...` |
| `2hop__23459_35124` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `DB6AD7FF4381...` |
| `2hop__244193_461106` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `42447A693F42...` |
| `2hop__247353_55227` | false | generic_compatibility / answer | generic_compatibility / answer | false | `DE8A3C2E8487...` |
| `2hop__249867_557232` | false | generic_compatibility / answer | generic_compatibility / answer | false | `E00DE3269F2B...` |
| `3hop1__103751_24918_24991` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `2A0CD5EFA63C...` |
| `3hop1__103881_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `F0B5728BA751...` |
| `3hop1__104996_160713_77246` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `F1C267954871...` |
| `3hop1__105767_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `5C0F8F102795...` |
| `3hop1__108833_720914_41132` | false | generic_compatibility / answer | generic_compatibility / answer | false | `EC1A441C69FD...` |
| `3hop1__128554_39743_24526` | false | no_fallback / abstain | no_fallback / abstain | false | `C9ABED8042FD...` |
| `3hop1__129499_33897_81096` | true | strict_certificate / answer | generic_compatibility / answer | false | `5EC8EE0F8E80...` |
| `3hop1__135659_87694_64412` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `4622D607A527...` |
| `3hop1__136129_87694_124169` | true | strict_certificate / answer | generic_compatibility / answer | false | `20768BF7AEE9...` |
| `3hop1__140786_2053_5289` | false | generic_compatibility / answer | generic_compatibility / answer | false | `A947EBFFB6F5...` |
| `3hop1__140786_2053_52946` | false | generic_compatibility / answer | generic_compatibility / answer | false | `A21D7F85C486...` |
| `3hop1__144439_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `BB96CFED2FE3...` |
| `3hop1__145194_160545_62931` | false | generic_compatibility / answer | generic_compatibility / answer | false | `35CD1263EDE8...` |
| `3hop1__159803_89752_75165` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `C104316880C1...` |
| `3hop1__222497_309482_27537` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `ED3FDE0B67DE...` |
| `4hop1__105401_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `9B14A67A4C5E...` |
| `4hop1__105688_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `E2746A90F353...` |
| `4hop1__131611_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `2E96FD8FA398...` |
| `4hop1__13170_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `7A39145A2982...` |
| `4hop1__145494_698949_157828_162309` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `FE8EF483F9E1...` |
| `4hop1__151650_5274_458768_33632` | false | no_fallback / abstain | no_fallback / abstain | false | `6F98FD7396E7...` |
| `4hop1__151650_5274_458768_33637` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `036091831714...` |
| `4hop1__152146_5274_458768_33632` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `2538ED190F1F...` |
| `4hop1__161605_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `53CAD172EC3E...` |
| `4hop1__161810_583746_457883_650651` | true | strict_certificate / answer | generic_compatibility / answer | false | `952C51F3DB9A...` |
| `4hop1__166471_49925_13759_736921` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `907164482332...` |
| `4hop1__17192_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `9ACF1866E056...` |
| `4hop1__236903_153080_33897_81096` | true | strict_certificate / abstain | generic_compatibility / abstain | false | `3608C25A696A...` |
| `4hop1__264443_49925_13759_736921` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `187B77E7AC52...` |
| `4hop1__28352_53706_795904_580996` | false | no_fallback / abstain | no_fallback / abstain | false | `51A89C2B93D3...` |

## Contract

Frozen runtime state, verifier, binding, proposal, budget, repair metadata, and retrieved evidence IDs only; no gold fields.

The replay reports sample IDs for audit only. It does not read gold
answers, decompositions, or gold support to select a lane or action.
