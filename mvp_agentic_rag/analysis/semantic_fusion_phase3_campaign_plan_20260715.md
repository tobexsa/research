# Semantic Fusion Phase-3 Campaign Plan

Date: 2026-07-15

## 1. Objective

- Campaign id: `semantic_fusion_phase3_20260715`
- Parent runs: R25 Fusion and matched R26 generic-only on stratified45.
- Main claim under test: the R25 gain over R26 is attributable to the strict
  certificate lane, deterministic adapters, or their interaction, and is not
  merely a one-run API fluctuation.
- User's fixed order: component ablations, independent repeated runs, then
  matched modern baselines. Non-leaking standard MuSiQue evaluation remains a
  later phase, and 300-sample or paper experiments remain last.
- Campaign outcome needed: a complete 2x2 component attribution, repeatability
  summary, and at least one fairly matched modern baseline package with an
  explicit comparability verdict.
- Selected outline ref: not applicable; this is a pre-paper evidence campaign.
- Paper experiment matrix: not applicable.
- Current frontier: run R27 and R28 serially, then aggregate the 2x2 matrix.

## 2. Boundary And Comparability

- Dataset: `data/musique_mvp_stratified45.jsonl`.
- Dataset SHA-256:
  `2B4A0DFAD40AC8B120FF59862FCBF216C5AD419EC7E2783E35534281653D63A5`.
- Fixed conditions: corpus, dense index, embedding model, Qwen3-14B answer and
  verifier backends, token budgets including the 2304-token slot verifier,
  top-k 5, three-round budget, prompts, retriever, evaluator, and metric
  definitions.
- Variables in the component matrix:
  `claim_evidence_fusion_strict_certificate_enabled` and
  `slot_binding_verifier_deterministic_bindings` only.
- API runs are serial, use fresh output directories, and never resume rows from
  another variant.
- Required safety boundary: final answered unsupported remains zero; malformed,
  parse failure, sentinel, genuine canonical conflict, and non-local evidence
  remain fail-closed through `no_fallback`.
- These 45 cases are a targeted development surface. They are not standard
  non-leaking MuSiQue dev/test results and cannot be compared directly with
  published paper numbers on other splits or protocols.

## 3. Slice Plan

| Exp id | Slice id | Tier | Class | Type | Research question | Changed factors | Priority | Code change? | Extra baseline? |
|---|---|---|---|---|---|---|---|---|---|
| P3-A1 | R27 adapter-only | main_required | claim-carrying | ablation | What do deterministic adapters add under generic routing? | strict off, adapters on | 1 | no | no |
| P3-A2 | R28 strict-only | main_required | claim-carrying | ablation | What does the strict lane add without deterministic adapters? | strict on, adapters off | 2 | no | no |
| P3-R1 | Fusion independent repeats | main_required | claim-carrying | robustness | Is R25 performance stable across fresh API responses? | independent reruns only | 3 | no | no |
| P3-R2 | Generic-only independent repeats | main_required | claim-carrying | robustness | Is the R25-R26 delta stable across fresh API responses? | independent reruns only | 4 | no | no |
| P3-B1 | Matched modern baseline(s) | main_required | supporting | baseline | Does Fusion remain competitive under the same 45-case runtime and evaluator contract? | method only | 5 | possibly | yes |

R25 (`strict=on`, `adapters=on`) and R26 (`strict=off`, `adapters=off`)
already fill two cells of the component matrix. R27 and R28 fill the remaining
cells without introducing another factor.

## 4. Hypotheses And Decision Value

- H1: strict routing and deterministic adapters have complementary value; the
  full R25 cell should exceed at least one single-component cell without
  increasing unsupported answers.
- H2: if R27 approaches R25 while R28 approaches R26, most observed gain comes
  from adapters. The reverse pattern attributes more value to strict routing.
- H3: if both single-component cells underperform R25, a positive interaction
  is plausible. If either exceeds R25, the full combination may contain a
  negative interaction and the Fusion claim must be narrowed.
- H4: a robust Fusion claim requires a positive paired mean delta over
  generic-only across independent runs, not merely the original R25/R26 pair.

## 5. Assets And Dependencies

- Available parent configs and complete outputs: R25 and R26.
- Available analysis: paired R25/R26 comparison and state replays.
- External dependency: SiliconFlow API credentials and endpoint availability.
- Baseline dependency: source identity, code path, split/metric contract, and
  feasibility must be audited before any modern baseline is accepted.
