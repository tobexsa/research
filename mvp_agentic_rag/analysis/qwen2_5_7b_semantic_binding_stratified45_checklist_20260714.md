# Qwen2.5-7B R12 Model-Swap Baseline Checklist

## Identity

- Baseline id: `semantic-binding-r12`.
- Variant: `siliconflow-qwen2.5-7b-instruct-stratified45-free-key-r2`.
- Route: reproduce / model-swap comparison.
- Owner stage: baseline.

## Core

- [x] Baseline object, source R12 config, and route are explicit.
- [x] Dataset/split and metric contract are explicit.
- [x] Plan captures command path, outputs, acceptance condition, risks, and fallback.
- [x] Unique config and output identity are reserved.
- [x] Canonical config diff proves only run/output identity and four model fields changed.
- [x] Static config/entrypoint smoke passes.
- [x] Active R22 run has exited and released its lock.
- [ ] Real 45-row run is launched with durable stdout/stderr logs.
- [ ] Run reaches 45 unique trajectories.
- [ ] Metrics and summary files are complete and finite.
- [ ] Qwen2.5-7B results are compared with R12.
- [ ] Verification verdict and caveats are recorded.

## Blocked Launch Record

- 2026-07-14: the sandboxed launch reached the first API call but failed with
  Windows socket permission error `WinError 10013`; it produced zero
  trajectories and no metrics.
- The follow-up unsandboxed request was rejected because it would authenticate
  to SiliconFlow with the project API key and transmit 45 MuSiQue questions
  plus retrieved context to an external service without a fresh, explicit,
  informed data-transfer approval.
- The API key was present and loaded successfully; this is a network/data-
  transfer authorization blocker, not a missing-key or invalid-key verdict.
- Do not retry or route around the restriction. Resume the same frozen config
  only after the user explicitly authorizes this external transfer and API
  usage.
- 2026-07-14: explicit authorization received; the user added and selected
  `SILICONFLOW_API_KEY_FREE`. A clean r2 config/output identity preserves r1
  as failed-launch evidence while keeping the experiment protocol unchanged.
- The unsandboxed r2 request was still denied by the execution environment
  after explicit authorization because workspace questions and retrieved
  context would be exported to an untrusted external service. This is a hard
  environment-policy denial, not an API-key verdict; no workaround was tried.
- No local Qwen2.5-7B weights exist under `D:\research\model`, so an equivalent
  offline run is not currently available.
- Safe handoff launcher: `scripts/run_qwen2_5_7b_free_key_r2.cmd`. It contains
  no key and relies on the existing `.env` loader.
- User-side r2 launch reached SiliconFlow but failed before row 1 with
  `HTTP 403 Forbidden`; the key was present and the output contains zero
  trajectories and no metrics.
- The existing client does not persist the HTTP error body, so the precise
  provider reason is not yet classified. A minimal fixed-string access probe
  is available at `scripts/probe_siliconflow_free_key.py`; it sends no MuSiQue
  question or retrieved context and redacts the key from any response text.

## Closeout

- [ ] Concise baseline summary written.
- [ ] Next stage named explicitly.
