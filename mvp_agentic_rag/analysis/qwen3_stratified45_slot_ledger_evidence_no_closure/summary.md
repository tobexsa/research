# Qwen3 Stratified45 Slot Ledger Evidence-Binding + No-Closure Pilot

## Headline

- This run tests the narrow follow-up after the permissive and strict explicit slot-ledger pilots.
- It keeps explicit slot-ledger final-answer generation enabled, switches final-slot binding to `claim_evidence_slot_binding_policy: evidence`, and disables closure answers under slot-ledger mode with `claim_evidence_slot_ledger_disable_closure: true`.
- The result is safer on closure but too conservative: overall `answer_f1=0.2082`, below guarded baseline, soft binding, permissive slot ledger, and strict-binding slot ledger.

## Run

- Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_evidence_no_closure_no_think.yaml`
- Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_evidence_no_closure_no_think`
- Dataset: `data/musique_mvp_stratified45.jsonl`
- Model endpoint: `http://172.18.8.31:8091/v1`
- Model: `qwen3-14B-int4`

## Overall Metrics

| run | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | cost_normalized_f1 | zero-F1 answered | closure_success | contamination | decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| guarded closure + cost cleanup | 0.2634 | 0.4667 | 0.5645 | 2.1111 | 0.1248 | 7 | 7 | 1 verifier non-JSON after repair | reference baseline |
| soft final-target binding | 0.2812 | 0.5111 | 0.5502 | 1.9778 | 0.1422 | 8 | 6 | clean | best previous prompt-only gate |
| permissive explicit slot ledger | 0.3220 | 0.6000 | 0.5366 | 1.8667 | 0.1725 | 9 | 12 | clean | numerically promising but unsafe |
| strict-binding explicit slot ledger | 0.2442 | 0.4444 | 0.5494 | 1.7556 | 0.1391 | 6 | 7 | clean | safer but below F1 gate |
| evidence-binding + no closure | 0.2082 | 0.2889 | 0.7207 | 1.8000 | 0.1157 | 2 | 0 | clean | too conservative; do not promote |

## Per-Hop Metrics

| hop | n | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | slot_answer | slot_missing | slot_next_query | final_target_bound | closure_success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2-hop | 15 | 0.4533 | 0.6667 | 0.6800 | 1.4000 | 10 | 2 | 6 | 10 | 0 |
| 3-hop | 15 | 0.1713 | 0.2000 | 0.8564 | 1.9333 | 3 | 2 | 14 | 3 | 0 |
| 4-hop | 15 | 0.0000 | 0.0000 | 0.0000 | 2.0667 | 0 | 3 | 15 | 0 | 0 |
| all | 45 | 0.2082 | 0.2889 | 0.7207 | 1.8000 | 13 | 7 | 35 | 13 | 0 |

## Zero-F1 Answered Cases

| id | hop | answer | gold | slot_answer | closure_success | failure mode |
| --- | --- | --- | --- | ---: | ---: | --- |
| `2hop__131951_643670` | 2-hop | Nieuwe Maas River | Het Scheur | 1 | 0 | verifier supported a wrong final-target passage; final slot then generated from the wrong evidence |
| `2hop__247353_55227` | 2-hop | Salma Hayek | Maria Bello | 1 | 0 | verifier first marked the wrong answer unsupported, but the ledger still accumulated the claim; second-round verification then marked the same wrong target supported |

## Largest Regressions vs Permissive Slot Ledger

