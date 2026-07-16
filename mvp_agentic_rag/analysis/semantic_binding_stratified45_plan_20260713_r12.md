# Semantic-binding stratified45 plan (R12)

## Selected idea

Evaluate whether canonical verifier topology, semantic target binding, and
monotonic slot-state control remain functional and safe beyond targeted7. The
run freezes the R10/R11 method and changes only the dataset and unique output
identity.

## Non-negotiable constraints

- Dataset remains `data/musique_mvp_stratified45.jsonl`.
- Evaluator, metric definitions, dense index, top-k, maximum rounds, and model
  assignments remain unchanged.
- No sample-specific gold access or answer override.
- Do not overwrite or mutate any previous run directory.
- Preserve malformed-topology atomic rejection and parse-failure short circuit.
- UNKNOWN-like sentinels remain excluded from candidate transitions.
- Do not claim causal superiority against a differently configured historical
  run.

## Run contract

- Run ID: `layer1_siliconflow_qwen3_14b_semantic_binding_stratified45_20260713_r12`
- Tier: main/stratified45 generalization gate
- Dataset: fixed 45-sample stratified set
- Method: `claim_risk`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Reference 1: monotonic-state stratified45 R1
- Reference 2: semantic-binding targeted7 R10 plus Nissan targeted1 R11
- Primary metrics: overall accuracy, answer F1, coverage, selective accuracy,
  average retrieval calls, wasted retrieval rate, final unsupported rate.
- Structural metrics: topology primary reason distribution, verifier invocation,
  ambiguous mapping, hop binding failure, missing-hint mapping, and sentinel
  isolation.
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_binding_stratified45_20260713_r12`

## Acceptance gate

1. 45 rows and 45 unique `(id, method)` keys;
2. finite metrics and complete trajectory files;
3. `final_answered_unsupported_rate=0`;
4. no silent consumption of malformed topology or parse-failure transitions;
5. real verifier invocation/topology diagnostics are present on every state step;
6. report aggregate and per-hop deltas honestly, including regressions.

## Execution

1. Confirm local suite and Nissan R11 gate (already passed).
2. Start one uniquely named R12 process with durable stdout/stderr logs.
3. Monitor completed row count and errors without launching a duplicate process.
4. If a transient API failure stops the process, resume the same frozen config;
   the runner must skip completed keys.
5. Validate outputs and write a result report before deciding any next scale-up.

## Revision log

- 2026-07-13: Created after targeted semantic gate and Nissan provenance
  closure passed.
