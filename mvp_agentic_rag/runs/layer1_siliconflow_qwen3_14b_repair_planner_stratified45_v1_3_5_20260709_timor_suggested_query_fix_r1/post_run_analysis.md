# Stratified45 Post-run Analysis

## Run Status

- Completed records: 45/45
- Resume behavior: two SiliconFlow read timeouts were recovered by resuming the same output directory.
- Final artifacts: `trajectories.jsonl`, `metrics.json`, `metrics.md`, and `run_summary.md`.

## Headline Metrics

| Metric | Current | Previous repair-planner 45 | Delta |
| --- | ---: | ---: | ---: |
| overall_acc / EM | 0.2000 | 0.1556 | +0.0444 |
| answer_f1 | 0.2289 | 0.2059 | +0.0230 |
| coverage | 0.2444 | 0.2222 | +0.0222 |
| selective_acc | 0.8182 | 0.7000 | +0.1182 |
| cost_normalized_f1 | 0.0912 | 0.0813 | +0.0099 |
| wasted_retrieval_rate | 0.7333 | 0.7778 | -0.0445 |
| final_answered_unsupported_rate | 0.0909 | 0.0000 | +0.0909 |
| final_answered_unsupported_excluding_structured_slot_verified_rate | 0.0000 | 0.0000 | 0.0000 |

## Hop Results

| Hop | Accuracy | Coverage | Answered |
| --- | ---: | ---: | ---: |
| 2-hop | 0.4667 | 0.6000 | 9/15 |
| 3-hop | 0.1333 | 0.1333 | 2/15 |
| 4-hop | 0.0000 | 0.0000 | 0/15 |

## Failure Slices

- Final actions: 11 answer, 34 abstain.
- Exact answers: 9/11 answered records.
- The two exact-match failures are near matches: `Apple Corps Ltd.` vs `Apple Corps`, and `More than 450.` vs `450`.
- Abstentions with all gold support retrieved: 7.
- Abstentions with partial gold support retrieved: 25.
- Abstentions with no gold support retrieved: 2.
- RepairPlanner applied on 34 samples and generated repair queries on 28 samples.
- Only 4 samples recorded new evidence after repair; 58/62 repair-query steps recorded no new evidence.

All-support abstentions:

- `2hop__132854_417697`
- `2hop__153573_44085`
- `2hop__247353_55227`
- `3hop1__108833_720914_41132`
- `3hop1__128554_39743_24526`
- `3hop1__140786_2053_5289`
- `3hop1__144439_443779_52195`

## Full-300 Gate

| Gate | Required | Observed | Result |
| --- | ---: | ---: | --- |
| overall_acc / EM | >= 0.20 | 0.2000 | pass |
| answer_f1 | >= 0.27 | 0.2289 | fail |
| coverage | >= 0.40 | 0.2444 | fail |
| cost_normalized_f1 | >= 0.125 | 0.0912 | fail |
| 4-hop coverage | > 0 | 0.0000 | fail |
| wrong_target_rate | 0 | no clear wrong-target answer | provisional pass |

Decision: do not launch the 300-record run from this version. The next work should target repair-query retrieval yield and all-support answer acceptance, with 4-hop coverage as a hard promotion condition.
