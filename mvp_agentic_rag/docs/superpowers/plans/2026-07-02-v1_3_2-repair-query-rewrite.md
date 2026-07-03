# v1.3.2 Repair Query Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic v1.3.2 repair-query rewriting for under-specified, entity-only, relation-only, and wrong-direction repair queries without loosening final-answer safety gates.

**Architecture:** Keep the change inside `ClaimRiskAgent` repair metadata construction. Classify the initially generated repair query, optionally rewrite bad buckets from ordered-hop and verifier context, reclassify, then preserve before/after metadata for audit. Retrieval may use the rewritten query, but answer acceptance gates remain unchanged.

**Tech Stack:** Python 3.12, pytest, existing MVP Agentic RAG test helpers.

---

### Task 1: Add RED Tests for Repair Query Rewrite

**Files:**
- Modify: `mvp_agentic_rag/tests/test_claim_risk_agent.py`

- [ ] **Step 1: Write failing tests**

Add tests near `test_repair_query_quality_classifier_covers_expected_buckets` and ordered-hop repair tests:

```python
def test_v1_3_2_rewrites_relation_only_repair_query_with_bridge_entity(self) -> None:
    ...
    self.assertEqual("Apple Records parent company", record["repair_next_query"])
    self.assertEqual("parent company", record["repair_query_original"])
    self.assertTrue(record["repair_query_rewrite_attempted"])
    self.assertTrue(record["repair_query_rewritten"])
    self.assertEqual("relation-only", record["repair_query_quality_bucket_before_rewrite"])
    self.assertEqual("useful", record["repair_query_quality_bucket"])
```

Also add entity-only and under-specified variants.

- [ ] **Step 2: Verify RED**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Expected: fails because rewrite metadata and behavior do not exist.

### Task 2: Implement Deterministic Rewrite

**Files:**
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/agents/claim_risk_agent.py`

- [ ] **Step 1: Add helper methods**

Add focused helpers on `ClaimRiskAgent`:

```python
def _maybe_rewrite_repair_query_v1_3_2(self, sample, record, verifier_output, query: str, quality: dict) -> tuple[str, dict, dict]:
    ...

def _repair_query_rewrite_candidates(self, sample, record, verifier_output, query: str) -> list[tuple[str, str]]:
    ...
```

- [ ] **Step 2: Integrate inside `_build_repair_metadata`**

After initial classification and before returning metadata, optionally rewrite when:

```python
bool(self.config.get("repair_query_rewrite_v1_3_2", False))
quality["bucket"] in {"under-specified", "entity-only", "relation-only", "wrong-direction"}
```

- [ ] **Step 3: Preserve metadata**

Record `repair_query_original`, `repair_query_rewrite_attempted`, `repair_query_rewritten`, `repair_query_rewrite_reason`, `repair_query_rewrite_source`, `repair_query_quality_bucket_before_rewrite`, and `repair_query_quality_reason_before_rewrite`.

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Expected: focused tests pass.

### Task 3: Add Safety Regression Test

**Files:**
- Modify: `mvp_agentic_rag/tests/test_claim_risk_agent.py`

- [ ] **Step 1: Write failing or guarding test**

Add a test proving rewritten retrieval does not bypass safety gates. Configure fake slot binding / final verifier so the repair query retrieves new evidence, but final validation rejects; assert final action remains `abstain`.

- [ ] **Step 2: Run focused test**

Run:

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

Expected: pass after Task 2; if it fails, fix only gate-preserving logic.

### Task 4: Add v1.3.2 Config

**Files:**
- Create: `mvp_agentic_rag/configs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think.yaml`

- [ ] **Step 1: Copy v1.3.1 config**

Duplicate v1.3.1 SiliconFlow config and update:

```yaml
run_name: layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think
output_dir: runs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think
repair_query_rewrite_v1_3_2: true
```

### Task 5: Final Verification

**Files:**
- No new files unless failures require fixes.

- [ ] **Step 1: Run focused tests**

```powershell
D:\python1\python.exe -m pytest tests\test_claim_risk_agent.py -q
```

- [ ] **Step 2: Run full tests**

```powershell
D:\python1\python.exe -m pytest -q
```

- [ ] **Step 3: Inspect git diff**

```powershell
git diff -- mvp_agentic_rag/src/mvp_agentic_rag/agents/claim_risk_agent.py mvp_agentic_rag/tests/test_claim_risk_agent.py mvp_agentic_rag/configs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_stratified45_five_stage_verifier_v1_3_2_repair_query_rewrite_no_think.yaml
```

Expected: only v1.3.2 repair-query rewrite behavior, tests, docs, and config changed.
