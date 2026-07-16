# Online Stability G1 Generic-Only Results

Date: 2026-07-15
Protocol: `semantic_adapter_generic_online_stability_v1_20260715`
Run: `generic_stability_s1`
Status: `complete_valid`

## Verdict

G1 completed all 45 frozen stratified cases and passes every predeclared
per-run validity and safety gate. It is accepted as the generic-only
observation for paired block 1.

In block 1, A1 minus G1 is positive for terminal-correct-certificate rate,
Answer F1, and coverage. This is partial support only: the frozen protocol
requires the corresponding certificate and Answer F1 deltas to be positive in
both paired blocks. G2 is therefore the only next authorized online run; A2,
matched modern baselines, non-leaking dev/test, and the 300-sample experiment
remain locked.

## Identity And Completion

- Config:
  `configs/layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s1.yaml`
- Config SHA-256:
  `ACCF9356D7346C2A43B465A325606472E208070B8A7AE0FF01936EFD24C86C2D`.
- Dataset: 45 frozen rows, 45 unique IDs, exact membership.
- Completed / skipped: `45 / 0`.
- Runtime: `6591.9` seconds.
- Remaining run lock: none.
- Live strict-certificate steps: `0`, as required.

## Existing Performance Metrics

- Overall accuracy / EM: `0.3111 / 0.3111`.
- Answer F1: `0.3457`.
- Coverage: `0.4000`.
- Selective accuracy / F1: `0.7778 / 0.8642`.
- Average retrieval calls: `2.4000`.
- Wasted retrieval rate: `0.6667`.
- Final answered unsupported: `0`.

Hop slices:

| Slice | Answer F1 | Coverage | Selective F1 |
|---|---:|---:|---:|
| 2-hop | 0.5000 | 0.6000 | 0.8333 |
| 3-hop | 0.5370 | 0.6000 | 0.8950 |
| 4-hop | 0.0000 | 0.0000 | 0.0000 |

## Layer A: Certificate Completion

- Deterministic adapter marker applications: `0`, as required for generic-only.
- Ever-complete local certificates: `23/45`.
- Terminal-complete local certificates: `23/45`.
- Terminal-complete and correct certificates: `16/45`.

The seven complete-but-incorrect certificates remain visible in the frozen
certificate-correctness measure; completion is not treated as correctness.

## Layer B: Terminal Policy

- Final answers / abstentions: `18 / 27`.
- Answer with a terminal-complete certificate: `18`.
- Answer without a terminal-complete certificate: `0`.
- Abstain with a terminal-complete certificate: `5`.
- Shared-policy/live action mismatches: `0`.
- Live final answered unsupported: `0`.
- State terminal invariant violations: `0`.
- Unsafe typed-state transitions: `0`.
- Shared strict-off terminal invariant violations: `0`.
- Byte-identical shared-policy replay deterministic across three repeats:
  `true`.

The five complete-certificate abstentions are reported as terminal-policy
behavior, separately from certificate production. They are not converted into
answers post hoc.

## Shared-Certificate Diagnostic

- Counterfactual strict-eligible terminal rows: `0`.
- Strict on/off terminal action changes: `0`.
- Strict-on violations: `0`.
- Strict-off violations: `0`.

This remains diagnostic only; live G1 used strict acceptance off.

## Paired Block 1

| Frozen paired metric | A1 | G1 | A1 - G1 |
|---|---:|---:|---:|
| Terminal-correct-certificate rate | 0.4444 | 0.3556 | +0.0889 |
| Answer F1 | 0.4171 | 0.3457 | +0.0714 |
| Coverage | 0.4444 | 0.4000 | +0.0444 |

All three block-1 directions are positive. The result cannot establish stable
adapter advantage until the independent G2/A2 block is complete and passes
the same validity, safety, and sign gates. The protocol forbids an additional
confirmatory draw if the two blocks disagree.

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

Analyzer verdict for G1: `valid=true`, with no validity reasons.

## Replay Console Note

`replay_typed_hop_state.py` successfully wrote the full UTF-8 JSON artifact,
then the Windows GBK console failed while printing a non-GBK character. The
durable JSON parses successfully and contains zero terminal/state violations.
This is a post-write console-encoding issue, not an experimental or replay
failure.

## Evidence And Hashes

- Trajectory:
  `runs/layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s1/trajectories.jsonl`
  (`4127284482A5EE0D779FECF3D8F6FE21E53FA9674A4C600951EAE8BC53544A24`)
- Metrics:
  `runs/layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s1/metrics.json`
  (`BD052A361A0E32B8055897184137D719FFD6051B127BFFC501C913711647CF25`)
- Run summary:
  `runs/layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s1/run_summary.md`
  (`09F16BADBD69511A051F64E71C57D008DEBA58F5CB19886D12C0D39DC7ECFD10`)
- State replay:
  `analysis/semantic_online_stability_g1_state_replay_20260715.json`
  (`6864BEDC8C7AD3A1635B6F511ECFD14FAD4F6DE3F9B47F81A6DE15E8A38F8987`)
- Shared replay:
  `analysis/semantic_online_stability_g1_shared_replay_20260715.json`
  (`124F18DC81BED9654529364E11E7DD4F233E3672E407921856473C262F8EEFED`)
- Block-1 frozen-analyzer dry aggregate:
  `analysis/semantic_online_stability_block1_dry_aggregate_20260715.json`
  (`FB0896BA118675FD8D12AB5652D950AC6220A3D5466FCAEE1F3774C0D87829C5`)

The block-1 analyzer invocation is marked dry-run because the frozen analyzer
does not issue the primary protocol decision before all four runs exist. G1's
per-run validity and all reported layer values are nevertheless evaluated by
the frozen analyzer and are primary run evidence.

## Next Protocol Step

The only authorized next run is G2:

```powershell
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s2.yaml
```

A2 must not start until G2 completes and passes its own audit.

## Runtime Interface Degradation

Managed `bash_exec`, artifact, and memory interfaces are unavailable. The run
directory, repository-local replay/audit files, report, and hashes are the
explicit durable fallback, not artifact-service records.