| id | hop | delta_f1 | permissive result | evidence/no-closure result | gold | main reason |
| --- | --- | ---: | --- | --- | --- | --- |
| `2hop__167577_31122` | 2-hop | -1.000 | answer `18th` | abstain | 18th | correct final value was blocked because verifier reported `final_target_match=false` / `answer_slot=date component` |
| `3hop1__136129_87694_124169` | 3-hop | -1.000 | answer `1952` | abstain | 1952 | supported final-value claim existed, but `final_target_match=false` vetoed final slot binding |
| `3hop1__140786_2053_5289` | 3-hop | -1.000 | answer `Oriole Records` | abstain | Oriole Records | final target was not bound because verifier labeled the answer slot unknown and target match false |
| `4hop1__161810_583746_457883_650651` | 4-hop | -1.000 | answer `NBC` | abstain | NBC | permissive answer was not slot-derived; no final slot was bound under evidence policy |
| `4hop1__161605_32392_823060_610794` | 4-hop | -0.500 | answer `Charleston County` | abstain | Richland County | conservative policy removed a partial but still wrong answer |
| `2hop__153573_44085` | 2-hop | -0.333 | answer `Metal Mickey` | abstain | The Mickey Mouse Club | conservative policy removed a partial but still wrong answer |
| `3hop1__103751_24918_24991` | 3-hop | -0.286 | answer `Dissolution of the Soviet Union` | abstain | Soviet flag | conservative policy removed a partial but still wrong answer |

## Interpretation

- Closure suppression worked as intended. `closure_success=0`, and the contamination scan found no `<think>`, invalid JSON, or non-JSON repair failures.
- The evidence-binding policy is too conservative because it still treats verifier `final_target_match=false` as a hard veto. The largest lost exact-answer cases are not retrieval failures; the retrieved and supported claims contain the final values, but the verifier labels them as `date component`, `unknown`, or intermediate.
- The local-evidence prefix rule is not the main bottleneck in this run. The visible regressions are dominated by verifier target-match vetoes and by final-slot binding requiring a claim that looks final under the current lexical type heuristic.
- The high `selective_answer_f1=0.7207` is not enough to promote the variant because coverage collapses to `0.2889`; 4-hop coverage is `0.0000`.
- The remaining unsafe answers show that a supported verifier claim is still not a sufficient final-slot binding signal. Wrong evidence can still be certified as the final target and then used by slot answer generation.

## Decision

- Do not run full300 from this evidence-binding + no-closure variant.
- Keep the explicit slot-ledger architecture, but do not keep `final_target_match=false` as a hard evidence-policy veto.
- The next useful implementation should separate two checks:
  1. final-value extraction from cited evidence using target type and question slot text;
  2. verifier sufficiency over a completed named slot ledger.
- Also prevent unsupported claims from entering any final slot before a later verifier pass can flip them to supported. The `2hop__247353_55227` case shows stale wrong-slot claims can survive across rounds.

## Follow-Up: Date Override and Chain Locality

Two narrow follow-ups were tested after the initial evidence-binding + no-closure result:

1. `date_override_no_closure`
   - Code change: snapshot `SlotLedger.to_record()` lists, classify `what century` as `century`, and allow date/year/century final-value claims to bypass `final_target_match=false` when the verifier labels them as `date component`.
   - Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_date_override_no_closure_no_think.yaml`
   - Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_date_override_no_closure_no_think`
   - Result: unchanged from evidence-binding + no-closure: `answer_f1=0.2082`, `coverage=0.2889`, `cost_normalized_f1=0.1157`, `closure_success=0`.
   - Interpretation: the intended recovery did not happen because `2hop__167577_31122` still has the `18th century` claim marked `unsupported`; it never becomes eligible for slot binding.

2. `chain_locality_no_closure`
   - Code change: keep date override and relax evidence locality only for MuSiQue sibling sample ids that share the same hop prefix and at least two decomposition ids in the suffix, for example `3hop1__64957_87694_124169::p1` relative to `3hop1__136129_87694_124169`.
   - Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_chain_locality_no_closure_no_think.yaml`
   - Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_chain_locality_no_closure_no_think`
   - Result: `answer_f1=0.2304`, `coverage=0.3111`, `selective_answer_f1=0.7407`, `avg_retrieval_calls=1.8222`, `cost_normalized_f1=0.1265`, `closure_success=0`, contamination clean.
   - Interpretation: this recovered exactly one important case, `3hop1__136129_87694_124169`, from abstain to correct `1952`. It confirms that strict sample-prefix locality was too narrow for MuSiQue sibling evidence, but the gain is still not enough to beat guarded baseline.

Follow-up per-hop metrics:

