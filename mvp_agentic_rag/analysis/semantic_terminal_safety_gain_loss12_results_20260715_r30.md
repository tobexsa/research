# Terminal Safety Repair Fixed-12 Gate: R30

Date: 2026-07-15

## Verdict

R30 is complete and safe but does not pass the 12/12 performance regression
gate. It retains 4/5 prior gains and 6/7 prior losses, for 10/12 overall.
Final answered unsupported and all new terminal invariant counts are zero.

## Metrics And Integrity

- 12 rows, 12 unique IDs, complete finite metrics.
- EM/F1/coverage: `0.8333 / 0.8333 / 0.8333`.
- Selective accuracy/F1: `1.0000 / 1.0000`.
- Final answered unsupported: `0`.
- Terminal invariant violations: `0`.
- Unsafe structural replay transitions: `0`.
- Trajectory SHA-256:
  `0A7CC14936997B20A88A558FE5B33E85BF55EE96DEB2180F2A25455BE6010AAA`.
- Metrics SHA-256:
  `4C1B8C6A503DD239CF7587B7D21DFD6B4C79433490CF616F2C546364E4E94BF6`.

## Regressions

- `2hop__167577_31122`: R24 answered `18th`; R30 abstained.
- `3hop1__140786_2053_5289`: R24 answered `Oriole Records`; R30 abstained.

For both rows, the final action was already abstain before the repaired generic
terminal authorization ran. Both show `state_controller_terminal_guard=false`,
no downgrade, and no terminal block reasons. The repair therefore did not
cause either action change. This is independent API/run variance in upstream
verifier/controller state.

## Decision

Run exactly one fresh full fixed-12 retry under an identity-only config change.
Do not change code or any experimental setting. If the retry still fails
12/12, stop paid retries and classify the gate as unstable rather than tuning
against stochastic outcomes.

