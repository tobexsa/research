from __future__ import annotations

import json
import os
from pathlib import Path

from .agents import AGENT_CLASSES
from .data_loader import load_corpus, load_samples
from .evaluator import write_metrics
from .progress import ProgressReporter
from .result_plot import write_metrics_svg
from .result_table import write_metrics_markdown
from .retriever import make_retriever
from .tui_result_summary import emit_tui_result_summary


def run_experiment(config: dict, progress_writer=None) -> dict:
    dataset_path = Path(config["dataset"])
    corpus_path = Path(config["corpus"])
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    with _OutputDirLock(output_dir):
        trajectories_path = output_dir / "trajectories.jsonl"
        samples = load_samples(dataset_path)
        non_leaking_runtime = bool(config.get("non_leaking_runtime_v1", False))
        predictions_only = bool(config.get("predictions_only", False))
        evaluation_labels_path = config.get("evaluation_labels_path")
        if non_leaking_runtime:
            _assert_non_leaking_samples(samples)
            if predictions_only and evaluation_labels_path:
                raise ValueError("predictions-only non-leaking runs must not load evaluation labels")
            if not predictions_only and not evaluation_labels_path:
                raise ValueError("non-leaking metric runs require evaluation_labels_path")
        if int(config.get("limit_samples", 0) or 0) > 0:
            samples = samples[: int(config["limit_samples"])]
        corpus = load_corpus(corpus_path)
        methods = list(
            config.get("methods", ["naive", "fixed_k", "self_stop", "prompt_verifier", "agentic_rag_baseline"])
        )
        top_k = int(config.get("top_k", 5))
        max_rounds = int(config.get("max_rounds", 3))
        retriever_name = str(config.get("retriever", "bm25"))
        progress_every = int(config.get("progress_every", 10) or 0)
        total = len(samples) * len(methods)

        # Backwards-compatible: if caller passed an explicit progress_writer,
        # use the old behaviour; otherwise create a ProgressReporter.
        if progress_writer is not None:
            reporter = None
            _emit = progress_writer
        else:
            progress_display = str(config.get("progress_display", "auto"))
            if progress_every <= 0 and "progress_display" not in config:
                progress_display = "none"
            reporter = ProgressReporter(
                total=total,
                output_dir=str(output_dir),
                every=max(progress_every, 1),
                display=progress_display,
            )
            _emit = reporter.update

        completed_keys = _load_completed_keys(trajectories_path)
        completed = 0
        skipped = 0
        runtime_config = _runtime_config(config) if non_leaking_runtime else config
        retriever = make_retriever(retriever_name, corpus, runtime_config)
        with trajectories_path.open("a", encoding="utf-8", newline="\n") as handle:
            for sample in samples:
                for method in methods:
                    key = (sample.sample_id, method)
                    if key in completed_keys:
                        skipped += 1
                        continue
                    agent = AGENT_CLASSES[method](
                        retriever,
                        top_k=top_k,
                        max_rounds=max_rounds,
                        config=runtime_config,
                    )
                    result = agent.run(sample)
                    handle.write(json.dumps(result.to_record(), ensure_ascii=False, sort_keys=True) + "\n")
                    handle.flush()
                    completed += 1
                    if reporter is not None:
                        reporter.update(completed, skipped)
                    elif progress_every > 0 and completed % progress_every == 0:
                        _emit(
                            f"progress: completed={completed} skipped={skipped} total={total} "
                            f"output_dir={output_dir}"
                        )

        if reporter is not None:
            reporter.finish(completed=completed, skipped=skipped)

        run_name = str(config.get("run_name", output_dir.name))
        result = {"completed": completed, "skipped": skipped, "output_dir": str(output_dir)}
        if predictions_only:
            predictions_path = _write_predictions(trajectories_path, output_dir / "predictions.jsonl")
            result["predictions"] = str(predictions_path)
            metrics = None
        else:
            metrics = write_metrics(
                output_dir,
                run_name,
                evaluation_labels_path=evaluation_labels_path,
            )
        if metrics is not None and bool(config.get("write_result_table", True)):
            table_path = write_metrics_markdown(metrics, output_dir / "run_summary.md")
            result["result_table"] = str(table_path)
            if reporter is not None:
                reporter.write_line(f"result_table: {table_path}")
            else:
                _emit(f"result_table: {table_path}")
        if metrics is not None and bool(config.get("print_result_summary", True)):
            if reporter is not None:
                emit_tui_result_summary(metrics, reporter.write_line)
            else:
                emit_tui_result_summary(metrics, _emit)
        if metrics is not None and bool(config.get("write_result_plot", False)):
            plot_path = write_metrics_svg(metrics, output_dir / "result_summary.svg")
            result["result_plot"] = str(plot_path)
            if reporter is not None:
                reporter.write_line(f"result_plot: {plot_path}")
            else:
                _emit(f"result_plot: {plot_path}")
        return result


def _runtime_config(config: dict) -> dict:
    excluded = {
        "evaluation_labels_path",
        "submission_map_path",
        "official_source_path",
    }
    return {key: value for key, value in config.items() if key not in excluded}


def _assert_non_leaking_samples(samples) -> None:
    allowed_metadata = {"runtime_contract", "candidate_passage_ids"}
    for sample in samples:
        if sample.gold_answer:
            raise ValueError(f"non-leaking runtime sample contains gold answer: {sample.sample_id}")
        if sample.supporting_passage_ids:
            raise ValueError(f"non-leaking runtime sample contains support labels: {sample.sample_id}")
        if sample.hop is not None:
            raise ValueError(f"non-leaking runtime sample contains hop label: {sample.sample_id}")
        unexpected = set(sample.metadata) - allowed_metadata
        if unexpected:
            raise ValueError(
                f"non-leaking runtime sample contains unexpected metadata {sorted(unexpected)}: "
                f"{sample.sample_id}"
            )
        if not sample.metadata.get("candidate_passage_ids"):
            raise ValueError(f"non-leaking runtime sample has no candidate passages: {sample.sample_id}")


def _write_predictions(trajectory_path: Path, output_path: Path) -> Path:
    with trajectory_path.open("r", encoding="utf-8") as source, output_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as target:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            target.write(
                json.dumps(
                    {
                        "id": str(record.get("id") or ""),
                        "method": str(record.get("method") or ""),
                        "prediction": str(record.get("final_answer") or ""),
                        "action": str(record.get("final_action") or ""),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )
    return output_path


class _OutputDirLock:
    def __init__(self, output_dir: Path):
        self.lock_path = output_dir / ".run.lock"
        self._fd: int | None = None

    def __enter__(self):
        self._reclaim_stale_lock()
        try:
            self._fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"output_dir is already locked by another run: {self.lock_path}") from exc
        os.write(self._fd, str(os.getpid()).encode("utf-8"))
        os.close(self._fd)
        self._fd = None
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass

    def _reclaim_stale_lock(self) -> None:
        if not self.lock_path.exists():
            return
        try:
            pid_text = self.lock_path.read_text(encoding="utf-8").strip()
            pid = int(pid_text)
        except (OSError, ValueError):
            return
        if pid <= 0:
            return
        if _pid_is_running(pid):
            return
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass


def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _load_completed_keys(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    keys = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            keys.add((str(record["id"]), str(record["method"])))
    return keys