| run | 2-hop F1 | 3-hop F1 | 4-hop F1 | coverage | zero-F1 answered | closure_success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| evidence-binding + no closure | 0.4533 | 0.1713 | 0.0000 | 0.2889 | 2 | 0 |
| date override + no closure | 0.4533 | 0.1713 | 0.0000 | 0.2889 | 2 | 0 |
| chain locality + no closure | 0.4533 | 0.2379 | 0.0000 | 0.3111 | 2 | 0 |

Follow-up conclusion:

- `chain_locality_no_closure` is the best safe evidence-binding variant so far, but it still misses the stratified45 gate: `answer_f1=0.2304 < 0.2634` guarded baseline and `0.2304 < 0.2812` soft binding.
- Closure safety is now clean across the no-closure variants, but 4-hop remains completely unanswered under evidence binding.
- The next bottleneck is not locality alone. It is final-slot completion from retrieved evidence when verifier claim status is `unsupported` or `unclear`, plus safe handling of entity/location final targets without reopening the permissive wrong-target failure mode.

## Follow-Up: Direct Final-Slot Completion

Two direct-completion variants were tested after `chain_locality_no_closure`.

1. `direct_completion_no_closure`
   - Code change: when verifier claim status is too conservative and no final slot is bound, scan retrieved local evidence directly for structured final values. This is restricted to `date`, `year`, `century`, `count`, `population`, and `number`; entity/person/location/company/network targets are not completed directly. Closure remains disabled under slot-ledger mode, and slot-derived answers are still verified before final answer acceptance.
   - Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_direct_completion_no_closure_no_think.yaml`
   - Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_direct_completion_no_closure_no_think`
   - Result: `answer_f1=0.2304`, `coverage=0.3111`, `selective_answer_f1=0.7407`, `avg_retrieval_calls=1.9333`, `cost_normalized_f1=0.1192`, `closure_success=0`, contamination clean.
   - Interpretation: safety was preserved because the final verifier rejected wrong completions, but the extractor was too broad. It triggered 6 direct-completion cases and did not improve any final F1. Five 4-hop cases paid one extra retrieval round, so cost-normalized F1 fell below `chain_locality_no_closure`.
   - Main bad extractions: count `1523` from a painting date for gold `22`; date/year `1990`, `1992`, `1571` from intermediate passages for golds `1930`, `2016`, and `May 4`.

2. `direct_completion_cue_aware_no_closure`
   - Code change: keep the same direct-completion architecture but require structured values to occur near final-target predicate cues from the original question. Count targets only use count-like cues (`occur`, `occurred`, `times`, `population`, `count`, `number`, `total`) and do not borrow bridge cues such as `died`. `what day` questions no longer accept a bare year fallback.
   - Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_direct_completion_cue_aware_no_closure_no_think.yaml`
   - Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_direct_completion_cue_aware_no_closure_no_think`
   - Result: `answer_f1=0.2304`, `coverage=0.3111`, `selective_answer_f1=0.7407`, `avg_retrieval_calls=1.8222`, `cost_normalized_f1=0.1265`, `closure_success=0`, contamination clean.
   - Per-hop F1: 2-hop `0.4533`, 3-hop `0.2418`, 4-hop `0.0000`.
   - Interpretation: cue-aware completion suppresses all 6 wrong direct-completion triggers from the previous run and removes the extra retrieval cost. In the actual stratified45 run it produced `0` direct-completion cases, so it behaves like `chain_locality_no_closure` on aggregate metrics. It is safer than the broad direct-completion variant, but not a promotable improvement.

Updated follow-up metrics:

| run | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | cost_normalized_f1 | direct cases | zero-F1 answered | closure_success | contamination | decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| chain locality + no closure | 0.2304 | 0.3111 | 0.7407 | 1.8222 | 0.1265 | 0 | 2 | 0 | clean | best safe no-closure reference |
| direct completion + no closure | 0.2304 | 0.3111 | 0.7407 | 1.9333 | 0.1192 | 6 | 2 | 0 | clean | safe but wastes cost on wrong structured values |
| cue-aware direct completion + no closure | 0.2304 | 0.3111 | 0.7407 | 1.8222 | 0.1265 | 0 | 2 | 0 | clean | safer extraction, no F1 gain |

Direct-completion decision:

