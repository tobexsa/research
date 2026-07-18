# Public Export Notice

This directory is the GitHub-safe export of the Evidence-DAG V2.3 experiment package.

The complete local audit package contains 90 files. Six G0 files are intentionally excluded from this public export because they disclose reserved Internal-Holdout samples, their source corpus, or identifiers and overlap examples that could help reconstruct the reservation. Publishing those files would invalidate the campaign's untouched one-shot holdout boundary.

Excluded from GitHub:

- `g0_holdout_feasibility/internal_holdout_a.jsonl`
- `g0_holdout_feasibility/internal_holdout_b.jsonl`
- `g0_holdout_feasibility/internal_holdout_corpus.jsonl`
- `g0_holdout_feasibility/holdout_reservation.json`
- `g0_holdout_feasibility/holdout_overlap_ledger.csv`
- `g0_holdout_feasibility/ambiguous_candidates.jsonl`

The aggregate, non-identifying feasibility result remains available in `g0_holdout_feasibility/holdout_feasibility_report.md`. Confirmation-120 was never queried by a model and no Confirmation sample content is included in this export.

The complete restricted package remains only in the authorized local workspace at `D:\research\artifacts\evidence_dag_next_protocol_v2_3` and on the experiment server. It must not be published before the holdout policy is explicitly retired.

All other copied artifacts are byte-for-byte copies of the finalized local package. The export contains no API key or authorization token.
