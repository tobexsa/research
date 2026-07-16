# Malformed-topology targeted2 closure plan (R13)

## Purpose

Validate the post-R12 atomic-rejection fix on the two real stratified45
samples that emitted schema-invalid required-hop objects. The run uses the
same frozen semantic-binding method and changes only the two-sample dataset and
unique output identity.

## Gate

- two unique rows complete with zero final unsupported answers;
- verifier/state diagnostics are present on every step;
- every `required_hops_malformed` step has an empty/non-supporting consumable
  binding and cannot create or update a candidate;
- every `verifier_parse_failure` step preserves prior state and creates no hop
  or candidate transition;
- UNKNOWN-like values never enter candidate-observed/state-updated events;
- if model stochasticity produces only valid topology, record that the live
  run did not re-exercise malformed output and rely on deterministic regressions
  for the atomic-rejection branch.

Do not rerun the full 45 samples solely to chase stochastic malformed output;
R12 already produced complete aggregate evidence and both affected samples
ended in abstention. R13 is a control-path closure gate.
