# Non-Leaking Standard MuSiQue Dev Pilot Freeze

Date: 2026-07-16
Parent protocol: `semantic_nonleaking_musique_v1_20260716`
Status: `frozen`

## Purpose

This 12-case pilot validates execution, label isolation, terminal safety, and
the adapter/generic path on official MuSiQue dev contexts. It is not a standard
dev result and cannot be used as the phase-4 headline metric.

## Membership And Assets

- Selection: first four opaque IDs per 2/3/4-hop group after sorting dev label
  sidecar; labels are used only by the offline builder/evaluator.
- Runtime rows / label rows / corpus rows: `12 / 12 / 240`.
- Runtime SHA-256:
  `BCB77328BD0DE352F2F6F03D58565EFA291EDCEACF647D30F15BC01F9B7F907C`.
- Labels SHA-256:
  `454DB3B333F464789B15774B0E889230628CA07928664027703C3DA47BA6C789`.
- Corpus SHA-256:
  `56421F6B53BC4BED89C682598225B6989EF768F4C56BFFC938C23E8D02D6A47F`.

## Frozen Runs

1. adapter incumbent:
   `configs/layer1_siliconflow_qwen3_14b_nonleaking_musique_dev_pilot12_adapter_20260716_s1.yaml`
   (`C110A1C4506607C6E8C2F44480DD957A2FC6FE476E86E79B31C963F656A819C2`)
2. generic-only:
   `configs/layer1_siliconflow_qwen3_14b_nonleaking_musique_dev_pilot12_generic_20260716_s1.yaml`
   (`EDBF2AFDA01B626E6AB5486015D83D2386124E7A9E8CF78A733AAE1D5A6B8E38`)

The configs differ only in run/output identity and deterministic bindings.
Strict acceptance is off in both.

## Hard Validity

- 12 opaque runtime IDs, 12 unique rows, zero skipped, no remaining lock;
- canonical trajectories have empty gold/support, null hop, no official ID, and
  only runtime-safe metadata;
- evidence gain equals retrieval novelty and cannot depend on support labels;
- metrics arise from offline sidecar join after trajectories are complete;
- final unsupported and terminal/state violations are zero;
- no oracle retriever or global cross-question retrieval;
- generic starts only after adapter completes and passes leakage audit.

## Local Verification

- Focused non-leaking tests: `35 passed`.
- Full regression: `659 passed`, `27 subtests`.
- Compileall: pass.
