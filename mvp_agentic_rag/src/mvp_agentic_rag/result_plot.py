from __future__ import annotations

import html
from pathlib import Path


DEFAULT_METRICS = ["answer_f1", "coverage", "avg_retrieval_calls", "answered_unsupported_rate"]


def render_metrics_svg(metrics: dict, metric_names: list[str] | None = None) -> str:
    metric_names = metric_names or DEFAULT_METRICS
    methods = list(metrics.get("methods", {}).items())
    width = 980
    row_height = 34
    group_gap = 26
    header_height = 92
    chart_width = 420
    label_width = 245
    value_width = 70
    height = header_height + len(metric_names) * (len(methods) * row_height + group_gap) + 30
    palette = ["#7F8F84", "#B7A99A", "#8A9199", "#B88C8C", "#D8D1C7"]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#F8F7F4"/>',
        f'<text x="28" y="38" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#242424">{_escape(metrics.get("run_name", "run"))}</text>',
        '<text x="28" y="64" font-family="Arial, sans-serif" font-size="13" fill="#555">Result summary generated from metrics.json</text>',
    ]
    y = header_height
    for metric_name in metric_names:
        max_value = max([float(values.get(metric_name, 0) or 0) for _, values in methods] + [1.0])
        lines.append(
            f'<text x="28" y="{y - 10}" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#333">{_escape(metric_name)}</text>'
        )
        for idx, (method, values) in enumerate(methods):
            value = float(values.get(metric_name, 0) or 0)
            bar_width = 0 if max_value <= 0 else int((value / max_value) * chart_width)
            bar_y = y + idx * row_height
            color = palette[idx % len(palette)]
            lines.extend(
                [
                    f'<text x="42" y="{bar_y + 20}" font-family="Arial, sans-serif" font-size="13" fill="#333">{_escape(method)}</text>',
                    f'<rect x="{label_width}" y="{bar_y + 6}" width="{chart_width}" height="18" rx="3" fill="#E5E0D8"/>',
                    f'<rect x="{label_width}" y="{bar_y + 6}" width="{bar_width}" height="18" rx="3" fill="{color}"/>',
                    f'<text x="{label_width + chart_width + 18}" y="{bar_y + 20}" font-family="Arial, sans-serif" font-size="13" fill="#333">{value:.4f}</text>',
                ]
            )
        y += len(methods) * row_height + group_gap
    lines.append("</svg>")
    return "\n".join(lines)


def write_metrics_svg(metrics: dict, output_path: str | Path, metric_names: list[str] | None = None) -> Path:
    path = Path(output_path)
    path.write_text(render_metrics_svg(metrics, metric_names=metric_names), encoding="utf-8")
    return path


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)
