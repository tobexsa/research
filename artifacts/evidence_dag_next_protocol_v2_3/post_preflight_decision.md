# V2.3 Post-Preflight Decision

- verdict: `neutral` (mixed evidence)
- action: `branch` into independent P1 structural diagnostics; `stop` span-dependent P2B/P2C promotion.
- decision question: which protocol slices can produce interpretable evidence after the safe-stage gates?

## Evidence

- support: P0A Pro passed 216/216 across Plain Text, Plain JSON, and Provider JSON Schema; P0B passed 432/432 Canonical JSON and Schema Semantic Match across all six real schema families; P0C standard passed 216/216.
- support: all P0 raw/metrics bundles passed machine validation; E0 passed 28 focused and 823 full-suite tests.
- boundary: G0 could reserve A/B only at `Compositional`, not Strict, independence.
- contradiction: P2A normalized and alias-resolved recall were both 68/90 (75.56%), below the frozen 98% gates.
- missing dependency: no exact strong-model comparator is frozen or authorized.

## Candidate routes and selection

Selection criteria were interpretability, prerequisite satisfaction, fixed-budget feasibility, comparability with Diagnostic-Dev-60, and risk of Gold leakage.

1. Winner: P1 Route A/B plus C4A Oracle Pairwise. These slices depend on the decoder/schema envelope that passed and do not require automatic span candidates.
2. Rejected for now: P2B/P2C automatic span/slot path. Its direct prerequisite failed by 22.44 percentage points.
3. Blocked: P3 strong-model comparison. Substituting another model would violate the protocol.
4. Deferred: P4/P5 and both internal holdouts. They remain downstream of a new P1 result and require their own exact freezes.

## Next checkpoint

Run the frozen P1 structural package on Diagnostic-Dev-60 only. After its machine-validated result, decide separately whether any route deserves a new freeze. Confirmation-120 remains exclusion-only and untouched by model calls.

## Compatibility note

The `decision` skill's artifact and `bash_exec` interfaces are unavailable in this runtime. This repository-local decision record, isolated Git worktree, raw JSONL, machine validation, and commit history are the durable compatibility path.
