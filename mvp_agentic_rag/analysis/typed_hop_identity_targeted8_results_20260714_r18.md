# Semantic certificate targeted8 R18 result

## Verdict

R18 is a valid completed run and a large improvement over R17, but it narrowly
fails the fixed gate because only 2/3 two-hop samples were retained. It does
not authorize stratified45.

## Frozen run and headline metrics

- Config: `configs/layer1_siliconflow_qwen3_14b_semantic_certificate_targeted8_20260714_r18.yaml`
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_certificate_targeted8_20260714_r18`
- Stdout/stderr: unique R18 files under `runs/logs/`; stderr is zero bytes.
- Completed: 8/8; `.run.lock` removed normally; metrics written.

| Metric | R17 | R18 | Delta |
| --- | ---: | ---: | ---: |
| Accuracy | 0.250 | 0.625 | +0.375 |
| F1 | 0.250 | 0.625 | +0.375 |
| Coverage | 0.250 | 0.625 | +0.375 |
| Selective accuracy | 1.000 | 1.000 | 0 |
| Average retrieval calls | 2.250 | 2.375 | +0.125 |
| Wasted retrieval rate | 0.375 | 0.375 | 0 |
| Final answered unsupported | 0 | 0 | 0 |

Correct answers: `June 1982`, `1952`, `NBC`, East-Coasting `Mario Andretti`,
and `Nissan Altima`. Abstentions: `18th`, Arizona `Mario Andretti`, and `two`.

## Gate audit

- Slot binding structured attempts: 19/19 `finish_reason=stop`.
- Length/parse/malformed: 0.
- Final unsupported: 0.
- Sentinel candidate transition/state: 0.
- Topology update/revision rejection: 0.
- 2-hop retained: 2/3, failed (`18th` regressed).
- `1952`: restored in two rounds, passed.
- At least one 4-hop correct: passed; NBC and East Coasting are both correct.

## Mechanism evidence

- `June 1982` answered in one round from the deterministic signing certificate,
  versus three retrieval calls and abstention in R17.
- `1952` kept Mantua -> Saint Peter verified, queried only `St. Peter's
  Basilica located_in`, then verified all three hops and answered.
- NBC preserved empty Country A/program country in round 1. Round 2 certified
  Philippines as bay/mission country and Brunei as embassy host/Country A/
  program country, then bound NBC. It answered in two rounds.
- East Coasting logged the two derived queries `Arizona largest city by
  population` and `Phoenix Indy Car race winner` in round 3, then verified the
  four-hop Charles Mingus chain and answered.
- Arizona's three-hop deterministic certificate and typed binding passed, but
  the generic verifier did not accept the negative-form largest-city evidence;
  the sample abstained. This does not invalidate evidence-to-hop binding, but
  exposes a later certificate/final-sufficiency arbitration limitation.

## Sole gate-blocking defect

The first `18th century` binding was role-rejected. Later rounds returned the
same candidate with a complete, conflict-free, typed-accepted binding over the
same evidence, but candidate bookkeeping required new evidence before clearing
the old rejection. The stale rejected status therefore survived even after
strict semantic correction. Round 2 also produced the canonicalizer variant
`18th.`, which the century evidence exception accepted only without trailing
punctuation.

The minimal R19 change is restricted to:

1. allow a previously rejected candidate to become verified on the same
   evidence only when the new record itself satisfies strict explicit verified
   binding and has no current reject/conflict category;
2. clear stale reject metadata on that transition and ensure the next repeated
   round produces no transition;
3. normalize terminal punctuation on a century ordinal.

Offline replay of the real R18 `18th` trajectory now changes round 2 from
rejected to verified with reason `strict_binding_clears_stale_rejection`, then
reports `await_final_gates`; a repeated round is idempotent. Full tests pass:
`608 passed, 27 subtests passed`, plus compileall and scoped diff check.

## Decision

Run one uniquely named R19 on the same fixed targeted8. Keep all model, data,
retrieval, token, round, safety, and metric settings identical. Do not create
stratified45 unless R19 passes every existing gate simultaneously.
