# Typed hop identity and missing-hint resolver plan

## 1. Objective

- Run line: `typed_hop_identity_hint_resolver_targeted_gate_20260713`.
- Current retry run ID: `layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r16`.
- Selected idea: create topology once, freeze typed hop identities, and treat
  later verifier output as state updates addressed by stable hop IDs. Replace
  free-text-only missing hints with structured requirements resolved against
  the dependency frontier.
- User requirements: solve cross-round hop identity drift and missing-hint to
  frozen-hop mapping; preserve strict topology, parse-failure, candidate, and
  final-answer safety invariants.
- Non-negotiable constraints:
  - do not relax malformed required-hop validation;
  - do not let parse failures, UNKNOWN-like values, ambiguous requirements, or
    topology revisions mutate hop/candidate state;
  - do not use gold answers/decompositions in runtime resolution;
  - preserve legacy verifier and test-double compatibility;
  - do not launch stratified45 before a bounded targeted gate passes.
- Research question: can stable typed hop addressing and deterministic missing
  requirement resolution reduce valid paraphrase drift and unmapped hints
  without increasing unsupported final answers?
- Null hypothesis: explicit hop identity and typed resolution do not improve
  update/hint attachment beyond the surface-key reducer.
- Alternative hypothesis: valid paraphrases update the intended frozen hop,
  structured/legacy hints resolve uniquely at the dependency frontier, and
  unsafe or ambiguous updates remain transition-free.

## 2. Baseline and comparability

- Baseline: semantic-binding stratified45 R12 plus malformed targeted2 R13.
- Dataset/split: no new selection split for implementation; deterministic
  regressions first, then a fixed targeted gate drawn from documented R12
  failures.
- Primary metrics: correct-candidate-rejected recovery, 3/4-hop coverage,
  final answered unsupported rate.
- Structural metrics: `hop_schema_drift_ignored`, resolved/ambiguous/unmapped
  missing requirements, explicit hop-update acceptance/rejection, sentinel and
  malformed candidate transitions.
- Required metric keys: overall accuracy/F1, coverage, selective accuracy/F1,
  average calls, wasted rate, final unsupported rate, per-hop metrics.
- Comparability risk: LLM output is stochastic; deterministic regressions carry
  protocol claims, while real targeted runs carry external-output evidence.

## 3. Code translation plan

| Path | Current role | Planned change | Why | Risk |
| --- | --- | --- | --- | --- |
| `slot_execution_state.py` | canonical reducer | add typed identity/version fields, typed matching, bridge identity propagation, and structured hint resolution | eliminate surface-key addressing | wrong alias merge |
| `slot_binding_verifier.py` | LLM schema/parser | add optional typed hop fields, frozen-state prompt, structured missing requirements, and state-aware entry point | make the model address frozen hops | prompt/schema compliance |
| `semantic_hop_resolver.py` | new | conservative entity/relation/type canonicalization and deterministic resolver | isolate auditable matching logic | ontology overreach |
| `repair_query_compiler.py` | state-derived query | compile from canonical relation, expected type, and resolved hop metadata | retrieve only the missing hop | unnatural canonical query |
| `claim_risk_agent.py` | orchestration | pass round-entry frozen state when supported and log resolver/update diagnostics | activate protocol in real runs | test-double compatibility |
| focused tests | regressions | paraphrase, alias, explicit ID, ambiguity, dependency frontier, malformed/parse/sentinel safety | prevent silent regressions | fixture breadth |

## 4. Execution design

- Minimal experiment: deterministic state/verifier/query tests with no network.
- Smoke/pilot: replay representative two-, three-, and four-hop updates through
  the reducer and run a small real SiliconFlow targeted gate.
- Full run: only after the R16 targeted gate passes, decide whether a uniquely
  named R17 stratified45 is justified.
- Expected outputs: code, focused/full test results, targeted config/run,
  structural diagnostic report, updated checklist.
