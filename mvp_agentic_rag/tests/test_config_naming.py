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


if __name__ == "__main__":
    unittest.main()
