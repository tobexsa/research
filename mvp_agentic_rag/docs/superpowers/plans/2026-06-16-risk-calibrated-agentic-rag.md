# Claim-Risk Selective Agentic RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition the current verifier-guided iterative RAG system into a claim-risk selective Agentic RAG system that decides when to answer, abstain, or continue retrieval under claim-level evidence uncertainty.

**Architecture:** Keep the existing runner, retriever, LLM client, verifier, and baseline agents intact. Add a new claim-risk agent and supporting signals rather than overwriting the current `agentic_rag_baseline` implementation, so experiments can compare `prompt_verifier`, original `agentic_rag_baseline`, and the new controller directly. The core contribution is not FAIR-RAG-style gap filling or Stop-RAG-style STOP/CONTINUE control; it is claim-level selective risk control over ANSWER / ABSTAIN / CONTINUE decisions.

**Tech Stack:** Python standard library, `unittest`, existing `mvp_agentic_rag` package, FAISS/BGE index already built, SiliconFlow OpenAI-compatible LLM config, JSONL trajectory outputs.

---

## Scope And Positioning

This plan deliberately avoids making structured evidence checklist refinement the main contribution, because that would be too close to FAIR-RAG. It also avoids framing the contribution as generic adaptive stopping for iterative RAG, because Stop-RAG already frames iterative retrieval control as a value-based STOP/CONTINUE problem. The method should instead emphasize:

- Low-yield retrieval loop detection.
- Claim-level evidence risk.
- ANSWER / ABSTAIN / CONTINUE action selection.
- Evidence-gain-aware and retrieval-novelty-aware abstention.
- Budgeted selective answering.
- Cost/risk evaluation beyond answer F1.

The existing `agentic_rag_baseline` agent remains as the iterative verifier-guided baseline. The new method should be added under a separate method name, initially `claim_risk`, so the experiment matrix can show:

- `prompt_verifier`: single-round verifier baseline.
- `agentic_rag_baseline`: current multi-round verifier-guided refinement.
- `claim_risk`: new claim-risk selective controller.

## File Map

Create or modify these files:

- Modify `src/mvp_agentic_rag/prompts.py`
  - Add configurable short-answer prompt behavior.
  - Keep old behavior available through config for apples-to-apples comparison.

- Modify `src/mvp_agentic_rag/answer_generator.py`
  - Pass prompt style config into `build_answer_prompt`.

- Modify `src/mvp_agentic_rag/evidence_ledger.py`
  - Add retrieval novelty / duplicate tracking in addition to current gold-based support gain.
  - Preserve current `add_retrieved(passages) -> float` behavior for existing tests.

- Create `src/mvp_agentic_rag/claim_risk_controller.py`
  - Implement the new claim-risk selective controller.
  - Keep it independent from the old `RiskPolicy` so the old `agentic_rag_baseline` remains unchanged.

- Create `src/mvp_agentic_rag/agents/claim_risk_agent.py`
  - New agent that uses `EvidenceLedger` plus `ClaimRiskController`.

- Modify `src/mvp_agentic_rag/agents/__init__.py`
  - Register `"claim_risk": ClaimRiskAgent`.

- Modify `src/mvp_agentic_rag/evaluator.py`
  - Add cost/risk metrics while preserving existing metric keys.

- Modify `scripts/analyze_errors.py`
  - Add fields useful for claim-risk analysis if not already present.

- Create configs:
  - `configs/layer1_api_balanced300_dense_bge_short_answer_subset10.yaml`
  - `configs/layer1_api_balanced300_dense_bge_short_answer_full300.yaml`
  - `configs/layer1_api_balanced300_dense_bge_claim_risk_subset10.yaml`
  - `configs/layer1_api_balanced300_dense_bge_claim_risk_subset30.yaml`
  - `configs/layer1_api_balanced300_dense_bge_claim_risk_full300.yaml`

- Add tests:
  - `tests/test_short_answer_prompt.py`
  - `tests/test_evidence_ledger_novelty.py`
  - `tests/test_claim_risk_controller.py`
  - `tests/test_claim_risk_agent.py`
  - Update `tests/test_runner.py` or add a targeted wiring test if needed.

---

## Task 1: Add Configurable Short-Answer Prompt

**Purpose:** Remove answer-format noise before testing method changes. Current LLM answers often include correct short answers inside long explanations, which depresses token F1.

**Files:**
- Modify: `src/mvp_agentic_rag/prompts.py`
- Modify: `src/mvp_agentic_rag/answer_generator.py`
- Test: `tests/test_short_answer_prompt.py`

- [ ] **Step 1: Write failing tests for prompt style**

Create `tests/test_short_answer_prompt.py`.

Test cases:

```python
from mvp_agentic_rag.prompts import build_answer_prompt
from mvp_agentic_rag.schemas import Passage, Sample


def _sample():
    return Sample(sample_id="s1", question="When was X released?", gold_answer="March 11, 2011")


def _evidence():
    return [Passage(passage_id="p1", title="X", text="X was released on March 11, 2011.")]


def test_default_answer_prompt_preserves_existing_instruction():
    messages = build_answer_prompt(_sample(), _evidence())
    content = messages[0]["content"]
    assert "Answer the question using only the provided evidence" in content


def test_short_answer_prompt_requests_no_explanation():
    messages = build_answer_prompt(_sample(), _evidence(), answer_style="short")
    content = "\n".join(message["content"] for message in messages)
    assert "Return only the short answer" in content
    assert "Do not explain" in content
    assert "UNKNOWN" in content
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```powershell
python -m unittest tests.test_short_answer_prompt -v
```

Expected:

```text
FAIL or ERROR because build_answer_prompt does not accept answer_style
```

- [ ] **Step 3: Implement prompt style**

Modify `src/mvp_agentic_rag/prompts.py`:

```python
def build_answer_prompt(sample: Sample, evidence: list[Passage], answer_style: str = "default") -> list[dict[str, str]]:
    if answer_style == "short":
        system = (
            "Answer the question using only the provided evidence. "
            "Return only the short answer. Do not explain. "
            "Do not include citations or evidence discussion. "
            "If evidence is insufficient, return UNKNOWN."
        )
    else:
        system = "Answer the question using only the provided evidence. If evidence is insufficient, say UNKNOWN."
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Question: {sample.question}\n\nEvidence:\n{format_evidence(evidence)}\n\nAnswer:"},
    ]
```

Modify `src/mvp_agentic_rag/answer_generator.py` so LLM answer generation reads:

```python
answer_style = str(self.config.get("answer_style", "default"))
return self.client.complete(build_answer_prompt(sample, evidence, answer_style=answer_style)).strip()
```

Use the exact local class names in `answer_generator.py`; do not refactor unrelated generator code.

- [ ] **Step 4: Run targeted tests**

Run:

```powershell
python -m unittest tests.test_short_answer_prompt tests.test_llm_client tests.test_llm_agent_wiring -v
```

Expected:

```text
OK
```

- [ ] **Step 5: Run all tests**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected:

```text
Ran ... tests
OK
```

---

## Task 2: Create Short-Answer Experiment Configs

**Purpose:** Establish a cleaner F1 baseline before changing the controller.

**Files:**
- Create: `configs/layer1_api_balanced300_dense_bge_short_answer_subset10.yaml`
- Create: `configs/layer1_api_balanced300_dense_bge_short_answer_full300.yaml`

- [ ] **Step 1: Copy the full300 LLM config**

Use `configs/layer1_api_balanced300_dense_bge_llm_verifier_full300.yaml` as the template.

- [ ] **Step 2: Create subset10 config**

Create `configs/layer1_api_balanced300_dense_bge_short_answer_subset10.yaml`:

```yaml
run_name: layer1_api_balanced300_dense_bge_short_answer_subset10
dataset: data/musique_mvp_300.jsonl
corpus: data/musique_corpus.jsonl
output_dir: runs/layer1_api_balanced300_dense_bge_short_answer_subset10
retriever: dense
index_path: indexes/faiss_musique_bge_base_en_v1_5.index
meta_path: indexes/faiss_musique_bge_base_en_v1_5_meta.pkl
embedding_backend: sentence_transformers
embedding_model: D:\research\model\models--BAAI--bge-base-en-v1.5\snapshots\a5beb1e3e68b9ab74eb54cfd186867f64f240e1a
limit_samples: 10
methods: [prompt_verifier, agentic_rag_baseline]
top_k: 5
max_rounds: 3
answer_style: short
answer_backend: openai_compatible
answer_base_url: https://api.siliconflow.cn/v1
answer_api_key_env: SILICONFLOW_API_KEY
answer_model: Qwen/Qwen2.5-14B-Instruct
answer_timeout: 60
answer_max_tokens: 128
verifier_backend: openai_compatible
verifier_base_url: https://api.siliconflow.cn/v1
verifier_api_key_env: SILICONFLOW_API_KEY
verifier_model: Qwen/Qwen2.5-14B-Instruct
verifier_timeout: 60
verifier_max_tokens: 768
```

- [ ] **Step 3: Create full300 config**

Create `configs/layer1_api_balanced300_dense_bge_short_answer_full300.yaml` with the same content, except:

```yaml
run_name: layer1_api_balanced300_dense_bge_short_answer_full300
output_dir: runs/layer1_api_balanced300_dense_bge_short_answer_full300
```

Remove `limit_samples`.

- [ ] **Step 4: Smoke run subset10**

Run:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_short_answer_subset10.yaml
```

Expected:

```text
{'completed': 20, 'skipped': 0, ...}
```

