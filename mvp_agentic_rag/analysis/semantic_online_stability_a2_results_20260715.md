# Online Stability A2 Adapter-Only Results

Date: 2026-07-15
Protocol: `semantic_adapter_generic_online_stability_v1_20260715`
Run: `adapter_stability_s2`
Status: `complete_valid`

## Verdict

A2 completed all 45 frozen stratified cases and passes every predeclared
per-run validity and safety gate. It is accepted as the adapter-only
observation for paired block 2.

Together with A1, G1, and G2, A2 completes the exact four-run protocol. The
frozen analyzer's primary decision is `pass_to_matched_modern_baselines`.

## Identity And Completion

- Config:
  `configs/layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s2.yaml`
- Config SHA-256:
  `652D0115C5CF10A39C4583835A4FC81773239AAD90BE6F94D7EA1D8DF539AAED`.
- Dataset: 45 frozen rows, 45 unique IDs, exact membership.
- Completed / skipped: `45 / 0`.
- Runtime: `4813.2` seconds.
- Remaining run lock: none.
- Live strict-certificate steps: `0`, as required.

## Existing Performance Metrics

- Overall accuracy / EM: `0.4222 / 0.4222`.
- Answer F1: `0.4400`.
- Coverage: `0.4667`.
- Selective accuracy / F1: `0.9048 / 0.9429`.
- Average retrieval calls: `2.3556`.
- Wasted retrieval rate: `0.6222`.
- Final answered unsupported: `0`.

## Layer A: Certificate Completion

- Deterministic adapter marker applications: `20`.
- Ever-complete local certificates: `26/45`.
- Terminal-complete local certificates: `25/45`.
- Terminal-complete and correct certificates: `21/45`.

## Layer B: Terminal Policy

- Final answers / abstentions: `21 / 24`.
- Answer with a terminal-complete certificate: `21`.
- Answer without a terminal-complete certificate: `0`.
- Abstain with a terminal-complete certificate: `4`.
- Terminal guards / answer-to-abstain downgrades: `1 / 1`.
- Shared-policy/live action mismatches: `0`.
- Live final answered unsupported: `0`.
- State terminal invariant violations: `0`.
- Unsafe typed-state transitions: `0`.
- Byte-identical shared-policy replay deterministic across three repeats:
  `true`.

The one downgrade is correct fail-closed behavior, not a violation: a live
proposal that did not satisfy the frozen terminal contract was converted to
abstention.

## Shared-Certificate Diagnostic

- Counterfactual strict-eligible terminal rows: `5`.
- Strict on/off terminal action changes: `0`.
- Strict-on violations: `0`.
- Strict-off violations: `0`.

Live A2 used strict acceptance off. The diagnostic again shows no terminal
action attributable to toggling strict acceptance on identical certificates.

## Paired Block 2

| Frozen paired metric | A2 | G2 | A2 - G2 |
|---|---:|---:|---:|
| Terminal-correct-certificate rate | 0.4667 | 0.3778 | +0.0889 |
| Answer F1 | 0.4400 | 0.3571 | +0.0829 |
| Coverage | 0.4667 | 0.4000 | +0.0667 |

All block-2 directions are positive, matching block 1.

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

Analyzer verdict for A2: `valid=true`, with no validity reasons.

## Evidence And Hashes

- Trajectory:
  `runs/layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s2/trajectories.jsonl`
  (`5E9C5D1E7E25A309634D950307EE2DA8401CB66608419EFD4ADCCA1F84FC0057`)
- Metrics:
  `runs/layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s2/metrics.json`
  (`BFA8D0D531C2E9038AB67DF4028B03352B5CEE2DF332A1F4CDDC22FBFB1E8418`)
- Run summary:
  `runs/layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s2/run_summary.md`
  (`04002144A50C8D147D8E185982CA43BF0B94E1AE779A093D7FB432F91980AB7B`)
- State replay:
  `analysis/semantic_online_stability_a2_state_replay_20260715.json`
  (`F5ED7DF9176EA267EFC4D1349FC6648A88385B772266B47D67E98FEC6BC9742D`)
- Shared replay:
  `analysis/semantic_online_stability_a2_shared_replay_20260715.json`
  (`4EE48634E3F5676F5E133C90C5CDA0C11A107D3EB3615C996F5108ED80A00673`)

## Next Protocol Step

The four-run package is complete. The frozen primary aggregate, not any single
run, authorizes matched modern baselines. Non-leaking standard MuSiQue
dev/test and the 300-sample experiment remain later stages in the user's fixed
order.

## Runtime Interface Degradation

Managed `bash_exec`, artifact, and memory interfaces are unavailable. The run
directory, repository-local replay/audit files, report, and hashes are the
explicit durable fallback, not artifact-service records.
