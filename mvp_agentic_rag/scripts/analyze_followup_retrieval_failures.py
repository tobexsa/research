from __future__ import annotations

import argparse
import csv
import json
import pickle
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

import sys

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.config import load_simple_config
from mvp_agentic_rag.data_loader import load_corpus, load_samples
from mvp_agentic_rag.query_decomposer import make_query_decomposer
from mvp_agentic_rag.retriever import make_retriever, tokenize


DEFAULT_CONFIG = (
    "configs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30.yaml"
)
DEFAULT_RUN = (
    "runs/layer1_api_balanced300_dense_bge_decomp_gate_claim_evidence_memory_structured_query_low_yield_abstain_claim_risk_subset30_agentic_rag_baseline"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze claim_risk follow-up retrieval failures.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--run-dir", default=DEFAULT_RUN)
    parser.add_argument("--output-dir", default="analysis/followup_retrieval_failures")
    parser.add_argument("--method", default="claim_risk")
    parser.add_argument("--raw-depth", type=int, default=50)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    config = load_simple_config(args.config)
    corpus = load_corpus(config["corpus"])
    samples = {sample.sample_id: sample for sample in load_samples(config["dataset"])}
    retriever = make_retriever(str(config.get("retriever", "dense")), corpus, config)
    decomposer = make_query_decomposer(config)
    index_passage_ids = _load_index_passage_ids(config)

    records = _load_records(Path(args.run_dir), args.method)
    cases = []
    for record in records:
        sample = samples[str(record["id"])]
        supporting_ids = set(sample.supporting_passage_ids)
        for idx, step in enumerate(record.get("trajectory", [])):
            if idx == 0:
                continue
            if float(step.get("evidence_gain", 0.0)) > 0:
                continue
            previous_retrieved_ids = {
                str(pid)
                for previous_step in record.get("trajectory", [])[:idx]
                for pid in previous_step.get("retrieved_ids", [])
            }
            cases.append(
                _analyze_case(
                    record=record,
                    step=step,
                    previous_retrieved_ids=previous_retrieved_ids,
                    sample=sample,
                    supporting_ids=supporting_ids,
                    corpus=corpus,
                    index_passage_ids=index_passage_ids,
                    retriever=retriever,
                    decomposer=decomposer,
                    raw_depth=args.raw_depth,
                    top_k=args.top_k,
                )
            )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = _summarize(cases)
    payload = {
        "run_dir": args.run_dir,
        "config": args.config,
        "case_definition": "claim_risk follow-up step with evidence_gain <= 0",
        "summary": summary,
        "cases": cases,
    }
    (output_dir / "followup_failure_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_cases_csv(output_dir / "followup_failure_cases.csv", cases)
    _write_markdown(output_dir / "followup_failure_summary.md", payload)
    print(json.dumps({"summary": summary, "output_dir": str(output_dir)}, ensure_ascii=False, indent=2))
    return 0


def _load_records(run_dir: Path, method: str) -> list[dict[str, Any]]:
    trajectory_path = run_dir / "trajectories.jsonl"
    records = []
    with trajectory_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("method") == method:
                records.append(record)
    return records


def _analyze_case(
    record: dict[str, Any],
    step: dict[str, Any],
    previous_retrieved_ids: set[str],
    sample,
    supporting_ids: set[str],
    corpus: dict,
    index_passage_ids: set[str],
    retriever,
    decomposer,
    raw_depth: int,
    top_k: int,
) -> dict[str, Any]:
    query = str(step.get("query", ""))
    retrieved_ids = [str(pid) for pid in step.get("retrieved_ids", [])]
    support_in_current_retrieved = sorted(supporting_ids & set(retrieved_ids))
    support_seen_before = sorted(supporting_ids & previous_retrieved_ids)
    new_support_in_current_retrieved = sorted((supporting_ids & set(retrieved_ids)) - previous_retrieved_ids)
    cumulative_support_after_step = sorted(supporting_ids & (previous_retrieved_ids | set(retrieved_ids)))
    support_in_corpus = sorted(pid for pid in supporting_ids if pid in corpus)
    support_missing_corpus = sorted(supporting_ids - set(support_in_corpus))
    support_in_index = sorted(pid for pid in supporting_ids if pid in index_passage_ids)
    support_missing_index = sorted(supporting_ids - set(support_in_index))

    raw_ids = [passage.passage_id for passage in retriever.search(query, raw_depth)]
    raw_topk_ids = raw_ids[:top_k]
    decomposed_queries = decomposer.decompose(sample, query)
    decomposed_ids = _merged_decomposed_ids(retriever, decomposed_queries, per_query_top_k=top_k, total_top_k=top_k)
    decomposed_deep_ids = _merged_decomposed_ids(
        retriever,
        decomposed_queries,
        per_query_top_k=raw_depth,
        total_top_k=raw_depth,
    )

    original_question_ids = [passage.passage_id for passage in retriever.search(sample.question, raw_depth)]
    query_terms = set(tokenize(query))
    question_terms = set(tokenize(sample.question))
    missing_question_terms = sorted(question_terms - query_terms)
    overlap_question_terms = sorted(query_terms & question_terms)

    support_titles = {pid: corpus[pid].title for pid in support_in_corpus}
    support_text = " ".join((corpus[pid].title + " " + corpus[pid].text) for pid in support_in_corpus)
    support_terms = set(tokenize(support_text))
    query_support_overlap = sorted(query_terms & support_terms)
    query_mentions_gold = bool(set(tokenize(sample.gold_answer)) & query_terms)

    categories = _categories(
        support_missing_corpus=support_missing_corpus,
        support_missing_index=support_missing_index,
        supporting_ids=supporting_ids,
        retrieved_ids=retrieved_ids,
        raw_topk_ids=raw_topk_ids,
        raw_ids=raw_ids,
        decomposed_ids=decomposed_ids,
        decomposed_deep_ids=decomposed_deep_ids,
        original_question_ids=original_question_ids,
        query_support_overlap=query_support_overlap,
        overlap_question_terms=overlap_question_terms,
        question_terms=question_terms,
        decomposed_queries=decomposed_queries,
        support_in_current_retrieved=support_in_current_retrieved,
        support_seen_before=support_seen_before,
        new_support_in_current_retrieved=new_support_in_current_retrieved,
        cumulative_support_after_step=cumulative_support_after_step,
        verifier_output=step.get("verifier_output", {}),
    )

    return {
        "run_id": record.get("id"),
        "round": step.get("round"),
        "query_source": step.get("query_source", ""),
        "action": step.get("action", ""),
        "query": query,
        "question": sample.question,
        "gold_answer": sample.gold_answer,
        "retrieved_ids": retrieved_ids,
        "support_in_current_retrieved": support_in_current_retrieved,
        "support_seen_before": support_seen_before,
        "new_support_in_current_retrieved": new_support_in_current_retrieved,
        "cumulative_support_after_step": cumulative_support_after_step,
        "supporting_ids": sorted(supporting_ids),
        "support_titles": support_titles,
        "support_missing_corpus": support_missing_corpus,
        "support_missing_index": support_missing_index,
        "support_in_raw_topk": sorted(supporting_ids & set(raw_topk_ids)),
        "support_in_raw_top50": sorted(supporting_ids & set(raw_ids)),
        "support_in_decomposed_topk": sorted(supporting_ids & set(decomposed_ids)),
        "support_in_decomposed_top50": sorted(supporting_ids & set(decomposed_deep_ids)),
        "support_in_original_question_top50": sorted(supporting_ids & set(original_question_ids)),
        "raw_rank_first_support": _first_rank(raw_ids, supporting_ids),
        "original_question_rank_first_support": _first_rank(original_question_ids, supporting_ids),
        "decomposed_queries": decomposed_queries,
        "missing_question_terms": missing_question_terms,
        "overlap_question_terms": overlap_question_terms,
        "query_support_overlap_terms": query_support_overlap,
        "query_mentions_gold_answer": query_mentions_gold,
        "categories": categories,
        "structured_query": step.get("structured_query", {}),
    }


def _categories(
    support_missing_corpus: list[str],
    support_missing_index: list[str],
    supporting_ids: set[str],
    retrieved_ids: list[str],
    raw_topk_ids: list[str],
    raw_ids: list[str],
    decomposed_ids: list[str],
    decomposed_deep_ids: list[str],
    original_question_ids: list[str],
    query_support_overlap: list[str],
    overlap_question_terms: list[str],
    question_terms: set[str],
    decomposed_queries: list[str],
    support_in_current_retrieved: list[str],
    support_seen_before: list[str],
    new_support_in_current_retrieved: list[str],
    cumulative_support_after_step: list[str],
    verifier_output: dict[str, Any],
) -> list[str]:
    categories = []
    if support_missing_corpus:
        categories.append("support_missing_from_corpus")
    if support_missing_index:
        categories.append("support_missing_from_index")
    if support_in_current_retrieved:
        categories.append("support_retrieved_but_no_evidence_gain")
    if support_seen_before and not new_support_in_current_retrieved:
        categories.append("support_already_seen_before_followup")
    if new_support_in_current_retrieved:
        categories.append("new_support_retrieved_but_gain_zero")
    if cumulative_support_after_step and _has_unsupported_critical_claim(verifier_output):
        categories.append("verifier_failed_despite_support_context")
    if not support_missing_corpus and not (supporting_ids & set(raw_ids)):
        categories.append("dense_recall_miss_top50")
    if supporting_ids & set(raw_ids) and not (supporting_ids & set(raw_topk_ids)):
        categories.append("top_k_too_small")
    if supporting_ids & set(raw_ids) and not (supporting_ids & set(decomposed_deep_ids)):
        categories.append("decomposition_hurts_recall")
    if supporting_ids & set(decomposed_deep_ids) and not (supporting_ids & set(decomposed_ids)):
        categories.append("per_subquery_or_total_top_k_too_small")
    if not query_support_overlap:
        categories.append("query_low_support_term_overlap")
    if len(overlap_question_terms) < max(2, min(4, len(question_terms) // 3)):
        categories.append("query_drops_question_constraints")
    if len(decomposed_queries) > 1 and not (supporting_ids & set(decomposed_deep_ids)):
        categories.append("decomposed_queries_miss_support")
    return categories or ["unclassified"]


def _has_unsupported_critical_claim(verifier_output: dict[str, Any]) -> bool:
    for claim in verifier_output.get("claims", []):
        if claim.get("is_critical") and claim.get("status") in {"unsupported", "unclear", "contradicted"}:
            return True
    return False


def _merged_decomposed_ids(retriever, queries: list[str], per_query_top_k: int, total_top_k: int) -> list[str]:
    merged = []
    seen = set()
    for query in queries:
        for passage in retriever.search(query, per_query_top_k):
            if passage.passage_id in seen:
                continue
            merged.append(passage.passage_id)
            seen.add(passage.passage_id)
            if len(merged) >= total_top_k:
                return merged
    return merged


def _first_rank(ids: list[str], targets: set[str]) -> int | None:
    for idx, pid in enumerate(ids, start=1):
        if pid in targets:
            return idx
    return None


def _load_index_passage_ids(config: dict) -> set[str]:
    meta_path = Path(str(config.get("meta_path", "")))
    if not meta_path.exists():
        return set()
    with meta_path.open("rb") as handle:
        meta = pickle.load(handle)
    return {str(pid) for pid in meta.get("passage_ids", [])}


def _summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(category for case in cases for category in case["categories"])
    source_counts = Counter(case["query_source"] or "missing" for case in cases)
    action_counts = Counter(case["action"] or "missing" for case in cases)
    raw_support = sum(1 for case in cases if case["support_in_raw_top50"])
    original_question_support = sum(1 for case in cases if case["support_in_original_question_top50"])
    return {
        "cases": len(cases),
        "category_counts": dict(category_counts.most_common()),
        "query_source_counts": dict(source_counts.most_common()),
        "action_counts": dict(action_counts.most_common()),
        "support_in_raw_top50_cases": raw_support,
        "support_in_raw_top50_rate": raw_support / len(cases) if cases else 0.0,
        "support_in_original_question_top50_cases": original_question_support,
        "support_in_original_question_top50_rate": original_question_support / len(cases) if cases else 0.0,
    }


def _write_cases_csv(path: Path, cases: list[dict[str, Any]]) -> None:
    fieldnames = [
        "run_id",
        "round",
        "query_source",
        "action",
        "query",
        "question",
        "gold_answer",
        "supporting_ids",
        "retrieved_ids",
        "support_in_current_retrieved",
        "support_seen_before",
        "new_support_in_current_retrieved",
        "cumulative_support_after_step",
        "raw_rank_first_support",
        "original_question_rank_first_support",
        "support_in_raw_top50",
        "support_in_original_question_top50",
        "categories",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for case in cases:
            writer.writerow({key: _csv_value(case.get(key, "")) for key in fieldnames})


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Follow-Up Retrieval Failure Analysis",
        "",
        f"Run: `{payload['run_dir']}`",
        "",
        f"Case definition: {payload['case_definition']}",
        "",
        "## Summary",
        "",
        f"- cases: {summary['cases']}",
        f"- support_in_raw_top50_rate: {summary['support_in_raw_top50_rate']:.4f}",
        f"- support_in_original_question_top50_rate: {summary['support_in_original_question_top50_rate']:.4f}",
        "",
        "## Category Counts",
        "",
        "| category | count |",
        "| --- | ---: |",
    ]
    for category, count in summary["category_counts"].items():
        lines.append(f"| {category} | {count} |")
    lines.extend(
        [
            "",
            "## Query Source Counts",
            "",
            "| query_source | count |",
            "| --- | ---: |",
        ]
    )
    for source, count in summary["query_source_counts"].items():
        lines.append(f"| {source} | {count} |")
    lines.extend(["", "## Representative Cases", ""])
    for case in payload["cases"][:10]:
        lines.extend(
            [
                f"### {case['run_id']} round {case['round']}",
                "",
                f"- query_source: `{case['query_source']}`",
                f"- action: `{case['action']}`",
                f"- categories: {', '.join(case['categories'])}",
                f"- raw_rank_first_support: {case['raw_rank_first_support']}",
                f"- original_question_rank_first_support: {case['original_question_rank_first_support']}",
                f"- support_seen_before: {', '.join(case['support_seen_before'])}",
                f"- support_in_current_retrieved: {', '.join(case['support_in_current_retrieved'])}",
                f"- new_support_in_current_retrieved: {', '.join(case['new_support_in_current_retrieved'])}",
                f"- question: {case['question']}",
                f"- query: {case['query']}",
                f"- supporting_ids: {', '.join(case['supporting_ids'])}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _csv_value(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
