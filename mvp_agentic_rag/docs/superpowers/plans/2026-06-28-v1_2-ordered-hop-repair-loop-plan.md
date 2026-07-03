# v1.2 Ordered-Hop Repair Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire v1.2 verifier repair actions into the claim-risk controller so `refine_missing_hop`, `ordered_hop_repair`, and `answer_extraction_repair` change the next retrieval or answer path instead of staying diagnostic-only.

**Architecture:** Keep the existing `ClaimRiskAgent` and `SlotLedger` flow. Add a small repair-router layer that inspects `slot_binding_verifier_result.decision_head.action` and the ordered-hop binding payload before falling back to the existing `slot_ledger.next_query()` path. Preserve current hard gates and trajectory logging; only change how the next query/repair candidate is chosen.

**Tech Stack:** Python, pytest/unittest, existing agentic_rag controller, existing slot binding verifier, existing slot ledger.

---

### Task 1: Capture the desired behavior in tests

**Files:**
- Modify: `tests/test_claim_risk_agent.py`

- [ ] **Step 1: Write the failing test for `refine_missing_hop` query routing**
- [ ] **Step 2: Write the failing test for `ordered_hop_repair` query routing**
- [ ] **Step 3: Write the failing test for `answer_extraction_repair` revalidation**
- [ ] **Step 4: Run the focused tests and confirm they fail for the missing behavior, not for typos**

### Task 2: Add the minimal repair-router helpers

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`

- [ ] **Step 1: Add a helper that reads the slot binding verifier decision head and ordered-hop payload**
- [ ] **Step 2: Build a targeted query for missing-hop repair**
- [ ] **Step 3: Build a targeted query for ordered-hop bridge/final-target repair**
- [ ] **Step 4: Add answer-extraction repair flow that retries slot verification before finalizing**

### Task 3: Keep the existing flow as fallback only

**Files:**
- Modify: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `src/mvp_agentic_rag/slot_ledger.py` if a small helper is needed

- [ ] **Step 1: Ensure the new repair-router feeds into the existing next-query path**
- [ ] **Step 2: Preserve fallback to `slot_ledger.next_query()` when no repair action is present**
- [ ] **Step 3: Preserve all current hard gates and logging fields**

### Task 4: Verify and re-run the experiment

**Files:**
- None

- [ ] **Step 1: Run the focused claim-risk tests**
- [ ] **Step 2: Run the full test suite**
- [ ] **Step 3: Launch a fresh local-api stratified45 run with a new output dir**
- [ ] **Step 4: Analyze the new run and compare coverage / cost-normalized F1 / wrong-target accepted count**
