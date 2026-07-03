# Partial Run Note

Status: incomplete external-API run.

Command:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_decomp_gate_answer_repair_claim_evidence_checklist_query_clean_v2_multiquery_question_repeat_no_gain_stop_claim_risk_full300.yaml
```

Run started after the matching real subset30 candidate passed the entry gate.

## Interruption

The run stopped after 349 trajectory rows out of the expected 900 rows. The output lock was released normally and there were no duplicate `(method, id)` rows.

The failing request was:

```text
method: agentic_rag_baseline
sample_id: 3hop1__248929_160713_77246
stage: answer generation
```

The SiliconFlow API response was:

```json
{"code":30001,"message":"Sorry, your account balance is insufficient","data":null}
```

This is an external account-balance failure, not a metric verdict and not a completed full300 result.

## Resume Contract

The runner resumes from completed `(sample_id, method)` pairs in `trajectories.jsonl`. After the SiliconFlow account has balance again, rerun the same command above. It should skip the 349 completed rows and continue from:

```text
method: agentic_rag_baseline
sample_id: 3hop1__248929_160713_77246
```

The partial diagnostic metrics were moved to:

```text
metrics_partial_349.json
metrics_partial_349.md
```

They are for diagnosis only and must not be reported as full300 metrics.
