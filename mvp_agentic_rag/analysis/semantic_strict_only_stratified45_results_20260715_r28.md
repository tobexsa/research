# Semantic Strict-Only Stratified45: R28

Date: 2026-07-15

## Verdict

R28 completed all 45 cases but fails the phase-3 safety gate. Final answered
unsupported is `0.0500` rather than zero. In addition, the run contains zero
`strict_certificate` lane steps, so it does not provide an observed strict-lane
treatment despite the strict-lane configuration switch being enabled.

The result must be retained as a negative component slice, not accepted as a
clean 2x2 cell. Independent repeats and matched modern baselines remain blocked
until the safety failure and lack of strict activation are resolved.

## Identity And Recovery Provenance

- Config SHA-256:
  `2B00BD5963951D6519A9ACD788013ACBE12A5AB4268DD63F8D448610A45D5959`
- Dataset SHA-256:
  `2B4A0DFAD40AC8B120FF59862FCBF216C5AD419EC7E2783E35534281653D63A5`
- Trajectory SHA-256:
  `A672148B60B721AC7EA79CC4FE9A901EF55B962EEF69BEFE99281F0889960D60`
- Metrics SHA-256:
  `2706F93430205157DB3CA928300E6C8E1747658E2F30BBF314FB3335AEF36DF5`
- Replay SHA-256:
  `F0BF88FCFCAE7C9C4EF96DDCAED578E38BD70CC27558B9FF063E753D4689C0F0`
- Completion: 45 rows, 45 unique IDs, no remaining lock, complete finite
  metrics.

The original background process stopped after 28 rows without stderr. A first
resume attempt added one valid unique row, then its parent shell failed. The
repository runner's Windows stale-lock probe subsequently raised WinError 87
while checking the dead PID. After directly verifying that PID `11644` did not
exist and that the lock path was inside the run directory, only that stale lock
was removed. The final monitored resume skipped 29 existing rows, completed 16,
and generated the complete metrics. No row was overwritten or duplicated.

## Metrics

- Accuracy / EM: `0.3778 / 0.3778`
- Answer F1: `0.3889`
- Coverage: `0.4444`
- Selective accuracy / F1: `0.8500 / 0.8750`
- Average retrieval calls: `2.3556`
- Wasted retrieval rate: `0.6444`
- Final answered unsupported: `0.0500` -- hard-gate failure

Hop slices:

- 2-hop: EM `0.5333`, F1 `0.5667`, coverage `0.6667`
- 3-hop: EM/F1 `0.6000`, coverage `0.6000`
- 4-hop: EM/F1 `0.0000`, coverage `0.0667`

Against R26 generic-only, R28 has three exclusive exact-correct samples and
three regressions, so there is no net exact-correct gain. Its small Answer F1
difference cannot be attributed to strict routing because strict routing never
activated.

## Treatment Integrity

- Generic-compatibility steps: 104
- Strict-certificate steps: 0
- No-fallback steps: 2
- Recognized deterministic adapter markers: 0, as required
- Topology-only compatibility marker:
  `final_hop_order_canonicalization` once

The factor switch was configured correctly, but no row satisfied the runtime
strict-certificate eligibility conditions without deterministic adapters.
Therefore the intended strict-only treatment had zero observed activation.

## Unsupported Final Answer

- Sample: `4hop1__151650_5274_458768_33632`
- Prediction: `7 October.`
- Gold answer: `May 4`
- Lane: `generic_compatibility`
- Controller-policy original action: `abstain`
- Final action: `answer`
- State label: `repairable_gap`
- Support coverage: `0.6`
- Missing critical hops: 3, 4, and 5 in the current verifier record
- Final slot covered: false
- Final verifier passed: false
- Slot verifier supports slot: false
- Slot-bound entailment: false
- Final claim status: `unclear`
- Final claim evidence IDs: empty
- Verifier message: `Verifier returned non-JSON after repair`

This is not a strict-certificate false acceptance. It is a generic terminal
handoff failure: the generic-compatibility terminal route answered after the
controller policy had selected abstention and after the final verifier still
reported an unclear, unsupported claim.

## State Replay

- Row count: 45
- Unsafe malformed/parse-failure candidate transitions: 0
- Canonical hop-conflict events: 0
- Same-round topology update rejections: 0
- Structured legacy requirement items: 0

The replay is structurally safe, but it does not cover the later terminal
generic-compatibility override exposed by the evaluator. Both audits are
necessary; replay success does not cancel the unsupported-final failure.

Replay artifact:
`analysis/semantic_strict_only_stratified45_r28_state_replay_20260715.json`.

## Decision

R28 is `complete_but_rejected`. Do not enter repeated runs or matched modern
baselines. The next decision must address two issues before rerunning this
component cell:

1. fail closed when a generic-compatibility terminal step has an unclear or
   unsupported final verifier result, incomplete critical hops, or an original
   controller abstention;
2. decide whether strict-only is a meaningful standalone intervention when
   deterministic adapters are absent and no strict certificate activates.
