# Semantic-binding stratified45 checklist (R12)

- [x] Targeted7 R10 complete and analyzed.
- [x] Nissan post-R10 provenance gate complete.
- [x] Arizona granularity issue separated from controller tuning.
- [x] Full local tests, compileall, and diff checks pass.
- [x] Go/no-go decision recorded with alternatives and caveats.
- [x] Freeze a unique R12 config and output path.
- [x] Start the real SiliconFlow 45-sample run with durable logs.
- [x] Validate 45 unique rows and complete outputs.
- [x] Validate safety and topology diagnostics.
- [x] Compare against the historical 45-sample reference.
- [x] Write the R12 result and next-step decision.

Execution note (2026-07-13 14:52 Asia/Shanghai):

- initial PID: `12216`;
- stdout: `runs/logs/layer1_siliconflow_qwen3_14b_semantic_binding_stratified45_20260713_r12.out.log`;
- stderr: `runs/logs/layer1_siliconflow_qwen3_14b_semantic_binding_stratified45_20260713_r12.err.log`;
- resume, if required, must use the same frozen config and output directory.

Outcome:

- 45/45 unique rows and 106 verifier/state steps completed in one process;
- accuracy/F1/coverage `0.3333/0.3511/0.3778`, matching the older historical
  headline reference and improving over broken-topology R1;
- topology ready on 105/106 steps and final unsupported rate zero;
- R12 exposed one malformed-output candidate bookkeeping leak; it was fixed
  after R12 and externally closed by R13 on the exact two affected samples;
- next bottleneck is deep-chain semantic identity/hint mapping, especially
  zero 4-hop coverage, not topology availability.
