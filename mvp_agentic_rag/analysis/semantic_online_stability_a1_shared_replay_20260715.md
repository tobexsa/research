# Shared-Certificate Terminal Replay

- Source: `runs\layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s1\trajectories.jsonl`
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
| `2hop__10620_49084` | false | generic_compatibility / answer | generic_compatibility / answer | false | `975F96699E5A...` |
| `2hop__129721_40482` | false | generic_compatibility / answer | generic_compatibility / answer | false | `D625FF7359EF...` |
| `2hop__131951_643670` | false | generic_compatibility / answer | generic_compatibility / answer | false | `9B3DE1DE064F...` |
| `2hop__132854_417697` | false | generic_compatibility / answer | generic_compatibility / answer | false | `CC829A3E0E83...` |
| `2hop__136179_13529` | true | strict_certificate / answer | generic_compatibility / answer | false | `A51A90CF4E98...` |
| `2hop__142699_67465` | false | generic_compatibility / answer | generic_compatibility / answer | false | `D6AC63E9D2D0...` |
| `2hop__151750_141308` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `7869090D86BD...` |
| `2hop__153573_44085` | false | generic_compatibility / answer | generic_compatibility / answer | false | `BF6D29BE9F05...` |
| `2hop__167577_31122` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `D4FE9CCFE8FD...` |
| `2hop__194469_83289` | false | generic_compatibility / answer | generic_compatibility / answer | false | `12857F745137...` |
| `2hop__20268_42014` | false | generic_compatibility / answer | generic_compatibility / answer | false | `CE979E2148C4...` |
| `2hop__23459_35124` | false | generic_compatibility / answer | generic_compatibility / answer | false | `8C6DA8D07B3F...` |
| `2hop__244193_461106` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `C3912D2C5147...` |
| `2hop__247353_55227` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `B71CE91A43BC...` |
| `2hop__249867_557232` | false | generic_compatibility / answer | generic_compatibility / answer | false | `75B00ECCD203...` |
| `3hop1__103751_24918_24991` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `2434E967C01E...` |
| `3hop1__103881_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `DDFEA358EC75...` |
| `3hop1__104996_160713_77246` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `C765BA776C20...` |
| `3hop1__105767_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `0DFAE18F1F1D...` |
| `3hop1__108833_720914_41132` | false | generic_compatibility / answer | generic_compatibility / answer | false | `827BA3EDD355...` |
| `3hop1__128554_39743_24526` | false | generic_compatibility / answer | generic_compatibility / answer | false | `8B4CF8399F22...` |
| `3hop1__129499_33897_81096` | true | strict_certificate / answer | generic_compatibility / answer | false | `8B564800E835...` |
| `3hop1__135659_87694_64412` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `6A48D5586868...` |
| `3hop1__136129_87694_124169` | true | strict_certificate / answer | generic_compatibility / answer | false | `C2A947DC96E2...` |
| `3hop1__140786_2053_5289` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `759ECA208807...` |
| `3hop1__140786_2053_52946` | false | generic_compatibility / answer | generic_compatibility / answer | false | `E839FBCF3079...` |
| `3hop1__144439_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `0FB23FD2C951...` |
| `3hop1__145194_160545_62931` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `3F3D5ECD294C...` |
| `3hop1__159803_89752_75165` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `7B2C5F9C1BE5...` |
| `3hop1__222497_309482_27537` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `F93816068125...` |
| `4hop1__105401_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `6DDF5613DF44...` |
| `4hop1__105688_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `E30A5F559DC6...` |
| `4hop1__131611_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `86D907DF70CA...` |
| `4hop1__13170_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `EECA35E17949...` |
| `4hop1__145494_698949_157828_162309` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `EBE7666E4535...` |
| `4hop1__151650_5274_458768_33632` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `76BE7501C1A3...` |
| `4hop1__151650_5274_458768_33637` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `01F43723653C...` |
| `4hop1__152146_5274_458768_33632` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `D656FA5176DA...` |
| `4hop1__161605_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `34CA5AD24F12...` |
| `4hop1__161810_583746_457883_650651` | true | strict_certificate / answer | generic_compatibility / answer | false | `5EB021DCB775...` |
| `4hop1__166471_49925_13759_736921` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `4FB59F41AE45...` |
| `4hop1__17192_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `D7CFC37EF0BA...` |
| `4hop1__236903_153080_33897_81096` | true | strict_certificate / abstain | generic_compatibility / abstain | false | `29768C39A087...` |
| `4hop1__264443_49925_13759_736921` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `129E9EDF1963...` |
| `4hop1__28352_53706_795904_580996` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `7975F60AF09D...` |

## Contract

Frozen runtime state, verifier, binding, proposal, budget, repair metadata, and retrieved evidence IDs only; no gold fields.

The replay reports sample IDs for audit only. It does not read gold
answers, decompositions, or gold support to select a lane or action.