If rerunning after a partial result, remove the subset run directory first or account for skipped records.

- [ ] **Step 5: Analyze subset10**

Run:

```powershell
python scripts\analyze_errors.py runs\layer1_api_balanced300_dense_bge_short_answer_subset10
```

Expected:

```text
runs\layer1_api_balanced300_dense_bge_short_answer_subset10\error_analysis.md
```

Decision gate:

- Continue only if answers are visibly shorter in trajectories.
- If answers are still verbose, tighten prompt before running full300.

---

## Task 3: Add Retrieval Novelty To EvidenceLedger

**Purpose:** Add deployable signals that do not require gold supporting passage IDs. Gold `evidence_gain` is useful offline, but retrieval novelty is usable in real systems.

**Files:**
- Modify: `src/mvp_agentic_rag/evidence_ledger.py`
- Test: `tests/test_evidence_ledger_novelty.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_evidence_ledger_novelty.py`:

```python
import unittest

from mvp_agentic_rag.evidence_ledger import EvidenceLedger
from mvp_agentic_rag.schemas import Passage, Sample


class EvidenceLedgerNoveltyTests(unittest.TestCase):
    def test_tracks_retrieval_novelty_for_new_passages(self):
        sample = Sample(sample_id="s1", question="q", gold_answer="a", supporting_passage_ids=["p2"])
        ledger = EvidenceLedger(sample=sample)

        first_gain = ledger.add_retrieved([
            Passage("p1", "t", "x"),
            Passage("p2", "t", "x"),
        ])
        first_novelty = ledger.retrieval_novelty_history[-1]

        second_gain = ledger.add_retrieved([
            Passage("p1", "t", "x"),
            Passage("p2", "t", "x"),
        ])
        second_novelty = ledger.retrieval_novelty_history[-1]

        self.assertEqual(first_gain, 1.0)
        self.assertEqual(first_novelty, 1.0)
        self.assertEqual(second_gain, 0.0)
        self.assertEqual(second_novelty, 0.0)

    def test_tracks_partial_novelty(self):
        sample = Sample(sample_id="s1", question="q", gold_answer="a")
        ledger = EvidenceLedger(sample=sample)
        ledger.add_retrieved([Passage("p1", "t", "x"), Passage("p2", "t", "x")])

        ledger.add_retrieved([Passage("p2", "t", "x"), Passage("p3", "t", "x")])

        self.assertEqual(ledger.retrieval_novelty_history[-1], 0.5)
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m unittest tests.test_evidence_ledger_novelty -v
```

Expected:

```text
ERROR because retrieval_novelty_history does not exist
```

- [ ] **Step 3: Implement novelty tracking**

Modify `EvidenceLedger`:

```python
retrieval_novelty_history: list[float] = field(default_factory=list)
new_passage_count_history: list[int] = field(default_factory=list)
duplicate_passage_count_history: list[int] = field(default_factory=list)
```

In `add_retrieved`:

```python
seen_passage_ids = {p.passage_id for p in self.retrieved_passages}
new_passage_ids = [p.passage_id for p in passages if p.passage_id not in seen_passage_ids]
duplicate_count = len(passages) - len(new_passage_ids)
novelty = len(new_passage_ids) / max(len(passages), 1)
...
self.retrieval_novelty_history.append(novelty)
self.new_passage_count_history.append(len(new_passage_ids))
self.duplicate_passage_count_history.append(duplicate_count)
```

Keep support-gain calculation unchanged.

- [ ] **Step 4: Run targeted tests**

Run:

```powershell
python -m unittest tests.test_evidence_ledger_novelty tests.test_policy tests.test_runner -v
```

Expected:

```text
OK
```

---

## Task 4: Implement ClaimRiskController

**Purpose:** Add the paper's core claim-level selective control logic separately from the old `RiskPolicy`. This controller is not a Stop-RAG-style STOP/CONTINUE policy; it explicitly chooses among `answer`, `abstain`, `continue_search`, and `refine_query`.

**Files:**
- Create: `src/mvp_agentic_rag/claim_risk_controller.py`
- Test: `tests/test_claim_risk_controller.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_claim_risk_controller.py`.

Test cases should cover:

