# Typed hop identity targeted8 R16 blocked incident

## Run contract

- Config: `configs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r16.yaml`
- Output: `runs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r16`
- R15 comparison contract is unchanged except
  `slot_binding_verifier_max_tokens: 1536 -> 2304`.
- Intended question: does the larger output budget eliminate all R15
  `finish_reason=length` parse failures while preserving safety and the Nissan
  recovery?

## Failure

R16 failed before completing the first sample on both the initial launch and
one auditable resume attempt. Both failures occurred on the first answer-model
request with `HTTP 403 Forbidden`.

Durable logs:

- `runs/logs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r16.err.log`
- `runs/logs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r16.retry1.err.log`

A separate `max_tokens=1` diagnostic request returned:

```json
{"status": 403, "code": 30001, "message": "Sorry, your account balance is insufficient"}
```

The API key was never printed or written to a new artifact.

## Artifact validity

- `trajectories.jsonl` exists but has `0` lines.
- No metrics, result table, or completed sample exists.
- The run therefore contains no evidence about the 2304-token hypothesis.
- R16 must be classified as `blocked / environment`, not success, failure of
  the algorithm, or a comparable experimental result.

## Recovery decision

Do not change code, data, metrics, config, or output directory. After the
SiliconFlow account balance is restored, resume the same R16 config and retain
the two failed logs. Use a new `retry2` stdout/stderr pair so the recovery is
auditable. Only after R16 reaches 8/8 should the length-truncation and targeted
acceptance gates be evaluated. Stratified45 remains unauthorized.

## 2026-07-14 resume attempt

The user explicitly resumed R16. Preflight reconfirmed that the config remains
a one-variable change relative to R15, the trajectory file still had zero
rows, no metrics existed, and no Python runner was active.

A `max_tokens=1` SiliconFlow probe returned HTTP 200, so the key itself was
valid. R16 was then resumed with new durable logs:

- `runs/logs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r16.retry2.out.log`
- `runs/logs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r16.retry2.err.log`

The real run again failed before writing sample 1. A follow-up short-prompt
probe using the actual answer setting `max_tokens=128` returned:

```json
{"status": 403, "code": 30001, "message": "Sorry, your account balance is insufficient"}
```

This distinguishes key validity from usable experiment balance: the account
can authorize a one-token probe but cannot authorize even the configured
128-token answer request. `trajectories.jsonl` remains at zero rows.

Do not lower `answer_max_tokens` or the R16 `slot_binding_verifier_max_tokens`
to fit the remaining balance. Either change would invalidate the frozen
single-variable comparison. After sufficient balance is restored, resume the
same config with new `retry3` logs.

## 2026-07-14 retry3 preflight

At 2026-07-14 10:20 +08:00, a new preflight again confirmed:

- the R15 -> R16 experiment delta is limited to the run/output identity and
  `slot_binding_verifier_max_tokens: 1536 -> 2304`;
- `trajectories.jsonl` still has zero rows and `metrics.json` is absent;
- no Python runner is active;
- neither retry3 log path exists.

The required `max_tokens=128` SiliconFlow authorization probe returned HTTP
403. This reproduces the already diagnosed insufficient-balance condition, so
the full runner was deliberately not launched. The retry3 stdout/stderr names
remain unused and can be used after balance recovery. R16 remains
`blocked / environment` and provides no evidence for or against the token
budget hypothesis. Stratified45 remains unauthorized.

Security note: during this preflight, a broad configuration search displayed
the active `.env` assignment in transient command output. The key value is not
copied into this incident or any run artifact, but it should be rotated before
the account is replenished or reused.

## 2026-07-14 recovery and closure

A later 128-token authorization probe returned HTTP 200. Several pre-run
launcher attempts were preserved rather than overwritten:

- retry3 and retry4 are zero-byte process-host failures;
- retry5 is an invalid PowerShell native-error-host attempt with no trajectory;
- retry6 records local sandbox network denial (`WinError 10013`) with no
  trajectory.

The identical frozen R16 config was then run with approved network access and
retry7 logs. It completed all eight samples in 1036.1 seconds with exit code
zero and zero-byte stderr. The canonical R16 output now contains eight
trajectory rows plus finite metrics.

The infrastructure blocker is closed. The experimental verdict is separate:
the 2304-token change eliminated all length truncation, but `1952` remained an
abstention and 4-hop accuracy remained zero. R16 is therefore partial and the
overall targeted gate failed. See
`analysis/typed_hop_identity_targeted8_results_20260714_r16.md`.
