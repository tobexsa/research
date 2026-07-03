from __future__ import annotations

import unittest

from mvp_agentic_rag.agents import AGENT_CLASSES
from mvp_agentic_rag.agents.agentic_rag_baseline_agent import AgenticRagBaselineAgent


class AgenticRagBaselineAgentTests(unittest.TestCase):
    def test_agent_is_registered_under_descriptive_name_only(self) -> None:
        self.assertIn("agentic_rag_baseline", AGENT_CLASSES)
        self.assertNotIn("ours", AGENT_CLASSES)
        self.assertIs(AgenticRagBaselineAgent, AGENT_CLASSES["agentic_rag_baseline"])
        self.assertEqual("agentic_rag_baseline", AgenticRagBaselineAgent.method)


if __name__ == "__main__":
    unittest.main()