- Baseline storage: reproduce under `baselines/local/<baseline_id>/` or attach
  under `baselines/imported/<baseline_id>/`; include setup, execution,
  verification, and metric-contract evidence.
- Runtime fallback: this environment lacks the skill's managed `bash_exec`,
  artifact, and memory interfaces. PowerShell plus durable configs, logs,
  analysis reports, and replay JSON are the explicit local substitute.

## 6. Execution Strategy

1. Freeze R27/R28 and mechanically prove that each differs from R25 only in
   identity and the intended component switch.
2. Run focused tests, full tests, compileall, config parsing, hashes, and output
   non-existence checks.
3. Run R27 to completion and audit rows, metrics, lane markers, deterministic
   adapter markers, safety replay, and hashes before starting R28.
4. Run and audit R28 under the same procedure.
5. Aggregate the 2x2 main effects, interaction, per-hop slices, per-sample
   correctness, retrieval cost, and safety metrics.
6. Freeze fresh independent repeat configs. Because the API exposes no reliable
   seed control, report these as independent repeated runs, never seeded runs.
7. Give R25 Fusion and R26 generic-only at least two additional fresh runs each
   when endpoint/cost constraints permit, producing three observations per main
   variant including the originals. Report mean, sample standard deviation,
   range, and per-example stability.
8. Only after repeats are complete, establish matched modern baselines using an
   explicit task/dataset/split/preprocessing/evaluator/metric contract. Published
   numbers alone do not satisfy this slice.

Monitoring cadence for each external run: inspect after the first rows, then at
roughly 60, 120, 300, 600, and 1800 seconds while checking row growth, log
freshness, process state, duplicate IDs, and expected outputs. Stop a run only
when it is invalid, stalled beyond endpoint retry behavior, or violates the
frozen contract.

Frozen component configs:

- R27 adapter-only SHA-256:
  `14F20854C5F4C89E27CAAF8D044BD1307AB80BE15C3E1E8E1B33BAA5CE192D95`.
- R28 strict-only SHA-256:
  `2B00BD5963951D6519A9ACD788013ACBE12A5AB4268DD63F8D448610A45D5959`.

## 7. Reporting And Gates

Every slice must report EM, Answer F1, coverage, selective accuracy/F1, average
retrieval calls, wasted retrieval, final unsupported, per-hop metrics, row and
ID integrity, relevant lane/adapter markers, and a safety replay.

- Stable support: Fusion has positive repeat-aggregated paired performance over
  generic-only, unsupported remains zero, and the 2x2 result has an interpretable
  component or interaction pattern.
- Contradiction: the repeat-aggregated delta is non-positive, safety regresses,
  or the component matrix shows R25's apparent gain was not attributable to the
  enabled components.
- Unresolved ambiguity: run variance or endpoint failures prevent a credible
  repeat comparison.
- Hard stop: duplicate/missing rows, config drift, incomplete/non-finite metrics,
  final unsupported above zero, or forbidden lane/adapter activation.
- Phase gate: do not start standard non-leaking MuSiQue dev/test until component
  ablations, repeats, and matched modern baselines all have durable verdicts.

## 8. Checklist Link

- Checklist: `analysis/semantic_fusion_phase3_campaign_checklist_20260715.md`.
- Next unchecked item: mechanically validate the frozen R27/R28 configs.

## 9. Revision Log

| Date | Change | Reason | Impact |
|---|---|---|---|
| 2026-07-15 | Created phase-3 charter and complete 2x2 design | R25/R26 completed phase 2 and authorized phase 3 | R27/R28 become the first executable slices |
| 2026-07-15 | Froze and locally verified R27/R28 | Mechanical config assertions, focused/full tests, compileall, and whitespace checks passed | R27 is cleared for serial launch |
| 2026-07-15 | Completed and accepted R27 adapter-only | 45 unique rows, F1 0.4444, coverage 0.4667, unsupported 0, strict lane 0, safe replay | Frozen R28 becomes the next and only active slice |
| 2026-07-15 | Completed but rejected R28 strict-only | Unsupported final rate 0.0500 and zero observed strict-lane activation despite 45 complete rows | Component campaign stops before repeats; safety/identifiability decision required |
| 2026-07-15 | Selected post-R28 repair and activation-aware attribution route | Preserve positive R25/R27 evidence while fixing the terminal safety hole and eliminating zero-activation causal ambiguity | Follow `semantic_fusion_phase3_r28_next_decision_20260715.md`; repeats remain blocked |
