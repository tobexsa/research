# Semantic Adapter-Only Stratified45: R27

Date: 2026-07-15

## Verdict

R27 completed the adapter-only cell of the phase-3 2x2 component design.
With strict-certificate routing disabled and deterministic adapters enabled,
Answer F1 and coverage both improve over the matched R26 generic-only run by
`+0.0667`, but remain `-0.0444` below full R25 Fusion. Final answered
unsupported remains zero. R28 is still required before attributing the
remaining difference to the strict lane or to interaction.

## Identity And Completion

- Config SHA-256:
  `14F20854C5F4C89E27CAAF8D044BD1307AB80BE15C3E1E8E1B33BAA5CE192D95`
- Dataset SHA-256:
  `2B4A0DFAD40AC8B120FF59862FCBF216C5AD419EC7E2783E35534281653D63A5`
- Trajectory SHA-256:
  `E7420BAE3AA3B6926BECB0CAF899C6C9DE809F27DD0AB424E761FC9AC6C0AC6C`
- Metrics SHA-256:
  `5040FBC9F99A2CD4A0B7D68F29841829C0C2ABE2D3910CE48FE64B9AD5FB3814`
- Replay SHA-256:
  `1C7EC9F6B00C5C83A766A16BBD6C170551BAE0F20BC87F4B0BEE78C035A6F635`
- Completion: 45 rows, 45 unique IDs, no remaining lock, empty stderr,
  complete finite metrics.

## Metrics

- Accuracy / EM / Answer F1: `0.4444 / 0.4444 / 0.4444`
- Coverage: `0.4667`
- Selective accuracy / F1: `0.9524 / 0.9524`
- Average retrieval calls: `2.4222`
- Wasted retrieval rate: `0.6000`
- Final answered unsupported: `0.0000`

Relative to R26 generic-only:

- Answer F1: `+0.0667`
- Coverage: `+0.0667`
- Selective accuracy: `+0.0079`
- Average retrieval calls: `+0.0222`
- Wasted retrieval rate: `-0.0889`

Relative to R25 full Fusion:

- Answer F1: `-0.0444`
- Coverage: `-0.0444`
- Selective accuracy: `-0.0041`
- Average retrieval calls: `+0.1333`
- Wasted retrieval rate: `+0.0222`

## Hop Slices

- 2-hop: EM/F1 `0.6667`, coverage `0.7333`
- 3-hop: EM/F1 `0.6000`, coverage `0.6000`
- 4-hop: EM/F1 `0.0667`, coverage `0.0667`

Each hop slice is `+0.0667` Answer F1 above R26. Relative to R25, R27 is
lower on 2-hop and 4-hop but higher on 3-hop. This reinforces the need for the
remaining strict-only cell rather than a one-dimensional attribution.

## Paired Correctness

Against R26 generic-only:

- R27-only correct: 4
- R26-only correct: 1
- Both correct: 16
- Both wrong: 24

R27-only IDs:

- `2hop__132854_417697`
- `2hop__247353_55227`
- `3hop1__145194_160545_62931`
- `4hop1__161810_583746_457883_650651`

R26-only ID:

- `2hop__23459_35124`

Against R25 Fusion, R27 has one exclusive correct case and R25 has three;
both are correct on 19 and wrong on 22.

## Routing, Adapter, And Safety Audit

- Generic-compatibility steps: 106
- Strict-certificate steps: 0, as required
- No-fallback steps: 3
- Recognized deterministic adapter marker applications: 20
- Topology-only compatibility markers: 0
- Unsafe failure-candidate transitions in replay: 0
- Canonical hop-conflict events in replay: 0
- Same-round topology update rejections: 0
- Structured legacy requirement items: 0

Replay artifact:
`analysis/semantic_adapter_only_stratified45_r27_state_replay_20260715.json`.

The replay command wrote the UTF-8 artifact successfully, then the Windows GBK
console failed while printing the complete JSON because one sample contained a
non-GBK character. Direct UTF-8 parsing of the durable artifact passed and all
reported replay invariants were verified.

## Decision

R27 passes its component-slice gate. Proceed serially to frozen R28
strict-only. Do not compute a 2x2 interaction or begin repeats until R28 is
complete and audited.