```python
import unittest

from mvp_agentic_rag.claim_risk_controller import ClaimRiskController
from mvp_agentic_rag.schemas import ClaimAssessment, VerifierOutput


def verifier(sufficiency="insufficient", claims=None):
    return VerifierOutput(
        claims=claims or [ClaimAssessment("x", "unsupported", is_critical=True)],
        overall_sufficiency=sufficiency,
        need_more_evidence=sufficiency != "sufficient",
        suggested_query="follow up",
    )


class ClaimRiskControllerTests(unittest.TestCase):
    def test_answers_when_sufficient_and_no_critical_unsupported(self):
        controller = ClaimRiskController()
        output = VerifierOutput(
            claims=[ClaimAssessment("x", "supported", is_critical=True)],
            overall_sufficiency="sufficient",
            need_more_evidence=False,
        )
        self.assertEqual(controller.decide(output, budget_remaining=2, evidence_gain=0.5, retrieval_novelty=1.0), "answer")

    def test_abstains_when_budget_exhausted(self):
        controller = ClaimRiskController()
        self.assertEqual(controller.decide(verifier(), budget_remaining=0, evidence_gain=0.0, retrieval_novelty=0.0), "abstain")

    def test_abstains_after_low_yield_retrieval_with_critical_missing_claim(self):
        controller = ClaimRiskController(min_retrieval_novelty=0.01)
        self.assertEqual(
            controller.decide(verifier(), budget_remaining=1, evidence_gain=0.0, retrieval_novelty=0.0, round_idx=2),
            "abstain",
        )

    def test_refines_when_missing_critical_claim_and_retrieval_is_still_novel(self):
        controller = ClaimRiskController(min_retrieval_novelty=0.01)
        self.assertEqual(
            controller.decide(verifier(), budget_remaining=1, evidence_gain=0.0, retrieval_novelty=0.8, round_idx=2),
            "refine_query",
        )

    def test_continues_for_noncritical_insufficient_evidence_with_retrieval_value(self):
        controller = ClaimRiskController(min_retrieval_novelty=0.01)
        output = verifier(claims=[ClaimAssessment("x", "unsupported", is_critical=False)])
        self.assertEqual(
            controller.decide(output, budget_remaining=1, evidence_gain=0.0, retrieval_novelty=0.8, round_idx=2),
            "continue_search",
        )
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m unittest tests.test_claim_risk_controller -v
```

Expected:

```text
ERROR because mvp_agentic_rag.claim_risk_controller does not exist
```

- [ ] **Step 3: Implement controller**

Create `src/mvp_agentic_rag/claim_risk_controller.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

from .schemas import VerifierOutput


@dataclass
class ClaimRiskController:
    min_retrieval_novelty: float = 0.01
    low_yield_abstain_after_round: int = 2

    def decide(
        self,
        verifier_output: VerifierOutput,
        budget_remaining: int,
        evidence_gain: float,
        retrieval_novelty: float,
        round_idx: int = 1,
    ) -> str:
        statuses = {claim.status for claim in verifier_output.claims}
        has_critical_unsupported = any(
            claim.is_critical and claim.status in {"unsupported", "unclear"}
            for claim in verifier_output.claims
        )
        if (
            verifier_output.overall_sufficiency == "sufficient"
            and not has_critical_unsupported
            and "contradicted" not in statuses
        ):
            return "answer"
        if budget_remaining <= 0:
            return "abstain"
        low_yield = (
            round_idx >= self.low_yield_abstain_after_round
            and evidence_gain <= 0
            and retrieval_novelty <= self.min_retrieval_novelty
        )
        if low_yield:
            return "abstain"
        if "contradicted" in statuses or has_critical_unsupported:
            return "refine_query"
        if verifier_output.overall_sufficiency in {"insufficient", "unclear"}:
            return "continue_search"
        return "answer"
```

- [ ] **Step 4: Run targeted tests**

Run:

```powershell
python -m unittest tests.test_claim_risk_controller -v
```

Expected:

```text
OK
```

---

## Task 5: Add ClaimRiskAgent

**Purpose:** Add the new method without disturbing the current `agentic_rag_baseline` baseline.

**Files:**
- Create: `src/mvp_agentic_rag/agents/claim_risk_agent.py`
- Modify: `src/mvp_agentic_rag/agents/__init__.py`
- Test: `tests/test_claim_risk_agent.py`

- [ ] **Step 1: Write failing wiring/behavior tests**

Create `tests/test_claim_risk_agent.py`.

Use fake retriever / fake answer generator / fake verifier patterns already present in existing tests. The minimum tests:

- agent is registered as `claim_risk`;
- agent abstains after a low-yield second round with unresolved critical claim risk;
- trajectory records retrieval novelty if added to step metadata, or at minimum records `evidence_gain=0.0` and stops at 2 rounds.

Example structure:

```python
import unittest

from mvp_agentic_rag.agents import AGENT_CLASSES


class ClaimRiskAgentTests(unittest.TestCase):
    def test_agent_is_registered(self):
        self.assertIn("claim_risk", AGENT_CLASSES)
```

