# Online Stability Protocol Freeze Record

Date: 2026-07-15
Protocol id: `semantic_adapter_generic_online_stability_v1_20260715`
Verdict: `frozen`

## Frozen Outcome

The adapter-only versus generic-only online stability protocol is fully
pre-registered before any new online result. It separates certificate
completion from terminal-policy behavior, fixes exactly two fresh independent
runs per variant, forbids extra confirmatory draws, and allows progression to
matched modern baselines only through the predeclared six-part pass rule.

No API run was started during protocol construction. All four output
directories were absent at final freeze audit.

## Exact Run Order

1. `adapter_stability_s1`
2. `generic_stability_s1`
3. `generic_stability_s2`
4. `adapter_stability_s2`

This `A1 -> G1 -> G2 -> A2` order may not be changed under protocol v1.

Exact commands:

```powershell
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s1.yaml
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s1.yaml
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_semantic_generic_only_stability_stratified45_20260715_s2.yaml
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_semantic_adapter_only_stability_stratified45_20260715_s2.yaml
```

Only the first command is currently executable under the order contract. Each
run must close, audit, and hash successfully before the next command becomes
authorized.

## Treatment Isolation

Both variants use:

- strict-certificate acceptance disabled;
- the same repaired shared generic terminal fail-closed guard;
- the same model, retrieval, budgets, prompts, evaluator, dataset, corpus,
  index, and source bundle.

The only scientific treatment difference is:

```yaml
slot_binding_verifier_deterministic_bindings: true   # adapter-only
slot_binding_verifier_deterministic_bindings: false  # generic-only
```

Mechanical comparison confirms the paired configs differ only in that field,
`run_name`, and `output_dir`. S1/S2 configs within each variant differ only in
run identity and output directory.

## Two-Layer Reporting Lock

Certificate-completion variance and terminal-policy behavior must be reported
as separate top-level sections.

Certificate layer includes complete/correct local certificate rates, adapter
applications, failure categories, run mean/sample-SD/range, paired block
deltas, and per-case 0/2, 1/2, 2/2 stability.

Terminal-policy layer includes answers/abstentions, answers without complete
certificates, abstentions despite complete certificates, guard/downgrade
counts, final unsupported, state/terminal violations, three-repeat frozen
policy determinism, and per-case action stability.

No certificate-generation difference may be relabeled as a terminal-policy
effect.

## Predeclared Progression Rule

Matched modern baselines are authorized only if all four runs are valid and:

- correct terminal-certificate adapter-minus-generic delta is positive in both
  paired blocks;
- Answer-F1 delta is positive in both paired blocks;
- aggregate Answer-F1 and coverage deltas are positive;
- answer without a complete terminal certificate is zero in all runs;
- final unsupported and all terminal/state safety counts are zero in all runs.

Mixed signs mean `unstable_stop_no_extra_draw`. They do not authorize another
repeat. Safety or validity failure returns to diagnosis. Certificate-only or
F1-only improvement does not authorize baselines.

## Validation Before Freeze

- Analyzer unit tests: `5 passed`.
- Focused protocol/state/replay tests: `38 passed`.
- Full suite: `653 passed, 27 subtests passed`.
- Compileall: passed.
- Whitespace check: passed.
- Machine manifest audit: 18 files checked, 0 errors.
- Historical R26/R27 dry-run: completed and explicitly excluded from primary
  aggregation/decision.

The dry-run intentionally reports one historical answer without a current
complete terminal certificate and four historical safety audit events. This is
expected pre-fix evidence and confirms the analyzer does not sanitize old
results to fit the new gate.

Gold answers are used only in the offline frozen evaluator to score certificate
correctness and final performance. They are not present in run configs or
runtime routing decisions.

## Freeze Hashes

- Protocol plan:
  `1E825465AF45F8D3C73B6FB3C49955A72C947BBEC99C1F0CF9BC9AC6657D67A0`
- Protocol checklist:
  `FA4A711293A58D4352117FD9708D8ADF8BC53E64E6C6EA43367A12273826F19D`
- Machine protocol JSON:
  `98C1ACCC3061676C73F1B76447212F0B017BA55370D7153854211BEC3CC89365`
- Source/data/config manifest:
  `394BCC1AD740DF34C2863F49D95F2CB8F0E95EB38CB55A078F9FE0DE0EE785D8`
- Analyzer:
  `BC9754F57437EB800F0970500E0952A8B5789C0743F8D226E4441383416C2356`
- Analyzer tests:
  `07B538F048436D8FD3D68CF056CF7606DE8F5981F9DA921F8AAFA1C36738878E`
- Historical dry-run JSON:
  `882A92B6561ABA0EA60C948AF805DCC33966CCFA0ADC427485AAD96F5A04526D`
- A1 config:
  `DE5A54A354E3F89EA88E418D5A6979E302DFA1E65CB2EF4449542F8CF00E1986`
- G1 config:
  `ACCF9356D7346C2A43B465A325606472E208070B8A7AE0FF01936EFD24C86C2D`
- G2 config:
  `52A01927635A62690540A7AC7908A5B83C85DED057F749525298AD91FF43F95F`
- A2 config:
  `652D0115C5CF10A39C4583835A4FC81773239AAD90BE6F94D7EA1D8DF539AAED`

## Mutation And Infrastructure Rules

Protocol v1 files must not be overwritten. Any source/config/analyzer/metric or
order change requires a new protocol version before more online calls.

A partial interrupted run may resume in the same output directory and remains
the same independent run. A replacement is allowed only if an external outage
occurs before any valid sample row exists. Low metrics, abstention, timeout,
parse failure, or variance after valid rows exist are experimental outcomes and
may not be discarded.

## Runtime Interface Degradation

Managed `bash_exec`, artifact, and memory interfaces were unavailable. The
repository-local plan, configs, analyzer, tests, dry-run, machine JSON,
manifest, and hashes are the explicit durable fallback, not artifact-service
records.
