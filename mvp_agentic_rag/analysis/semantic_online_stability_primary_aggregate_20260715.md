# Adapter-vs-Generic Online Stability Analysis

- Protocol: `semantic_adapter_generic_online_stability_v1_20260715`
- Status: `primary_complete`
- Dry run: `false`
- Decision: `pass_to_matched_modern_baselines`

## Certificate-Completion Layer

| Variant/run | Terminal complete | Terminal correct | Adapter markers | Valid |
|---|---:|---:|---:|---:|
| adapter_only / `layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s1` | 24/45 | 20/45 | 19 | true |
| adapter_only / `layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s2` | 25/45 | 21/45 | 20 | true |
| generic_only / `layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s1` | 23/45 | 16/45 | 0 | true |
| generic_only / `layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s2` | 22/45 | 17/45 | 0 | true |

## Terminal-Policy Layer

| Variant/run | Answer/abstain | Answer w/o complete cert | Downgrades | Policy mismatch | Safety violations |
|---|---:|---:|---:|---:|---:|
| adapter_only / `layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s1` | 20/25 | 0 | 0 | 0 | 0 |
| adapter_only / `layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s2` | 21/24 | 0 | 1 | 0 | 0 |
| generic_only / `layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s1` | 18/27 | 0 | 1 | 0 | 0 |
| generic_only / `layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s2` | 18/27 | 0 | 2 | 0 | 0 |

## Paired Blocks

| Block | Correct-certificate delta | Answer F1 delta | Coverage delta |
|---:|---:|---:|---:|
| 1 | 0.0889 | 0.0714 | 0.0444 |
| 2 | 0.0889 | 0.0829 | 0.0667 |

Historical dry runs are schema checks only and must not be used in
the primary pre-registered decision.
