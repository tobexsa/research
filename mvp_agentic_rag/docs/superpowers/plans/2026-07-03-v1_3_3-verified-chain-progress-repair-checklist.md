# v1.3.3 Verified Chain Progress Repair Checklist

## Analysis Campaign

- [x] Add failing tests for v1.3.2 failure-mode analysis.
- [x] Implement `scripts/analyze_v1_3_2_failure_modes.py`.
- [x] Generate `analysis/v1_3_2_failure_modes.json`.
- [x] Generate answered unsupported audit report.
- [x] Generate v1.3.1 vs v1.3.2 delta report.
- [x] Generate 4-hop bottleneck report.
- [x] Decide whether `answered_unsupported_rate` is final-answer risk or intermediate-claim noise.
- [x] Decide whether 4-hop failures expose verified chain progress.

## v1.3.3 Implementation

- [x] Add failing tests for verified-chain-progress repair.
- [x] Add `repair_verified_chain_progress_v1_3_3` config flag.
- [x] Route verified prefix + next missing hop to `partial_chain_next_hop_repair`.
- [x] Prevent placeholder or unverified ordered-hop repair from being rewritten into a confident query.
- [x] Add v1.3.3 SiliconFlow config.
- [x] Run focused tests.
- [x] Run regression tests.

## Stratified45 Run

- [x] Launch v1.3.3 stratified45.
- [x] Confirm 45 / 45 completion.
- [x] Generate metrics and run summary.
- [x] Compare against v1.3.2.
- [x] Record post-run recommendation.
