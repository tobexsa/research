# Final Decision

- verdict: `bad` for the current Planner candidate; `good` for the Gold-query dense retriever component; `partial` for R0 downstream execution.
- action: `stop` and archive the current candidate.

The alternative of proceeding to Internal Holdout was rejected because P2A, Route A, C2P and C4A all failed their diagnostic purpose. The alternative of tuning the same prompt was rejected because P0 already isolates schema support and P1 exposes both decoder whitespace loops and schema-valid semantic errors. The alternative of a strong-model substitution was rejected because no exact comparator was frozen.

Reopen when a new explicit candidate passes Diagnostic structure, span/binding, budget and machine-validation gates. Until then, keep both internal holdouts and Confirmation unused.
