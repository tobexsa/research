# Claim Risk v1.3.5 Answer Safety Guard Runtime Experiment

## Selected Idea

v1.3.5 keeps the v1.3.4 controller_policy_v1 stack and adds only a targeted answer safety guard. The guard blocks terminal `answer` when explicit conflict or wrong-target metadata is present, and routes wrong-target answers to structured repair when a repair signal and budget remain.

## User Requirements

- Start the next experiment after implementing and merging the answer safety guard.
- Do not claim runtime improvement until a fresh guarded runtime run is exported and evaluated.
- Keep the previous v1.3.4 runtime artifacts read-only for comparison.

## Run Contract

- Run id: `claim_risk_v1_3_5_answer_safety_guard_runtime`
- Runtime run name: `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think`
- Tier: `main/test`
- Date: `2026-07-07`
- Branch/commit: `main` at `34a2d69`
- Hypothesis: explicit answer safety guard reduces runtime unsafe answers versus v1.3.4 controller_policy_v1 without introducing schema issues or breaking diagnostic export.
- Null hypothesis: guarded runtime metrics are unchanged or worse; unsafe answers stay above the v1.3.4 baseline or repair/action accuracy regresses materially.
- Dataset: `data/musique_mvp_stratified45.jsonl`
- Diagnostic gold: `diagnostic_sets/claim_risk_v1/test_v4_strict.jsonl`
- Corpus/index: `data/musique_corpus.jsonl`, `indexes/faiss_musique_bge_base_en_v1_5.*`
- Config: `configs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think.yaml`
- Output run dir: `runs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`, OpenAI-compatible endpoint `https://api.siliconflow.cn/v1`

## Baseline Contract

Compare against:

- Runtime v1.3.4 controller_policy_v1 metrics:
  `diagnostic_sets/claim_risk_v1/results/current_claim_risk_controller_policy_v1_runtime_metrics_v4_strict.json`
- Prior headline:
  - `evaluated_count = 120`
  - `prediction_schema_issue_count = 0`
  - `oracle_action_accuracy = 0.4250`
  - `oracle_action_macro_f1 = 0.2203`
  - `missed_repair_opportunity_rate = 0.5376`
  - `over_abstain_rate = 0.2162`
  - `unsafe_answer_rate = 0.2308`

Offline replay is a target ceiling, not the direct runtime baseline:

- `oracle_action_accuracy = 0.6667`
- `unsafe_answer_rate = 0.1000`
- `missed_repair_opportunity_rate = 0.2366`

## Acceptance Gate

The runtime result is evaluable only if:

- `prediction_count = 120`
- `evaluated_count = 120`
- `prediction_schema_issue_count = 0`
- diagnostic export has `unmatched_count = 0`
- generated trajectories come from the v1.3.5 output dir, not the old v1.3.4 run dir

The policy remains no-go if:

- `unsafe_answer_rate > 0.1000`, or
- `oracle_action_accuracy < 0.4250` without a clear compensating safety gain, or
- schema/export integrity fails.

## Execution Steps

1. Preflight paths, API key presence, config uniqueness, and tests.
2. Run v1.3.5 runtime:
   `python scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_5_answer_safety_guard_controller_policy_v1_no_think.yaml`
3. Export predictions with source override set to the v1.3.5 run name.
4. Evaluate against `test_v4_strict.jsonl`.
5. Generate error attribution and repair miss analysis for the v1.3.5 prediction file.
6. Compare v1.3.5 against v1.3.4 runtime and offline replay.
7. Decide whether the next route is deeper target-slot/binder repair, repair lifecycle extraction, or disambiguation action support.

## Expected Outputs

- `runs/...v1_3_5.../trajectories.jsonl`
- `runs/...v1_3_5.../metrics.json`
- `runs/...v1_3_5.../run_summary.md`
- `diagnostic_sets/claim_risk_v1/predictions/current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_v4_strict.jsonl`
- `diagnostic_sets/claim_risk_v1/results/current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_metrics_v4_strict.json`
- `diagnostic_sets/claim_risk_v1/results/current_claim_risk_controller_policy_v1_runtime_v1_3_5_answer_safety_guard_metrics_v4_strict.md`
- `diagnostic_sets/claim_risk_v1/results/controller_policy_v1_runtime_v1_3_5_answer_safety_guard_decision_report_v4_strict.md`

## Caveats

- This guard only acts on explicit conflict/wrong-target metadata. It may not catch the known `Nieuwe Waterweg` wrong-target case if the runtime again marks it as sufficient final answer with no risk metadata.
- A better unsafe rate does not prove the repair lifecycle gap is solved. Repair recall and missed repair opportunity remain separate gates.
