from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mvp_agentic_rag.config import load_simple_config
from mvp_agentic_rag.data_loader import load_corpus, load_samples, read_jsonl
from mvp_agentic_rag.env import load_env_file
from mvp_agentic_rag.slot_binding_verifier import make_slot_binding_verifier
from mvp_agentic_rag.slot_verifier_gate import (
    acceptance_eligible_samples,
    evaluate_slot_verifier_sample,
    summarize_slot_verifier_gate,
    write_slot_verifier_gate_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the slot verifier against fixed gold evidence only.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--required-correct-count", type=int, default=5)
    parser.add_argument("--min-parse-success-rate", type=float, default=0.9)
    args = parser.parse_args()

    load_env_file(ROOT / ".env")
    config = load_simple_config(args.config)
    samples = acceptance_eligible_samples(load_samples(ROOT / str(config["dataset"])))
    corpus = load_corpus(ROOT / str(config["corpus"]))
    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "slot_verifier_gate_records.jsonl"
    records = list(read_jsonl(records_path)) if records_path.exists() else []
    completed_ids = {str(record.get("id") or "") for record in records}
    verifier = make_slot_binding_verifier(config)

    for sample in samples:
        if sample.sample_id in completed_ids:
            continue
        missing_ids = [passage_id for passage_id in sample.supporting_passage_ids if passage_id not in corpus]
        if missing_ids:
            raise ValueError(f"Missing gold evidence for {sample.sample_id}: {missing_ids}")
        evidence = [corpus[passage_id] for passage_id in sample.supporting_passage_ids]
        record = evaluate_slot_verifier_sample(sample, evidence, verifier)
        with records_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        records.append(record)
        print(
            f"completed={len(records)}/{len(samples)} id={sample.sample_id} "
            f"parse={record['parse_status']} candidate_match={record['candidate_match']}",
            flush=True,
        )

    records_by_id = {str(record.get("id") or ""): record for record in records}
    ordered_records = [records_by_id[sample.sample_id] for sample in samples if sample.sample_id in records_by_id]
    summary = summarize_slot_verifier_gate(
        ordered_records,
        required_correct_count=args.required_correct_count,
        min_parse_success_rate=args.min_parse_success_rate,
    )
    summary.update(
        {
            "config": str(Path(args.config).as_posix()),
            "dataset": str(config["dataset"]),
            "corpus": str(config["corpus"]),
        }
    )
    paths = write_slot_verifier_gate_report(output_dir, summary)
    print(f"verdict={'GO' if summary['passed'] else 'NO-GO'}", flush=True)
    print(f"summary_json={paths['json']}", flush=True)
    print(f"summary_markdown={paths['markdown']}", flush=True)
    return 0 if summary["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
