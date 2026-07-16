# Adapter-vs-Generic Online Stability Protocol Checklist

## Identity

- Protocol id: `semantic_adapter_generic_online_stability_v1_20260715`
- Parent: post-shared-certificate phase-3 decision
- Current status: `frozen`; API runs are authorized only in the fixed order

## Launch Contract

- [x] Claim, incumbent, comparator, and user-ordered boundary are explicit.
- [x] Certificate variance and terminal-policy behavior are separate layers.
- [x] Exactly two fresh independent runs per variant are fixed.
- [x] `A1 -> G1 -> G2 -> A2` order and no extra confirmatory draw are fixed.
- [x] Historical R26/R27 are excluded from primary aggregation.
- [x] Hard validity, safety, progression, and stopping rules are fixed.

## Frozen Assets

- [x] Dataset, corpus, index, source paths, and current hashes identified.
- [x] Four exact YAML configs created and mechanically compared.
- [x] Machine-readable protocol JSON created.
- [x] Source/data/config manifest created and hashed.
- [x] All planned output directories confirmed absent.

## Analyzer Before Outcomes

- [x] Certificate-completion analyzer implemented.
- [x] Terminal-policy analyzer implemented using shared frozen replay.
- [x] Mean, sample SD, range, paired deltas, and per-case stability implemented.
- [x] Analyzer unit tests pass: 5 passed.
- [x] Historical R26/R27 dry run completes and is labeled non-primary.

## Final Local Freeze

- [x] Focused and full tests pass: 38 focused; 653 full plus 27 subtests.
- [x] Compileall and whitespace checks pass.
- [x] Gold is used only in the frozen offline evaluator; runtime configs and
  routing contain no gold/sample-specific branch.
- [x] Protocol/config/analyzer/test hashes recorded.
- [x] Protocol status changed from `pre_registration_in_progress` to `frozen`.

## Paid Runs — Locked Until Freeze

- [x] A1 adapter-only completed and audited: 45/45 unique, `valid=true`, all
  safety/policy hard gates pass.
- [x] G1 generic-only completed and audited: 45/45 unique, `valid=true`, all
  safety/policy hard gates pass; block-1 certificate/F1/coverage deltas are
  positive but remain partial evidence pending block 2.
- [x] G2 generic-only completed and audited: 45/45 unique, `valid=true`, all
  safety/policy hard gates pass; A2 is the only next authorized run.
- [x] A2 adapter-only completed and audited: 45/45 unique, `valid=true`, all
  safety/policy hard gates pass.

## Aggregation And Route

- [x] Certificate variance report completed.
- [x] Terminal-policy behavior report completed.
- [x] Predeclared decision rule applied without modification:
  `pass_to_matched_modern_baselines`.
- [x] Matched baseline package launched only after the repeat package passed;
  135/135 rows completed and locally verified.
