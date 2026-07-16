# R31 Fixed-12 Identity-Only Retry Contract

Date: 2026-07-15

## Identity

- Run id: `layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_terminal_safety_20260715_r31`
- Tier: `auxiliary/dev` safety-regression gate.
- Research question: after the terminal fail-closed repair, can an otherwise
  unchanged independent API execution restore the frozen 12-case gate while
  keeping every safety invariant at zero?
- Baseline references: R24 (12/12 pre-repair gate) and R30 (safe 10/12
  post-repair execution).
- Dataset: `data/musique_semantic_fusion_gain_loss12_20260714.jsonl` (12 rows,
  5 gain cases and 7 loss cases).

## Frozen Intervention And Comparability

- R31 is identity-only relative to R30: only `run_name` and `output_dir`
  differ.
- No code, prompt, model, retriever, budget, evaluator, data, or metric change
  is authorized before or during this run.
- Configuration SHA-256:
  `680A2BE6BD40DA7014F3B2CCCC880BFE18A28D4D0D788F09029A0ADF2D2ED69F`.
- Dataset SHA-256:
  `04F15DB77255C0DA10B5F811081D7E2B0ADC3B11572F1D4336959E4654E090FB`.

## Hypotheses

- Null: the repaired fixed-12 gate remains below 12/12 because the online
  certificate/controller pipeline is not stable enough for a per-run 12/12
  contract.
- Alternative: R30's two abstentions were upstream API variation, and one
  unchanged retry restores all 12 expected outcomes without a safety failure.
- Strongest confounder: nondeterministic remote model responses despite an
  otherwise frozen local configuration.

## Acceptance Gate

R31 passes only if all conditions hold:

- exactly 12 completed rows and 12 unique sample IDs;
- gains: 5/5 correct;
- losses: 7/7 correct;
- final answered unsupported rate/count: zero;
- terminal invariant violation count: zero;
- unsafe typed-state replay transition count: zero;
- configuration, dataset, trajectory, metrics, and replay evidence are
  durably hashable.

Strict/generic/no-fallback lane activation and adapter applications must also
be reported, but are diagnostics rather than substitutes for the hard gate.

## Command And Outputs

Command:

```powershell
D:\python1\python.exe scripts\run_layer1_skeleton.py --config configs\layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_terminal_safety_20260715_r31.yaml
```

Expected output directory:

`runs/layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_terminal_safety_20260715_r31`

The run output directory was absent at preflight.

## Stop And Next-Route Contract

- This is the single authorized identity-only full retry after R30.
- If R31 passes, close Phase C and proceed to activation-aware
  shared-certificate attribution; do not jump directly to repeats or larger
  samples.
- If R31 misses any hard criterion, do not retry or tune. Record the fixed-12
  online gate as stochastically unstable and move to a deterministic frozen
  certificate-stream or multi-run stability contract decision.
- Under neither outcome may this run authorize a 300-case experiment.

## Runtime Interface Degradation

The current runtime exposes neither managed `bash_exec` nor artifact/memory
interfaces. Execution therefore uses PowerShell and repository-local durable
files under `analysis/` and `runs/`. These files are fallback evidence, not
artifact-service records.
