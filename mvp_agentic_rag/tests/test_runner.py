import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mvp_agentic_rag.layer1_runner import run_experiment
from mvp_agentic_rag.progress import ProgressReporter


class RunnerTests(unittest.TestCase):
    def test_runner_executes_all_methods_and_resume_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            out = root / "run"
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "What city is the capital of France?",
                        "answer": "Paris",
                        "supporting_passage_ids": ["p1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps({"id": "p1", "title": "Paris", "text": "Paris is the capital of France."})
                + "\n",
                encoding="utf-8",
            )
            config = {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "bm25",
                "methods": ["naive", "fixed_k", "self_stop", "prompt_verifier", "agentic_rag_baseline"],
                "top_k": 1,
                "max_rounds": 2,
            }

            first = run_experiment(config)
            second = run_experiment(config)
            lines = (out / "trajectories.jsonl").read_text(encoding="utf-8").strip().splitlines()

        self.assertEqual(first["completed"], 5)
        self.assertEqual(second["skipped"], 5)
        self.assertEqual(len(lines), 5)

    def test_runner_reports_progress_and_writes_result_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            out = root / "run"
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "What city is the capital of France?",
                        "answer": "Paris",
                        "supporting_passage_ids": ["p1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps({"id": "p1", "title": "Paris", "text": "Paris is the capital of France."})
                + "\n",
                encoding="utf-8",
            )
            messages = []
            config = {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "bm25",
                "methods": ["naive", "fixed_k"],
                "top_k": 1,
                "max_rounds": 1,
                "progress_every": 1,
            }

            result = run_experiment(config, progress_writer=messages.append)
            table_exists = (out / "run_summary.md").exists()

        self.assertTrue(any("progress:" in message for message in messages))
        self.assertIn("result_table", result)
        self.assertTrue(table_exists)

    def test_runner_refuses_to_start_when_output_dir_is_locked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            out = root / "run"
            out.mkdir()
            (out / ".run.lock").write_text("existing run", encoding="utf-8")
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "What city is the capital of France?",
                        "answer": "Paris",
                        "supporting_passage_ids": ["p1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps({"id": "p1", "title": "Paris", "text": "Paris is the capital of France."})
                + "\n",
                encoding="utf-8",
            )
            config = {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "bm25",
                "methods": ["naive"],
                "top_k": 1,
                "max_rounds": 1,
            }

            with self.assertRaisesRegex(RuntimeError, "already locked"):
                run_experiment(config)

    def test_runner_progress_every_zero_suppresses_progress_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = root / "samples.jsonl"
            corpus = root / "corpus.jsonl"
            out = root / "run"
            dataset.write_text(
                json.dumps(
                    {
                        "id": "q1",
                        "question": "What city is the capital of France?",
                        "answer": "Paris",
                        "supporting_passage_ids": ["p1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            corpus.write_text(
                json.dumps({"id": "p1", "title": "Paris", "text": "Paris is the capital of France."})
                + "\n",
                encoding="utf-8",
            )
            config = {
                "dataset": str(dataset),
                "corpus": str(corpus),
                "output_dir": str(out),
                "retriever": "bm25",
                "methods": ["naive"],
                "top_k": 1,
                "max_rounds": 1,
                "progress_every": 0,
            }
            stdout = io.StringIO()

            with patch("sys.stdout", stdout):
                run_experiment(config)

        self.assertNotIn("progress:", stdout.getvalue())
        self.assertIn("result_table:", stdout.getvalue())


class ProgressReporterTests(unittest.TestCase):
    """Unit tests for the ProgressReporter in isolation (no experiment runner)."""

    @staticmethod
    def _make_reporter(total=30, every=1, display="plain", out=None):
        return ProgressReporter(
            total=total,
            output_dir="runs/test_run",
            every=every,
            display=display,
            out=out,
        )

    def test_plain_writes_progress_lines(self):
        buf = io.StringIO()
        reporter = self._make_reporter(every=3, display="plain", out=buf)
        for c in range(1, 10):
            reporter.update(c, skipped=0)
        reporter.finish()
        lines = buf.getvalue().splitlines()
        # 3, 6, 9: three progress lines + one finish line.
        self.assertGreaterEqual(len(lines), 3)
        self.assertTrue(all("progress:" in line for line in lines))

    def test_tui_writes_carriage_return_and_bar(self):
        buf = io.StringIO()
        reporter = self._make_reporter(every=1, display="tui", out=buf)
        reporter.update(10, skipped=1)
        output = buf.getvalue()
        self.assertIn("\r", output)
        self.assertIn("[", output)
        self.assertIn("]", output)
        self.assertIn("11/30", output)
        self.assertIn("elapsed=", output)

    def test_none_suppresses_output(self):
        buf = io.StringIO()
        reporter = self._make_reporter(display="none", out=buf)
        reporter.update(1, skipped=0)
        reporter.update(2, skipped=0)
        reporter.finish()
        self.assertEqual(buf.getvalue(), "")

    @patch("sys.stdout.isatty", return_value=True)
    def test_auto_detects_tty_and_uses_tui(self, _mock):
        buf = io.StringIO()
        buf.isatty = lambda: True
        reporter = ProgressReporter(
            total=30, output_dir="runs/test", every=1, display="auto", out=buf
        )
        reporter.update(5, skipped=0)
        self.assertIn("\r", buf.getvalue())

    @patch("sys.stdout.isatty", return_value=False)
    def test_auto_detects_no_tty_and_falls_back_to_plain(self, _mock):
        buf = io.StringIO()
        buf.isatty = lambda: False
        reporter = ProgressReporter(
            total=30, output_dir="runs/test", every=1, display="auto", out=buf
        )
        reporter.update(5, skipped=0)
        self.assertIn("progress:", buf.getvalue())

    def test_respects_every(self):
        buf = io.StringIO()
        reporter = self._make_reporter(every=3, display="plain", out=buf)
        for c in range(1, 7):
            reporter.update(c, skipped=0)
        lines = buf.getvalue().splitlines()
        # Only completions 3 and 6 should have produced lines.
        self.assertEqual(len(lines), 2)
        self.assertIn("completed=3", lines[0])
        self.assertIn("completed=6", lines[1])

    def test_rejects_bad_display_value(self):
        with self.assertRaises(ValueError):
            self._make_reporter(display="invalid")

    def test_write_line_always_emits(self):
        buf = io.StringIO()
        reporter = self._make_reporter(display="none", out=buf)
        reporter.write_line("result_table: path/table.md")
        self.assertIn("result_table:", buf.getvalue())

    def test_tui_progress_counts_resumed_skips_toward_total(self):
        buf = io.StringIO()
        reporter = self._make_reporter(total=900, every=1, display="tui", out=buf)
        reporter.update(10, skipped=601)
        output = buf.getvalue()
        self.assertIn("611/900", output)
        self.assertIn("67.9%", output)
        self.assertIn("completed=10", output)
        self.assertIn("skipped=601", output)

    def test_finish_preserves_final_completed_and_skipped_counts(self):
        buf = io.StringIO()
        reporter = self._make_reporter(total=900, every=500, display="tui", out=buf)
        reporter.finish(completed=299, skipped=601)
        output = buf.getvalue()
        self.assertIn("900/900", output)
        self.assertIn("100.0%", output)
        self.assertIn("completed=299", output)
        self.assertIn("skipped=601", output)