Add a second test using existing runner fake LLM config if straightforward. If setup becomes too large, split the behavior into `ClaimRiskController` tests and keep agent test as wiring only.

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m unittest tests.test_claim_risk_agent -v
```

Expected:

```text
FAIL because claim_risk is not registered
```

- [ ] **Step 3: Implement agent**

Create `src/mvp_agentic_rag/agents/claim_risk_agent.py`.

Start from `AgenticRagBaselineAgent`, but replace `RiskPolicy` with `ClaimRiskController`:

```python
class ClaimRiskAgent(BaseAgent):
    method = "claim_risk"

    def __init__(self, retriever, top_k: int = 5, max_rounds: int = 3, config: dict | None = None):
        super().__init__(retriever, top_k, max_rounds, config)
        self.controller = ClaimRiskController(
            min_retrieval_novelty=float(self.config.get("min_retrieval_novelty", 0.01)),
            low_yield_abstain_after_round=int(self.config.get("low_yield_abstain_after_round", 2)),
        )
```

In the loop:

```python
gain = ledger.add_retrieved(passages)
retrieval_novelty = ledger.retrieval_novelty_history[-1]
...
action = self.controller.decide(
    verifier_output,
    budget_remaining=budget_remaining,
    evidence_gain=gain,
    retrieval_novelty=retrieval_novelty,
    round_idx=round_idx,
)
```

For the trajectory record, keep current `TrajectoryStep` unchanged initially. Do not expand schema unless needed for metrics. The analysis script can infer novelty later if records include retrieved IDs per step.

- [ ] **Step 4: Register agent**

Modify `src/mvp_agentic_rag/agents/__init__.py`:

```python
from .claim_risk_agent import ClaimRiskAgent

AGENT_CLASSES = {
    ...
    "claim_risk": ClaimRiskAgent,
}
```

- [ ] **Step 5: Run targeted tests**

Run:

```powershell
python -m unittest tests.test_claim_risk_agent tests.test_claim_risk_controller tests.test_runner -v
```

Expected:

```text
OK
```

---

## Task 6: Add Selective QA Risk And Cost Metrics

**Purpose:** Support the paper's new claim with metrics that FAIR-RAG-style F1-only evaluation and Stop-RAG-style final-answer stopping evaluation do not emphasize: answered-risk, abstention quality, coverage, and wasted retrieval.

**Files:**
- Modify: `src/mvp_agentic_rag/evaluator.py`
- Test: `tests/test_evaluator_risk_metrics.py`

- [ ] **Step 1: Write failing metric test**

Create `tests/test_evaluator_risk_metrics.py`.

Expected new metric keys:

```text
coverage
selective_answer_f1
cost_normalized_f1
wasted_retrieval_rate
answered_unsupported_rate
abstention_precision
abstention_gold_answerable_rate
```

Definitions:

- `coverage`: fraction of records whose `final_action == "answer"`.
- `selective_answer_f1`: mean F1 over answered records only; `0.0` if no answered records.
- `cost_normalized_f1`: `answer_f1 / avg_retrieval_calls`, guarding divide-by-zero.
- `wasted_retrieval_rate`: fraction of records with any post-first-round duplicate/no-new retrieval. Initially reuse existing logic: any `step.evidence_gain <= 0` after round 1.
- `answered_unsupported_rate`: fraction of answered records with any unsupported, unclear, or contradicted verifier claim.
- `abstention_precision`: fraction of abstentions whose final answer F1 would be zero or whose verifier state was not sufficient. Use available trajectory/verifier data; if there is no reliable counterfactual answer, base it on final verifier sufficiency.
- `abstention_gold_answerable_rate`: fraction of abstentions where the method had retrieved at least one gold supporting passage. This is an offline diagnostic, not a deployable metric.

Test should call `evaluate_records(records, "test")` directly.

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m unittest tests.test_evaluator_risk_metrics -v
```

Expected:

```text
FAIL because new metric keys are missing
```

- [ ] **Step 3: Implement metrics**

Modify `evaluate_records` in `src/mvp_agentic_rag/evaluator.py`.

Add:

```python
answered_f1s = [
    token_f1(item.get("final_answer", ""), item.get("gold_answer", ""))
    for item in items
    if item.get("final_action") == "answer"
]
coverage = mean([1 if item.get("final_action") == "answer" else 0 for item in items]) if items else 0.0
avg_retrieval = mean(retrieval_calls) if retrieval_calls else 0.0
```

In method metrics:

```python
"coverage": coverage,
"selective_answer_f1": mean(answered_f1s) if answered_f1s else 0.0,
"cost_normalized_f1": (mean(f1s) / avg_retrieval) if avg_retrieval else 0.0,
"wasted_retrieval_rate": mean(no_new_evidence) if no_new_evidence else 0.0,
"answered_unsupported_rate": ...,
"abstention_precision": ...,
"abstention_gold_answerable_rate": ...,
```

Keep the old `no_new_evidence_call_rate` key for backward compatibility, even if it duplicates `wasted_retrieval_rate`.

- [ ] **Step 4: Run targeted and full tests**

Run:

```powershell
python -m unittest tests.test_evaluator_risk_metrics tests.test_tables tests.test_runner -v
python -m unittest discover -s tests -v
```

Expected:

```text
OK
```

---

