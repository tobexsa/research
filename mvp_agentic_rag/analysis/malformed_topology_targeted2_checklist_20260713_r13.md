# Malformed-topology targeted2 closure checklist (R13)

- [x] Identify the two R12 schema-invalid samples.
- [x] Diagnose verifier and reducer leakage paths.
- [x] Add verifier-level atomic rejection.
- [x] Add reducer-level malformed-primary short circuit.
- [x] Add deterministic regressions for both repair paths and state bookkeeping.
- [x] Pass full suite: 572 tests and 27 subtests.
- [x] Pass compileall and relevant diff checks.
- [x] Freeze a unique targeted2 dataset, config, and output identity.
- [x] Run the real SiliconFlow targeted2 gate.
- [x] Validate malformed/parse/sentinel transition invariants.
- [x] Update the R12 report and final decision.

Outcome:

- 2/2 rows, 6/6 verifier-invoked steps, stderr empty;
- one real `required_hops_malformed` step was fully non-supporting and emitted
  only `incoming_topology_invalid`;
- one real parse-failure step emitted no transition and preserved prior state;
- sentinel diagnostics produced zero candidate transitions;
- final unsupported rate remained zero.
