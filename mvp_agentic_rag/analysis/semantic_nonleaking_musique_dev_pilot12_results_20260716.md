# Non-Leaking Standard MuSiQue Dev Pilot12 Results

Date: 2026-07-16
Protocol: `semantic_nonleaking_musique_v1_20260716`
Pilot freeze: `semantic_nonleaking_musique_dev_pilot12_freeze_20260716.md`
Status: `complete_valid_nonleaking_pilot_only`

## Scope

This is a 12-case execution and leakage pilot over the official MuSiQue dev
contexts, stratified as four opaque examples from each of the 2-hop, 3-hop,
and 4-hop groups. It is not the 2,417-case standard dev result and must not be
reported as a headline benchmark result.

Both runs use the same runtime samples, candidate-scoped BM25 retriever,
non-leaking novelty ledger, model/backend settings, shared fail-closed terminal
guard, and strict certificate acceptance off. The only method-relevant config
difference is deterministic slot-binding adapters on versus off.

## Results

| Flow | Completed | EM | Answer F1 | Coverage | Selective F1 | Avg retrieval calls | Wasted retrieval | Final unsupported |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Adapter incumbent | 12/12 | 0.0833 | 0.1917 | 0.2500 | 0.7667 | 2.6667 | 0.3333 | 0 |
| Generic-only | 12/12 | 0.1667 | 0.2083 | 0.2500 | 0.8333 | 2.5000 | 0.1667 | 0 |
| Adapter minus generic | -- | -0.0833 | -0.0167 | 0.0000 | -0.0667 | +0.1667 | +0.1667 | 0 |

The two flows made the same terminal answer/abstain choice on all 12 examples:
both answered exactly three opaque IDs and abstained on the other nine.

| Opaque ID | Adapter answer | Generic answer | Surface relation |
|---|---|---|---|
| `q_00b7b7947d662df65733c4d0` | `Plymouth Notch, Vermont` | `Plymouth Notch` | semantically compatible, not exact-string identical |
| `q_00ba96c23347b8d74456e3af` | `Bering Sea` | `Bering Sea` | identical |
| `q_0056b70f2e6a2356f20bfa03` | `KUAT-TV 6` | `KUAT-TV 6` | identical |

Therefore the `+0.0167` generic Answer F1 difference is an answer-surface
variation on a shared answer set, not evidence that the generic terminal
policy selected better cases.

## Mechanism Activation

- Adapter activation markers: `0/12` in the adapter run. No deterministic
  binding reason (`deterministic_*`) appears in its canonical trajectories.
- Generic activation markers: `0/12`, as expected with deterministic bindings
  disabled.
- Strict-certificate eligible examples: `0/12` in each run.
- Strict-on versus strict-off replay action changes: `0/12` in each run.
- Replay terminal-invariant violations: `0` in each run.

The adapter run consequently exercised the shared generic path, not a
deterministic adapter path. The pilot provides no standard-distribution
evidence for an adapter effect, positive or negative. Its small metric
difference primarily reflects online generation and answer-surface variation.

## Leakage And Safety Audit

| Check | Adapter | Generic |
|---|---:|---:|
| Leakage audit valid | true | true |
| Opaque trajectory rows | 12 | 12 |
| Retrieval-novelty steps checked | 32 | 30 |
| Leakage violations | 0 | 0 |
| Official/source IDs in trajectories | 0 | 0 |
| Gold/support/hop leakage | 0 | 0 |
| Scoped-retrieval violations | 0 | 0 |
| State/terminal safety violations | 0 | 0 |

Canonical trajectory SHA-256:

- adapter:
  `E1AE6CE5E1B5AAFAEB11DD71EFEB2EE952C3F2A273FB803FD58155801745EC17`;
- generic:
  `F0381AF9E9F72E538E4B8AD2BAB95F0E91921C52AA08063CD4EE7A2ACF4D1124`.

Metrics SHA-256:

- adapter:
  `668FEA06A599E6D18E9F5B07C186519EAD010F21ADACF2F67563E9666A6BFB4F`;
- generic:
  `8626DAEAA65E615212E610D59FAC0E74C33CD313D2C8AC1DB53D57351048354F`.

## Interpretation Boundary

The targeted45 campaign still supports a narrow statement: the existing
deterministic adapters improve that relation-heavy development distribution
under the shared fail-closed guard. This pilot blocks a broader statement that
the same adapters already generalize to standard MuSiQue. With zero observed
activation, the targeted45 adapter advantage cannot be extrapolated to the
official dev distribution.

## Full-Dev Cost Projection

Observed pilot wall-clock time was approximately `1,306.7 s` for adapter and
`1,687.6 s` for generic across 12 examples. Linear projection to 2,417 dev
examples gives:

- adapter flow: approximately `73.1 h`;
- generic flow: approximately `94.4 h`;
- both flows: approximately `167.5 h`, with a practical planning range of
  roughly `140-190 h` before retries or service instability.

Spending this budget while adapter activation remains zero would mostly
measure the shared generic path and API variance. Full dev is therefore not
authorized by this pilot.

## Evidence Paths

- `runs/layer1_siliconflow_qwen3_14b_nonleaking_musique_dev_pilot12_adapter_20260716_s1/`
- `runs/layer1_siliconflow_qwen3_14b_nonleaking_musique_dev_pilot12_generic_20260716_s1/`
- `analysis/semantic_nonleaking_dev_pilot12_adapter_leakage_audit_20260716.json`
- `analysis/semantic_nonleaking_dev_pilot12_generic_leakage_audit_20260716.json`
- `analysis/semantic_nonleaking_dev_pilot12_adapter_state_replay_20260716.json`
- `analysis/semantic_nonleaking_dev_pilot12_generic_state_replay_20260716.json`
- `analysis/semantic_nonleaking_dev_pilot12_adapter_shared_replay_20260716.json`
- `analysis/semantic_nonleaking_dev_pilot12_generic_shared_replay_20260716.json`

