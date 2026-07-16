# Typed hop identity and missing-hint resolver checklist

## Identity

- Run ID: `typed_hop_identity_hint_resolver_targeted_gate_20260713`
- Stage: implementation and targeted experiment

## Planning

- [x] Selected idea and ordering recorded.
- [x] R12/R13 baseline and comparability confirmed.
- [x] Code touchpoints and risks listed.
- [x] Smoke, targeted, fallback, and stop conditions written.

## Implementation

- [x] Add conservative entity/relation/type canonicalization.
- [x] Add stable typed fields and topology identity to state records.
- [x] Interpret later records as updates to frozen hop IDs.
- [x] Add structured missing requirements and dependency-frontier resolver.
- [x] Pass frozen state into the real verifier when supported.
- [x] Compile repair queries from resolved typed hops.
- [x] Add trajectory diagnostics for update/resolution decisions.
- [x] Preserve legacy verifier/test-double behavior.

## Pilot / smoke

- [x] Add and pass focused deterministic regressions.
- [x] Pass the final full local suite, compileall, and diff checks.
- [x] Replay representative deep-chain updates without unsafe transitions.
- [x] Confirm metric/evaluator definitions remain unchanged.

## Main targeted gate

- [x] Freeze a unique targeted dataset/config/output path.
- [x] Launch and monitor the real SiliconFlow run.

Execution note: targeted8 R14 started with PID `9644`; stdout/stderr use the
matching unique files under `runs/logs/` and the frozen output directory is
`runs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r14`.
- [x] Validate R14 structural and final-safety gates.
- [x] Classify R14 as partial / gate failed / iterate.

R14 result: correct `3/8` versus matched R12 `1/8`, but standard final
unsupported was non-zero, same-round topology refreshes were rejected, and
trusted complete NBC/Nissan chains could not replace incorrect first-round
decompositions. R14 does not authorize stratified45.

## R15 repair pass

- [x] Ignore model topology version/fingerprint only for same-round idempotent refresh.
- [x] Preserve structured requirements emitted under legacy `missing_critical_hops`.
- [x] Canonicalize hop-ID aliases across parser, resolver, updates, and repair targets.
- [x] Add strict evidence-closed deterministic topology revision.
- [x] Fix final-interrogative target-type classification.
- [x] Synchronize century local-evidence acceptance with a supported final verifier record.
- [x] Add Nissan partial model topology and exact single-hop query regression.
- [x] Pass focused deterministic regressions.
- [x] Pass the full suite (`597 passed, 27 subtests passed`), compileall, and diff check.
- [x] Replay R14 trajectories and validate structural deltas.
- [x] Freeze and run unique R15 targeted8 config/output/log paths.
- [x] Validate R15: partial / gate failed; final unsupported fixed, 4-hop gate not met.

## R16 length-truncation retry

- [x] Attribute every R15 parse failure to primary and repair `finish_reason=length`.
- [x] Freeze a unique R16 targeted8 config with only max output tokens changed 1536 -> 2304.
- [x] Run R16 to 8/8 with durable stdout/stderr. The valid retry7 execution completed in 1036.1 seconds with exit code zero, eight trajectory rows, and zero-byte stderr.
- [x] Confirm `finish_reason=length = 0` and final unsupported remains zero: 29/29 structured attempts ended with `stop`; parse failure, malformed topology, and topology-update rejection are also zero.
- [x] Confirm Nissan and the two other 2-hop recoveries remain correct: 3/3 2-hop accuracy and coverage.
- [ ] Confirm `1952` is restored and at least one 4-hop sample is correct. **Failed:** `1952` still abstains and 4-hop remains 0/3.
- [x] Decide whether R17 stratified45 is authorized. **Not authorized:** the R16 structural token gate passed, but the targeted quality gate failed.

Recovery record: preserve the initial through retry6 failure/empty logs. They
document insufficient balance, Windows process-host failures, and a sandbox
network denial before any sample was written. Retry7 is the sole valid R16
network execution and produced the canonical eight rows and metrics. No failed
log was overwritten.

## Closeout

- [x] Write the R15 result and limitation report.
- [x] Write the R16 result and decide explicitly whether to iterate or launch uniquely named R17 stratified45: iterate on semantic binding; do not scale.

## R17 semantic-certificate targeted8

