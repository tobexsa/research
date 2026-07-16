# Adapter-vs-Generic Online Stability Analysis

- Protocol: `semantic_adapter_generic_online_stability_v1_20260715`
- Status: `dry_run_complete`
- Dry run: `true`
- Decision: `dry_run_no_primary_decision`

## Certificate-Completion Layer

| Variant/run | Terminal complete | Terminal correct | Adapter markers | Valid |
|---|---:|---:|---:|---:|
| adapter_only / `layer1_siliconflow_qwen3_14b_semantic_adapter_only_stratified45_20260715_r27` | 25/45 | 21/45 | 20 | true |
| generic_only / `layer1_siliconflow_qwen3_14b_semantic_generic_only_stratified45_20260714_r26` | 22/45 | 18/45 | 0 | false |

## Terminal-Policy Layer

| Variant/run | Answer/abstain | Answer w/o complete cert | Downgrades | Policy mismatch | Safety violations |
|---|---:|---:|---:|---:|---:|
| adapter_only / `layer1_siliconflow_qwen3_14b_semantic_adapter_only_stratified45_20260715_r27` | 21/24 | 0 | 1 | 0 | 0 |
| generic_only / `layer1_siliconflow_qwen3_14b_semantic_generic_only_stratified45_20260714_r26` | 18/27 | 1 | 1 | 2 | 4 |

## Paired Blocks

| Block | Correct-certificate delta | Answer F1 delta | Coverage delta |
|---:|---:|---:|---:|
| 1 | 0.0667 | 0.0667 | 0.0667 |

Historical dry runs are schema checks only and must not be used in
the primary pre-registered decision.
