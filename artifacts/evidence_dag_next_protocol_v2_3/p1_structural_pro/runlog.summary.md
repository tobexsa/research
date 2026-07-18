# P1 Run Log Summary

- 12:31:45 +08:00: P1 manifest/freeze created for code commit `7771bba`; 362 calls frozen.
- pre-run: 30 focused tests passed; clean-tree Preflight status `pass` at commit `aef24e4`.
- 12:34:56 +08:00: exact frozen command started with 8 workers.
- 12:35:54 +08:00: all 362 raw records and aggregate outputs completed.
- post-run: raw/metrics bundle Preflight status `pass`; 362 unique request IDs; C2P and C4A evaluations each contain 60 rows.
- follow-up: offline failure analysis separated 83 `finish=length` whitespace loops from 187 schema-valid but semantically wrong outputs.

No retry or prompt change was made. Confirmation-120 and Internal-Holdout-A/B were not queried.
