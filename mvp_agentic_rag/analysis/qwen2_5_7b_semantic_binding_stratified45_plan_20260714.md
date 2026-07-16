# Qwen2.5-7B R12 Model-Swap Baseline Plan

Date: 2026-07-14

## 1. Core Contract

- Quest goal: rerun the current best R12 semantic-binding baseline with `Qwen/Qwen2.5-7B-Instruct`.
- User requirement: replace the model and rerun the full comparable experiment.
- Non-negotiable constraints: preserve the R12 dataset, corpus, retriever, controller flags, budgets, evaluator, and safety metrics; use a unique run identity; do not overwrite R12 or active R22 outputs.
- Route: reproduce a supplementary model-swap baseline.
- Baseline id: `semantic-binding-r12`.
- Variant id: `siliconflow-qwen2.5-7b-instruct-stratified45-free-key-r2`.
- Source baseline config: `configs/layer1_siliconflow_qwen3_14b_semantic_binding_stratified45_20260713_r12.yaml`.
- Task: MuSiQue answerable multi-hop QA with claim-risk selective answering.
- Dataset/split: `data/musique_mvp_stratified45.jsonl`, 45 rows; SHA-256 `2B4A0DFAD40AC8B120FF59862FCBF216C5AD419EC7E2783E35534281653D63A5`.
- Metric contract: overall accuracy/EM, answer F1, coverage, selective accuracy/F1, average retrieval calls, wasted retrieval rate, and final answered unsupported rate.
- Expected entrypoint: `scripts/run_layer1_skeleton.py --config <new-config>`.
- Expected outputs: unique run directory containing `trajectories.jsonl`, `metrics.json`, `metrics.md`, and `run_summary.md`, plus durable stdout/stderr logs.
- Acceptance condition: 45 unique trajectories; complete finite metrics; stderr contains no fatal error; final result is explicitly compared with R12 without hiding protocol caveats.
- Cheapest fallback: preserve completed rows and resume the same frozen config after a transient endpoint failure.

## 2. Execution Path

- Working directory: `D:\research\mvp_agentic_rag`.
- Environment: existing repository Python route and `.env`-provided `SILICONFLOW_API_KEY`; no dependency changes.
- Required downloads: none; dense BGE index/model are local.
- Smoke decision: configuration/static smoke only, because the model id is user-specified and a separate paid one-row run would add stochastic/API cost without validating the 45-row comparison.
- Main config: `configs/layer1_siliconflow_qwen2_5_7b_instruct_semantic_binding_stratified45_20260714_free_key_r2.yaml`.
- Main output: `runs/layer1_siliconflow_qwen2_5_7b_instruct_semantic_binding_stratified45_20260714_free_key_r2`.
- Logs: `runs/logs/layer1_siliconflow_qwen2_5_7b_instruct_semantic_binding_stratified45_20260714_free_key_r2.{out,err}.log`.
- Fastest failure signals: model-not-found/permission HTTP response, repeated HTTP 403, output lock failure, or no new durable trajectory after the normal per-row API window.

## 3. Risks And Revision

- Main risks: SiliconFlow access/balance/rate limiting; Qwen2.5 response-format differences; current source tree contains post-R12 fixes, so this is config-level model isolation rather than a byte-identical historical-code rerun.
- Concurrency rule: wait for the active R22 external run to release its output lock before launch; do not interrupt it.
- Plan revision trigger: any required change beyond model fields, run identity, output identity, or a transparent resume of the same frozen config.

## 4. Verification Plan

- Required result files: `trajectories.jsonl`, `metrics.json`, `metrics.md`, `run_summary.md`.
- Required trajectory checks: exactly 45 rows and 45 unique `(id, method)` keys.
- Required model check: all four LLM roles use `Qwen/Qwen2.5-7B-Instruct`.
- Comparability check: canonicalized config differs from R12 only in `run_name`, `output_dir`, and the four model fields.
- Downgrade condition: incomplete run, protocol drift, non-finite/missing metrics, or repeated endpoint failure.

## 5. Checklist Link

- `analysis/qwen2_5_7b_semantic_binding_stratified45_checklist_20260714.md`
- Next item: launch the explicitly authorized r2 run with
  `SILICONFLOW_API_KEY_FREE` and monitor durable progress.

## 6. Revision Log

| Time | What changed | Why | Impact |
|---|---|---|---|
| 2026-07-14 | Initial model-swap contract | User requested Qwen2.5-7B rerun | New independent 45-row run; R12 remains read-only |
| 2026-07-14 | Launch paused for explicit informed approval | SiliconFlow call sends questions and retrieved context externally; sandboxed socket was denied and unsandboxed review rejected the unapproved transfer | Frozen config remains unchanged at 0/45; no workaround permitted |
| 2026-07-14 | User supplied and explicitly selected `SILICONFLOW_API_KEY_FREE` | Continue the same disclosed SiliconFlow transfer with a dedicated credential | Preserve r1 failure evidence; use new r2 config/output identity |
| 2026-07-14 | r2 external run denied despite explicit authorization | Execution policy still classifies export of questions/retrieved context to SiliconFlow as high-risk | Do not retry or bypass; provide a key-free local launcher for user-side execution |
| 2026-07-14 | User-side r2 launch returned HTTP 403 before row 1 | Key loading and network reachability succeeded; provider rejected the request | Run a fixed-string access probe to capture the provider error code before changing credentials or model |
