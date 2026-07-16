# Adapter-vs-Generic Online Stability Protocol Plan

Date: 2026-07-15
Protocol id: `semantic_adapter_generic_online_stability_v1_20260715`
Status: `frozen`; the protocol, four configs, analyzer, tests, machine-readable
contract, and integrity manifest are complete. Online execution is authorized
only in the predeclared order and may not modify this protocol version.

## 1. Objective

- Parent decision:
  `analysis/semantic_fusion_phase3_post_shared_certificate_decision_20260715.md`.
- Incumbent: deterministic adapters plus the shared generic terminal
  fail-closed guard, with strict-certificate acceptance disabled.
- Comparator: generic-only certificate generation with the same shared generic
  terminal fail-closed guard and strict-certificate acceptance disabled.
- Research question: across fresh independent remote-model executions, do
  deterministic adapters improve correct certificate completion and final
  performance without changing terminal-policy safety?
- Required outcome: report certificate-generation variance separately from
  terminal-policy behavior before deciding whether 45-case repeats pass and
  matched modern baselines may begin.
- This is an auxiliary/dev robustness campaign, not standard MuSiQue dev/test
  and not a paper/300-sample experiment.

## 2. Boundary And Comparability

Fixed across all four runs:

- dataset: `data/musique_mvp_stratified45.jsonl`, exactly 45 unique rows;
- dataset SHA-256:
  `2B4A0DFAD40AC8B120FF59862FCBF216C5AD419EC7E2783E35534281653D63A5`;
- corpus, FAISS index/meta, embedding model, retriever, top-k, maximum rounds,
  query decomposition, prompts, answer/verifier/binding models, timeouts,
  retry policy, terminal guard, evaluator, and current repaired source bundle;
- `claim_evidence_fusion_strict_certificate_enabled: false` in both variants;
- one sequential process at a time; no concurrent API experiments;
- no result-dependent code/config/evaluator changes.

The only scientific treatment variable is:

```yaml
slot_binding_verifier_deterministic_bindings: true   # adapter-only incumbent
slot_binding_verifier_deterministic_bindings: false  # generic-only comparator
```

Allowed identity-only differences are `run_name` and `output_dir`.

Historical R26/R27 are context only. They are excluded from primary means,
standard deviations, paired deltas, and pass/fail decisions because they were
generated before this repaired-code pre-registration.

## 3. Run Set And Order

Exactly two fresh independent full 45-case runs per variant are predeclared:

| Block | Order | Run id | Variant | Required rows |
|---:|---:|---|---|---:|
| 1 | 1 | `adapter_stability_s1` | adapters on, strict off | 45 |
| 1 | 2 | `generic_stability_s1` | adapters off, strict off | 45 |
| 2 | 3 | `generic_stability_s2` | adapters off, strict off | 45 |
| 2 | 4 | `adapter_stability_s2` | adapters on, strict off | 45 |

The `A1 -> G1 -> G2 -> A2` sequence balances first/last position across
variants. Runs are called independent repeats, not seeded repeats, because the
remote API does not expose a controlled seed in this contract.

No optional fifth/sixth confirmatory run is allowed. A mixed result is reported
as instability rather than resolved by further sampling.

## 4. Two Separately Reported Layers

### Layer A: certificate-completion variance

For every sample and run, the analyzer must derive from runtime records:

- deterministic adapter marker applications;
- ever-complete local certificate;
- terminal-complete local certificate;
- terminal-complete-and-correct certificate, where correctness is evaluated
  outside routing against gold using the frozen evaluator;
- raw final-verifier sufficiency;
- certificate failure category:
  `missing_binding`, `missing_evidence`, `nonlocal_evidence`,
  `incomplete_chain`, `uncovered_final_slot`, `missing_required_hops`,
  `insufficient_evidence_set`, `binding_conflict`, `wrong_bound_value`, or
  `other`;
- per-case completion frequency across the two repeats of the same variant.

A complete local certificate means all of the following:

- `supports_slot=true`;
- non-empty binding evidence IDs, all mapping to passages actually retrieved
  in that run up to the evaluated round;
- `chain_complete=true` and no missing critical hops;
- final slot and all required hops covered;
- evidence set sufficient;
- no bridge/final-slot conflict.

The report must provide, per run and per variant:

- completion counts/rates;
- correct-completion counts/rates;
- mean, sample standard deviation, and range across the two fresh runs;
- paired adapter-minus-generic deltas for blocks 1 and 2;
- per-example stability buckets: completed in `0/2`, `1/2`, or `2/2` runs.

### Layer B: terminal-policy behavior

Terminal policy is held fixed: generic compatibility plus the repaired shared
fail-closed guard, strict acceptance off.

For every run, report separately:

- final answer / abstain counts and coverage;
- answer given a terminal-complete certificate;
- abstain given a terminal-complete certificate;
- answer without a terminal-complete certificate;
- terminal guard activations and answer-to-abstain downgrades;
- final answered unsupported;
- terminal invariant violations and unsafe typed-state transitions;
- within-stream deterministic replay, repeated three times on byte-identical
  terminal inputs;
