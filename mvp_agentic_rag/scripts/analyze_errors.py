from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.evaluator import token_f1


BASELINE_METHOD = "agentic_rag_baseline"
PROMPT_METHOD = "prompt_verifier"
LEGACY_METHOD_ALIASES = {"ours": BASELINE_METHOD}


def build_error_analysis(run_dir: str | Path, max_cases: int = 10) -> str:
    run_path = Path(run_dir)
    records = _load_records(run_path / "trajectories.jsonl")
    by_method: dict[str, list[dict]] = defaultdict(list)
    by_id: dict[str, dict[str, dict]] = defaultdict(dict)
    for record in records:
        record = dict(record)
        record["method"] = _canonical_method_name(str(record["method"]))
        record["_f1"] = token_f1(record.get("final_answer", ""), record.get("gold_answer", ""))
        by_method[record["method"]].append(record)
        by_id[str(record["id"])][record["method"]] = record

    lines: list[str] = []
    lines.append(f"# Error Analysis: {run_path.name}")
    lines.append("")
    lines.append("## Run Shape")
    lines.append(f"- total records: {len(records)}")
    lines.append(f"- paired samples with both methods: {_count_paired_samples(by_id)}")
    lines.append("")

    for method in sorted(by_method):
        lines.extend(_format_method_summary(method, by_method[method]))

    pairs = [methods for methods in by_id.values() if BASELINE_METHOD in methods and PROMPT_METHOD in methods]
    lines.extend(_format_pairwise_summary(pairs))
    if BASELINE_METHOD in by_method:
        lines.extend(_format_baseline_retrieval_summary(by_method[BASELINE_METHOD]))
        lines.extend(_format_baseline_verifier_summary(by_method[BASELINE_METHOD]))
    lines.extend(_format_case_sections(pairs, max_cases=max_cases))
    return "\n".join(lines)


def write_error_analysis(run_dir: str | Path, max_cases: int = 10) -> Path:
    run_path = Path(run_dir)
    output = build_error_analysis(run_path, max_cases=max_cases)
    output_path = run_path / "error_analysis.md"
    output_path.write_text(output, encoding="utf-8")
    return output_path