## Task 7: Create Claim-Risk Experiment Configs

**Purpose:** Run a staged ablation without immediately spending full300 API budget.

**Files:**
- Create: `configs/layer1_api_balanced300_dense_bge_claim_risk_subset10.yaml`
- Create: `configs/layer1_api_balanced300_dense_bge_claim_risk_subset30.yaml`
- Create: `configs/layer1_api_balanced300_dense_bge_claim_risk_full300.yaml`

- [ ] **Step 1: Create subset10 config**

Base it on `configs/layer1_api_balanced300_dense_bge_short_answer_subset10.yaml`.

Change:

```yaml
run_name: layer1_api_balanced300_dense_bge_claim_risk_subset10
output_dir: runs/layer1_api_balanced300_dense_bge_claim_risk_subset10
methods: [prompt_verifier, agentic_rag_baseline, claim_risk]
min_retrieval_novelty: 0.01
low_yield_abstain_after_round: 2
```

- [ ] **Step 2: Create subset30 config**

Same config, but:

```yaml
run_name: layer1_api_balanced300_dense_bge_claim_risk_subset30
output_dir: runs/layer1_api_balanced300_dense_bge_claim_risk_subset30
limit_samples: 30
```

- [ ] **Step 3: Create full300 config**

Same config, but:

```yaml
run_name: layer1_api_balanced300_dense_bge_claim_risk_full300
output_dir: runs/layer1_api_balanced300_dense_bge_claim_risk_full300
```

Remove `limit_samples`.

- [ ] **Step 4: Run subset10**

Run:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_claim_risk_subset10.yaml
```

Expected:

```text
30 completed records
```

Because:

```text
10 samples * 3 methods = 30 trajectories
```

- [ ] **Step 5: Analyze subset10**

Run:

```powershell
python scripts\analyze_errors.py runs\layer1_api_balanced300_dense_bge_claim_risk_subset10
```

Decision gate:

- Confirm `claim_risk` appears in `metrics.json`.
- Confirm `claim_risk.avg_retrieval_calls <= agentic_rag_baseline.avg_retrieval_calls`.
- Confirm trajectories do not show obvious premature abstention on cases where first round was sufficient.
- Confirm claim-risk decisions include both `answer` and `abstain`, not only cost reduction by universal abstention.

- [ ] **Step 6: Run subset30**

Only after subset10 passes:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_claim_risk_subset30.yaml
```

Expected:

```text
90 completed records
```

Decision gate:

- `claim_risk.answer_f1` should not collapse relative to `agentic_rag_baseline`.
- `claim_risk.avg_retrieval_calls` should be meaningfully lower than `agentic_rag_baseline`.
- `claim_risk.wasted_retrieval_rate` should be lower than `agentic_rag_baseline`.
- `claim_risk.coverage` should remain non-trivial.
- `claim_risk.answered_unsupported_rate` should not exceed `agentic_rag_baseline`.

---

## Task 8: Full300 Claim-Risk Run

**Purpose:** Produce the main comparable run for the revised paper direction.

**Files:**
- Uses: `configs/layer1_api_balanced300_dense_bge_claim_risk_full300.yaml`
- Outputs: `runs/layer1_api_balanced300_dense_bge_claim_risk_full300`

- [ ] **Step 1: Preflight**

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected:

```text
OK
```

Check `.env` has `SILICONFLOW_API_KEY`:

```powershell
Select-String -Path .env -Pattern '^\s*SILICONFLOW_API_KEY\s*='
```

- [ ] **Step 2: Run full300**

Run:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_claim_risk_full300.yaml
```

Expected:

```text
900 completed records
```

Because:

```text
300 samples * 3 methods = 900 trajectories
```

If running in a background process, log stdout/stderr under `runs/logs/`.

- [ ] **Step 3: Analyze full300**

Run:

```powershell
python scripts\analyze_errors.py runs\layer1_api_balanced300_dense_bge_claim_risk_full300
```

Expected:

```text
runs\layer1_api_balanced300_dense_bge_claim_risk_full300\error_analysis.md
```

- [ ] **Step 4: Compare against previous full300**

Use these two runs:

```text
runs/layer1_api_balanced300_dense_bge_llm_verifier_full300
runs/layer1_api_balanced300_dense_bge_claim_risk_full300
```

Compare:

- `answer_f1`
- `coverage`
- `selective_answer_f1`
- `avg_retrieval_calls`
- `cost_normalized_f1`
- `unsupported_claim_rate`
- `wasted_retrieval_rate`
- `answered_unsupported_rate`
- `abstention_precision`
- `abstention_gold_answerable_rate`

Acceptance criteria:

- Primary: `claim_risk.avg_retrieval_calls < agentic_rag_baseline.avg_retrieval_calls`.
- Primary: `claim_risk.wasted_retrieval_rate < agentic_rag_baseline.wasted_retrieval_rate`.
- Primary: `claim_risk.answered_unsupported_rate <= agentic_rag_baseline.answered_unsupported_rate`.
- Guardrail: `claim_risk.answer_f1` should be close to `agentic_rag_baseline`; a small drop is acceptable if cost reduction is large, but a collapse is not.
- Guardrail: `claim_risk.unsupported_claim_rate` should not increase substantially.
- Guardrail: `claim_risk.coverage` should not collapse into near-universal abstention.

---

## Task 9: Add Iterative Control Baselines

**Purpose:** Make the paper safer by explicitly comparing against simple iterative control baselines rather than ignoring FAIR-RAG-style gap filling or Stop-RAG-style stop/continue control. These are category baselines only; they must not be described as reproductions of FAIR-RAG or Stop-RAG.

**Files:**
- Create: `src/mvp_agentic_rag/agents/always_refine_agent.py`
- Create: `src/mvp_agentic_rag/agents/stop_continue_agent.py`
- Modify: `src/mvp_agentic_rag/agents/__init__.py`
- Test: `tests/test_always_refine_agent.py`
- Test: `tests/test_stop_continue_agent.py`
- Config: optional subset/full configs after local tests.

- [ ] **Step 1: Write registration test**

Create `tests/test_always_refine_agent.py`:

```python
import unittest

