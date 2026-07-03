# Evidence Utilization Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conservative evidence-utilization gate that stops follow-up retrieval when unresolved critical claims already cite retrieved evidence and the latest retrieval produced no new support.

**Architecture:** Keep the mechanism small and auditable: a helper classifies verifier output against the current ledger, `ClaimRiskAgent` applies the gate only after the existing controller chooses to retrieve again, and trajectory metadata records why the gate fired. The verifier prompt is tightened to distinguish missing passages from present evidence that still needs reasoning or grounding.

**Tech Stack:** Python dataclasses, existing unittest suite, existing YAML configs and runner.

---

### Task 1: Add Utilization Assessment Helper

**Files:**
- Create: `src/mvp_agentic_rag/claim_evidence_utilization.py`
- Test: `tests/test_claim_evidence_utilization.py`

- [ ] Write failing tests for unresolved critical claims with existing retrieved evidence.
- [ ] Verify tests fail because the module does not exist.
- [ ] Implement `assess_evidence_utilization`.
- [ ] Verify helper tests pass.

### Task 2: Gate ClaimRiskAgent Retrieval Decisions

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Test: `tests/test_claim_risk_agent.py`

- [ ] Write a failing test where round 2 has `evidence_gain=0`, the verifier cites already retrieved evidence, and the agent should abstain instead of launching round 3.
- [ ] Implement config-gated behavior:
  - `claim_evidence_utilization_gate`
  - `claim_evidence_utilization_policy: abstain`
  - `claim_evidence_utilization_require_zero_gain`
- [ ] Record trajectory metadata:
  - `utilization_gate`
  - `utilization_reason`
  - `utilization_evidence_ids`
- [ ] Verify targeted tests pass.

### Task 3: Tighten Verifier Prompt

**Files:**
- Modify: `src/mvp_agentic_rag/prompts.py`
- Test: `tests/test_llm_client.py`

- [ ] Write a failing prompt test for `missing_passage` and `evidence_present_but_reasoning_unresolved` instructions.
- [ ] Update verifier prompt text without changing parser schema.
- [ ] Verify prompt tests pass.

### Task 4: Add Subset30 Config And Run

**Files:**
- Create: `configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_utilization_gate_claim_risk_subset30.yaml`
- Modify: `docs/experiment_results_and_decisions_2026-06-17.md`

- [ ] Copy the low-yield abstain subset30 config and add utilization gate keys.
- [ ] Run full unittest discovery.
- [ ] Run real subset30 experiment.
- [ ] Append result section to the experiment decisions document.
