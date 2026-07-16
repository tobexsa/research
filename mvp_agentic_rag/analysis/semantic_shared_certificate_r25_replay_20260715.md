# Shared-Certificate Terminal Replay

- Source: `runs\layer1_siliconflow_qwen3_14b_semantic_fusion_stratified45_20260714_r25\trajectories.jsonl`
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
| `2hop__10620_49084` | false | generic_compatibility / answer | generic_compatibility / answer | false | `20BC87778053...` |
| `2hop__129721_40482` | false | generic_compatibility / answer | generic_compatibility / answer | false | `DB70F7ED6D65...` |
| `2hop__131951_643670` | false | generic_compatibility / answer | generic_compatibility / answer | false | `3AEE18819EA5...` |
| `2hop__132854_417697` | false | generic_compatibility / answer | generic_compatibility / answer | false | `20710ABB64F4...` |
| `2hop__136179_13529` | true | strict_certificate / answer | generic_compatibility / answer | false | `2905A5E18ADC...` |
| `2hop__142699_67465` | false | generic_compatibility / answer | generic_compatibility / answer | false | `1BF45304AEA8...` |
| `2hop__151750_141308` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `6CEEC68303A7...` |
| `2hop__153573_44085` | false | generic_compatibility / answer | generic_compatibility / answer | false | `E4E76C1D1C94...` |
| `2hop__167577_31122` | false | generic_compatibility / answer | generic_compatibility / answer | false | `66B8AFDB9CC5...` |
| `2hop__194469_83289` | false | generic_compatibility / answer | generic_compatibility / answer | false | `CB6304A19243...` |
| `2hop__20268_42014` | false | generic_compatibility / answer | generic_compatibility / answer | false | `A96006AFEB8F...` |
| `2hop__23459_35124` | false | generic_compatibility / answer | generic_compatibility / answer | false | `9AAC1D3AE971...` |
| `2hop__244193_461106` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `D286C8CE97BB...` |
| `2hop__247353_55227` | false | generic_compatibility / answer | generic_compatibility / answer | false | `0ECBBE5D2663...` |
| `2hop__249867_557232` | false | generic_compatibility / answer | generic_compatibility / answer | false | `7E1A1A9969CC...` |
| `3hop1__103751_24918_24991` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `D070A3B0C7AA...` |
| `3hop1__103881_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `D3E7EA6A91A2...` |
| `3hop1__104996_160713_77246` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `35F6AA87214F...` |
| `3hop1__105767_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `DB705661BB96...` |
| `3hop1__108833_720914_41132` | false | generic_compatibility / answer | generic_compatibility / answer | false | `FD5EAB6FE518...` |
| `3hop1__128554_39743_24526` | false | no_fallback / abstain | no_fallback / abstain | false | `65327D895427...` |
| `3hop1__129499_33897_81096` | true | strict_certificate / abstain | generic_compatibility / abstain | false | `385E217DAAA2...` |
| `3hop1__135659_87694_64412` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `A78E1388AE77...` |
| `3hop1__136129_87694_124169` | true | strict_certificate / answer | generic_compatibility / answer | false | `431F482C3EDE...` |
| `3hop1__140786_2053_5289` | false | generic_compatibility / answer | generic_compatibility / answer | false | `14764E29E22D...` |
| `3hop1__140786_2053_52946` | false | generic_compatibility / answer | generic_compatibility / answer | false | `CA26A10E5975...` |
| `3hop1__144439_443779_52195` | false | generic_compatibility / answer | generic_compatibility / answer | false | `70C10DE2B3C6...` |
| `3hop1__145194_160545_62931` | false | generic_compatibility / answer | generic_compatibility / answer | false | `5E43A29AC06C...` |
| `3hop1__159803_89752_75165` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `8407EF8B31A9...` |
| `3hop1__222497_309482_27537` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `2856B092A1B7...` |
| `4hop1__105401_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `2CCB877A9503...` |
| `4hop1__105688_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `1D47A9ADD0E0...` |
| `4hop1__131611_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `3A6246807472...` |
| `4hop1__13170_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `F8835CEF2A7A...` |
| `4hop1__145494_698949_157828_162309` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `E96CE488E09C...` |
| `4hop1__151650_5274_458768_33632` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `71E43D9F9D07...` |
| `4hop1__151650_5274_458768_33637` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `7AF36C0CF29E...` |
| `4hop1__152146_5274_458768_33632` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `00F134A6628C...` |
| `4hop1__161605_32392_823060_610794` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `A30161FA34B2...` |
| `4hop1__161810_583746_457883_650651` | true | strict_certificate / answer | generic_compatibility / answer | false | `C626DA3FAA65...` |
| `4hop1__166471_49925_13759_736921` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `26BF71066648...` |
| `4hop1__17192_17130_70784_79935` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `F0E0CDDF0F40...` |
| `4hop1__236903_153080_33897_81096` | true | strict_certificate / answer | generic_compatibility / answer | false | `BF3DAB2B1E29...` |
| `4hop1__264443_49925_13759_736921` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `2567B16B7155...` |
| `4hop1__28352_53706_795904_580996` | false | generic_compatibility / abstain | generic_compatibility / abstain | false | `B95311493DB3...` |

## Contract

Frozen runtime state, verifier, binding, proposal, budget, repair metadata, and retrieved evidence IDs only; no gold fields.

The replay reports sample IDs for audit only. It does not read gold
answers, decompositions, or gold support to select a lane or action.
