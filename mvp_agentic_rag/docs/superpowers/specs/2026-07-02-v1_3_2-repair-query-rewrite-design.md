# v1.3.2 Repair Query Rewrite Design

## Problem

v1.3.1 completed the repair lifecycle cleanup and exposed the dominant repair-query failure modes on stratified45:

- `under-specified`: 17 repair steps
- `entity-only`: 12 repair steps
- `relation-only`: 2 repair steps

These queries often reach retrieval as fragments such as `meaning`, `Apple Records`, or `parent company`. They do not reliably retrieve the missing hop evidence, especially in longer chains. The next experiment should improve repair query generation while preserving the existing final-answer safety gates.

## Goal

v1.3.2 rewrites low-quality repair queries into targeted entity-plus-relation retrieval queries before the next retrieval round. It must not relax any final answer acceptance gate.

## Non-goals

- Do not add new final-answer acceptance paths.
- Do not loosen typed-target, slot-binding, slot-final-verifier, unsupported, or wrong-target guards.
- Do not increase `max_rounds` or add 4-hop extra rounds.
- Do not use an LLM to rewrite repair queries in this version.
- Do not treat local repair acceptance as final success unless the final action is `answer`.

## Architecture

The change lives in `ClaimRiskAgent` near repair metadata construction:

1. Existing code chooses a repair query using `_query_from_missing_hop`, `_query_from_ordered_hop`, or `_query_from_answer_extraction`.
2. Existing `_classify_repair_query_quality()` classifies the query.
3. If `repair_query_rewrite_v1_3_2` is enabled and the bucket is one of `under-specified`, `entity-only`, `relation-only`, or `wrong-direction`, a deterministic rewriter builds a replacement query from:
   - ordered-hop `bound_bridge_values`
   - ordered-hop `missing_critical_hops`
   - ordered-hop `final_relation`
   - verifier `suggested_query`
   - original question as last fallback
4. The rewritten query is reclassified and used for retrieval.
5. Metadata records both original and rewritten query state for audit.

## Rewrite Rules

The rewriter is conservative and deterministic:

1. Prefer a query built from the last usable bound bridge value and the most specific relation-like phrase:
   - `last_bound_bridge + final_relation`
   - `last_bound_bridge + first_missing_hop`
2. For `entity-only`, preserve the entity and add the best relation phrase from ordered-hop state or verifier suggested query.
3. For `relation-only`, preserve the relation and add the best subject/entity from ordered-hop state or verifier suggested query.
4. If no bridge/relation pair can be formed, use verifier `suggested_query` only when it classifies better than the original query.
5. If no rewrite improves the query, keep the original query and record `repair_query_rewritten=false`.

## Metadata Contract

When rewriting is attempted, each repair step should include:

```json
{
  "repair_query_original": "meaning",
  "repair_query_rewrite_attempted": true,
  "repair_query_rewritten": true,
  "repair_query_rewrite_reason": "single_token_query",
  "repair_query_rewrite_source": "v1_3_2_ordered_hop_context",
  "repair_query_quality_bucket_before_rewrite": "under-specified",
  "repair_query_quality_reason_before_rewrite": "single_token_query",
  "repair_next_query": "Ankahi released country creation India meaning",
  "repair_query_quality_bucket": "useful"
}
```

If rewrite is enabled but no better query exists:

```json
{
  "repair_query_rewrite_attempted": true,
  "repair_query_rewritten": false,
  "repair_query_rewrite_reason": "no_better_rewrite_candidate"
}
```

## Safety Invariant

The only behavior change is the retrieval query used on a repair round. Final answer production still requires the same downstream checks:

- generic verifier support
- slot binding verifier support
- typed target acceptance
- slot-final verifier when configured
- final unsupported guard

If rewritten retrieval finds a candidate that fails these gates, the final action remains `abstain`.

## Test Plan

Add tests in `tests/test_claim_risk_agent.py`:

- Under-specified repair query is rewritten using ordered-hop context.
- Entity-only repair query is rewritten by adding relation context.
- Relation-only repair query is rewritten by adding entity context.
- Wrong-direction repair query is rewritten from safer ordered-hop or verifier-suggested context.
- Bad query with no better rewrite candidate records `repair_query_rewritten=false`.
- Rewrite metadata records before/after buckets and original query.
- Existing safety gate remains strict: a rewritten query can retrieve evidence, but final action remains `abstain` when typed-target/final verifier rejects.

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
D:\python1\python.exe -m pytest -q
```

## Experiment Plan

Create a v1.3.2 config derived from v1.3.1 with only:

```yaml
repair_query_rewrite_v1_3_2: true
```

Run stratified45 only. Do not run full-300 until gates are met.

Minimum success criteria:

- `final_answered_unsupported_rate = 0`
- `answer_f1 >= 0.2059`
- `coverage >= 0.2444`
- no duplicate `(id, method)` rows
- no answered F1=0 regression
- lower bad repair-query bucket share than v1.3.1
