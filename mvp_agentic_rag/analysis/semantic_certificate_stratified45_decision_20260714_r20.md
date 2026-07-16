# Decision after R20 stratified45

Date: 2026-07-14

- Verdict: `neutral` / mixed evidence
- Action: `iterate`
- Parent run: `layer1_siliconflow_qwen3_14b_semantic_certificate_stratified45_20260714_r20`
- Next direction: strict-certificate / generic-compatibility fusion

## Reason

R20 preserves final safety and recovers five targeted cases, including the
first two correct 4-hop answers in this 45-sample line. However, it loses seven
R12-correct cases, reduces aggregate accuracy/F1/coverage, and increases
average calls and wasted retrieval. The method is therefore valuable as a
specialized lane, not as a global replacement for the R12 controller.

## Alternatives rejected

- Continue scaling the current R20 package: rejected because aggregate quality
  and cost are both worse than R12.
- Remove all R19/R20 certificate work: rejected because five gains are real,
  safe, and reproducible, including NBC and East 4-hop recovery.
- Add one deterministic binder per lost case: rejected because the 99
  dependency-incomplete events show an architectural routing problem rather
  than seven isolated extraction bugs.
- Relax all strict gates globally: rejected because malformed, sentinel,
  conflict, and nonlocal-evidence protections are required safety invariants.

## Next contract

Route recognized evidence-closed certificates through the strict R19 lane and
ordinary valid topologies through an R12-compatible lane. Never use fallback
for malformed/parse-failed/sentinel/conflicted records. Validate first on a
fixed 12-sample gain/loss gate; do not launch another stratified45 until every
gain is retained, every lost R12-correct case is recovered, and final
unsupported remains zero.
