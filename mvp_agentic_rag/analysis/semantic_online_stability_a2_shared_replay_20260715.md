# Shared-Certificate Terminal Replay

- Source: `runs\layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s2\trajectories.jsonl`
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
| `2hop__10620_49084` | false | generic_compatibility / answer | generic_compatibility / answer | false | `5D3AE7B01EC3...` |
| `2hop__129721_40482` | false | generic_compatibility / answer | generic_compatibility / answer | false | `44B4EB401E44...` |
| `2hop__131951_643670` | false | generic_compatibility / answer | generic_compatibility / answer | false | `80C478A1921D...` |
| `2hop__132854_417697` | false | generic_compatibility / answer | generic_compatibility / answer | false | `CF48F2CED7AF...` |
| `2hop__136179_13529` | true | strict_certificate / answer | generic_compatibility / answer | false | `D4A937E33E68...` |
| `2hop__142699_67465` | false | generic_compatibility / answer | generic_compatibility / answer | false | `993D93829B8F...` |
| `2hop__151750_141308` | false | generic_compatibility / answer | generic_compatibility / answer | false | `7C1E131EE2D9...` |
| `2hop__153573_44085` | false | generic_compatibility / answer | generic_compatibility / answer | false | `BAFBE59E3E2A...` |
| `2hop__167577_31122` | false | generic_compatibility / answer | generic_compatibility / answer | false | `1D6246029B3E...` |
| `2hop__194469_83289` | false | generic_compatibility / answer | generic_compatibility / answer | false | `495CD35F669C...` |
| `2hop__20268_42014` | false | generic_compatibility / answer | generic_compatibility / answer | false | `7AFEB777B18A...` |
| `2hop__23459_35124` | false | generic_compatibility / answer | generic_compatibility / answer | false | `73C99C9F5BD0...` |
| `2hop__244193_461106` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `5885A45BFCBA...` |
| `2hop__247353_55227` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `14CD0048806F...` |
| `2hop__249867_557232` | false | generic_compatibility / answer | generic_compatibility / answer | false | `19EEB086FDC8...` |
| `3hop1__103751_24918_24991` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `C935A47DDED9...` |
| `3hop1__103881_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `E4F08D87288A...` |
| `3hop1__104996_160713_77246` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `16613D6C18FA...` |
| `3hop1__105767_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `B3C5452D30B4...` |
| `3hop1__108833_720914_41132` | false | generic_compatibility / answer | generic_compatibility / answer | false | `AAD3797CD2D9...` |
| `3hop1__128554_39743_24526` | false | no_fallback / abstain | no_fallback / abstain | false | `BAB23D709345...` |
| `3hop1__129499_33897_81096` | true | strict_certificate / answer | generic_compatibility / answer | false | `66574B5CBB12...` |
| `3hop1__135659_87694_64412` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `C929D2EAE5DC...` |
| `3hop1__136129_87694_124169` | true | strict_certificate / answer | generic_compatibility / answer | false | `DC5806015626...` |
| `3hop1__140786_2053_5289` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `F0D1AA1EE386...` |
| `3hop1__140786_2053_52946` | false | generic_compatibility / answer | generic_compatibility / answer | false | `43A0CB384312...` |
| `3hop1__144439_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `DB09BF1D4C9E...` |
| `3hop1__145194_160545_62931` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `19389EA11B46...` |
| `3hop1__159803_89752_75165` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `8A462F2780FE...` |
| `3hop1__222497_309482_27537` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `2F46D866A656...` |
| `4hop1__105401_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `2CD1CABEEEC4...` |
| `4hop1__105688_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `5E4A23B52EA8...` |
| `4hop1__131611_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `92CC3B7ABEA7...` |
| `4hop1__13170_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `B16FA0AE1EAC...` |
| `4hop1__145494_698949_157828_162309` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `5F739B4F6CA8...` |
| `4hop1__151650_5274_458768_33632` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `7DB7F8609CD5...` |
| `4hop1__151650_5274_458768_33637` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `FB8EEF765FD6...` |
| `4hop1__152146_5274_458768_33632` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `DC700D8CBE84...` |
| `4hop1__161605_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `75BA2EC6D033...` |
| `4hop1__161810_583746_457883_650651` | true | strict_certificate / answer | generic_compatibility / answer | false | `24C805AC44F9...` |
| `4hop1__166471_49925_13759_736921` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `175A31EBEE88...` |
| `4hop1__17192_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `4D3BFCE3DDE3...` |
| `4hop1__236903_153080_33897_81096` | true | strict_certificate / abstain | generic_compatibility / abstain | false | `5166FC115055...` |
| `4hop1__264443_49925_13759_736921` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `15E37D16E226...` |
| `4hop1__28352_53706_795904_580996` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `1A2A6A106EDA...` |

## Contract

Frozen runtime state, verifier, binding, proposal, budget, repair metadata, and retrieved evidence IDs only; no gold fields.

The replay reports sample IDs for audit only. It does not read gold
answers, decompositions, or gold support to select a lane or action.
