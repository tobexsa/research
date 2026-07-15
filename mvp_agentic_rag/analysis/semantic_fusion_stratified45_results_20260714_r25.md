# Semantic Fusion Stratified45: R25

Date: 2026-07-14

## Verdict

R25 completed the 45-case Fusion run with materially higher Answer F1 and
coverage than both R12 and R20, while keeping final answered unsupported at
zero. This is the first half of phase 2; no Fusion-vs-generic-only conclusion
is allowed until R26 completes.

## Identity

- Config SHA-256: `194C75669E907A050C6817985FCA9F2E7DBEAC985C58D32C859B1CFBB6A88F72`
- Trajectory SHA-256: `D516AD0988AB69876BE6599FA904A0FB2D07E1F8EAFFE2F9481E8C33FF24D277`
- Metrics SHA-256: `CF82CF1D934B106BE18623A79A1C3581EBD6544DD401258427F89C4BC8601019`
- Completion: 45 rows, 45 unique IDs, no lock, empty stderr.

## Metrics

- Accuracy / EM / Answer F1: `0.4889 / 0.4889 / 0.4889`
- Coverage: `0.5111`
- Selective accuracy / F1: `0.9565 / 0.9565`
- Average retrieval calls: `2.2889`
- Wasted retrieval rate: `0.5778`
- Final answered unsupported: `0.0000`

Against R12, Answer F1 improves by `+0.1378` and coverage by `+0.1333`.
Against R20, Answer F1 improves by `+0.1889` and coverage by `+0.1778`.

## Hop Slices

- 2-hop: EM/F1 `0.8000`, coverage `0.8667`
- 3-hop: EM/F1 `0.5333`, coverage `0.5333`
- 4-hop: EM/F1 `0.1333`, coverage `0.1333`

## Routing And Safety

- Generic-compatibility steps: `91`
- Strict-certificate steps: `11`
- No-fallback steps: `1`
- Unsafe failure-candidate transitions in replay: `0`
- Canonical hop-conflict events in replay: `0`
- Same-round topology update rejections: `0`

Replay artifact:
`analysis/semantic_fusion_stratified45_r25_state_replay_20260714.json`.

## Decision

Proceed to the frozen R26 generic-only run. Do not enter phase 3 until the
matched paired comparison is complete.