- per-case action stability across the two repeats of each variant.

Certificate-completion changes must not be described as terminal-policy
changes. Terminal-policy contribution is only an action difference observed
after conditioning on the same certificate state or in byte-identical replay.

## 5. Performance Metrics

The existing evaluator remains authoritative. Report without redefining:

- overall EM / Answer F1;
- coverage;
- selective accuracy / selective F1;
- average retrieval calls;
- wasted retrieval rate;
- final answered unsupported rate;
- 2-hop, 3-hop, and 4-hop slices;
- paired per-example correctness deltas.

For each variant report mean, sample standard deviation, and range. For each
block report adapter-minus-generic paired deltas. No metric may be dropped
after observing an unfavorable result.

## 6. Hard Run-Validity Gate

Every run must satisfy all of the following before it enters aggregation:

- exact frozen config hash and source/data manifest;
- 45 completed rows, 45 unique IDs, and exact dataset membership;
- zero skipped rows and no remaining run lock;
- complete finite metrics using the existing evaluator;
- final answered unsupported `= 0`;
- terminal invariant violation count `= 0`;
- unsafe typed-state transition count `= 0`;
- shared terminal replay deterministic across three repeats;
- strict lane activation `= 0` in the live run, as required by both configs;
- no accepted answer without a complete local terminal certificate.

If a completed run violates a safety or comparability condition, the campaign
stops and the run remains visible as rejected. It may not be replaced by a
fresh draw.

Infrastructure handling:

- a partial output caused by interruption may resume in the same output
  directory and remains the same independent run;
- one replacement is allowed only when the run fails before producing any
  valid sample row because of a documented external infrastructure outage;
- timeout, parse failure, abstention, low score, or model variance after valid
  rows exist is experimental data, not infrastructure invalidity.

## 7. Predeclared Campaign Decision Rule

The repeat package passes to matched modern baselines only if:

1. all four runs pass the hard validity/safety gate;
2. adapter-minus-generic terminal-correct-certificate rate is strictly positive
   in both paired blocks;
3. adapter-minus-generic Answer F1 is strictly positive in both paired blocks;
4. repeat-aggregated adapter-minus-generic Answer F1 and coverage are positive;
5. adapter-only does not increase `answer_without_complete_certificate`, which
   must remain zero in every run;
6. final answered unsupported and all terminal/state invariant counts remain
   zero in every run.

Decision branches are fixed:

- certificate and F1 criteria both pass: promote adapter-only incumbent to
  matched modern baselines;
- certificate improves but F1 does not: stop and diagnose wrong-target or
  over-abstention translation; no baselines;
- F1 improves but certificate completion does not: treat the mechanism claim
  as unsupported/confounded; no baselines;
- paired blocks disagree in sign: classify online effect as unstable; no extra
  confirmatory draw and no baselines;
- any safety failure: return immediately to terminal/certificate diagnosis;
- both paired blocks are non-positive: reject adapter advantage and stop the
  current line or return to idea selection.

## 8. Execution And Monitoring

Before the first paid run:

- freeze four YAML configs and their hashes;
- freeze a machine-readable protocol JSON and source/data manifest;
- implement and test the analyzer on historical R26/R27 only as a dry run;
- rerun the full local test suite and compileall;
- confirm every planned output directory is absent.

Execution order is serial. For each run:

1. launch the exact frozen command;
2. monitor at approximately 60 s, 120 s, 300 s, 600 s, then every 600 s;
3. report completed/unique rows and any infrastructure error, without inspecting
   comparative headline metrics until the run closes;
4. audit and hash the completed run before launching the next one.

No code/config/analyzer edit is permitted between S1 and S2. Any necessary
change invalidates the remaining frozen package and requires a new protocol
version before more calls.

## 9. Required Outputs

- four run directories and their raw metrics/trajectories;
- state replay and shared-terminal replay JSON for every run;
- per-run certificate-layer and terminal-policy-layer summaries;
- aggregate JSON and Markdown with all predeclared metrics;
- config/source/data/output hashes;
- explicit pass/unstable/reject decision;
- no paper claim, standard dev/test claim, or 300-sample claim.

## 10. Runtime Interface Degradation

The current runtime lacks managed `bash_exec`, artifact, and memory interfaces.
PowerShell plus repository-local configs, analyzer/tests, JSON, Markdown, and
hash manifests are the declared fallback. These are not artifact-service
records.

## 11. Checklist

- `analysis/semantic_online_stability_protocol_checklist_20260715.md`
- Next unchecked item: launch and audit A1 with the exact frozen config; no
  other run may start first.

## 12. Revision Log

| Date | Change | Reason | Impact |
|---|---|---|---|
| 2026-07-15 | Protocol v1 drafted before new online calls | R30/R31 refuted a single-draw 12/12 oracle; shared replay isolated adapters from terminal strict policy | Four-run paired ABBA package, separate certificate/policy reporting |
| 2026-07-15 | Protocol v1 frozen before online outcomes | Four configs, analyzer, dry-run, tests, machine JSON, and 18-file manifest pass integrity audit | A1 is the only next authorized online run |
