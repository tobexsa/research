from __future__ import annotations

from collections.abc import Callable, Sequence


ColumnSpec = tuple[str, str]


DEFAULT_TUI_COLUMNS: list[ColumnSpec] = [
    ("count", "count"),
    ("overall_acc", "overall_acc"),
    ("answer_f1", "answer_f1"),
    ("coverage", "coverage"),
    ("selective_acc", "selective_acc"),
    ("selective_answer_f1", "selective_f1"),
    ("avg_retrieval_calls", "avg_calls"),
    ("wasted_retrieval_rate", "wasted_rate"),
    ("final_answered_unsupported_rate", "final_unsup"),
    ("cost_normalized_acc", "cost_acc"),
    ("cost_normalized_f1", "cost_f1"),
]


def render_tui_result_summary(metrics: dict, columns: Sequence[ColumnSpec] | None = None) -> str:
    """Render final run metrics as a terminal-friendly table, not Markdown."""
    selected_columns = list(columns or DEFAULT_TUI_COLUMNS)
    run_name = str(metrics.get("run_name", "run"))
    methods = metrics.get("methods", {})

    headers = ["method", *[label for _key, label in selected_columns]]
    rows = []
    for method, values in sorted(methods.items()):
        row = [str(method)]
        for key, _label in selected_columns:
            row.append(_format_value(values.get(key, 0)))
        rows.append(row)

    widths = _column_widths(headers, rows)
    lines = [f"results: {run_name}", ""]
    lines.append(_format_row(headers, widths))
    lines.append(_format_row(["-" * width for width in widths], widths))
    for row in rows:
        lines.append(_format_row(row, widths))
    return "\n".join(lines)


def emit_tui_result_summary(
    metrics: dict,
    write_output: Callable[[str], object],
    columns: Sequence[ColumnSpec] | None = None,
) -> None:
    """Emit the terminal result summary through a caller-owned writer."""
    write_output(render_tui_result_summary(metrics, columns=columns))


def _column_widths(headers: list[str], rows: list[list[str]]) -> list[int]:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    return widths


def _format_row(row: list[str], widths: list[int]) -> str:
    cells = []
    for index, cell in enumerate(row):
        if index == 0:
            cells.append(cell.ljust(widths[index]))
        else:
            cells.append(cell.rjust(widths[index]))
    return "  ".join(cells).rstrip()


def _format_value(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)
