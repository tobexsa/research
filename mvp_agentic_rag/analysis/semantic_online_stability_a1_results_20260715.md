# Online Stability A1 Adapter-Only Results

Date: 2026-07-15
Protocol: `semantic_adapter_generic_online_stability_v1_20260715`
Run: `adapter_stability_s1`
Status: `complete_valid`

## Verdict

A1 completed all 45 frozen stratified cases and passes every predeclared
per-run validity and safety gate. It is accepted as the adapter-only observation
for paired block 1. This does not yet establish an adapter advantage because
G1, G2, and A2 have not been completed or aggregated.

G1 becomes the only next authorized online run. G2 and A2 remain locked behind
the protocol order.

## Identity And Completion

- Config:
  `configs/layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s1.yaml`
- Config SHA-256:
  `DE5A54A354E3F89EA88E418D5A6979E302DFA1E65CB2EF4449542F8CF00E1986`.
- Dataset: 45 frozen rows, 45 unique IDs, exact membership.
- Completed / skipped: `45 / 0`.
- Runtime: `5482.4` seconds.
- Remaining run lock: none.
- Live strict-certificate steps: `0`, as required.

## Existing Performance Metrics

- Overall accuracy / EM: `0.4000 / 0.4000`.
- Answer F1: `0.4171`.
- Coverage: `0.4444`.
- Selective accuracy / F1: `0.9000 / 0.9385`.
- Average retrieval calls: `2.3556`.
- Wasted retrieval rate: `0.5778`.
- Final answered unsupported: `0`.

Hop slices:

| Slice | Answer F1 | Coverage | Selective F1 |
|---|---:|---:|---:|
| 2-hop | 0.6667 | 0.7333 | 0.9091 |
| 3-hop | 0.5179 | 0.5333 | 0.9712 |
| 4-hop | 0.0667 | 0.0667 | 1.0000 |

These metrics are recorded for later paired aggregation. No comparison verdict
is drawn from A1 alone.

## Layer A: Certificate Completion

- Deterministic adapter marker applications: `19`.
- Ever-complete local certificates: `25/45`.
- Terminal-complete local certificates: `24/45`.
- Terminal-complete and correct certificates: `20/45`.

The difference between terminal-complete and terminal-correct certificates is
reported explicitly. A complete certificate is not automatically assumed to
be a correct certificate.

## Layer B: Terminal Policy

- Final answers / abstentions: `20 / 25`.
- Answer with a terminal-complete certificate: `20`.
- Answer without a terminal-complete certificate: `0`.
- Abstain with a terminal-complete certificate: `4`.
- Terminal answer-to-abstain downgrades: `0`.
- Shared-policy/live action mismatches: `0`.
- Live final answered unsupported: `0`.
- State terminal invariant violations: `0`.
- Unsafe typed-state transitions: `0`.
- Shared strict-off terminal invariant violations: `0`.
- Byte-identical shared-policy replay deterministic across three repeats:
  `true`.

The four complete-certificate abstentions are retained as policy/translation
evidence for later cross-run analysis. They are not silently converted into
answers and do not invalidate A1 under the frozen protocol.

## Shared-Certificate Diagnostic

- Counterfactual strict-eligible terminal rows: `5`.
- Strict on/off terminal action changes: `0`.
- Strict-on violations: `0`.
- Strict-off violations: `0`.

This remains a diagnostic only; live A1 used strict acceptance off.

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

Analyzer verdict for A1: `valid=true`, with no validity reasons.

## Replay Console Note

`replay_typed_hop_state.py` successfully wrote the full UTF-8 JSON artifact,
then the Windows GBK console failed while printing one non-GBK character. The
durable JSON parses successfully and contains zero terminal/state violations.
This is a console-encoding issue after artifact creation, not an experimental
or replay failure.

## Evidence And Hashes

- Trajectory:
  `runs/layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s1/trajectories.jsonl`
  (`44BC2EDFD2D5C86AD53DD591F69B8BC39C7350E2BB801F4C4FE4E5332D0197E0`)
- Metrics:
  `runs/layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s1/metrics.json`
  (`39175CDC6EC044AF72C37F69B48BF0B357000610E97293F98C0D546AD1B7C370`)
- Run summary:
  `runs/layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s1/run_summary.md`
  (`FBA6ED65CADF1986AB90487141C036972ADFD0F1AC80BE6E2B7AF5A6F84A7D26`)
- State replay:
  `analysis/semantic_online_stability_a1_state_replay_20260715.json`
  (`43B65CA5F7F5DA2CFC91830961F5F4F0340DC46F7BBDB03C48465E0C1EEB704D`)
- Shared replay:
  `analysis/semantic_online_stability_a1_shared_replay_20260715.json`
  (`C3BE53B19B73DBE32DCD1BEEA6E98E59E9D83971987B9E7F0BD0C6C3CE018361`)
- Frozen analyzer audit:
  `analysis/semantic_online_stability_a1_audit_with_historical_generic_20260715.json`
  (`1019CFDD619CA668CDB58A484422B8A5F883F6EBD92B101ADDBB8CDF56364C5E`)

The audit file uses historical R26 only to satisfy the frozen analyzer's dry-run
schema. Its combined historical comparison totals are non-primary; all A1
validity and layer values above come from the A1 run record itself.

## Next Protocol Step

The only authorized next run is G1:

```powershell
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s1.yaml
```

No block-1 adapter-minus-generic conclusion may be drawn until G1 completes
and passes its own audit.

## Runtime Interface Degradation

Managed `bash_exec`, artifact, and memory interfaces were unavailable. The run
directory, repository-local replay/audit files, report, and hashes are the
explicit durable fallback, not artifact-service records.
