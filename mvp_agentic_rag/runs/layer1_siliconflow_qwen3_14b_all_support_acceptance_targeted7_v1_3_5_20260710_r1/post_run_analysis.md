# All-Support Acceptance Targeted7 Post-run Analysis

## Run Status

- Completed records: 7/7.
- API failures or resumed records: 0.
- Fixed baseline: Qwen3-14B for answer/verifier/slot verifiers, dense BGE retrieval, controller policy v1, RepairPlanner v1.
- Changed runtime variable: code at commit `7c2f307` plus the evaluation-slice exclusivity correction made after this run.
- Runtime artifacts: `trajectories.jsonl`, `metrics.json`, `metrics.md`, and `run_summary.md`.

## Headline Result

| Metric | Result |
| --- | ---: |
| actionable exact answers | 0/5 |
| total exact answers | 0/7 |
| coverage | 0.0000 |
| answer F1 | 0.0000 |
| average retrieval calls | 3.0000 |
| no-new-evidence call rate | 1.0000 |
| wasted retrieval rate | 1.0000 |
| unsafe or unsupported final answers | 0 |

The promotion gate failed. Do not launch a new 45-record run from this runtime state.

## Evaluation Slices

The two dataset/evidence ambiguity records are excluded from acceptance-failure slices.

| Slice | Count | Eligible | Sample IDs |
| --- | ---: | ---: | --- |
| all_support_retrieved_no_candidate | 2 | 3 | `2hop__247353_55227`, `3hop1__140786_2053_5289` |
| correct_candidate_rejected | 0 | 0 | none |
| gold_support_not_textually_entailing | 2 | 7 | `3hop1__108833_720914_41132`, `3hop1__128554_39743_24526` |

`correct_candidate_rejected=0` is not evidence of successful acceptance. No eligible record produced a recognizable correct final candidate.

## Sample Outcomes

| Sample | Gold | Gold support retrieved | Outcome | Primary failure |
| --- | --- | ---: | --- | --- |
| `2hop__132854_417697` | Nissan Altima | 1/2 | abstain | Final passage was not retrieved; slot verifier was non-JSON in 3/3 rounds. |
| `2hop__153573_44085` | The Mickey Mouse Club | 2/2 | abstain | Only Mickey Mouse was labeled as a bridge candidate; no final show candidate was bound. |
| `2hop__247353_55227` | Maria Bello | 2/2 | abstain | Slot verifier was non-JSON in 3/3 rounds, so title/person-relation hints never became a binding. |
| `3hop1__140786_2053_5289` | Oriole Records | 3/3 across rounds | abstain | Slot verifier was non-JSON in 3/3 rounds; same-candidate fallback had no candidate to preserve. |
| `3hop1__144439_443779_52195` | Francisco Guterres | 2/3 | abstain | Round 1 planned the correct East Timor president query, but retrieval missed the president passage; a round-2 parse failure erased progress and replanning returned to birthplace. |
| `3hop1__108833_720914_41132` | 22 | 3/3 across rounds | safe abstain | Correctly classified as gold support not textually entailing the Titian death-location hop. |
| `3hop1__128554_39743_24526` | upper 40s-lower 50s F | 3/3 | safe abstain | Correctly excluded for entity-type collision; the planner drifted to Minnesota, but no unsafe answer was accepted. |

## Dominant Bottlenecks

### 1. Slot-verifier structured-output failure

- Targeted7: 16 non-JSON results in 21 slot-verifier attempts, rate 0.7619.
- Previous 45-record run: 75 non-JSON results in 106 attempts, rate 0.7075.
- The targeted sample is too small to claim a statistically meaningful regression, but both rates are operationally unacceptable.

The current client sends a large duplicated JSON example but does not request an API-enforced JSON response format. Raw failed completions and finish reasons are discarded, so truncation versus prose/code-fence failure cannot yet be distinguished. The large output contract and `slot_binding_verifier_max_tokens=1536` make truncation a plausible cause, not a proven one.

### 2. Retrieval instability prevents acceptance-path isolation

The seven records were selected because the previous 45-record run had retrieved all gold support. The new live run did not reproduce that condition for Nissan Altima or Francisco Guterres. Answer/verifier variation changes repair queries, so this is not a controlled acceptance-only experiment.

### 3. Acceptance hooks were not exercised

- Oriole same-candidate fallback: no runtime candidate was generated.
- Timor structured candidate preservation: the final-hop evidence and final candidate were absent.
- Nissan/Mickey/Maria title, alias, and person-relation hints: only Mickey produced a structured result, and it labeled the bridge entity rather than the final show.

## Decision

Verdict: targeted gate failed; stop before the 45-record rerun.

Next route:

1. Add parse-failure observability: response length, finish reason when available, and a bounded/raw-safe diagnostic for failed slot-verifier completions.
2. Make the slot-verifier output contract compact and canonical instead of requesting duplicate legacy and v1.2 structures.
3. Where supported by the provider, request JSON-object response format; otherwise add one bounded compact JSON-repair retry.
4. Validate the slot verifier against fixed saved evidence for the five actionable records, so retrieval cannot mask acceptance behavior.
5. Rerun this same live Targeted7 only after structured parse success reaches at least 90% and the fixed-evidence check produces all five expected candidates.