- R15 targeted acceptance gate:
  - standard `final_answered_unsupported_rate = 0` (no evaluator exception);
  - the three R14 recovered answers remain recovered;
  - Nissan and NBC deterministic complete chains are not rejected by stale
    frozen topology, and at least one 4-hop sample is answered correctly;
  - same-round planning/terminal refresh produces no
    `topology_update_rejected`;
  - structured missing requirements remain JSON objects and hop-ID aliases
    resolve canonically;
  - malformed topology, parse failure, ambiguity, and sentinel values produce
    zero candidate transitions.
- Stop condition: any malformed/parse/sentinel output mutates candidates,
  verified hops regress, ambiguous mapping is guessed, ordinary LLM drift can
  revise topology, or final unsupported becomes non-zero.
- Abandonment condition: typed canonicalization cannot distinguish relation
  direction/type without broad heuristic merging; fall back to explicit-ID-only
  updates and keep unresolved hints conservative.
- Strongest alternative: retain surface topology but improve prompts only. It
  is cheaper, but R12's 146 drift and 104 unmapped events show that prompt-only
  output stability is insufficient.

## 5. Runtime strategy

- Smoke command: focused pytest for resolver, state, verifier, query compiler,
  and claim-risk orchestration.
- Main command: full pytest/compile/diff checks, then a uniquely named
  SiliconFlow targeted run.
- Expected budget: implementation plus local tests and R14 trajectory replay
  first; one fixed eight-sample SiliconFlow retry only after local acceptance.
  No stratified45 budget is consumed in this phase.
- Artifacts: `analysis/`, `configs/`, `runs/`, and durable stdout/stderr logs.
- Efficiency: reuse the existing dense index, fixed corpus, and runner resume.
- Monitoring: 55-second process/row/error checks for real API runs; terminate
  only on explicit failure, invalid output contract, or superseding evidence.

## 6. Fallbacks and recovery

- Endpoint failure: preserve completed keys and resume the same frozen config.
- Code-path failure after smoke: revert only the current typed-protocol delta by
  forward repair; do not reset the dirty worktree.
- Model ignores structured updates: retain deterministic resolver over legacy
  required-hop records and record prompt compliance separately.
- Non-comparable full run: mark partial and do not claim aggregate improvement.

## 7. Checklist link

- `analysis/typed_hop_identity_and_hint_resolver_checklist_20260713.md`
- Next unchecked item: implement the typed canonicalization/resolver module.

## 8. Revision log

| Time | Change | Reason | Impact |
| --- | --- | --- | --- |
| 2026-07-13 | Initial contract | R12 moved bottleneck from topology availability to semantic addressing | no metric/protocol change yet |
| 2026-07-13 | R14 classified partial / gate failed | 3/8 recovered, but same-round fingerprint rejection, structured-requirement stringification, stale frozen topology, target-type leakage, and century verifier desynchronization remain | iterate locally; do not run stratified45 |
| 2026-07-13 | R15 retry contract frozen | restrict topology revision to strict evidence-closed deterministic binders; preserve all existing safety gates | targeted8 remains comparable to R14; new config/run/output paths required |
| 2026-07-13 | R15 partial / gate failed | final unsupported reached zero and Nissan recovered, but four length-truncated slot-verifier responses caused 1952 regression and kept 4-hop coverage at zero | do not scale; retry one variable only |
| 2026-07-13 | R16 targeted retry | raise only slot-binding output budget from 1536 to 2304 tokens | same data/code/metrics; fastest falsification is any remaining `finish_reason=length` |
| 2026-07-13 | R16 blocked before sample 1 | SiliconFlow returned HTTP 403 / code 30001 / insufficient account balance twice; trajectory remains 0 lines | no experiment conclusion; resume identical R16 after external balance recovery |
| 2026-07-14 | R16 retry2 blocked before sample 1 | 1-token probe passed but configured 128-token answer probe and real run returned code 30001; balance is valid but insufficient for the frozen request budget | preserve all logs and resume identical R16 with retry3 only after sufficient top-up |
| 2026-07-14 | R16 completed / structural gate passed / quality gate failed | 29/29 structured attempts stopped normally and safety stayed clean, but `1952` remained abstained and 4-hop stayed 0/3 | keep 2304 tokens fixed; move to R17 targeted semantic-certificate repair, not stratified45 |
| 2026-07-14 | R17 completed / targeted gate failed | output safety remained clean, but 2-hop retained fell to 2/3, `1952` remained abstained, and 4-hop stayed 0/3 | preserve R17; repair state locality, conflict scope, dynamic backfill, and deterministic final binding before one R18 retry |
| 2026-07-14 | R18 completed / one gate remains | accuracy reached 5/8; `1952`, NBC, and East were restored with safety clean, but stale candidate rejection caused `18th` to abstain and 2-hop retention was 2/3 | one minimal R19 candidate-bookkeeping retry; still no stratified45 |
| 2026-07-14 | R19 targeted gate passed | 6/8 correct, 3/3 two-hop, `1952` restored, 2/3 four-hop, zero structural/safety violations | authorize one uniquely named R20 stratified45 with the R19 execution contract |
| 2026-07-14 | R20 stratified45 completed / mixed negative aggregate | five targeted gains and 2/15 four-hop recovery, but seven R12-correct losses and worse accuracy/F1/coverage/cost | stop scaling; iterate on strict-certificate / generic-compatibility fusion using a fixed 12-case gate |

