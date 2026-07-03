# LLM Verifier and Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OpenAI-compatible LLM answer generation and claim verification while keeping offline heuristic behavior as the default.

**Architecture:** Introduce `llm_client.py` for OpenAI-compatible chat completion calls, `prompts.py` for prompt construction, and LLM-backed classes in `answer_generator.py` and `verifier.py`. Runner passes config into agents; agents choose heuristic or LLM components based on config.

**Tech Stack:** Python standard library `urllib`, JSON, unittest fake clients; optional external OpenAI-compatible API at runtime.

---

### Task 1: LLM Client and Prompts

**Files:**
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/llm_client.py`
- Create: `mvp_agentic_rag/src/mvp_agentic_rag/prompts.py`
- Test: `mvp_agentic_rag/tests/test_llm_client.py`

- [ ] Write failing tests for fake client and OpenAI payload parsing.
- [ ] Run tests and verify failure.
- [ ] Implement client interface, fake client, and OpenAI-compatible client.
- [ ] Implement prompt builders.
- [ ] Run tests and verify pass.

### Task 2: LLM Verifier

**Files:**
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/verifier.py`
- Test: `mvp_agentic_rag/tests/test_llm_verifier.py`

- [ ] Write failing tests for parsing valid verifier JSON and graceful fallback on invalid JSON.
- [ ] Run tests and verify failure.
- [ ] Implement `LLMClaimVerifier` and `make_verifier`.
- [ ] Run tests and verify pass.

### Task 3: LLM Answer Generator and Agent Wiring

**Files:**
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/answer_generator.py`
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/agents/base.py`
- Modify: `mvp_agentic_rag/src/mvp_agentic_rag/layer1_runner.py`
- Test: `mvp_agentic_rag/tests/test_llm_agent_wiring.py`

- [ ] Write failing tests proving config can select fake LLM answer/verifier.
- [ ] Run tests and verify failure.
- [ ] Implement `LLMAnswerGenerator`, `make_answer_generator`, config passing, and agent component selection.
- [ ] Run tests and verify pass.

### Task 4: Configs and Docs

**Files:**
- Add: `mvp_agentic_rag/configs/layer1_api_balanced300_dense_bge_llm_verifier_subset2.yaml`
- Modify: `mvp_agentic_rag/README.md`
- Modify: `mvp_agentic_rag/runs/mvp_decision.md`

- [ ] Add safe subset config using environment variable for API key.
- [ ] Document required env vars and no-key fallback behavior.
- [ ] Run full tests.
