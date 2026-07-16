# Semantic Fusion Phase-3 Campaign Results

Completed: 2026-07-16
Campaign: `semantic_fusion_phase3_20260715`
Outcome: `stable_support_with_narrowed_attribution`

## Headline

Phase 3 is complete. Deterministic adapters produce a repeat-stable gain in
correct terminal certificates and Answer F1 under a shared fail-closed generic
terminal policy. Strict acceptance receives no independent terminal-action
credit. The resulting incumbent substantially outperforms the matched local
verifier-guided adaptive RAG comparator.

## Component Attribution

- The original R28 strict-only cell was invalid because generic terminal
  handoff could answer without the complete terminal contract and live strict
  activation was zero.
- The shared terminal hole was repaired and frozen with deterministic tests and
  replay invariants.
- Shared-certificate replay on identical inputs found adapter-created strict
  eligibility, but strict on/off changed zero terminal actions.
- Supported component: deterministic adapters improve certificate
  construction/eligibility.
- Unsupported independent claim: strict terminal acceptance improves actions
  or performance.

Promoted incumbent:

```text
deterministic adapters
+ shared generic fail-closed terminal guard
+ strict certificate acceptance off
```

## Independent Online Stability

All A1/G1/G2/A2 runs are valid, 45/45 unique, with zero answer-without-complete-
certificate cases and zero safety violations.

| Paired block | Correct-certificate A-G | Answer F1 A-G | Coverage A-G |
|---|---:|---:|---:|
| A1 - G1 | +0.0889 | +0.0714 | +0.0444 |
| A2 - G2 | +0.0889 | +0.0829 | +0.0667 |

Aggregate adapter-minus-generic Answer F1 is `+0.0772`; coverage is `+0.0556`.

## Matched Baselines

The matched baseline package uses the same 45 cases, corpus, dense index,
Qwen3-14B, top-k, maximum retrieval rounds, and evaluator.

| System | Answer F1 | Coverage | Selective F1 | Avg retrieval calls |
|---|---:|---:|---:|---:|
| Adapter incumbent mean | 0.4285 | 0.4556 | 0.9407 | 2.3556 |
| Verifier-guided agentic baseline | 0.1511 | 0.2667 | 0.5667 | 2.4889 |
| Fixed-k infrastructure baseline | 0.2493 | 1.0000 | 0.2493 | 3.0000 |
| Prompt-verifier infrastructure baseline | 0.1111 | 0.2000 | 0.5556 | 1.0000 |

The primary matched comparator is locally verified but is only a closed-corpus
modern-pattern approximation, not a full named-paper reproduction.

## Stable Support, Fragility, And Limits

Stable support:

- correct-certificate and F1 gains are positive in both predeclared blocks;
- shared terminal policy is deterministic conditional on inputs;
- all hard terminal/state safety totals are zero;
- incumbent beats the primary matched local comparator on quality, coverage,
  selective quality, and recorded retrieval cost.

Fragility and limits:

- independent online runs still vary at the per-case certificate/action level;
- only two fresh runs per variant were permitted by the frozen protocol;
- stratified45 is a targeted development surface and may leak design choices;
- exact Self-RAG/Adaptive-RAG/CRAG/FLARE reproduction was not established;
- reliable cross-agent LLM-call accounting is incomplete.

## Verdict And Route

Phase 3 verdict: `stable_support_with_narrowed_attribution`.

Next authorized stage: establish a non-leaking standard MuSiQue dev/test
evaluation with a mechanically audited no-gold runtime contract. Do not begin
300 samples or paper-facing main experiments yet.
