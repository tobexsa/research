# Online Stability G2 Generic-Only Results

Date: 2026-07-15
Protocol: `semantic_adapter_generic_online_stability_v1_20260715`
Run: `generic_stability_s2`
Status: `complete_valid`

## Verdict

G2 completed all 45 frozen stratified cases and passes every predeclared
per-run validity and safety gate. It is accepted as the generic-only
observation for paired block 2.

G1 and G2 show small certificate-completion and Answer F1 variation without
any terminal-policy or safety violation. This is exactly the separation the
frozen protocol was designed to measure. A2 is now the only next authorized
online run. No block-2 adapter-minus-generic sign or four-run promotion
decision exists until A2 completes and passes audit.

## Identity And Completion

- Config:
  `configs/layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s2.yaml`
- Config SHA-256:
  `52A01927635A62690540A7AC7908A5B83C85DED057F749525298AD91FF43F95F`.
- Dataset: 45 frozen rows, 45 unique IDs, exact membership.
- Completed / skipped: `45 / 0`.
- Runtime: `4320.4` seconds.
- Remaining run lock: none.
- Live strict-certificate steps: `0`, as required.

## Existing Performance Metrics

- Overall accuracy / EM: `0.3111 / 0.3111`.
- Answer F1: `0.3571`.
- Coverage: `0.4000`.
- Selective accuracy / F1: `0.7778 / 0.8927`.
- Average retrieval calls: `2.4667`.
- Wasted retrieval rate: `0.7111`.
- Final answered unsupported: `0`.

## Layer A: Certificate Completion

- Deterministic adapter marker applications: `0`, as required for generic-only.
- Ever-complete local certificates: `24/45`.
- Terminal-complete local certificates: `22/45`.
- Terminal-complete and correct certificates: `17/45`.

## Layer B: Terminal Policy

- Final answers / abstentions: `18 / 27`.
- Answer with a terminal-complete certificate: `18`.
- Answer without a terminal-complete certificate: `0`.
- Abstain with a terminal-complete certificate: `4`.
- Shared-policy/live action mismatches: `0`.
- Live final answered unsupported: `0`.
- State terminal invariant violations: `0`.
- Unsafe typed-state transitions: `0`.
- Shared strict-off terminal invariant violations: `0`.
- Byte-identical shared-policy replay deterministic across three repeats:
  `true`.

## Shared-Certificate Diagnostic

- Counterfactual strict-eligible terminal rows: `0`.
- Strict on/off terminal action changes: `0`.
- Strict-on violations: `0`.
- Strict-off violations: `0`.

This remains diagnostic only; live G2 used strict acceptance off.

## Generic-Only Repeat Variation

| Frozen measure | G1 | G2 | G2 - G1 |
|---|---:|---:|---:|
| Ever-complete certificate rate | 0.5111 | 0.5333 | +0.0222 |
| Terminal-complete certificate rate | 0.5111 | 0.4889 | -0.0222 |
| Terminal-correct-certificate rate | 0.3556 | 0.3778 | +0.0222 |
| Answer F1 | 0.3457 | 0.3571 | +0.0114 |
| Coverage | 0.4000 | 0.4000 | 0.0000 |

These values describe generic-only online variance. They do not establish the
adapter effect; the predeclared effect is evaluated within paired blocks after
A2 exists.

## Hard-Gate Audit

| Gate | Result |
|---|---|
| Frozen config/source/data identity | pass |
| 45 rows / 45 unique / exact membership | pass |
| Zero skipped / no remaining lock | pass |
| Complete finite existing metrics | pass |
| Final answered unsupported zero | pass |
| Terminal invariant violations zero | pass |
| Unsafe typed-state transitions zero | pass |
| Shared-policy replay deterministic | pass |
| Live strict activation zero | pass |
| Answer without complete certificate zero | pass |
| Shared-policy action matches live action | pass |

Analyzer verdict for G2: `valid=true`, with no validity reasons.

## Evidence And Hashes

- Trajectory:
  `runs/layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s2/trajectories.jsonl`
  (`4781416ABB8AC2449D1FBD64290F723D42F08C13C9EBB5769B8EC4BE44283AE8`)
- Metrics:
  `runs/layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s2/metrics.json`
  (`A05E9971ABD34BC7F95F7A528DF2119FF35FE2E1536BBBAA2DD400E57B8F5646`)
- Run summary:
  `runs/layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s2/run_summary.md`
  (`E9C5ABE218118775E974C8B696D43C31805753F84487B2897383617F70BDCAC5`)
- State replay:
  `analysis/semantic_online_stability_g2_state_replay_20260715.json`
  (`3379C2E93BA80717BCE2C613FBD34C264BE8A2CAD7CD3DDAFA9DC541FB6F828B`)
- Shared replay:
  `analysis/semantic_online_stability_g2_shared_replay_20260715.json`
  (`548F5A6527C2F296F71B024BAB2E2C352733548ED95CF34E003F7AE3D3E1F5EE`)
- Frozen-analyzer interim dry aggregate:
  `analysis/semantic_online_stability_g2_interim_dry_aggregate_20260715.json`
  (`9D06336D5B61CCD4C13F1FE68F361D638FCB832A0F2267A62BEC95CDACBBE21A`)

The interim analyzer invocation is marked dry-run because the frozen analyzer
does not issue the primary protocol decision before all four runs exist. G2's
per-run validity and reported layer values are evaluated by the frozen
analyzer and are primary run evidence.

## Next Protocol Step

The only authorized next run is A2:

```powershell
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s2.yaml
```

Matched modern baselines remain locked until A2 is complete, all four runs are
valid, and the frozen four-run decision rule is applied without modification.

## Runtime Interface Degradation

Managed `bash_exec`, artifact, and memory interfaces are unavailable. The run
directory, repository-local replay/audit files, report, and hashes are the
explicit durable fallback, not artifact-service records.
