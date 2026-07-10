from __future__ import annotations

import unittest
from pathlib import Path

from mvp_agentic_rag.config import load_simple_config


class ConfigNamingTests(unittest.TestCase):
    def test_configs_using_agentic_rag_baseline_write_to_renamed_output_dirs(self) -> None:
        config_paths = sorted(Path("configs").glob("*.yaml"))
        checked = 0
        for config_path in config_paths:
            config = load_simple_config(config_path)
            methods = config.get("methods", [])
            if "agentic_rag_baseline" not in methods:
                continue
            checked += 1
            run_name = str(config.get("run_name", ""))
            output_dir = str(config.get("output_dir", ""))
            self.assertIn("agentic_rag_baseline", run_name, config_path.as_posix())
            self.assertIn("agentic_rag_baseline", output_dir, config_path.as_posix())

        self.assertGreater(checked, 0)

    def test_controller_policy_v1_config_is_isolated_and_enabled(self) -> None:
        config_path = Path(
            "configs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_"
            "stratified45_five_stage_verifier_v1_3_4_controller_policy_v1_no_think.yaml"
        )

        config = load_simple_config(config_path)

        self.assertEqual(
            "layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_"
            "stratified45_five_stage_verifier_v1_3_4_controller_policy_v1_no_think",
            config.get("run_name"),
        )
        self.assertEqual(
            "runs/layer1_siliconflow_qwen3_14b_decomp_gate_answer_repair_claim_risk_"
            "stratified45_five_stage_verifier_v1_3_4_controller_policy_v1_no_think",
            config.get("output_dir"),
        )
        self.assertEqual(["claim_risk"], config.get("methods"))
        self.assertTrue(config.get("claim_risk_controller_policy_v1"))
        self.assertTrue(config.get("repair_verified_chain_progress_v1_3_3"))
        self.assertTrue(config.get("repair_query_rewrite_v1_3_2"))


if __name__ == "__main__":
    unittest.main()
