# Evidence-DAG Next Experiment Campaign V2.3

## 1. Objective

- campaign id: `evidence-dag-next-protocol-v2-3`
- parent run: `evidence-dag-planner-diagnostic-protocol-v1` (`a7842f3`)
- main claim under test: the previous 7B Planner failure must be decomposed into Decoder/Schema, Holdout feasibility, Span generation, graph matching, and downstream component effects before any new Planner route or Confirmation run is trusted.
- user's core requirement: execute the V2.3 plan within its safety gates and produce a result report.
- campaign outcome needed: machine-verifiable safe-stage evidence, an explicit Preflight decision, and only then any allowed downstream slices.
- selected outline ref: not paper-facing; none required.
- paper experiment matrix path: not applicable.
- current execution frontier: `G0`, `P0A`, split `P0B`, `P0C`, `P2A`, and `E0` only until V2.3 machine validation passes.

## 2. Boundary And Comparability

- baseline comparison contract: V1 Diagnostic-60/Smoke-6 artifacts committed at `4a9a3bd`; Confirmation-120 remains untouched.
- fixed conditions: SiliconFlow API, `Pro/Qwen/Qwen2.5-7B-Instruct` unless a slice explicitly compares standard/Pro, temperature 0, strict raw logging, no malformed JSON repair, same parser/validator contracts.
- variables that may change: response mode/backend in P0, schema family in P0B, holdout independence level in G0, candidate generation method in P2A.
- non-comparable slices: standard vs Pro is a system-level Endpoint comparison; TF-IDF and BGE retrieval are not interchangeable; Oracle inputs are diagnostic only.
- Gold policy: Gold may be used only in explicitly Oracle/fixture slices and never enter production Planner or automatic span generation.
- runtime deviation: the skill-required `bash_exec`, artifact, and memory interfaces are unavailable; SSH sessions, repository-local files, JSONL evidence, and Git commits are the compatibility path.

## 3. Slice Plan

| Exp id | Slice id | Tier | Slice class | Type | Research question | Success / decision value | Priority | Code change? | Extra baseline? |
|---|---|---|---|---|---|---|---:|---|---|
| G0 | `g0_holdout_feasibility` | main_required | claim-carrying | boundary | Can two 36-item internal holdouts be built at Strict, Compositional, or Lexical independence? | exact level and overlap ledger; A/B frozen only if feasible | 1 | yes | no |
| P0A | `p0a_minimal_decoder` | main_required | claim-carrying | robustness | Can the endpoint exactly emit fixed minimal payloads in text/JSON/schema modes? | 72/72 exact, stop, no length/repetition per mode | 2 | yes | standard/Pro optional P0C |
| P0B | `p0b_schema_envelope` | main_required | claim-carrying | ablation | Which real schema families fail independently of semantic planning? | canonical JSON and semantic match per Topology/Hop/Shape/Slot/Query/Validator | 3 | yes | no |
| P0C | `p0c_backend_isolation` | main_required | claim-carrying | environment | Is failure specific to response backend or Endpoint? | matched payload/prompt across backend/Endpoint | 4 | yes | standard endpoint |
| P2A | `p2a_span_candidates` | main_required | supporting | error analysis | Can automatic NER/NP/rules cover Gold and non-NER input spans without reading Gold? | normalized and alias-resolved recall; hard-negative audit | 5 | yes | no |
| E0 | `e0_fixture_properties` | main_required | auxiliary | robustness | Do Oracle engine, graph matcher, schemas, and invariants hold under fixtures/property tests? | all deterministic tests and schema validation pass | 6 | yes | no |
| MV | `machine_validation` | main_required | claim-carrying | boundary | Can manifests/freeze locks/raw/metrics be validated and unsafe runs rejected? | all positive fixtures pass; every required negative case is rejected | 7 | yes | no |
| P1+ | `post_preflight_routes` | conditional | claim-carrying | follow-up | Which Route A/B/C and downstream ladder slices remain executable? | only launched after clean Preflight and explicit frozen configs | 8 | likely | strong model may be blocked |

## 4. Highlight Hypotheses

- H-Decoder: if P0A/P0B fail on fixed canonical payloads, semantic Planner experiments are not interpretable.
- H-Holdout: Strict independence is likely infeasible for scarce MuSiQue topologies; Compositional may be the strongest honest level.
- H-Span: deterministic span candidates may achieve high entity recall but expose a non-NER phrase boundary.
- H-MachineGate: dirty trees, hash mismatches, Gold-policy conflicts, reused holdouts, budget mismatches, and unresolved placeholders must be rejected before P1+.

## 5. Assets And Dependencies

- available: Diagnostic-60, frozen Confirmation-120, Smoke-6, 3,720-passage corpus, Gold decompositions, V1 raw evidence, graph matcher primitives, API credential, standard/Pro endpoints.
- missing or restricted: exact strong 32B comparator, disclosed guided-decoding backend/revision, independent human review, managed `bash_exec`/artifact/memory services.
- fallback: record blocked strong-model or backend-specific claims; never substitute a different model silently.

## 6. Execution Strategy

