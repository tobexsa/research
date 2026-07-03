from __future__ import annotations

from pathlib import Path


DEFAULT_COLUMNS = [
    "count",
    "overall_acc",
    "answer_f1",
    "coverage",
    "selective_acc",
    "selective_answer_f1",
    "avg_retrieval_calls",
    "wasted_retrieval_rate",
    "answered_unsupported_rate",
    "final_answered_unsupported_rate",
    "cost_normalized_acc",
    "cost_normalized_f1",
]


def render_metrics_markdown(metrics: dict, columns: list[str] | None = None) -> str:
    columns = columns or DEFAULT_COLUMNS
    run_name = str(metrics.get("run_name", "run"))
    lines = [f"# Results: {run_name}", ""]
    header = ["method", *columns]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")
    for method, values in sorted(metrics.get("methods", {}).items()):
        row = [method]
        for column in columns:
            row.append(_format_value(values.get(column, 0)))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return "\n".join(lines)


def write_metrics_markdown(metrics: dict, output_path: str | Path, columns: list[str] | None = None) -> Path:
    path = Path(output_path)
    path.write_text(render_metrics_markdown(metrics, columns=columns), encoding="utf-8")
    return path


def _format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
