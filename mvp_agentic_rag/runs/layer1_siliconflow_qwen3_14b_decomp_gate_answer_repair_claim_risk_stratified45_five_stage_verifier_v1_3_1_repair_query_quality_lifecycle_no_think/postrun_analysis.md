# v1.3.1 Repair Query Quality / Lifecycle Post-run Analysis

## Run status

- Run: `layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_1_repair_query_quality_lifecycle_no_think`
- Model/API: SiliconFlow `Qwen/Qwen3-14B`
- Dataset: `data/musique_mvp_stratified45.jsonl`
- Initial state: interrupted partial run with `18 / 45` rows in `trajectories.jsonl`
- Resume path: reran the same config; `layer1_runner._load_completed_keys()` skipped the existing 18 `(id, method)` records and appended the remaining rows.
- Final state: completed `45 / 45`, no duplicate `(id, method)` keys, no residual `.run.lock`
- Output files: `trajectories.jsonl`, `metrics.json`, `metrics.md`, `run_summary.md`, `postrun_analysis.md`

## Interruption diagnosis

The partial run left `.run.lock` containing PID `13992`, but that process was no longer alive. The stdout log stopped at `completed=15` while `trajectories.jsonl` contained 18 valid JSONL rows. Stderr was empty.

This pattern is most consistent with an external abrupt termination after row 18, not a Python exception:

- Python exceptions would normally produce stderr and run the context manager cleanup path.
- Normal completion would remove `.run.lock` and write metrics.
- The partial `trajectories.jsonl` parsed cleanly, so the interrupted state was safe to resume.

One foreground resume attempt failed inside the sandbox with `WinError 10013` while opening the SiliconFlow HTTPS connection. After network permission was available, the same resume command completed.

## Headline metrics

| metric | v1.2.9 reference | v1.3.0 observed | v1.3.1 observed | delta vs v1.3.0 |
| --- | ---: | ---: | ---: | ---: |
| overall_acc | 0.1556 | 0.1556 | 0.1556 | +0.0000 |
| overall_em | 0.1556 | 0.1556 | 0.1556 | +0.0000 |
| answer_f1 | 0.2133 | 0.1815 | 0.2059 | +0.0244 |
| coverage | 0.2444 | 0.2222 | 0.2444 | +0.0222 |
| selective_acc | 0.6364 | 0.7000 | 0.6364 | -0.0636 |
| selective_answer_f1 | 0.8727 | 0.8167 | 0.8424 | +0.0258 |
| cost_normalized_acc | 0.0673 | 0.0619 | 0.0642 | +0.0023 |
| cost_normalized_f1 | 0.0923 | 0.0723 | 0.0850 | +0.0127 |
| avg_retrieval_calls | 2.3111 | 2.5111 | 2.4222 | -0.0889 |
| wasted_retrieval_rate | 0.7333 | 0.8222 | 0.7778 | -0.0444 |
| final_answered_unsupported_rate | 0.0000 | 0.0000 | 0.0000 | +0.0000 |

v1.3.1 recovers some utility relative to v1.3.0, but it does not beat the v1.2.9 reference on answer F1 or cost-normalized F1. The safety invariant `final_answered_unsupported_rate = 0` is preserved.

## Hop-level metrics

| hop | answered / count | overall_acc | answer_f1 | coverage | selective_acc | selective_answer_f1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2hop | 8 / 15 | 0.3333 | 0.4311 | 0.5333 | 0.6250 | 0.8083 |
| 3hop | 3 / 15 | 0.1333 | 0.1867 | 0.2000 | 0.6667 | 0.9333 |
| 4hop | 0 / 15 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

The main unresolved bottleneck remains 4-hop recovery: v1.3.1 still answers `0 / 15` 4-hop samples.

## Final-action and repair lifecycle

Final actions:

- `answer`: 11 / 45
- `abstain`: 34 / 45

Repair lifecycle steps: 42

| repair_query_quality_bucket | count |
| --- | ---: |
| under-specified | 17 |
| entity-only | 12 |
| useful | 11 |
| relation-only | 2 |

| repair_closed | count |
| --- | ---: |
| repair_unresolved_terminal | 28 |
| repair_rejected | 7 |
| repair_expired | 5 |
| repair_superseded_by_final_answer | 1 |
| accepted_final | 1 |

The v1.3.1 instrumentation is useful: it replaces the prior ambiguous pending state with explicit terminal states and exposes that most failed repair attempts are still low-quality query problems, especially `under-specified` and `entity-only`.

## Full-300 gate

v1.3.1 should not enter full-300.

| gate | threshold | v1.3.1 | status |
| --- | ---: | ---: | --- |
| overall_acc / EM | >= 0.20 | 0.1556 | fail |
| answer_f1 | >= 0.27 | 0.2059 | fail |
| coverage | >= 0.40 | 0.2444 | fail |
| cost_normalized_f1 | >= 0.125 | 0.0850 | fail |
| 4-hop coverage | > 0 | 0.0000 | fail |
| final_answered_unsupported_rate | 0 | 0.0000 | pass |

## Recommendation

Do not scale v1.3.1. Treat it as a successful observability and lifecycle-cleanup run, not as a full-300 candidate. The next experiment should target repair query generation itself:

1. Block or rewrite `under-specified`, `entity-only`, and `relation-only` repair queries before retrieval.
2. Use missing-hop text plus original question context to construct relation-specific repair queries.
3. Keep the final-answer safety gate unchanged.
4. Add a 4-hop canary slice so any claimed recovery must answer at least one 4-hop case without increasing `final_answered_unsupported_rate`.
