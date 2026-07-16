# R21 Partial Failure Analysis

## Verdict

R21 is an incomplete 8/12 run and has already failed the fixed gate. It retains four of five completed gains and recovers two of three completed losses; phase 2 is not authorized.

## Partial Metrics (Not Full-Gate Metrics)

- Accuracy: 0.7500
- Answer F1: 0.8125
- Coverage: 0.8750
- Final unsupported: 0.0000

## Failure 1: False Ordinal Conflict

`18th century` and `18th` were treated as different bound objects. The reducer emitted `competing_bound_object_conflict` and the no-fallback lane safely abstained. This is a type-aware identity bug, not a reason to relax hard-conflict safety.

## Failure 2: Date Granularity Collapse

The verifier emitted `2011`, while retrieved binding evidence contains the unique full date `March 11, 2011`. A generic date target must not lose available day-level precision.

## External Failure

SiliconFlow returned HTTP 403 after eight rows and again before the retry could add a row. This is recorded as an endpoint failure, not a method result.

## Decision

Do not launch phase 2. Repair ordinal equivalence and unique local date precision as explicit generic-compatibility invariants, validate offline, then retry the same fixed 12-case gate when the endpoint is available.
