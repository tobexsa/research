# Phase-4 Non-Leaking Standard MuSiQue Evaluation Plan

Date: 2026-07-16
Protocol id: `semantic_nonleaking_musique_v1_20260716`
Status: `pilot_complete_full_dev_held_for_route_decision`

## Objective And Order

Build a mechanically non-leaking evaluation path over the official
MuSiQue-Ans v1.0 dev and test splits after phase 3 completed. The promoted
incumbent remains deterministic adapters plus the shared fail-closed generic
terminal guard with strict acceptance off. Generic-only remains the required
ablation comparator.

This phase must finish before the old 300-sample or paper-facing main
experiment is considered.

## Official Source Identity

| Split | Rows | Gold/decomposition | SHA-256 |
|---|---:|---|---|
| train | 19,938 | present | `83A75B1E11E4E9BB8F8308E72AC40CA617AE4431B3A0D955B61CAB259248490A` |
| dev | 2,417 | present | `15FA63794D18A94CE12411ACA6E2327E65B6E83B0B1490EFAB3F1962E48ABF3B` |
| test | 2,459 | absent | `92EE3067957B8EBCE885BAA71156A7C0C29F3BC72CCA04510AEF506911DD768F` |

All train/dev/test source ID intersections are empty.

The official test file has no answer or decomposition labels. Phase 4 can
produce audited blind test predictions and a submission map, but local test
EM/F1 is impossible without an official hidden-label evaluator.

## Leakage Findings To Remove

- `EvidenceLedger.add_retrieved()` currently computes gain from gold
  `supporting_passage_ids`; gain affects controller and retrieval behavior.
- heuristic answer and verifier paths read `gold_answer` and gold support IDs.
- oracle retrieval directly prioritizes support IDs.
- the runner writes gold fields into online trajectories before evaluation.
- source sample IDs expose hop/decomposition identity.

Existing targeted results remain development evidence and are not relabeled as
non-leaking.

## Frozen Runtime Contract

The builder must create:

- opaque question IDs and opaque passage IDs;
- runtime sample JSONL containing only opaque ID, question, candidate passage
  IDs, and a non-sensitive runtime marker;
- corpus JSONL containing title/text and no support metadata;
- dev label sidecar containing gold answer, aliases, support IDs, hop, and
  source ID, never loaded by agents/retriever/controller;
- test submission map containing opaque-to-official ID mapping, never loaded by
  agents;
- manifest with source/output hashes, counts, field allowlists, and overlap
  audit.

Online trajectories must contain empty/no gold answer, no gold support IDs, no
hop, no decomposition, and no official sample ID. Dev labels are joined only
in evaluator memory after trajectory completion. Joined labeled trajectories
must not be written back as the canonical online trajectory.

## Retrieval And Evidence Gain

- Use a per-question scoped retriever over the official candidate paragraphs
  supplied in runtime-safe metadata: dev has 17–20 and test has 18–20.
- Do not use the oracle retriever.
- In `non_leaking_runtime_v1`, retrieval gain is passage novelty, not gold
  support recall.
- Verifier-cited evidence IDs may become accepted runtime evidence after the
  verifier response; gold support IDs never do.

## Execution Stages

1. Implement converter, scoped retriever, blind runner/evaluator join, and
   novelty ledger mode.
2. Add unit/integration tests proving no runtime gold/support/decomposition
   access and exact offline label join.
3. Build official dev/test runtime assets and audit their hashes/fields.
4. Run deterministic/fake-LLM smoke on a bounded dev subset only.
5. Freeze a real dev pilot before any full standard dev call budget.
6. Freeze full dev evaluation only after pilot validity and cost are known.
7. Keep official test untouched until the dev protocol and method are frozen;
   then generate blind predictions only. Report no local test EM/F1.

## Post-Pilot Update

The frozen 12-case adapter and generic pilots both completed and passed the
leakage, scoped-retrieval, state-replay, and terminal-safety audits. However,
deterministic adapter activation and strict-certificate eligibility were both
`0/12`; the two runs made the same answer/abstain choice on every example.

Accordingly, stage 6 is not yet authorized. The full two-flow dev cost is
projected at approximately `140-190 h`, and running it now would mostly measure
the shared generic path. The evidence and route frontier are frozen in:

- `analysis/semantic_nonleaking_musique_dev_pilot12_results_20260716.md`;
- `analysis/semantic_nonleaking_musique_post_pilot_decision_20260716.md`.

No full dev, blind test prediction, 300-sample, or paper-main run starts until
the post-pilot route is selected and its corresponding protocol is frozen.

## Hard Gates

- no runtime label or source-ID fields;
- zero train/dev/test official ID overlap;
- corpus support metadata absent;
- no oracle/sample-support retrieval;
- no support-derived evidence gain;
- canonical trajectories remain blind;
- dev evaluator label IDs match trajectory IDs exactly;
- test path cannot invoke labeled metrics;
- source/config/code changes after freeze require a new protocol version.

## Runtime Degradation

Managed `bash_exec`, artifact, and memory services are unavailable. PowerShell,
repository-local plans/tests/manifests, and hashes are the durable fallback.
