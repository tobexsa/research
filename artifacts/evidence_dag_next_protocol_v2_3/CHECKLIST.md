# Evidence-DAG Next Experiment V2.3 Checklist

## Identity

- campaign: `evidence-dag-next-protocol-v2-3`
- parent: `evidence-dag-planner-diagnostic-protocol-v1` / `a7842f3`

## Launch

- [x] V2.3 protocol read completely.
- [x] Claim, safety frontier, comparability boundary, and parent evidence identified.
- [x] Isolated branch/worktree created.
- [x] `PLAN.md`, `CHECKLIST.md`, and compatibility deviation documented.
- [x] Campaign files committed before real API slices (`40b56c1`, infrastructure at `b6a244f`).

## G0 Holdout Feasibility

- [x] Audit Sample ID, complete decomposition, base subquestion, normalized near-duplicate, answer entity, source passage, and topology availability.
- [x] Determine Strict/Compositional/Lexical feasibility separately (Strict bounded search failed; Compositional and Lexical passed).
- [x] Reserve Internal-Holdout-A and B at the strongest feasible `Compositional` level (36 each; 6 per topology).
- [x] Produce `holdout_feasibility_report.md` and `holdout_overlap_ledger.csv`.
- [x] Keep Confirmation-120 untouched (`confirmation_touched_by_model=false`).

## Machine Validation

- [x] Implement `manifest.schema.json`.
- [x] Implement `freeze_lock.schema.json`.
- [x] Implement `raw_record.schema.json`.
- [x] Implement `metrics.schema.json`.
- [x] Implement `validate_experiment_preflight.py`.
- [x] Reject placeholders, required nulls, hash mismatch, dirty tree, holdout reuse, budget mismatch, Gold-policy conflict, unfair comparison, and schema/version mismatch.
- [x] Positive and negative fixtures pass (16 focused tests passed before safe-stage runs).

## P0 Decoder Envelope

- [x] P0A one-call smoke for Plain Text / Plain JSON / Provider JSON Schema.
- [x] P0A 72 calls per mode, 216 total: 216/216 exact and stop; 0 length; 0 repetition.
- [x] P0B Topology canonical payload (72/72 canonical and semantic).
- [x] P0B Hop canonical payload (72/72 canonical and semantic).
- [x] P0B Shape canonical payload (72/72 canonical and semantic).
- [x] P0B Slot canonical payload (72/72 canonical and semantic).
- [x] P0B Query canonical payload (0/72 byte exact; 72/72 canonical and semantic).
- [x] P0B Validator canonical payload (72/72 canonical and semantic).
- [x] Byte Exact, Canonical JSON, and Schema Semantic Match reported separately.
- [x] P0C matched standard Endpoint isolation executed: 216/216 exact and stop; 0 length; 0 repetition.

## P2A Span Candidates

- [x] Gold acceptable spans, normalized values, alias sets, and hard negatives represented without leaking into automatic generation.
- [x] Automatic NER + NP chunking + rule generator implemented.
- [x] Normalized, alias-resolved, and non-NER phrase recall reported with full denominators.
- [x] Gate decision recorded: failed at 68/90 normalized and alias-resolved recall (75.56%; required 98%).

## E0 / Canonical Matcher

- [x] CanonicalGraphMatcher supports root-order invariance, node rename, merge-parent order invariance, identity removal, and alternative DAGs across all six topologies.
- [x] Reject missing relation semantics, extra non-identity step, wrong source/output type, wrong merge, and invalid answer sink.
- [x] E0 matcher/invariant/property fixtures pass (28 focused tests; 823 full-suite tests).

## Conditional P1+

- [x] Preflight passes on clean committed tree `d401ff7` before P1+ consideration.
- [x] Plan revised with exact P1 candidate configs and budgets before P1+.
- [x] Route A, C1/C2O/C2P, and Oracle C4A executed on Diagnostic-Dev-60; no failed route was promoted.
- [x] P2B/P2C automatic-span promotion stopped after P2A failed; Query factorial, Validator, Holdout, and Confirmation remain prerequisite-gated.
- [x] Strong model is never substituted silently; P3 remains blocked because no exact comparator is frozen.
- [x] P4 Gold×Gold Retriever Oracle Gate rerun on contract-matched 3,720-passage BGE index: Recall@10 182/200, All-Steps 44/60, timeout 0; gate passed.
- [x] Invalid P4 corpus/index run retained and excluded after audit showed only 11/200 Gold targets were indexable.
- [x] P5 R0 zero-LLM Oracle attribution completed: 182/200 resolved steps, 178/200 support recall, 50/60 Answer Ready/EM, 0 cross-hypothesis mix.
- [x] P5 R1/X0/X1/X2/V0/V1 marked blocked/skipped: production relation/binding/query prerequisites failed and no exact strong validator was authorized.

## Aggregation And Closeout

- [x] Every executed slice has raw evidence, metrics, and an explicit status; blocked/skipped slices are recorded without fabricated run artifacts.
- [x] Stable support / partial support / contradiction / ambiguity separated.
- [x] Chinese aggregate report generated.
- [x] Required artifacts copied to local workspace (`D:\research\artifacts\evidence_dag_next_protocol_v2_3`; 90 files; JSON/JSONL parse and manifest-path checks passed).
- [x] Focused and full regressions pass (34/34 focused during final slices; 829/829 full).
- [x] Remote branch committed and clean after report commit `081deeb`; final closure delta is documentation-only.
- [x] Next route recorded explicitly in `final_decision.md` and `resume_packet.md`.
