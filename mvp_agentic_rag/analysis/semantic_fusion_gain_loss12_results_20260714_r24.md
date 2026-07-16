# Semantic Fusion Fixed-12 Gate: R24

Date: 2026-07-14

## Verdict

R24 passes phase 1. It retains all five R20 gains, recovers all seven R12
losses, and keeps final answered unsupported at zero. The user-ordered phase
2 Fusion / generic-only stratified45 comparison is now authorized.

## Frozen Contract

- Config: `configs/layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_20260714_r24.yaml`
- Config SHA-256: `C675691E5016F78508381C9C5806A214DE0DAABAAF6B619A90AF063A89CD8E17`
- Dataset SHA-256: `04F15DB77255C0DA10B5F811081D7E2B0ADC3B11572F1D4336959E4654E090FB`
- Output: `runs/layer1_siliconflow_qwen3_14b_semantic_fusion_gain_loss12_20260714_r24`
- Trajectory SHA-256: `04E4EA141F84FB4A8C95F7CEE56E0EAB08FA143D0B676A7B674708125747F395`
- Metrics SHA-256: `2EC5117BB09780B632D631B03FE6B3BC7A0F9AB945F00C7ED213CF6066136FAC`
- Completion: 12 rows, 12 unique IDs, no remaining run lock, empty stderr.

## Metrics

- Accuracy / EM: `1.0000`
- Answer F1: `1.0000`
- Coverage: `1.0000`
- Selective accuracy / F1: `1.0000 / 1.0000`
- Average retrieval calls: `1.8333`
- Wasted retrieval rate: `0.1667`
- Final answered unsupported rate: `0.0000`
- Correct candidate rejected count: `0`

These are fixed, targeted-gate metrics and must not be reported as
distribution-level MuSiQue performance.

## Hard Gate

- Retained gains: `5/5`
- Recovered losses: `7/7`
- Final answered unsupported: `0`
- Unsafe failure-candidate transitions in replay: `0`
- Canonical hop-conflict events in replay: `0`
- Same-round topology update rejections: `0`

The two candidate-level contradictions remained unscoped and did not become
hard hop conflicts.

## Mechanism Evidence

- Date output remains `March 11, 2011` after the post-slot handoff.
- Count output is normalized to the structured numeric surface `450`.
- The deterministic state-only cast binding replaces the stale ledger
  candidate and returns `Maria Bello`.
- The first Francisco case uses the natural repair query `East Timor
  president` and retrieves the final-hop evidence in round 2.
- Oriole and the second Francisco case remain correctly answerable.
- All five strict-certificate gains remain correct.

## Decision

Advance to phase 2 only. Freeze and run two matched 45-case configurations:

1. R24 Fusion on the original stratified45 dataset.
2. Generic-only on the same dataset with specialized certificate adapters and
   strict-certificate activation disabled while preserving all other model,
   retrieval, budget, and evaluator settings.

Do not start phase 3 ablations, repeats, or modern baselines until both phase
2 runs are complete and compared.
