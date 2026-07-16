# R21 Partial Failure Analysis Checklist

## Launch

- [x] Parent run and failed claim identified.
- [x] Three automated slices defined.
- [x] Existing assets and comparators confirmed.

## Execution

- [x] Generate partial metrics without treating them as full-gate metrics.
- [x] Attribute the `18th` regression from state transitions.
- [x] Attribute the exact-date regression from binding/evidence granularity.
- [x] Classify the repeated HTTP 403 independently from method quality.

## Aggregation

- [x] Write JSON and Markdown campaign outputs.
- [x] Classify support, contradiction, and unresolved ambiguity.
- [x] Decide the smallest R22 implementation delta.
- [x] Keep phase 2 blocked.

Outcome: the routing hypothesis retains partial support, but R21 fails the hard
gate. Two generic-compatibility invariants were isolated: type-aware ordinal
equivalence and unique local full-date precision. R22 is authorized only as a
repeat of the same fixed 12-case gate after deterministic closure; phase 2 is
not authorized.
