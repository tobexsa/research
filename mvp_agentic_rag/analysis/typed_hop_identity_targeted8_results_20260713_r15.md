# Typed hop identity targeted8 R15 results

## Research question

Can same-round topology identity, structured requirement preservation,
evidence-closed deterministic topology revision, final-slot type inference, and
century verifier synchronization recover the R14 failures without weakening any
candidate or final-answer safety gate?

## Research type and objective

This is an `auxiliary/dev` targeted mechanism gate on the same fixed eight
MuSiQue samples used by R14. The objective is structural validation before any
new stratified45 run.

## Setup

- Config: `configs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r15.yaml`
- Run: `runs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r15`
- Dataset and retriever are unchanged from R14.
- R15 has unique config, output, stdout, and stderr paths.
- Local gate before launch: `597 passed, 27 subtests passed`; compileall and
  diff check passed.
- Network run completed `8/8` in 851.2 seconds; stderr length is zero.

## Results

| Metric | R14 | R15 | Delta |
| --- | ---: | ---: | ---: |
| accuracy / F1 | 0.375 / 0.375 | 0.375 / 0.375 | 0 |
| coverage | 0.375 | 0.375 | 0 |
| selective accuracy / F1 | 1.0 / 1.0 | 1.0 / 1.0 | 0 |
| average calls | 2.500 | 2.625 | +0.125 |
| wasted retrieval | 0.750 | 0.875 | +0.125 |
| standard final unsupported | 0.3333 | 0 | -0.3333 |
| 2-hop accuracy / coverage | 0.6667 / 0.6667 | 1.0 / 1.0 | +0.3333 / +0.3333 |
| 4-hop accuracy / coverage | 0 / 0 | 0 / 0 | 0 |

Per-sample outcome:

- retained: `June 1982`, `18th`;
- recovered: `Nissan Altima`;
- regressed under stochastic verifier truncation: `1952`;
- still abstained: both `Mario Andretti` samples, `two`, and `NBC`.

Structural evidence:

- same-round `topology_update_rejected`: `0`;
- malformed/parse-failure candidate transitions: `0`;
- `hop_schema_drift_ignored`: `0` in the real stored events;
- `unmapped_missing_critical_hint`: `0` in the real stored events;
- `topology_revision_applied`: Nissan complete model chain;
- Nissan round 1 query target became exactly
  `What model of Nissan does Mohammed Atta have?`, and round 2 returned the
  strict deterministic model-chain certificate;
- standard final unsupported became zero because the century acceptance now
  emits a normal supported final verifier record.

## Failure analysis

R15 did not fail because of the new state protocol. All four observed slot
binding parse failures have `finish_reason=length` on both primary and repair
attempts. Responses were truncated at roughly 4.8k–5.9k characters under
`slot_binding_verifier_max_tokens: 1536`:

- Arizona Mario, round 3;
- Liam/1952, round 1;
- NBC, rounds 2 and 3.

This explains both the 1952 stochastic regression and why NBC never reached
its already-implemented deterministic country/network binder in this run. It
also explains the extra calls and worse wasted-retrieval rate. The parser
correctly short-circuited each exhausted failure and caused zero unsafe
candidate transitions.

## Conclusion and decision

Verdict: **partial; R15 gate failed; do not run stratified45**.

The mechanism claims for same-round identity, structured addressing, Nissan
model-chain targeting, and final-answer safety are supported. The claim that
the targeted gate is ready for scale is not supported because 4-hop coverage
remains zero and R14's `1952` recovery was not retained.

The next retry changes exactly one experimental variable: increase only
`slot_binding_verifier_max_tokens` from `1536` to `2304` in a unique R16
targeted8 config. The fastest falsification signal is any remaining
`finish_reason=length`. Stratified45 is deferred to at least R17 and only after
the targeted gate passes.
