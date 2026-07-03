from .fixed_k_agent import FixedKAgent
from .agentic_rag_baseline_agent import AgenticRagBaselineAgent
from .claim_risk_agent import ClaimRiskAgent
from .naive_rag import NaiveRagAgent
from .prompt_verifier_agent import PromptVerifierAgent
from .self_stop_agent import SelfStopAgent

AGENT_CLASSES = {
    "naive": NaiveRagAgent,
    "fixed_k": FixedKAgent,
    "self_stop": SelfStopAgent,
    "prompt_verifier": PromptVerifierAgent,
    "agentic_rag_baseline": AgenticRagBaselineAgent,
    "claim_risk": ClaimRiskAgent,
}
