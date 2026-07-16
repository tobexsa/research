# Shared-Certificate Deterministic Gate Checklist

## Planning

- [x] Parent R31 failure decision fixed.
- [x] Gold-free replay boundary and input streams fixed.
- [x] Success and strict-claim abandonment criteria recorded.

## Test First

- [x] Deterministic identical-input replay red test added.
- [x] Complete local certificate positive control added.
- [x] Non-local verifier evidence negative control added.
- [x] Synthetic strict-on/off action-delta control added.

## Implementation

- [x] Frozen terminal state/verifier/binding reconstruction implemented.
- [x] Strict-on/off replay uses an identical input digest.
- [x] Repeated replay stability and terminal invariants implemented.
- [x] JSON/Markdown output and overwrite guard implemented.

## Validation

- [x] Focused tests pass: 3 passed.
- [x] Wider state/replay tests pass: 182 passed, 25 subtests passed.
- [x] Full tests and compileall pass: 648 passed, 27 subtests passed.
- [x] Source scan confirms no gold/sample-specific routing branch.

## Evidence

- [x] R31 fixed-12 stream replayed and audited.
- [x] R25/R27 adapter-on and R26/R28 no-adapter streams replayed and audited.
- [x] Strict eligibility and action changes interpreted.
- [x] Next decision recorded without starting a paid run.
