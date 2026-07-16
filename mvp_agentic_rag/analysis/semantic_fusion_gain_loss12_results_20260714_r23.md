# Semantic Fusion Fixed-12 Gate: R23

Date: 2026-07-14

## Verdict

R23 completed all 12 fixed cases but failed phase 1. It retained all five
R20 gains, recovered two of seven R12 losses, and kept final unsupported at
zero. Phase 2 (Fusion / generic-only stratified45) remains unauthorized.

## Frozen Contract

- Config: `configs/layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_20260714_r23.yaml`
- Config SHA-256: `56B55143AF28532C75CE685E85A9BB472CB36DEFF11CD81136AB07BCD1533F91`
- Dataset SHA-256: `04F15DB77255C0DA10B5F811081D7E2B0ADC3B11572F1D4336959E4654E090FB`
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_20260714_r23`
- Trajectory SHA-256: `9B85263CAB2FCC69B42C9F57343B7AE04DB3C70DC23A9FAE0FF3111D20CCDF03`
- Metrics SHA-256: `17D02E7660071F5EDBEE27CE1459C8945AB63EF4FB9DD81ED4A0B6003EB06990`
- Completion: 12 rows, 12 unique IDs, no remaining run lock, empty stderr.

## Metrics

- Accuracy / EM: `0.5833`
- Answer F1: `0.6667`
- Coverage: `0.7500`
- Selective accuracy: `0.7778`
- Selective F1: `0.8889`
- Average retrieval calls: `2.3333`
- Wasted retrieval rate: `0.5000`
- Final answered unsupported rate: `0.0000`

These are targeted-gate metrics, not distribution-level MuSiQue results.

## Hard Gate

Gains retained (`5/5`):

- `2hop__136179_13529`: `June 1982`
- `2hop__167577_31122`: `18th`
- `3hop1__136129_87694_124169`: `1952`
- `4hop1__161810_583746_457883_650651`: `NBC`
- `4hop1__236903_153080_33897_81096`: `Mario Andretti`

Losses recovered (`2/7`):

- `2hop__194469_83289`: `Matt Bennett`
- `3hop1__144439_443779_52195`: `Francisco Guterres`

Losses not recovered (`5/7`):

- Date: the binding correctly promoted `March 11, 2011`, and trajectory
  metadata recorded the surface reconciliation, but the later slot-ledger
  handoff overwrote the final answer with `2011`.
- Count: a complete local count binding returned `more than 450`; the final
  short-answer surface retained the qualifier instead of the structured
  numeric value `450`.
- Maria: a complete deterministic cast binding returned `Maria Bello`, but a
  state-only call did not replace the stale slot-ledger candidate `Salma
  Hayek`; the generic verifier then exhausted the budget.
- Francisco A: the false canonical hard conflict is fixed, and the first
  repair query was valid. The last repair query degraded to the unnatural
  `East Timor president_of`, and the final-hop passage was never retrieved.
- Oriole: the final round produced a complete, local, conflict-free binding
  for `Oriole Records` that passed typed structured acceptance, but a later
  stochastic generic verifier still forced abstention.

## Safety Replay

- Replayed rows: `12`
- Unsafe failure-candidate transitions: `0`
- Same-round topology update rejections: `0`
- Canonical hop-conflict events: `0`
- Candidate-level contradictions remained unscoped and did not become hard
  hop conflicts.

Replay artifact:
`analysis/semantic_fusion_r23_state_replay_20260714.json`.

## R24 Boundary

R24 may change only the generic structured-handoff boundary and repair-query
surface normalization:

1. reapply safe date/count surface reconciliation after slot-ledger handoff;
2. allow a strict deterministic state-only binding to replace a stale ledger
   candidate;
3. stabilize a complete, local, conflict-free, typed-accepted structured
   final binding with explicit candidate and relation support in cited text;
4. run existing single-hop cleanup on planner repair queries so relation
   identifiers such as `president_of` are not sent to dense retrieval.

Malformed output, parse failure, sentinel candidates, non-local evidence,
incomplete chains, invalid typed decisions, and real conflicts remain
fail-closed. Model, retriever, top-k, three-round budget, dataset, corpus, and
evaluator remain unchanged.

## Decision

Do not enter phase 2. Validate the bounded R24 handoff/query changes with
focused and full tests, freeze a unique config, and rerun the same 12 cases.