- Do not run full300 from either direct-completion variant.
- The broad variant validates the integration safety boundary but exposes an extraction-precision bottleneck.
- The cue-aware variant fixes the observed wrong-target/cost regression, but because it fires on no stratified45 cases it does not yet address the core coverage/F1 problem.
- The next useful route is not broader direct extraction. It should either make final-slot completion relation-aware with explicit target-slot predicates, or improve named slot decomposition so final evidence can be bound before answer generation without depending on verifier claim status.

## Follow-Up: Prompt Slot-Binding Verifier

方案 A tested a prompt-based `SlotBindingVerifier`: instead of broad value extraction, it asks the local Qwen3 model whether retrieved evidence directly completes the `final_target` slot. The module is still safety-gated:

- only structured final target types are eligible: `date`, `year`, `century`, `count`, `population`, `number`;
- `person`, `location`, `company`, `network`, and other entity targets are not completed by this module;
- returned `evidence_ids` must have been retrieved in the current trajectory;
- returned `evidence_ids` must pass the same local / MuSiQue sibling-chain locality rule as evidence-binding slot ledger;
- returned `bound_value` must be non-empty;
- `supports_slot`, `slot_relation_match`, and `answer_type_match` must all be true;
- final answers still go through existing slot-answer generation and final verifier checking.

Runs:

1. `slot_binding_verifier_no_closure`
   - Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_verifier_no_closure_no_think.yaml`
   - Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_verifier_no_closure_no_think`
   - Result: `answer_f1=0.2304`, `coverage=0.3111`, `selective_answer_f1=0.7407`, `avg_retrieval_calls=1.8444`, `cost_normalized_f1=0.1249`, contamination clean.
   - Diagnostic: 16 slot-binding attempts, 2 accepted bindings. One accepted binding was correct (`3hop1__108833_720914_41132`, value `22`) but the final verifier still did not accept the slot-derived answer, so final F1 stayed 0. The other accepted binding was wrong-target (`4hop1__145494_698949_157828_162309`, value `1920` from a `3hop1...` evidence id for gold `2016`); the final verifier blocked the answer, but the run paid one extra retrieval round.

2. `slot_binding_verifier_locality_no_closure`
   - Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_verifier_locality_no_closure_no_think.yaml`
   - Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_verifier_locality_no_closure_no_think`
   - Result: `answer_f1=0.2304`, `coverage=0.3111`, `selective_answer_f1=0.7407`, `avg_retrieval_calls=1.8222`, `cost_normalized_f1=0.1265`, contamination clean.
   - Diagnostic: 17 slot-binding attempts, 1 accepted binding. The locality gate suppresses the wrong-target `1920` binding and restores the cost profile to the `chain_locality_no_closure` level. The one accepted binding remains the correct `22` case, but final verifier rejection means it still does not improve F1.

Updated slot-verifier follow-up metrics:

| run | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | cost_normalized_f1 | binding attempts | accepted bindings | zero-F1 answered | contamination | decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| chain locality + no closure | 0.2304 | 0.3111 | 0.7407 | 1.8222 | 0.1265 | 0 | 0 | 2 | clean | safe no-closure reference |
| prompt slot binder + no closure | 0.2304 | 0.3111 | 0.7407 | 1.8444 | 0.1249 | 16 | 2 | 2 | clean | not promotable; one wrong binding and no F1 gain |
| prompt slot binder + locality + no closure | 0.2304 | 0.3111 | 0.7407 | 1.8222 | 0.1265 | 17 | 1 | 2 | clean | safer, but no F1 gain |

Slot-binding verifier conclusion:

- 方案 A validates the right interface: slot-level binding can identify at least one correct final slot (`22`) that normal claim-status binding misses.
- It does not yet solve the bottleneck because the downstream final verifier still rejects the slot-derived candidate answer. In this case, the blocking point moves from slot completion to final answer verification.
- The prompt binder also shows the expected wrong-target risk: without locality, it accepts a related but non-current-chain Olympic attendance year (`1920`). The locality gate blocks this, so the safety boundary is necessary.
- Do not run full300 from the prompt slot-binding verifier variants.
- The next useful verifier work is not just another binder prompt. It should split final verification into a slot-aware final verifier that receives `final_target` evidence and the slot-binding result, so a correctly bound final value like `22` is not re-rejected by an answer-level verifier that lacks the slot-binding context.