from mvp_agentic_rag.agents import AGENT_CLASSES


class AlwaysRefineAgentTests(unittest.TestCase):
    def test_agent_is_registered(self):
        self.assertIn("always_refine", AGENT_CLASSES)
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
python -m unittest tests.test_always_refine_agent -v
```

Expected:

```text
FAIL because always_refine is not registered
```

- [ ] **Step 3: Implement baseline**

Create `src/mvp_agentic_rag/agents/always_refine_agent.py`.

Behavior:

- Same as `AgenticRagBaselineAgent` in retrieval/generation/verifier.
- If verifier says sufficient, answer.
- If budget remains and verifier is not sufficient, always continue using `suggested_query`.
- Only abstain when budget is exhausted.

This intentionally represents a FAIR-RAG-like "keep filling gaps until budget ends" control pattern, but without claiming to reproduce FAIR-RAG exactly.

- [ ] **Step 4: Add a simple stop/continue baseline**

Create `tests/test_stop_continue_agent.py`:

```python
import unittest

from mvp_agentic_rag.agents import AGENT_CLASSES


class StopContinueAgentTests(unittest.TestCase):
    def test_agent_is_registered(self):
        self.assertIn("stop_continue", AGENT_CLASSES)
```

Create `src/mvp_agentic_rag/agents/stop_continue_agent.py`.

Behavior:

- Same retrieval/generation/verifier loop as `AgenticRagBaselineAgent`.
- If verifier says sufficient, stop and answer.
- If verifier is not sufficient and budget remains, continue using `suggested_query`.
- If budget is exhausted, abstain.
- Do not add learned value estimation, Q-learning, MDP training, or claims of Stop-RAG reproduction.

This baseline is only meant to separate our claim-risk action space from ordinary STOP/CONTINUE control. Stop-RAG itself is a learned value-based method and should remain a related-work method unless fully reproduced later.

- [ ] **Step 5: Register and test**

Modify `agents/__init__.py`:

```python
from .always_refine_agent import AlwaysRefineAgent
from .stop_continue_agent import StopContinueAgent
...
"always_refine": AlwaysRefineAgent,
"stop_continue": StopContinueAgent,
```

Run:

```powershell
python -m unittest tests.test_always_refine_agent tests.test_stop_continue_agent tests.test_runner -v
```

Expected:

```text
OK
```

- [ ] **Step 6: Add to subset comparison only**

First run only subset10 or subset30:

```yaml
methods: [prompt_verifier, agentic_rag_baseline, always_refine, stop_continue, claim_risk]
```

Do not run full300 with this baseline until subset results justify the API cost.

---

## Task 10: Create Comparison Table Script Or Extend Existing Table Builder

**Purpose:** Produce paper-facing numbers for the revised claim.

**Files:**
- Modify: `src/mvp_agentic_rag/eval/table_builder.py`
- Modify or use: `scripts/make_mvp_tables.py`
- Test: `tests/test_tables.py`

- [ ] **Step 1: Inspect current table builder**

Read:

```powershell
Get-Content -Raw src\mvp_agentic_rag\eval\table_builder.py
Get-Content -Raw tests\test_tables.py
```

- [ ] **Step 2: Add test for new metrics**

Update `tests/test_tables.py` so table output includes:

```text
coverage
selective_answer_f1
cost_normalized_f1
wasted_retrieval_rate
```

- [ ] **Step 3: Run and verify failure**

Run:

```powershell
python -m unittest tests.test_tables -v
```

- [ ] **Step 4: Implement table support**

Extend the table builder with the new metric keys while preserving existing output.

- [ ] **Step 5: Generate tables**

Run:

```powershell
python scripts\make_mvp_tables.py
```

Expected:

```text
tables or markdown summaries include cost/risk metrics
```

---

## Task 11: Write The Revised Method Description

**Purpose:** Lock the paper narrative so implementation does not drift back into FAIR-RAG overlap or Stop-RAG-style generic stopping.

**Files:**
- Create: `docs/claim_risk_method.md`

- [ ] **Step 1: Create method note**

Write `docs/claim_risk_method.md` with these sections:

```markdown
# Claim-Risk Selective Agentic RAG

