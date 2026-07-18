# P1 Structural Experiment Summary

The fixed-payload decoder envelope did not transfer to semantic structural classification. Route A scored 0/60 with 50/60 invalid; Route B C2P scored 7/60 (11.67%); Oracle Pairwise C4A produced only 1/60 exact graphs.

## Research contract

- question: can a 7B model recover useful topology through Direct Topology, Hop→Shape, or Gold-decomposition Pairwise interfaces after the provider JSON-schema envelope passes?
- type: auxiliary/dev structural diagnostic.
- null: no route beats the frozen majority baseline or produces globally consistent graphs at a usable rate.
- alternative: at least one decomposed route produces a materially usable structural signal within the 1/2-call Planner budget.
- baseline: attached V1 C1/D1 and C2O/D2 on the identical Diagnostic-Dev-60.

## Results

- Route A: exact topology 0/60; invalid 50/60; macro-F1 0.0000; majority baseline 10/60.
- C1 attached: hop accuracy 24/60; invalid 8/60.
- C2O attached, 3/4-hop only: shape accuracy 7/50; invalid 31/50.
- C2P: end-to-end topology 7/60; invalid 18/60; macro-F1 0.0751; mean 1.8667 calls/question.
- C4A: pair relation 85/250; pair invalid 23/250; global consistency 2/60; exact graph 1/60; mean edge F1 0.0250.
- transport succeeded for 362/362 new calls, proving the failures are not network loss.

## Analysis

There are two separable failures. First, 83/362 calls end at length because the constrained decoder emits long runs of whitespace after an opening brace or partial legal field; this is not caught by a lexical repeated-token detector. Second, among 279 schema-valid outputs, 187 are semantically wrong. Merely increasing `max_tokens` would not resolve the second failure and would change the freeze.

## Conclusion

Verdict: `refuted` for promoting any tested P1 structural route. The result narrows the earlier diagnosis: SiliconFlow accepts and can perfectly execute the same schema families on fixed-copy P0, but real question-conditioned decoding and semantic classification remain unusable. Do not open Internal Holdout or Confirmation for these candidates.
