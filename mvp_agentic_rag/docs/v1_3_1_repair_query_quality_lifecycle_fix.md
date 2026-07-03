# v1.3.1 Repair Query Quality and Lifecycle Fix

## Objective

This implementation pass addresses the immediate post-v1.3.0 bottleneck:

1. classify repair query quality into explicit buckets;
2. prevent `accepted_final` from being used when a repair is only locally accepted but the final action is still `abstain`;
3. eliminate terminal `pending` repair states from completed trajectories.

This is a code-level lifecycle and observability fix. It does not change retrieval, verifier prompting, model selection, dataset split, or metric definitions.

## Implemented Behavior

### Repair query quality buckets

Each generated repair query now records:

- `repair_query_quality_bucket`
- `repair_query_quality_reason`
- `repair_query_quality_features`

Supported buckets:

| bucket | meaning |
| --- | --- |
| `placeholder` | empty or placeholder-like query |
| `wrong-direction` | relation appears before subject, e.g. `religion of Edward Egan` |
| `under-specified` | too short, single-token, or dangling relation query |
| `entity-only` | query has entity-like tokens but no relation cue |
| `relation-only` | query has relation cues but no entity anchor |
| `useful` | query contains both entity anchor and relation cue |

The classifier is intentionally heuristic and metadata-only. It does not block or rewrite queries yet; its purpose is to support v1.3.1 analysis and later targeted repair-query changes.

### Accepted repair closure

Before this change, a repair step could be labeled:

```text
repair_closed = accepted_final
```

even when later gates changed the sample-level final action to:

```text
final_action = abstain
```

The run-final lifecycle sweep now corrects this case to:

```text
repair_closed = accepted_intermediate_but_not_final
repair_final_action_answered = false
```

`accepted_final` is now reserved for repair steps whose own trajectory action and sample-level final action both close as `answer`.

### Terminal pending archival

Completed trajectories should not leave repair steps with:

```text
repair_acceptance = pending
repair_closed = pending
```

At run finalization, unresolved pending repair steps are converted to:

```text
repair_acceptance = unresolved
repair_state = repair_unresolved_terminal
repair_closed = repair_unresolved_terminal
```

New repair attempts that are generated on a terminal step with no budget still keep the sharper existing label:

```text
repair_acceptance = expired
repair_state = repair_expired
repair_closed = repair_expired
```

This preserves the distinction between:

- a prior repair request that never closed after later rounds;
- a newly proposed repair request that could not be executed because the budget ended.

## Tests

Focused test command:

```powershell
python -m pytest tests\test_claim_risk_agent.py -q
```

Result:

```text
63 passed, 6 subtests passed
```

Full test command:

```powershell
python -m pytest -q
```

Result:

```text
222 passed, 6 subtests passed
```

## Next Experimental Step

The next run should use the same stratified45 protocol and inspect the distribution of:

- `repair_query_quality_bucket`
- `repair_closed`
- `accepted_intermediate_but_not_final`
- `repair_unresolved_terminal`
- `repair_expired`

The goal is not only to improve headline metrics immediately, but to identify which repair-query bucket is most responsible for low evidence gain and 4-hop all-abstain behavior.
