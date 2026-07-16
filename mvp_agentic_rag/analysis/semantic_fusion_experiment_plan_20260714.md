# Semantic Fusion Experiment Plan

Date: 2026-07-14

## 1. Objective

- Run ID: `semantic_fusion_gain_loss12_20260714_r21`.
- Selected idea: retain the evidence-certified typed-hop controller only when
  runtime provenance establishes a complete strict certificate; otherwise use
  the R12-compatible generic path. Malformed, parse-failed, sentinel, hard-
  conflicted, or non-local evidence remains fail-closed with no compatibility
  fallback.
- User route, in order:
  1. freeze and pass the 12-case dual-lane gate;
  2. run Fusion and generic-only stratified45;
  3. add component ablations, repeats, and matched modern baselines;
  4. establish a non-leaking standard MuSiQue dev/test evaluation;
  5. only then consider 300 samples or a paper-facing main experiment.
- Non-negotiable constraints:
  - route without sample ID, gold answer, gold decomposition, or gold support;
  - do not change the source samples, corpus, retriever, model, top-k, three-
    round budget, evaluator, or final safety metric;
  - do not relax malformed, parse-failure, sentinel, conflict, or evidence-
    locality invariants;
  - do not launch stratified45 until deterministic tests/replay and the fixed
    12-case real gate pass;
  - preserve R12 and R20 runs/configs as read-only evidence.
- Research question: can an applicability-aware dual-lane controller retain
  the five R20 certificate gains and recover the seven R12 regressions without
  unsupported final answers or additional execution budget?
- Null hypothesis: runtime-only routing cannot separate the gain and loss
  cases; fusion either loses strict-certificate gains or repeats R20's generic
  coverage regression.
- Alternative hypothesis: certificate provenance and fail-closed safety state
  are sufficient to activate strict enforcement only where it is beneficial.

## 2. Baseline And Comparability

- Baseline: R12 semantic-binding stratified45.
- Strict comparator: R20 semantic-certificate stratified45.
- Source dataset: `data/musique_mvp_stratified45.jsonl`, 45 rows, SHA-256
  `2B4A0DFAD40AC8B120FF59862FCBF216C5AD419EC7E2783E35534281653D63A5`.
- Fixed gate output: `data/musique_semantic_fusion_gain_loss12_20260714.jsonl`,
  SHA-256 `04F15DB77255C0DA10B5F811081D7E2B0ADC3B11572F1D4336959E4654E090FB`.
- Fixed gate: five R20-only normalized-correct gains plus seven R12-only
  normalized-correct losses, derived with the repository evaluator.
- Primary gate: all five gains retained and all seven losses recovered.
- Hard safety: `final_answered_unsupported_rate = 0`; zero sentinel candidate
  state/transitions; zero malformed/parse-failed topology mutation; no hard-
  conflict or non-local-evidence compatibility fallback.
- Required metrics: accuracy/EM, answer F1, coverage, selective accuracy/F1,
  average retrieval calls, wasted retrieval rate, final unsupported rate,
  lane counts, lane reasons, per-hop metrics, and gain/loss retention.
- R12 config hash: `EE6845C722E28790DE5543ADFC88D698C9092C2944AABD80EF352405CB8EB477`.
- R20 config hash: `1FE4D3A07A64718679FBF1B267C66C627D02D9B1F1C1E41F9F26B93E312F6966`.
- Comparability risks: stochastic verifier output; R20 uses a 2304-token slot
  verifier versus R12's 1536; targeted sample selection can overfit routing;
  relation-specific deterministic certificates can mimic generality.

## 3. Fixed Gate Membership

R20 gains to retain:

- `2hop__136179_13529` (`June 1982`)
- `2hop__167577_31122` (`18th`)
- `3hop1__136129_87694_124169` (`1952`)
- `4hop1__161810_583746_457883_650651` (`NBC`)
- `4hop1__236903_153080_33897_81096` (`Mario Andretti`)

R12 losses to recover:

- `2hop__142699_67465` (`March 11, 2011`)
- `2hop__194469_83289` (`Matt Bennett`)
- `2hop__23459_35124` (`450`)
- `2hop__247353_55227` (`Maria Bello`)
- `3hop1__103881_443779_52195` (`Francisco Guterres`)
- `3hop1__140786_2053_5289` (`Oriole Records.`)
- `3hop1__144439_443779_52195` (`Francisco Guterres`)

## 4. Code Translation Plan

| Path | Current role | Planned change | Why | Risk |
| --- | --- | --- | --- | --- |
| `state_controller.py` | strict canonical-state controller | add a pure runtime-only fusion-lane classifier | centralize auditable lane selection | unsafe generic fallback |
| `claim_risk_agent.py` | orchestration and final action | apply state enforcement only in strict/no-fallback lanes and log decisions | stop strict state from globally blocking valid legacy answers | hidden typed-prompt effect remains |
| `tests/test_state_controller.py` | controller regressions | add strict/generic/no-fallback classifier tests | freeze routing contract | fixtures may miss live metadata |
| `tests/test_claim_risk_agent.py` | integration regressions | add terminal/repair lane behavior and no-gold tests | validate actual orchestration | large test surface |
| `scripts/build_semantic_fusion_gate.py` | new data builder | deterministically materialize the fixed 12 rows | reproducible membership | accidental overwrite |
| `scripts/replay_semantic_fusion_gate.py` | new replay audit | audit R12/R20 lane signals and gate expectations | cheap discriminative preflight | replay is not live evidence |
| `configs/*semantic_fusion_gain_loss12*` | new run config | derive from R20 with only run/data/output and fusion flag changed | matched real run | API stochasticity |