## Motivation
Verifier-guided iterative RAG can enter low-yield retrieval loops when evidence-gap signals trigger additional retrieval but the retriever repeatedly fails to surface new supporting evidence.

## Difference From FAIR-RAG
FAIR-RAG focuses on structured evidence assessment and adaptive gap filling. This work focuses on claim-level selective answering: deciding whether to answer, abstain, or continue when evidence remains uncertain.

## Difference From Stop-RAG
Stop-RAG frames iterative retrieval control as a value-based STOP/CONTINUE problem for answer quality. This work uses explicit claim-level risk signals and includes ABSTAIN as a first-class action, so stopping can mean either answering safely or refusing to answer.

## Controller Signals
- verifier sufficiency
- critical unsupported claims
- evidence gain
- retrieval novelty
- budget remaining

## Actions
- answer
- abstain
- continue_search
- refine_query

## Evaluation
- answer F1
- coverage
- selective answer F1
- unsupported claim rate
- answered unsupported rate
- abstention precision
- average retrieval calls
- wasted retrieval rate
- cost-normalized F1
```

- [ ] **Step 2: Add current empirical motivation**

Include the current full300 finding:

```text
In the existing full300 run, 76.7% of `agentic_rag_baseline` records triggered extra retrieval and also had no-new-evidence behavior, while mean F1 on those records was 0.002820 versus 0.181985 without no-new-evidence behavior.
```

- [ ] **Step 3: Review consistency**

Check that the method note does not claim:

- We introduce structured evidence checklist refinement as the main contribution.
- We reproduce FAIR-RAG exactly.
- We outperform FAIR-RAG without running it.
- We reproduce Stop-RAG exactly.
- The main contribution is generic adaptive stopping.

---

## Execution Order

Recommended order:

1. Task 1: Short-answer prompt.
2. Task 2: Short-answer subset10 and optionally full300.
3. Task 3: EvidenceLedger novelty.
4. Task 4: ClaimRiskController.
5. Task 5: ClaimRiskAgent.
6. Task 6: Risk/cost metrics.
7. Task 7: Claim-risk subset10/subset30.
8. Task 8: Claim-risk full300 only after subset gates pass.
9. Task 9: Iterative control baselines only after the main controller is stable.
10. Task 10: Comparison tables.
11. Task 11: Revised method description.

## Main Acceptance Criteria

The revised line is successful if the full300 comparison shows:

- `claim_risk` has substantially lower `avg_retrieval_calls` than original `agentic_rag_baseline`.
- `claim_risk` has lower `wasted_retrieval_rate` / `no_new_evidence_call_rate`.
- `claim_risk` has lower or equal `answered_unsupported_rate` than original `agentic_rag_baseline`.
- `claim_risk.answer_f1` is not materially worse than original `agentic_rag_baseline`.
- `claim_risk.unsupported_claim_rate` does not materially increase.
- `claim_risk.coverage` does not collapse into near-universal abstention.
- The method description clearly distinguishes the work from FAIR-RAG by avoiding evidence-gap refinement as the main contribution.
- The method description clearly distinguishes the work from Stop-RAG by focusing on ANSWER / ABSTAIN / CONTINUE claim-risk decisions rather than STOP / CONTINUE answer-quality control.

## Stop Or Reconsider Criteria

Stop and reassess if:

- Short-answer prompting does not shorten answers in subset10.
- `claim_risk` collapses answer F1 on subset30.
- `claim_risk` reduces retrieval calls only by abstaining on almost everything.
- New metrics show no meaningful cost/risk advantage over original `agentic_rag_baseline`.
- The implementation drifts toward structured evidence checklist refinement as the central contribution.

## Commands Summary

Run all tests:

```powershell
python -m unittest discover -s tests -v
```

Run current full300 analysis:

```powershell
python scripts\analyze_errors.py runs\layer1_api_balanced300_dense_bge_llm_verifier_full300
```

Run short-answer subset:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_short_answer_subset10.yaml
```

Run claim-risk subset:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_claim_risk_subset10.yaml
```

Run claim-risk full300:

```powershell
python scripts\run_layer1_skeleton.py --config configs\layer1_api_balanced300_dense_bge_claim_risk_full300.yaml
```