- first checkpoint: G0 + machine schema/preflight fixtures, before any model calls.
- P0 smoke: one payload per mode/schema before 72-run slices.
- long-run policy: append-only raw JSONL, compound resume keys, explicit finish/token/latency logging, isolated output folder per slice.
- post-Preflight policy: revise this plan and checklist before launching any P1+ slice.
- abandonment: if P0A cannot meet the fixed-payload gate across backends, stop semantic route promotion and report Decoder/Backend boundary first.

Monitoring plan:

- compatibility cadence: 60s, 120s, 300s, 600s, then 1800s for remote detached/long SSH sessions.
- healthy signals: growing JSONL, progress records, recent file modification, nonzero CPU/network, valid finish metadata.
- redesign/kill triggers: no durable progress beyond the bounded cadence, invalid schema contract, leaked Gold, dirty-tree freeze attempt, or repeated transport failure.

## 7. Reporting Plan

- stable support: preregistered gates met on all planned denominators, with raw evidence and machine validation.
- contradiction: fixed canonical payload or invariants fail reproducibly.
- unresolved ambiguity: provider backend/model revision unavailable, comparator absent, or conditional metrics too sparse.
- final report: lead with G0/P0/MachineGate decisions, then P2A/E0, then any conditionally executed P1+ slices; include skipped/blocked items.

## 8. Checklist Link

- checklist: `analysis/evidence_dag_next_protocol_v2_3/CHECKLIST.md`
- next unchecked item: create and validate campaign-control files in the isolated worktree.

## 9. Revision Log

| Time | Change | Reason | Impact |
|---|---|---|---|
| 2026-07-18 | Initial safe-stage frontier frozen | V2.3 section 18 forbids P1–P5 before machine validation | G0/P0/P2A/E0 first; downstream conditional |
| 2026-07-18 | Post-Preflight frontier opened for independent P1 only | P0A/P0B/P0C and clean-tree Machine Validation passed; P2A recall gate failed | Launch Route A, Route B C1/C2O/C2P, and Oracle Pairwise C4A on Diagnostic-Dev-60; keep P2B/P2C automatic-span routes stopped |
| 2026-07-18 | P1 routes stopped; bounded P4 Oracle Retriever branch opened | Route A 0/60, C2P 7/60, C4A exact 1/60; dense retriever assets and prior baseline are available | Run only Gold×Gold BGE Recall@10/All-Steps gate; do not run Query factorial, production rollout, Holdout, or Confirmation |
| 2026-07-18 | P4 corpus/index contract repaired before one final rerun | First run used an old 6,000-passage index containing only 11/200 Diagnostic targets, so 9/200 Recall was invalid | Rebuild the same BGE encoder index on the frozen 3,720-passage Diagnostic corpus; require 200/200 target coverage before rerun |

## 10. Post-Preflight P1 Freeze Intent

- dataset: `Diagnostic-Dev-60` only; neither Internal-Holdout-A/B nor Confirmation-120 may be queried.
- model/backend: `Pro/Qwen/Qwen2.5-7B-Instruct` through SiliconFlow; provider `json_schema`; temperature 0; strict no-repair parsing.
- Route A: 60 direct-topology calls.
- Route B C1: 60 hop-count calls.
- Route B C2O: no call for 2-hop; one Gold-hop-conditioned shape call for each 3/4-hop item (50 calls).
- Route B C2P: reuse each C1 prediction; no call when predicted hop is 2, otherwise at most one shape call; at most 60 calls.
- C4A Oracle Pairwise: one unordered-pair relation call using Gold decomposition; 250 calls total.
- per-question deployment budget for Route A/B remains at most 1/2 Planner calls; C4A is explicitly Oracle diagnostic and not a deployment candidate.
- report full planned denominators, invalid/transport failure as failures, majority baselines, topology collapse/entropy, per-hop recall, end-to-end topology metrics, pair relation accuracy, edge F1, exact graph recovery, and global consistency.
- abandonment: do not promote an automatic span/slot route while P2A remains below 98%; do not query a strong-model substitute; do not open Internal Holdout or Confirmation from Diagnostic results.

## 11. P4 Retriever Oracle Freeze Intent

- target retriever: `dense` FAISS index rebuilt with the same local `BAAI/bge-base-en-v1.5` snapshot on the exact Diagnostic corpus, CUDA, no reranker, `top_k=10`.
- dataset: Diagnostic-Dev-60 only; 200 Gold decomposition steps.
- corpus: frozen `data/evidence_dag_planner_protocol_v1/retrieval_corpus.jsonl` (3,720 passages); the index metadata must contain all 3,720 IDs and all 200 Gold targets.
- query: Gold step question with only prior Gold bindings substituted; no Gold passage text enters the query.
- primary gates: step Recall@10 >=75%; All-Steps Recall >=60%; timeouts exactly 0.
- Merge Joint Recall: descriptive Dev freeze using all direct merge parents plus the merge step.
- this slice is independent component isolation, not evidence that any failed Planner route is deployable.
- abandon all remaining query-factorial and P5 model slices if no prerequisite production relation/binding candidate or exact strong model exists after this gate.
