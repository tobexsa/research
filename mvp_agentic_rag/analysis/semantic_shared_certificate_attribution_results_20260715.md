# Shared-Certificate Strict-Router Attribution Results

Date: 2026-07-15

## Outcome

The deterministic shared-certificate gate passes, but the strict terminal
acceptance component shows zero action-level contribution on every observed
eligible certificate stream. Deterministic adapters create strict eligibility;
turning strict acceptance on or off after the certificate is fixed does not
change a single terminal action.

This narrows the component claim. The observed R25 full-Fusion advantage over
R27 adapter-only cannot be attributed to terminal strict acceptance.

## Method

For each frozen terminal row, the replay reconstructs only:

- canonical execution state;
- final verifier output;
- slot-binding certificate;
- cumulative retrieved evidence IDs;
- proposed terminal action and remaining budget;
- repair and preterminal controller metadata.

The byte-identical input is replayed three times with strict acceptance on and
off. The only changed configuration field is
`claim_evidence_fusion_strict_certificate_enabled`. Gold answer,
decomposition, and gold support are not read by action logic.

Each counterfactual answer is audited with the same terminal invariants used
for R29-R31.

## Results

| Frozen stream | Rows | Strict eligible | Strict on/off action changes | On violations | Off violations | Deterministic |
|---|---:|---:|---:|---:|---:|---:|
| R31 repaired fixed-12 | 12 | 4 | 0 | 0 | 0 | yes |
| R25 adapter-on / strict-on | 45 | 5 | 0 | 0 | 0 | yes |
| R27 adapter-on / strict-off | 45 | 5 | 0 | 0 | 0 | yes |
| R26 no-adapter / strict-off | 45 | 0 | 0 | 0 | 0 | yes |
| R28 no-adapter / strict-on | 45 | 0 | 0 | 0 | 0 | yes |

R25 and R27 have exactly the same five eligible terminal samples:

- `2hop__136179_13529`
- `3hop1__129499_33897_81096`
- `3hop1__136129_87694_124169`
- `4hop1__161810_583746_457883_650651`
- `4hop1__236903_153080_33897_81096`

For R25, strict-on and strict-off both produce 23 answers and 22 abstentions.
For R27, both produce 21 answers and 24 abstentions. The two independently
sampled streams differ from each other, but toggling strict policy within
either fixed stream changes nothing.

## Causal Interpretation

### Supported: adapters create eligibility

Both adapter-on 45-case streams contain five eligible terminal certificates.
Both no-adapter streams contain zero. R31 contains four eligible fixed-12
terminal certificates. Eligibility is therefore tied to certificate
construction/repair, not to merely enabling the strict switch.

### Refuted on tested streams: strict terminal acceptance adds decisions

There are ten eligible adapter-on terminal comparisons across R25 and R27 and
four more in R31. Strict-on changes zero answers, abstentions, or safety
outcomes relative to strict-off on identical inputs.

The strict switch changes lane labels, but no terminal decision in these
streams. It cannot carry a claim of an independently observed terminal-policy
benefit.

### Unresolved: upstream protocol interaction

The live router can also select a typed state-aware binding protocol before the
terminal certificate exists. R25 and R27 were independent online executions,
so their `+0.0444` R25 Answer-F1/coverage difference could reflect:

- a real upstream strict-protocol interaction;
- stochastic verifier/candidate variation;
- both.

The terminal replay intentionally holds certificate output fixed and therefore
does not measure certificate-generation interaction. No causal claim is made
for this residual difference.

### Boundary result: R28

R28 has zero eligible terminal certificates even when strict is enabled.
Current repaired replay safely blocks the historical unsafe terminal outputs,
with zero counterfactual terminal invariant violations. R28 remains a
zero-activation no-adapter boundary, not a strict-router treatment estimate.

## Deterministic Gate Verdict

The gate passes as a code/safety oracle:

- all inputs are unique and hashable;
- three repeats are identical;
- strict on/off share one input digest per case;
- all accepted counterfactual answers have zero terminal invariant violations;
- strict activation is measured instead of inferred from configuration;
- action logic is gold-free.

It does not retroactively turn R31 into a 12/12 online performance run. Online
stability remains a separate unresolved contract.

## Validation

- New focused controls: `3 passed`.
- Wider state/replay/agent suite: `182 passed, 25 subtests passed`.
- Full suite: `648 passed, 27 subtests passed`.
- `compileall`: passed.
- `git diff --check` on new code/tests/plans: passed.
- Source scan: the new replay contains no gold answer, gold decomposition,
  gold support, or sample-specific action branch.

## Evidence And Hashes

- R31 replay JSON:
  `analysis/semantic_shared_certificate_r31_replay_20260715.json`
  (`F7F2D912CB158B969470EA9FD4472BA375AE7CE1F9F0899362C026D2215226F2`)
- R25 replay JSON:
  `analysis/semantic_shared_certificate_r25_replay_20260715.json`
  (`9255C2F058162DA41B8B5EDB2317793B99FAB1B54F40CAD8A7B6D0204C3839AE`)
- R27 replay JSON:
  `analysis/semantic_shared_certificate_r27_replay_20260715.json`
  (`1208B85959A558CEDCE69897497B29B9B64D17D5E5B954750007EC23EF034615`)
- R26 replay JSON:
  `analysis/semantic_shared_certificate_r26_replay_20260715.json`
  (`AC1B1FCFB15F8DF28DD457349F1BC5DF6812D02D0AD17A7A96A07A874163646B`)
- R28 replay JSON:
  `analysis/semantic_shared_certificate_r28_replay_20260715.json`
  (`7FDA9C5AE75B384520F836A86EFA1652C773810C80D9035DC1AAFB8727A2B704`)
- Replay implementation:
  `scripts/replay_shared_certificate_terminal.py`
  (`84A972085C4EFAD3D67D5206701B10EF1F7A225D7EC82ABA3E72A0EB28C2C8A9`)
- Tests:
  `tests/test_replay_shared_certificate_terminal.py`
  (`0EAC1D7FF7E9A0846885B97588F7D9022A55C846651513C52DA3A103E0B14612`)

## Runtime Interface Degradation

Managed `bash_exec`, artifact, and memory interfaces were unavailable.
Repository-local code, tests, JSON, Markdown, and hashes are fallback evidence,
not artifact-service records.
