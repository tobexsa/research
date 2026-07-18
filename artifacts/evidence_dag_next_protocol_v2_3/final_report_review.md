# Final Report Evidence Review

## Review verdict

Ready to finalize after one claim-ledger correction. No critical metric mismatch was found between the Chinese aggregate report and the committed experiment metrics.

## Evidence checks completed

- Verified the new model-call total: 12 P0 smoke + 864 formal P0 + 362 P1 = 1,238. Attached V1 D1/C1 and D2/C2O records are not counted as new calls.
- Verified the P2A gate uses the full planned denominator, 68/90 (75.56%), rather than the conditional 68/89 result.
- Verified P1 reports both independent failure modes: 83/362 `finish=length` whitespace continuations and 187/279 schema-valid but semantically wrong outputs.
- Verified the invalid P4 run (9/200) is retained only as a corpus/index-contract incident and is excluded from final evidence.
- Verified corrected P4 metrics: Recall@10 182/200, All-Steps 44/60, timeout 0/200, with 3,720/3,720 corpus/index ID agreement and 200/200 Gold-target coverage.
- Verified P5 R0 metrics: 182/200 resolved steps, 178/200 supporting-document recall, 50/60 Answer Ready/EM, and 0/60 cross-hypothesis mix.
- Verified Internal-Holdout-A/B remain unused and Confirmation-120 has zero model calls.
- Verified Strict holdout infeasibility is described only as bounded-search evidence, not a mathematical impossibility result.
- Verified P4 and R0 are described as Gold-query/Oracle component upper bounds, not production end-to-end results.
- Verified provider conclusions are limited to endpoint/system-level evidence because model revision, quantization, and guided-decoding backend are undisclosed.
- Verified grammar-constrained decoding is proposed only as a diagnostic for whitespace loops and is not claimed to solve semantic errors.

## Correction applied

Claim C5, “The R0 Oracle downstream path is completely lossless,” is classified as `unsupported`, not `partially_supported`: 50/60 Answer Ready/EM directly refutes perfect losslessness. The weaker statement that R0 is partially usable remains supported in the report.

## Remaining caveats

- Not every protocol slice was executed. P2B/P2C, P3, the P4 predicted-query factorial, P5 R1/X0/X1/X2/V0/V1, Internal Holdout, and Confirmation were correctly blocked or skipped because prerequisites or an exact frozen comparator were absent.
- The campaign supports stopping the current Planner candidate; it does not establish that all Qwen2.5-7B deployments or local grammar-constrained decoding will fail.
- The final regression result, 829 passed, is retained from the code-complete state. Closure-only Markdown/JSON changes do not alter runtime code.
