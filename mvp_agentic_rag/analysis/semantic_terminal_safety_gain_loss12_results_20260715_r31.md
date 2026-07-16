# Terminal Safety Repair Fixed-12 Gate: R31

Date: 2026-07-15

## Verdict

R31 is complete and safe, but it is rejected as a pass of the old
per-execution 12/12 regression gate. It retains all 5/5 prior gain cases but
only 5/7 prior loss cases, for 10/12 overall. Final answered unsupported,
terminal invariant violations, and unsafe structural replay transitions are
all zero.

This was the single authorized identity-only retry after R30. No R32 retry or
post-result tuning is authorized.

## Frozen Identity And Completion

- Rows / unique IDs: `12 / 12`.
- Completed / skipped: `12 / 0`.
- Runtime: `1330.4` seconds.
- R31 differs mechanically from R30 only in `run_name` and `output_dir`.
- Config SHA-256:
  `680A2BE6BD40DA7014F3B2CCCC880BFE18A28D4D0D788F09029A0ADF2D2ED69F`.
- Dataset SHA-256:
  `04F15DB77255C0DA10B5F811081D7E2B0ADC3B11572F1D4336959E4654E090FB`.
- Trajectory SHA-256:
  `9CCAA3C8861639A175AF0C6FA3F4424E63ED8A8868CCD2B83205B96FC85A6562`.
- Metrics SHA-256:
  `FEC30B1BF4C8400A4F747A62EC8F1EE88040AC34F8E50CF965FCDF0D0B82B452`.
- Replay SHA-256:
  `FF9E3A9D89B7558E762F4948FEFC8DAF4A981F24D703D8EDEE41DBCBBCBCED1D`.

## Metrics And Hard Gates

- Accuracy / EM / Answer F1: `0.8333 / 0.8333 / 0.8333`.
- Coverage: `0.8333`.
- Selective accuracy / selective F1: `1.0000 / 1.0000`.
- Average retrieval calls: `2.0833`.
- Wasted retrieval rate: `0.2500`.
- Final answered unsupported rate: `0`.
- Terminal invariant violation count: `0`.
- Unsafe structural replay transitions: `0`.
- Gains retained: `5/5`.
- Losses recovered: `5/7`.

The raw metric `unsupported_claim_rate=0.6667` is an intermediate-trajectory
diagnostic and must not be confused with final answered unsupported. The
accepted-answer safety metric is `final_answered_unsupported_rate=0`.

## Routing And Adapter Activation

- Strict-certificate steps: `8`.
- Generic-compatibility steps: `17`.
- No-fallback steps: `0`.
- Final strict/generic samples: `4 / 8`.
- Recognized deterministic adapter marker applications: `12`.
- Terminal answer-to-abstain downgrades: `1`.

R31 therefore has nonzero strict treatment activation. It is not another
strict-on/zero-activation cell like R28.

## Two Failed Cases

### `2hop__247353_55227` — upstream verifier/controller abstention

- Gold: `Maria Bello`.
- Final action: abstain after three generic-compatibility rounds.
- The deterministic cast binding repeatedly found `Maria Bello`, with
  `supports_slot=true`, `chain_complete=true`, and local evidence `p6/p17`.
- The final verifier nevertheless emitted an unsupported claim for `Salma
  Hayek`, `overall_sufficiency=insufficient`, and `need_more_evidence=true`.
- The controller's original terminal action was already abstain.
- The repaired terminal guard did not run an answer downgrade and has no block
  reasons on this row.

Classification: online verifier/candidate instability upstream of the terminal
repair, not a guard regression.

### `3hop1__140786_2053_5289` — intended non-local-evidence block

- Gold: `Oriole Records.`.
- The final binding found `Oriole Records` with a complete, slot-supporting
  certificate.
- The final verifier called its two claims supported and sufficient, but one
  critical claim cited several passage IDs that were not retrieved in this
  sample execution.
- The controller's original terminal action was answer.
- The repaired guard changed answer to abstain with the single reason
  `final_claim_nonlocal_evidence`.

Classification: direct activation of the new fail-closed invariant. The
surface answer happens to match gold, but accepting it would violate the
predeclared local-evidence contract. It is therefore a performance loss under
the safety policy, not evidence that the safety check should be removed.

## R30 Versus R31 Identity-Only Stability

Both runs finish at 10/12 and final unsupported zero, but their case outcomes
are not identical:

| Sample | R30 | R31 | Interpretation |
|---|---|---|---|
| `2hop__167577_31122` | abstain | correct `18th` | R30 upstream abstention recovered without a code/config change |
| `2hop__247353_55227` | correct `Maria Bello` | abstain | a new upstream verifier/candidate failure appeared |
| `3hop1__140786_2053_5289` | abstain | abstain | same outcome, but R30 was upstream insufficient while R31 was a local-evidence guard block |

The changed failure identity and changed causal path under an identity-only
retry confirm that a single online execution is not a deterministic code
regression oracle.

## Claim Validation

| Claim | Observable | R31 result | Verdict |
|---|---|---|---|
| The repair prevents unsafe terminal answers | final unsupported and terminal replay invariants | both zero | supported |
| The repaired fixed-12 online gate is stable at 12/12 | R30/R31 identity-only outcomes | both 10/12; failure set shifts | refuted |
| Every R31 abstention was caused by the new guard | per-case terminal original action and downgrade | only Oriole was downgraded | refuted |
| Strict routing actually activated in R31 | strict lane steps | 8 | supported |
| The Oriole downgrade is a false safety block | local evidence contract | verifier cited unretrieved IDs | not supported; the block matches the frozen rule |

## Evidence Paths

- Run directory:
  `runs/layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_terminal_safety_20260715_r31`
- Replay:
  `analysis/semantic_terminal_safety_r31_state_replay_20260715.json`
- Frozen contract:
  `analysis/semantic_terminal_safety_r31_run_contract_20260715.md`
- Failure campaign:
  `analysis/semantic_terminal_safety_r31_failure_campaign_results_20260715.md`

## Runtime Interface Degradation

The runtime did not expose managed `bash_exec`, artifact, or memory interfaces.
The run, hashes, replay, and repository-local reports are durable fallback
evidence, not artifact-service records.
