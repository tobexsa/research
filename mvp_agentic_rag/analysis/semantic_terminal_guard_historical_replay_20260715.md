# Semantic Terminal Guard Historical Replay

Date: 2026-07-15

## Outcome

The repaired generic terminal authorization leaves every answered R25 full
Fusion and R27 adapter-only row unchanged in historical replay. It would
downgrade two R26 and two R28 answers whose runtime evidence does not satisfy
the new terminal invariants.

| Run | Answered samples changed | Terminal invariant events | Interpretation |
|---|---:|---:|---|
| R25 full Fusion | 0 | 0 | Known full-Fusion answers preserved |
| R26 generic-only | 2 | 4 | Two correct but non-certifiable answers become abstentions |
| R27 adapter-only | 0 | 0 | Known adapter-only answers preserved |
| R28 strict-only boundary | 2 | 9 | Unsupported target and one unsupported-binding answer blocked |

## R28 Target Failure

`4hop1__151650_5274_458768_33632` is blocked for eight independent runtime
reasons: original abstention, need for more evidence, unclear critical claim,
no critical-claim evidence, unsupported slot binding, incomplete binding chain,
uncovered final slot, and incomplete critical ancestor closure. No gold answer
is required to derive any reason.

## Non-Target Changes

- `2hop__167577_31122` in R28 is correct by gold but has
  `supports_slot=false`; the repaired policy abstains rather than accepting an
  uncertified answer.
- `2hop__23459_35124` in R26 is correct by gold but has an incomplete,
  unsupported binding and incomplete canonical closure; it becomes abstention.
- `3hop1__140786_2053_5289` in R26 cites a verifier evidence ID not present in
  the retrieved local evidence set; it becomes abstention.

These are intentional safety/coverage tradeoffs. They are not counted as
implementation regressions because the predeclared contract requires local,
complete evidence for terminal answers. The paid fixed-12 gate remains the
decisive regression check.

## Local Verification

- Focused: 281 passed, 27 subtests passed.
- Full: 645 passed, 27 subtests passed.
- Compileall: passed.
- Source scan: no sample ID, gold answer, gold decomposition, or gold-support
  branch was introduced.

## Decision

Proceed only to the single offending-case API probe. Run the repaired fixed-12
gate only if that probe abstains or produces a fully supported answer.

