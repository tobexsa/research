# Semantic Generic-Only Stratified45: R26

Date: 2026-07-14

## Verdict

R26 completed the matched generic-only 45-case run. It is weaker than Fusion
R25 on Answer F1, coverage, retrieval efficiency, and paired correctness,
while both keep final answered unsupported at zero.

## Identity

- Config SHA-256: `1D71BBE5C629E88448AEEE5F64E7F72A6F94070E00A90820C9A2FA2BE429A693`
- Trajectory SHA-256: `F577401B5BC2FF16C9CA56A2D53F3F613B1D61942B42AA71A31BF5A6D09FBF39`
- Metrics SHA-256: `19019A0A85377505A0BBD5C1ED1BA25E2044C497F04BDA9A5F02A3926E3615FB`
- Completion: 45 rows, 45 unique IDs, no lock, empty stderr.

## Metrics

- Accuracy / EM / Answer F1: `0.3778 / 0.3778 / 0.3778`
- Coverage: `0.4000`
- Selective accuracy / F1: `0.9444 / 0.9444`
- Average retrieval calls: `2.4000`
- Wasted retrieval rate: `0.6889`
- Final answered unsupported: `0.0000`

## Matched Audit

- Strict-certificate lane steps: `0`
- Generic-compatibility steps: `107`
- No-fallback steps: `1`
- Recognized deterministic certificate-adapter markers: `0`
- Topology-only compatibility marker: one
  `final_hop_order_canonicalization`; this is a generic schema ordering repair,
  not a candidate certificate adapter.
- Unsafe failure-candidate transitions in replay: `0`
- Canonical hop-conflict events in replay: `0`
- Same-round topology update rejections: `0`

Replay artifact:
`analysis/semantic_generic_only_stratified45_r26_state_replay_20260714.json`.

## Fusion Delta

R25 minus R26:

- Answer F1 / EM: `+0.1111`
- Coverage: `+0.1111`
- Selective accuracy: `+0.0121`
- Average retrieval calls: `-0.1111`
- Wasted retrieval rate: `-0.1111`
- Final answered unsupported: unchanged at `0`

Paired correctness:

- Fusion-only correct: `6`
- Generic-only correct: `1`
- Both correct: `16`
- Both wrong: `22`

## Decision

Phase 2 is complete. Proceed to phase 3 component ablations, independent
repeats, and matched modern baselines. The fixed-12 and 45-case results are
development evidence, not yet a standard non-leaking MuSiQue benchmark claim.
