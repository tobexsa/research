# Arizona / Maricopa County Granularity Audit

Date: 2026-07-13

Sample: `2hop__249867_557232`

Question:

> Which country is the Desert Forest Golf Club located in?

Gold answer: `Maricopa County`

Question decomposition in the diagnostic dataset:

1. `Desert Forest Golf Club >> located in the administrative territorial entity`
   → `Carefree`
2. `#1 >> located in the administrative territorial entity`
   → `Maricopa County`

Retrieved evidence used by R8:

> Desert Forest Golf Club is a private golf club located in Carefree, Arizona.

The R8 candidate `Arizona` is directly supported as a location in the retrieved
passage, but it does not satisfy the two-hop gold decomposition. The question
asks for a country, while the gold answer is a county reached through the
administrative-entity chain `Carefree → Maricopa County`.

## Finding

This is a dataset/question-granularity inconsistency, not evidence absence and
not a generic final-slot safety failure. The current evaluator marks `Arizona`
wrong against the gold `Maricopa County`, although the answer is a supported
coarser location.

## Decision

Do not add an Arizona-specific answer override yet. First decide whether the
evaluation contract should:

- preserve the two-hop gold and rewrite the question target as the final
  administrative entity;
- preserve the question target and revise the gold to the country-level answer;
- or explicitly evaluate hierarchical/granularity-aware correctness.

Until that decision is made, the sample should remain an audit exclusion from
controller tuning and should not be used as evidence that the semantic binder
is hallucinating.
