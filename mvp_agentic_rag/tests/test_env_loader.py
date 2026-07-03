from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from mvp_agentic_rag.env import load_env_file


class EnvLoaderTests(unittest.TestCase):
    def test_loads_values_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "# local credentials",
                        "",
                        "SILICONFLOW_API_KEY=test-key",
                        "VALUE_WITH_EQUALS=a=b=c",
                    ]
                ),
                encoding="utf-8",
            )
            self.addCleanup(os.environ.pop, "SILICONFLOW_API_KEY", None)
            self.addCleanup(os.environ.pop, "VALUE_WITH_EQUALS", None)
            os.environ.pop("SILICONFLOW_API_KEY", None)
            os.environ.pop("VALUE_WITH_EQUALS", None)

            loaded = load_env_file(env_path)

        self.assertEqual({"SILICONFLOW_API_KEY": "test-key", "VALUE_WITH_EQUALS": "a=b=c"}, loaded)
        self.assertEqual("test-key", os.environ["SILICONFLOW_API_KEY"])
        self.assertEqual("a=b=c", os.environ["VALUE_WITH_EQUALS"])

    def test_does_not_override_existing_environment_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("SILICONFLOW_API_KEY=file-key\n", encoding="utf-8")
            original = os.environ.get("SILICONFLOW_API_KEY")
            os.environ["SILICONFLOW_API_KEY"] = "existing-key"
            self.addCleanup(self._restore_env, "SILICONFLOW_API_KEY", original)

            loaded = load_env_file(env_path)

        self.assertEqual({}, loaded)
        self.assertEqual("existing-key", os.environ["SILICONFLOW_API_KEY"])

    def test_missing_env_file_is_noop(self) -> None:
        loaded = load_env_file(Path("does-not-exist.env"))

        self.assertEqual({}, loaded)

    @staticmethod
    def _restore_env(key: str, value: str | None) -> None:
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