## 9. R15 implementation delta

| Path | Change | Acceptance evidence |
| --- | --- | --- |
| `semantic_hop_resolver.py` | canonicalize `2`, `hop_2`, `required_hop_2`, and `hop_index: 2` to one hop ID | unit tests for requirement and update aliases |
| `slot_binding_verifier.py` | migrate dict items accidentally emitted in legacy `missing_critical_hops` into `missing_requirements`; never stringify them | parser round-trip preserves object |
| `slot_execution_state.py` | validate topology version/fingerprint only across rounds; add strict allowlisted deterministic topology revision | same-round idempotence and NBC/Nissan revision regressions |
| `target_slot_binder.py` | classify the final interrogative slot before bridge-clause cues | NBC `network -> organization`; count remains `count` |
| `claim_risk_agent.py` | when strict century local-evidence acceptance fires, replace the generic final verifier result with an explicitly supported local-evidence result | ordinary final-unsupported evaluator returns zero |

Trusted topology revision is not a general recovery path. It is allowed only
when the binding reason is one of the existing deterministic allowlist entries,
the chain is strictly schema-valid and complete, every hop is bound by local
evidence, the final object equals the bound candidate, all coverage/conflict
gates are clean, and parsing/topology diagnostics are safe. Applying a revision
increments `topology_version`, recomputes the canonical fingerprint, discards
old hop/candidate state, and emits `topology_revision_applied`. Any failed
precondition leaves the frozen state unchanged and emits
`topology_revision_rejected`.

## 10. R17 targeted semantic-certificate repair contract

R17 keeps the R16 dataset, retriever, model, round budget, verifier token
budgets, evaluator, metrics, and safety gates fixed. Its implementation delta
is limited to semantic topology and evidence-certificate binding. It must not
relax chain completeness, typed target binding, final verification, or
unsupported-answer rejection.

### 10.1 Shared-saint relation topology (`1952`)

- Interpret “the same saint” as an equality constraint over two church
  relations, not as an entity edge between two saint names.
- Reject or deterministically repair any topology that asserts
  `Saint X --same_as--> Saint Y` when the normalized saint names differ.
- Build an evidence-closed chain from:
  `question cathedral --dedicated_to--> saint`,
  `basilica for that saint --located_in--> city`, and
  `governor of city --death_year--> year`.
- A wrong-but-supported church branch is a constraint mismatch/distractor, not
  a contradiction of its underlying `dedicated_to` or `located_in` facts.
  Shared evidence IDs may not mark multiple bridge hops conflicted unless the
  contradicted claim semantically scopes to those hop facts.
- Deterministic regression: the R16 Saint Peter/San Feliciano topology must
  contain no `same_as` hop, Foligno facts must not become hard conflicts, and
  the next query must target the matching Saint Peter basilica location.

### 10.2 Typed country identity (`NBC`)