- [x] Freeze the implementation and acceptance contract in the plan; keep all R16 model/data/token/metric settings fixed.
- [x] Replace different-saint `same_as` topology with an evidence-closed shared-saint constraint chain.
- [x] Prevent wrong but supported Foligno facts from becoming hard hop conflicts through unscoped contradiction evidence.
- [x] Add deterministic R16 Saint Peter/San Feliciano regression.
- [x] Add partial and complete typed NBC country-identity certificates with dynamic Country-A program identity.
- [x] Add deterministic NBC cross-round identity/query regressions.
- [x] Add Arizona and East Coasting evidence-to-hop certificate binding.
- [x] Split binding diagnostics into subject, relation, and expected-type mismatches.
- [x] Pass focused semantic/state/verifier/query tests (`241 passed, 27 subtests passed`).
- [x] Pass the full suite (`603 passed, 27 subtests passed`), compileall, and scoped diff check.
- [x] Freeze a unique R17 targeted8 config/output/stdout/stderr; R16 execution settings are unchanged.
- [x] Run R17 targeted8 and validate every structural, safety, 2-hop, `1952`, and 4-hop gate. **Failed:** structural/safety gates passed, but 2-hop retained was 2/3, `1952` abstained, and 4-hop remained 0/3.
- [x] Authorize stratified45 only if every R17 targeted gate passes. **Not authorized.**

## R18 semantic execution repair

- [x] Make complete shared-saint/geographic certificates use explicit `fills_final_slot` candidate roles.
- [x] Allow only strict allowlisted certificates to bind currently retrieved cross-sample duplicate passages into state.
- [x] Prefer exact sample-local evidence when an equivalent duplicate is also retrieved.
- [x] Scope text-bearing contradiction claims to the semantic hop fact before applying conflict.
- [x] Run East evidence-driven certificate backfill even when static extra queries are empty.
- [x] Add the deterministic named-after player signing-date certificate for `June 1982`.
- [x] Add regressions for NBC conflict attribution, certificate locality, East no-extra backfill, and local duplicate selection.
- [x] Pass focused tests (`264 passed, 27 subtests passed`) and final full suite (`607 passed, 27 subtests passed`), compileall, and scoped diff check.
- [x] Replay R17 trajectories: June and 1952 reach `await_final_gates`; Arizona applies its trusted complete topology; NBC does not hard-conflict hop 1; East advances through Charles Mingus -> Arizona before the new dynamic backfill.
- [x] Freeze a unique R18 config/output/stdout/stderr with all R17 execution settings unchanged.
- [x] Run R18 targeted8 and validate every gate. **Failed narrowly:** 5/8 accuracy, `1952` restored, NBC and East 4-hop correct, all safety/structure gates clean, but 2-hop retained was 2/3 because `18th` abstained.
- [x] Create/run stratified45 only if R18 passes every gate simultaneously. **Not authorized because 2-hop retention failed.**

## R19 stale-rejection correction

- [x] Identify R18's sole gate blocker as a strict same-evidence semantic correction being unable to clear an old role rejection.
- [x] Allow only `rejected -> verified` strict explicit clean binding to recover without new evidence; contradictions still require new clean evidence.
- [x] Clear stale typed-reject metadata and emit `strict_binding_clears_stale_rejection`.
- [x] Verify the next identical round emits no candidate transition.
- [x] Normalize terminal punctuation for century ordinals such as `18th.`.
- [x] Replay R18 `18th`: round 2 candidate becomes verified and state reaches `await_final_gates`.
- [x] Pass focused tests (`258 passed, 27 subtests passed`) and full suite (`608 passed, 27 subtests passed`), compileall, and scoped diff check.
- [x] Freeze and run a unique R19 config with only run/output names changed from R18.
- [x] Authorize stratified45 only if every fixed gate passes. **Authorized:** every R19 gate passed; decision recorded separately.

## R20 stratified45 generalization

- [x] Record the explicit go decision and comparison contract.
- [x] Freeze a unique R20 stratified45 config derived from R19; only dataset/run/output changed.
- [x] Confirm the 45-row dataset and unique output/log paths.
- [x] Launch and monitor 45/45 with durable logs; completed naturally with zero-byte stderr.
- [x] Validate metrics, per-hop results, structure/safety diagnostics, and deltas versus R12.
- [x] Record the final decision after R20: `iterate`, do not scale the current globally strict package.

## R20 failure-analysis slice

- [x] Compare gained/lost normalized-correct samples against R12.
- [x] Compare 2/3/4-hop coverage and correctness.
- [x] Audit length/parse/malformed, sentinel, topology rejection, and final unsupported.
- [x] Attribute coverage loss to 99 dependency-incomplete, 11 subject-mismatch, and 14 expected-type-mismatch events plus later final-verifier arbitration.
- [x] Define a strict-certificate / generic-compatibility fusion direction.
- [ ] Build the fixed 12-case gain/loss dataset and implementation plan before further code changes.