def _load_records(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _canonical_method_name(method: str) -> str:
    return LEGACY_METHOD_ALIASES.get(method, method)


def _count_paired_samples(by_id: dict[str, dict[str, dict]]) -> int:
    return sum(1 for methods in by_id.values() if {BASELINE_METHOD, PROMPT_METHOD} <= set(methods))


def _format_method_summary(method: str, items: list[dict]) -> list[str]:
    f1s = [record["_f1"] for record in items]
    action_counts = Counter(record.get("final_action") for record in items)
    retrieval_counts = Counter(record.get("cost", {}).get("retrieval_calls", 0) for record in items)
    round_counts = Counter(len(record.get("trajectory", [])) for record in items)
    return [
        f"## {method}",
        f"- count: {len(items)}",
        f"- mean_f1: {_safe_mean(f1s):.6f}",
        f"- median_f1: {median(f1s) if f1s else 0.0:.6f}",
        f"- f1_zero: {sum(1 for value in f1s if value == 0)} ({_pct(sum(1 for value in f1s if value == 0), len(f1s))})",
        f"- f1_positive: {sum(1 for value in f1s if value > 0)} ({_pct(sum(1 for value in f1s if value > 0), len(f1s))})",
        f"- f1_ge_0_5: {sum(1 for value in f1s if value >= 0.5)} ({_pct(sum(1 for value in f1s if value >= 0.5), len(f1s))})",
        f"- final_action_counts: {dict(action_counts)}",
        f"- retrieval_call_counts: {dict(sorted(retrieval_counts.items()))}",
        f"- trajectory_round_counts: {dict(sorted(round_counts.items()))}",
        "",
    ]


def _format_pairwise_summary(pairs: list[dict[str, dict]]) -> list[str]:
    wins = losses = ties = 0
    baseline_answer_prompt_abstain = 0
    baseline_abstain_prompt_answer = 0
    both_abstain = 0
    both_answer = 0
    for pair in pairs:
        baseline = pair[BASELINE_METHOD]
        prompt = pair[PROMPT_METHOD]
        if baseline["_f1"] > prompt["_f1"]:
            wins += 1
        elif baseline["_f1"] < prompt["_f1"]:
            losses += 1
        else:
            ties += 1
        baseline_action = baseline.get("final_action")
        prompt_action = prompt.get("final_action")
        baseline_answer_prompt_abstain += int(baseline_action == "answer" and prompt_action == "abstain")
        baseline_abstain_prompt_answer += int(baseline_action == "abstain" and prompt_action == "answer")
        both_answer += int(baseline_action == "answer" and prompt_action == "answer")
        both_abstain += int(baseline_action == "abstain" and prompt_action == "abstain")
    return [
        "## Pairwise Comparison",
        f"- {BASELINE_METHOD} wins: {wins}",
        f"- {BASELINE_METHOD} losses: {losses}",
        f"- ties: {ties}",
        f"- {BASELINE_METHOD} answer / prompt abstain: {baseline_answer_prompt_abstain}",
        f"- {BASELINE_METHOD} abstain / prompt answer: {baseline_abstain_prompt_answer}",
        f"- both answer: {both_answer}",
        f"- both abstain: {both_abstain}",
        "",
    ]


def _format_baseline_retrieval_summary(items: list[dict]) -> list[str]:
    extra = [record for record in items if record.get("cost", {}).get("retrieval_calls", 0) > 1]
    no_new = [record for record in items if _has_no_new_evidence(record)]
    without_no_new = [record for record in items if not _has_no_new_evidence(record)]
    return [
        "## agentic_rag_baseline Retrieval Behavior",
        f"- extra_retrieval_records: {len(extra)} ({_pct(len(extra), len(items))})",
        f"- no_new_evidence_records: {len(no_new)} ({_pct(len(no_new), len(items))})",
        f"- no_new_evidence_and_abstain: {sum(1 for record in no_new if record.get('final_action') == 'abstain')}",
        f"- no_new_evidence_and_answer: {sum(1 for record in no_new if record.get('final_action') == 'answer')}",
        f"- mean_f1_with_no_new_evidence: {_safe_mean([record['_f1'] for record in no_new]):.6f}",
        f"- mean_f1_without_no_new_evidence: {_safe_mean([record['_f1'] for record in without_no_new]):.6f}",
        "",
    ]


def _format_baseline_verifier_summary(items: list[dict]) -> list[str]:
    need_more_counts: Counter[str] = Counter()
    sufficiency_counts: Counter[str] = Counter()
    risk_scores = []
    suggested_empty = 0
    suggested_nonempty = 0
    for record in items:
        for step in record.get("trajectory", []):
            verifier_output = step.get("verifier_output", {})
            need_more_counts[str(verifier_output.get("need_more_evidence"))] += 1
            sufficiency_counts[str(verifier_output.get("overall_sufficiency"))] += 1
            risk_score = verifier_output.get("risk_score")
            if isinstance(risk_score, (int, float)):
                risk_scores.append(float(risk_score))
            if verifier_output.get("suggested_query"):
                suggested_nonempty += 1
            else:
                suggested_empty += 1
    lines = [
        "## agentic_rag_baseline Verifier Decision Signals",
        f"- need_more_evidence_counts_by_step: {dict(need_more_counts)}",
        f"- overall_sufficiency_counts_by_step: {dict(sufficiency_counts)}",
    ]
    if risk_scores:
        lines.append(f"- risk_score_mean: {mean(risk_scores):.6f}")
        lines.append(f"- risk_score_max: {max(risk_scores):.6f}")
    lines.extend(
        [
            f"- suggested_query_nonempty_steps: {suggested_nonempty}",
            f"- suggested_query_empty_steps: {suggested_empty}",
            "",
        ]
    )
    return lines


def _format_case_sections(pairs: list[dict[str, dict]], max_cases: int) -> list[str]:
    sections = [
        (
            f"{BASELINE_METHOD} wins over {PROMPT_METHOD}",
            sorted(
                [pair for pair in pairs if pair[BASELINE_METHOD]["_f1"] > pair[PROMPT_METHOD]["_f1"]],
                key=lambda pair: pair[BASELINE_METHOD]["_f1"] - pair[PROMPT_METHOD]["_f1"],
                reverse=True,
            )[:max_cases],
        ),
        (
            f"{BASELINE_METHOD} loses to {PROMPT_METHOD}",
            sorted(
                [pair for pair in pairs if pair[BASELINE_METHOD]["_f1"] < pair[PROMPT_METHOD]["_f1"]],
                key=lambda pair: pair[PROMPT_METHOD]["_f1"] - pair[BASELINE_METHOD]["_f1"],
                reverse=True,
            )[:max_cases],
        ),
        (
            f"{BASELINE_METHOD} no-new-evidence abstentions",
            sorted(
                [
                    pair
                    for pair in pairs
                    if _has_no_new_evidence(pair[BASELINE_METHOD])
                    and pair[BASELINE_METHOD].get("final_action") == "abstain"
                ],
                key=lambda pair: pair[BASELINE_METHOD].get("cost", {}).get("retrieval_calls", 0),
                reverse=True,
            )[:max_cases],
        ),
    ]
    lines: list[str] = []
    for title, rows in sections:
        lines.append(f"## Cases: {title}")
        for idx, pair in enumerate(rows, 1):
            lines.extend(_format_pair_case(idx, pair))
        lines.append("")
    return lines


def _format_pair_case(idx: int, pair: dict[str, dict]) -> list[str]:
    baseline = pair[BASELINE_METHOD]
    prompt = pair.get(PROMPT_METHOD, {})
    lines = [
        f"{idx}. id={baseline['id']}",
        f"   - question: {_short(baseline.get('question'))}",
        f"   - gold: {_short(baseline.get('gold_answer'))}",
        (
            f"   - {BASELINE_METHOD}: action={baseline.get('final_action')} f1={baseline['_f1']:.3f} "
            f"calls={baseline.get('cost', {}).get('retrieval_calls')} "
            f"answer={_short(baseline.get('final_answer'))}"
        ),
    ]
    if prompt:
        lines.append(
            f"   - prompt: action={prompt.get('final_action')} f1={prompt['_f1']:.3f} "
            f"calls={prompt.get('cost', {}).get('retrieval_calls')} answer={_short(prompt.get('final_answer'))}"
        )
    if baseline.get("trajectory"):
        last = baseline["trajectory"][-1]
        verifier_output = last.get("verifier_output", {})
        lines.append(
            f"   - {BASELINE_METHOD}_last: round={last.get('round')} evidence_gain={last.get('evidence_gain')} "
            f"suff={verifier_output.get('overall_sufficiency')} need_more={verifier_output.get('need_more_evidence')} "
            f"risk={verifier_output.get('risk_score')} suggested={_short(verifier_output.get('suggested_query', ''), 120)}"
        )
    return lines


def _has_no_new_evidence(record: dict) -> bool:
    return any(step.get("evidence_gain", 0) <= 0 for step in record.get("trajectory", [])[1:])


def _safe_mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def _pct(count: int, total: int) -> str:
    return f"{(count / total) if total else 0.0:.1%}"


def _short(value: object, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze trajectory-level errors for a run directory.")
    parser.add_argument("run_dir", nargs="?", default="runs/offline_bm25_smoke_all_methods")
    parser.add_argument("--max-cases", type=int, default=10)
    args = parser.parse_args()
    output_path = write_error_analysis(args.run_dir, max_cases=args.max_cases)
    _safe_print(str(output_path))
    _safe_print(output_path.read_text(encoding="utf-8"))
    return 0


def _safe_print(text: str, stream=sys.stdout) -> None:
    try:
        print(text, file=stream)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(safe_text, file=stream)


if __name__ == "__main__":
    raise SystemExit(main())