- Maintain distinct identities for city, bay, bay-country, embassy-host
  country (`Country A`), localized program, and network.
- A country-A certificate requires an embassy passage whose mission country
  matches the certified bay-country and whose host country is explicit.
- Before that certificate exists, no concrete localized-program country may
  be guessed and no Philippines-version network query may be emitted.
- After certification, instantiate the program subject from the certified
  `Country A` value and require the program passage to match that same country
  before accepting its creator network.
- Preserve the existing evidence-closed deterministic full-chain revision;
  add a partial typed topology only to address the first unresolved identity
  without inventing an object.

### 10.3 Evidence-to-hop certificates (Arizona and East Coasting)

- Add conservative, passage-derived certificates for:
  feature/work -> state/person, state -> largest city, and city/race -> winner.
- Arizona must bind Poachie Range -> Arizona, Arizona -> Phoenix, and the 1993
  Phoenix Indy relation -> Mario Andretti to their exact hops.
- East Coasting must bind album -> Charles Mingus before origin-state evidence
  can advance the next hop; Charles Mingus -> Arizona, Arizona -> Phoenix, and
  Phoenix -> Mario Andretti remain dependency ordered.
- A failed missing-requirement mapping must report one of
  `hop_binding_subject_mismatch`, `hop_binding_relation_mismatch`, or
  `hop_binding_expected_type_mismatch` when determinable. The generic
  `hop_binding_failure` may remain only as an aggregate fallback.

### 10.4 R17 acceptance and stop conditions

The same fixed targeted8 must simultaneously satisfy:

- `finish_reason=length = 0`;
- actual verifier parse failure and `required_hops_malformed = 0`;
- `final_answered_unsupported_rate = 0`;
- sentinel candidate transition/state count = 0;
- 2-hop accuracy and coverage remain `3/3`;
- `1952` is answered correctly;
- at least one 4-hop sample is answered correctly.

Any safety regression, candidate transition from malformed/parse/sentinel
input, or ordinary model topology drift is an immediate no-go. Only a complete
R17 targeted pass may authorize creation of a later stratified45 run.

## 11. R18 semantic execution repair contract

R18 uses the exact R17 dataset, model, 2304-token slot-verifier budget,
three-round budget, retriever, metric definitions, and safety gates. Only the
implementation fixes diagnosed from the valid R17 trajectory may change.

- For strict deterministic shared-saint and geographic-race certificates,
  evidence locality means the passage is present in the current retrieval
  ledger. Every hop and binding evidence ID must still be a subset of that
  ledger, the deterministic reason and marker must agree, and ordinary LLM
  topology remains subject to sample-ID locality.
- Prefer an exact sample-local duplicate when multiple retrieved passages
  support the same certificate fact. This prevents a cross-sample FC Barcelona
  duplicate from replacing the available local signing passage.
- A text-bearing contradicted claim may conflict a hop only when its subject
  and relation/object semantically scope to that hop. Shared evidence ID alone
  is insufficient. Text-free legacy claims retain their narrow fallback.
- Evidence-driven certificate backfill must run after the primary query even
  when no static extra/backfill query exists.
- Complete deterministic final candidates use `fills_final_slot`, followed by
  the unchanged strict typed validation.

R18 is accepted only if all fixed gates hold simultaneously. A structurally
clean run that misses any answer-quality gate is still a failed gate and does
not authorize stratified45.

## 12. R19 stale-rejection correction contract

R19 changes no experiment setting. The sole semantic state change allows an
old `rejected` candidate to transition to `verified` without new evidence only
when the incoming binding is explicitly and strictly verified: same explicit
candidate, complete chain, all required hops covered, evidence local to the
current reducer certificate, no current typed-reject category, and no
contradiction. A merely repeated observation, support-incomplete record, or
contradicted candidate cannot use this path. The transition clears stale reject
metadata and carries an explicit reason; the next identical round must be
idempotent and emit no transition.

Century ordinal canonicalization additionally removes terminal punctuation
from forms such as `18th.`. This is an equivalence-preserving output cleanup,
not a metric exception. R19 retains every R18 gate unchanged.