## Follow-Up: Scoped Slot-Aware Final Verifier

A narrow `SlotFinalVerifier` was added after the prompt slot-binding verifier diagnosis. It verifies only slot-derived answers whose final slot was filled by `slot_binding_verifier`; existing slot-ledger final answers continue to use the generic verifier. This scope is important.

Implementation guardrails:

- the module does not generate or repair answers;
- it receives only the original question, slot ledger, candidate short answer, and final-target evidence;
- it is called only when final slot evidence came from `slot_binding_verifier`;
- eligible target types remain restricted to `date`, `year`, `century`, `count`, `population`, and `number`;
- accepted verifier output must have `overall_sufficiency=sufficient`, `need_more_evidence=false`, `final_target_match=true`, and `answer_slot=final requested target`;
- all supported critical-claim evidence ids must be non-empty, local, and a subset of the final-slot evidence ids.

Runs:

1. Initial unscoped slot-final verifier diagnostic
   - Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_slot_final_verifier_no_closure_no_think`
   - Result: `answer_f1=0.1638`, `coverage=0.2444`, `selective_answer_f1=0.6699`, `avg_retrieval_calls=1.8222`, `cost_normalized_f1=0.0899`, contamination clean.
   - Diagnostic: the verifier recovered the target case (`3hop1__108833_720914_41132` -> `22`), but it also replaced the generic verifier on ordinary slot-ledger answers and rejected four previously correct date/year answers because Qwen labeled them `answer_slot=date component`. This confirmed the trigger must be scoped to slot-binding-verifier completions only.

2. Scoped slot-final verifier
   - Config: `configs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_slot_final_verifier_no_closure_no_think.yaml`
   - Run: `runs/layer1_local_qwen3_14b_int4_decomp_gate_answer_repair_claim_risk_stratified45_slot_ledger_slot_binding_slot_final_verifier_scoped_no_closure_no_think`
   - Result: `answer_f1=0.2526`, `coverage=0.3333`, `selective_answer_f1=0.7579`, `avg_retrieval_calls=1.8000`, `cost_normalized_f1=0.1404`, `final_answered_unsupported_rate=0`, contamination clean.
   - Diagnostic: exactly one sample changed relative to `slot_binding_verifier_locality_no_closure`: `3hop1__108833_720914_41132` moved from abstain to answer `22`. The slot-final verifier was called once, accepted once, and had no rejects.

Updated slot-verifier metrics:

| run | answer_f1 | coverage | selective_answer_f1 | avg_retrieval_calls | cost_normalized_f1 | slot-final calls | accepted | zero-F1 answered | contamination | decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| prompt slot binder + locality + no closure | 0.2304 | 0.3111 | 0.7407 | 1.8222 | 0.1265 | 0 | 0 | 2 | clean | safe no-closure reference |
| unscoped slot-final verifier | 0.1638 | 0.2444 | 0.6699 | 1.8222 | 0.0899 | 13 | 3 | 1 | clean | rejected existing correct slot answers; do not use |
| scoped slot-final verifier | 0.2526 | 0.3333 | 0.7579 | 1.8000 | 0.1404 | 1 | 1 | 2 | clean | narrow gain; promising but still below soft binding |

Scoped slot-final verifier conclusion:

- The intended bottleneck was confirmed. The correct slot binding for `22` can become a final answer when the final verification step is slot-aware.
- The scoped version improves over the locality slot-binding reference: `answer_f1 +0.0222`, `coverage +0.0222`, and `cost_normalized_f1 +0.0139`, without increasing retrieval rounds or contamination.
- It remains below the soft final-target binding reference (`answer_f1=0.2812`) and below the guarded stratified45 baseline (`answer_f1=0.2634`) on F1, but its cost-normalized F1 (`0.1404`) is above guarded closure + cost cleanup (`0.1248`).
- Do not run full300 yet. The result is a useful positive micro-step, not a promotable full line. The next step should focus on increasing the number of safe slot-binding completions, not broadening slot-final verification beyond slot-binding-verifier completions.
