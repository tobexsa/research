# Semantic Fusion Terminal Safety Repair Plan

Date: 2026-07-15

## 1. Objective

- Run id: `semantic_fusion_terminal_safety_repair_20260715`
- Tier: `auxiliary/dev` safety and mechanism repair.
- Selected idea: make every generic terminal answer pass canonical-state,
  verifier, slot-binding, local-evidence, and critical-ancestor closure checks.
  Preserve strict-certificate acceptance and safe generic repair recovery.
- User requirement: implement the previously approved post-R28 plan before any
  repeats, baselines, standard dev/test, or 300-case run.
- Non-negotiable constraints: no sample IDs, gold answers, gold decompositions,
  or gold support in routing; no evaluator changes; preserve R25-R28 outputs as
  read-only evidence; fail closed on uncertainty.
- Research question: can a general terminal guard remove the R28 unsupported
  handoff without erasing legitimate strict or generic supported answers?
- Null hypothesis: the failure cannot be blocked without broad regressions.
- Alternative hypothesis: the failure is localized to generic terminal answer
  authorization and can be blocked by existing runtime evidence.

## 2. Baseline And Comparability

- Last-known-good safety reference: R24 fixed-12 and R25 full Fusion.
- Failure reference: R28 sample `4hop1__151650_5274_458768_33632`.
- Dataset contract: existing fixed-12 and stratified45 only; no new dataset.
- Primary gate: final answered unsupported remains zero.
- Required supporting gates: 5/5 gains, 7/7 losses, zero terminal invariant
  violations, and no reduction in evidence-locality/conflict protections.
- Comparability risk: any code change affects later online runs, so all accepted
  post-fix online comparisons must use the repaired version.

## 3. Code Translation Plan

| Path | Current role | Planned change | Why | Risk |
|---|---|---|---|---|
| `agents/claim_risk_agent.py` | Terminal lane handoff | Require generic answers to pass state/verifier/binding/ancestor checks; keep safe repair recovery | Closes R28 fail-open | Over-abstention |
| `slot_execution_state.py` or a pure helper | Canonical hop state | Expose critical ancestor-closure eligibility without deleting local verified facts | Separates local truth from global answer eligibility | Incorrect handling of optional hops |
| `scripts/replay_typed_hop_state.py` | Structural replay | Add terminal answer invariants | Existing replay missed R28 | Historical metadata may be sparse |
| `tests/test_state_controller.py` | Router/controller contract | Add R28 negative and supported positive terminal cases | Deterministic falsification | Test fixture must mirror real semantics |
| replay-focused tests | Audit contract | Assert the R28 row is flagged before repair and counterfactually blocked | Prevents audit regression | Avoid gold dependence |

## 4. Execution Design

- Minimal experiment: pure terminal-controller unit tests using a generic lane,
  incomplete state, unclear verifier, unsupported slot binding, and original
  abstention.
- Positive control: complete state, supported local-evidence binding, sufficient
  verifier, and no abstention signal remains answerable.
- Smoke: focused state-controller, claim-risk-agent, slot-state, and replay tests.
- Full validation: entire pytest suite, compileall, config/diff/whitespace checks,
  then offline replay of R25-R28.
- Paid pilot only after local gate: offending case, then frozen 12-case gate.
- Stop condition: any gold/sample-specific branch, legitimate positive control
  blocked, prior fixed-12 regression, or unsupported above zero.
- Abandonment condition: two bounded repairs fail the same deterministic state.
- Strongest alternative: the bug arises earlier from stale state construction;
  if the terminal guard is insufficient, move ancestor eligibility into the
  state reducer rather than stacking terminal exceptions.

## 5. Runtime Strategy

- Focused command: pytest relevant controller/state/agent/replay tests.
- Full command: `python -m pytest -q --basetemp <project-local-path>`.
- Compile command: `python -m compileall -q src scripts`.
- Outputs: updated tests/code, replay summaries, repair result report, and this
  plan/checklist.
- API budget before local pass: zero.
- API budget after local pass: one offending case plus the 12-case gate.
- Current runtime lacks managed `bash_exec`, artifact, and memory interfaces;
  use PowerShell plus durable repository artifacts as the explicit fallback.

## 6. Fallbacks And Recovery

- If direct verifier/binding objects are unavailable at terminal handoff, pass
  the existing in-memory objects explicitly rather than re-parsing logs.
- If historical rows lack a terminal field, report `not_observable` instead of
  treating missing metadata as safe.
- If the guard is too broad, retain canonical-state blocking first and add only
  the minimum positive-evidence exception supported by tests.
- If the paid offending case is stochastic, acceptance is abstention or a fully
  supported answer; do not require a specific generated surface answer.

## 7. Checklist Link

- `analysis/semantic_fusion_terminal_safety_repair_checklist_20260715.md`
- Next unchecked item: add failing R28 terminal regression tests.

## 8. Revision Log

| Date | Change | Reason | Impact |
|---|---|---|---|
| 2026-07-15 | Initial repair contract | User approved post-R28 plan | No paid run before deterministic gate |
| 2026-07-15 | Completed local implementation and historical replay | R25/R27 preserved; R28 target mechanically blocked; full suite passed | Single-case paid probe authorized by the frozen plan |
| 2026-07-15 | R29 offending-case probe safely abstained | Unsupported and terminal violations were zero; original controller already abstained in this stochastic run | Proceed to repaired fixed-12 gate; deterministic test remains direct guard evidence |
| 2026-07-15 | R30 was safe but reached only 10/12 | Two upstream stochastic abstentions had no terminal-guard activation or downgrade | Permit one identity-only R31 full retry; stop if it also misses 12/12 |
| 2026-07-15 | R31 was safe but again reached 10/12 with a shifted failure set | The one authorized retry confirms single-run online instability; one R31 loss was upstream and one was an intended non-local-evidence block | Close paid retries and replace the single-draw oracle with a frozen-certificate deterministic gate before attribution |
