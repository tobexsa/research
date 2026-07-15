# Post-R28 Route Decision

Date: 2026-07-15

## Verdict And Action

- Verdict: `neutral` on the overall Fusion line, `bad` for the current R28
  strict-only cell as a valid causal ablation.
- Action: `iterate` on terminal safety and replace the naive strict-only 2x2
  interpretation with activation-aware certificate/router analysis.
- Do not start repeats, baselines, non-leaking dev/test, or 300-case runs yet.

## Decisive Evidence

- R25 full Fusion beats R26 generic-only by `+0.1111` Answer F1 and coverage,
  with unsupported zero and lower retrieval cost.
- R27 adapter-only beats R26 by `+0.0667` Answer F1 and coverage, with
  unsupported zero.
- R28 completed 45 unique cases but has unsupported `0.0500`.
- R28 configured strict routing on and adapters off, yet observed zero strict
  lane steps. R25 observed 11 strict steps only when adapters were enabled.
- The R28 unsupported case ended in generic compatibility after the controller
  selected abstain, with an unclear final claim, no claim evidence, an
  incomplete dependency chain, and an uncovered final slot.
- Structural state replay reported zero unsafe transitions, proving that a
  terminal-level invariant is missing from the current replay contract.

Evidence:

- `analysis/semantic_fusion_stratified45_comparison_20260714.md`
- `analysis/semantic_adapter_only_stratified45_results_20260715_r27.md`
- `analysis/semantic_strict_only_stratified45_results_20260715_r28.md`

## Selected Route

### Phase A: Minimal terminal safety repair

Add one general fail-closed rule, not a sample-specific patch. Generic
compatibility must not convert a terminal abstention into an answer when any of
the following holds:

- the controller's original action is abstain;
- the final verifier contains unsupported, contradicted, or unclear claims;
- the final verifier requests more evidence;
- the final slot is not covered or the final verifier did not pass;
- critical-hop ancestor closure is incomplete;
- the final claim lacks local evidence IDs;
- slot entailment or slot support is false.

Only a newly established complete, local, conflict-free strict certificate may
override a prior abstention.

Also make downstream verified hops ineligible for final acceptance when their
critical ancestors are unresolved. They may remain locally observed/verified
for monotonic logging, but cannot satisfy global certificate closure.

### Phase B: Deterministic verification before paid runs

1. Add a regression test reproducing the R28 terminal state and requiring
   abstention.
2. Add tests for the positive exception: a complete strict certificate may
   answer.
3. Extend replay with terminal invariants for abstain override, unclear final
   claims, local evidence, final-slot coverage, and ancestor closure.
4. Replay R25-R28 trajectories and report every action changed by the repair.
5. Run focused tests, full tests, compileall, and whitespace/config checks.

Gate: all deterministic tests and replays pass; the repair must be generic and
must not inspect sample IDs, gold answers, gold decomposition, or gold support.

### Phase C: Small paid gates

1. Run the offending R28 case as a targeted safety probe.
2. Re-run the frozen 12-case gain/loss gate under the repaired code.

Gate:

- offending case abstains or produces a fully supported correct answer;
- 5/5 prior gains retained;
- 7/7 prior losses restored;
- final unsupported zero;
- no malformed, parse-failure, conflict, sentinel, or non-local fallback.

Any failure returns to Phase A. Do not expand sample size.

### Phase D: Activation-aware component attribution

Do not treat a configured switch as a delivered treatment. Record for every
cell:

- strict-eligible certificates;
- actual strict lane steps;
- adapter applications;
- answers changed by routing;
- unsupported and dependency-closure violations.

Use a shared-certificate counterfactual replay as the primary strict-router
ablation:

1. freeze adapter-on verifier/certificate outputs;
2. replay the same outputs with strict acceptance on and off;
3. compare terminal actions and metrics without new LLM sampling;
4. separately compare raw verifier versus adapter-repaired certificates to
   measure adapter contribution.

This isolates:

- adapter effect: certificate construction/repair;
- router effect: acceptance policy on an identical certificate stream;
- interaction: adapters creating certificates that become strict-eligible.

The raw no-adapter/strict-on cell remains a boundary test. If eligibility is
zero again, report that strict routing has no standalone activation rather than
claiming a zero-valued causal treatment.

After offline attribution is valid, run only the necessary repaired online
45-case packages. All online comparison packages must share one code version,
dataset, model, retriever, budgets, evaluator, and safety guard.

Gate:

- every accepted online package has 45 unique rows and unsupported zero;
- any package claimed to test strict routing has nonzero measured activation,
  or is explicitly classified as a zero-activation boundary result;
- shared-certificate replay and online lane logs agree on eligibility rules.

### Phase E: Independent repeats

Only after Phase D passes:

- add at least two fresh independent runs each for repaired full Fusion and
  repaired generic-only;
- call them independent repeats, not seeded repeats;
- report mean, sample standard deviation, range, paired deltas, lane activation,
  per-example stability, and unsupported for every run.

Gate: repeat-aggregated Fusion minus generic-only remains positive on the
headline metrics and unsupported is zero in every run.

### Phase F: Later stages in the user-approved order

1. matched modern baselines;
2. non-leaking standard MuSiQue dev/test contract and evaluation;
3. only then 300 cases or paper main experiments.

## Rejected Alternatives

- Continue repeats immediately: rejected because the current version has a
  known unsupported terminal answer and an invalid strict-only treatment cell.
- Re-run R28 unchanged: rejected because it can repeat stochastic calls but
  cannot repair the terminal safety hole or guarantee strict activation.
- Jump to 300 cases: rejected because the code is not frozen and the result
  would be pre-fix, non-standard, and likely require a full rerun.
- Drop the whole Fusion line now: rejected because R25 and R27 provide real
  positive evidence; the failure is localized and testable.

## Success And Abandonment Criteria

Success:

- general terminal fail-closed invariant passes deterministic and paid gates;
- fixed 12-case gate remains 12/12 with unsupported zero;
- strict contribution is measured on identical certificate outputs with
  nonzero activation where claimed;
- repaired 45-case packages and repeats keep unsupported zero.

Abandon or narrow the strict-router claim if:

- strict activation remains zero even on adapter-repaired shared certificates;
- strict routing adds no stable action or metric benefit over adapter-only;
- safety repairs repeatedly erase the claimed gain;
- the same terminal unsupported failure recurs after the general guard.

In that case, retain adapter-only as the incumbent and report strict routing as
an unsupported or redundant extension.