## 5. Execution Design

- Minimal experiment: pure lane-classifier unit tests plus stored-trajectory
  replay on the fixed 12 cases.
- Smoke: focused state-controller, execution-state, verifier, and claim-risk
  tests; then a bounded fake-LLM or offline replay.
- Real gate: one unique SiliconFlow Qwen3-14B run on all 12 fixed rows.
- Full next run: only after the real gate passes, freeze Fusion and generic-
  only stratified45 configs and run them sequentially.
- Stop condition: any unsafe lane fallback, missing/duplicate gate row,
  incomplete metrics, final unsupported answer, or budget/protocol drift.
- Abandonment condition: the runtime-only classifier cannot retain strict gains
  and generic losses without sample/relation allowlists, or two justified
  implementations fail the same fixed gate.
- Strongest alternative: the regression is caused primarily by the typed
  verifier prompt/output distribution rather than state-controller enforcement;
  if so, a single-call post-hoc lane overlay is insufficient and a separate
  generic verifier call or earlier applicability prediction is required.

## 6. Runtime Strategy

- Focused tests: `python -m pytest tests/test_state_controller.py
  tests/test_slot_execution_state.py tests/test_claim_risk_agent.py -q`.
- Full tests before network: `python -m pytest -q`, then compileall and scoped
  diff checks.
- Runner: use the existing repository CLI/config path and unique run/log names.
- Expected budget: local tests and replay first; approximately one 12-sample
  paid API run only after all deterministic gates pass.
- Frozen R21 config SHA-256:
  `CB38C8C58906E0B66140D92D3C8AF7CD549EA72841EEA8FDDE1CA5D84A9B461C`.
- Frozen R23 config SHA-256:
  `56B55143AF28532C75CE685E85A9BB472CB36DEFF11CD81136AB07BCD1533F91`.
- R23 differs from R22 only in `run_name` and `output_dir`; model,
  retriever, top-k, three-round budget, dataset, corpus, and evaluator remain
  fixed.
- Frozen R24 config SHA-256:
  `C675691E5016F78508381C9C5806A214DE0DAABAAF6B619A90AF063A89CD8E17`.
- R24 differs from R23 only in `run_name` and `output_dir`; all comparison
  settings remain fixed.
- Monitoring: check process/log/row counts at about 60, 120, 300, 600, and
  then 1800 seconds; kill only for explicit invalidity, fatal error, or a
  superseding contract failure.
- Outputs: `data/`, `configs/`, `runs/`, `runs/logs/`, and `analysis/` under
  this repository. Failed attempts are preserved under unique names.

## 7. Fallbacks And Recovery

- Endpoint/network failure: preserve completed rows and logs; resume the same
  frozen config only if the runner's completed-key contract remains valid.
- Environment failure: use the already working repository interpreter; do not
  install or upgrade dependencies during this gate.
- Smoke failure: repair forward from R20; do not reset the dirty worktree.
- Non-comparable real run: mark partial and do not advance to stratified45.
- If typed verifier behavior, not enforcement, causes losses: record the gate
  failure and redesign lane selection before the verifier call; do not mask it
  with relation/sample special cases.

## 8. Checklist Link

- `analysis/semantic_fusion_experiment_checklist_20260714.md`
- Next unchecked item: finish lane integration tests and deterministic replay.

## 9. Revision Log

| Time | Change | Reason | Impact |
| --- | --- | --- | --- |
| 2026-07-14 | Initial five-stage contract and fixed 12-case gate | user authorized ordered execution after R20 mixed result | no runtime or metric change |
| 2026-07-14 | Materialized immutable 12-row gate | source hash and gain/loss membership verified | 12 rows: six 2-hop, four 3-hop, two 4-hop |
| 2026-07-14 | Froze R21 real-run config | R20 settings preserved; only run/data/output and fusion flag differ | ready for one 12-case API gate |
| 2026-07-14 | Real R21 launch blocked before row 1 | sandbox denied network, then safety review required explicit approval for sending questions/retrieved passages to external SiliconFlow | phase 1 remains partial; no stratified45 authorized |
| 2026-07-14 | R21 completed 8/12 then repeated HTTP 403 | endpoint failure preserved partial rows; gate already failed on `18th` and exact-date loss | analyze, repair, and rerun all 12 under R22; phase 2 blocked |
| 2026-07-14 | R22 deterministic closure | ordinal equivalence prevents false conflict; unique local binding date restores full precision; 622 tests and 27 subtests pass | authorize one unique R22 12-case retry when endpoint accepts requests |
| 2026-07-14 | R22 completed / gate failed | 5/5 gains retained, 3/7 losses recovered, final unsupported zero | phase 2 blocked; isolate structured surface handoff and candidate/hop conflict scope for R23 |
| 2026-07-14 | R23 deterministic preflight passed | hypothesis-only entailment scope removes the false Indonesia/East Timor hard conflict; generic repair recovery is limited to a valid attributed repair with budget and conflict-free canonical state; full suite 632/27 | freeze one unique R23 12-case run; phase 2 remains blocked pending 5/5 + 7/7 + unsupported 0 |
| 2026-07-14 | R23 completed / gate failed | 5/5 gains, 2/7 losses, final unsupported zero; failures isolate post-slot surface overwrite, stale state-only candidate handoff, typed-accepted binding instability, and unnatural repair relation rendering | validate one bounded R24 structured-handoff/query-surface revision; keep all safety and comparability constraints fixed |
| 2026-07-14 | R24 completed / phase-1 gate passed | 5/5 gains, 7/7 losses, final unsupported zero, unsafe replay transitions zero | authorize phase 2 only: matched Fusion and generic-only stratified45 runs |
