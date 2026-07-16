# Typed hop identity targeted8 R16 results

## Research question

Does increasing only `slot_binding_verifier_max_tokens` from 1536 to 2304
eliminate the four R15 `finish_reason=length` parse failures while preserving
the safety gates and the three correct 2-hop answers?

## Research type and objective

This is an `auxiliary/dev` targeted mechanism gate on the same fixed eight
MuSiQue samples as R15. R16 is a strict one-variable retry. It is not a new
algorithm version and is not evidence for stratified45 readiness unless both
the structural token gate and the targeted quality gate pass.

## Setup

- Baseline config/run:
  `configs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r15.yaml`
  and
  `runs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r15`.
- R16 config/run:
  `configs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r16.yaml`
  and
  `runs/layer1_siliconflow_qwen3_14b_typed_hop_identity_targeted8_20260713_r16`.
- The only non-identity config delta is
  `slot_binding_verifier_max_tokens: 1536 -> 2304`.
- Dataset, samples, retriever, model, maximum rounds, evaluator, metrics, code,
  and feature flags are unchanged.
- The valid network execution used the preserved retry7 stdout/stderr logs.
  It completed `8/8` in 1036.1 seconds with exit code zero and zero-byte
  stderr.
- Earlier retries that produced no sample are preserved. They record account
  balance, Windows process-host, and sandbox-network failures; they are not
  experimental observations.

## Results

| Metric | R15 | R16 | Delta |
| --- | ---: | ---: | ---: |
| accuracy / F1 | 0.375 / 0.375 | 0.375 / 0.375 | 0 |
| coverage | 0.375 | 0.375 | 0 |
| selective accuracy / F1 | 1.0 / 1.0 | 1.0 / 1.0 | 0 |
| average retrieval calls | 2.625 | 2.500 | -0.125 |
| reported wasted retrieval | 0.875 | 0.625 | -0.250 |
| final answered unsupported | 0 | 0 | 0 |
| 2-hop accuracy / coverage | 1.0 / 1.0 | 1.0 / 1.0 | 0 |
| 3-hop accuracy / coverage | 0 / 0 | 0 / 0 | 0 |
| 4-hop accuracy / coverage | 0 / 0 | 0 / 0 | 0 |

R16 made 20 retrieval calls versus 21 in R15. The only per-sample call-count
change was `1952: 3 -> 2`; all answer/abstain outcomes were unchanged. Under
the current sample-level wasted metric, samples containing a zero-gain call
dropped from `7/8` to `5/8`. At the follow-up-call level, zero-gain calls
dropped from `7/13` to `5/12` (53.8% to 41.7%).

Per-sample outcome:

- correct and retained: `June 1982`, `18th`, `Nissan Altima`;
- abstained: `Mario Andretti` (both samples), `1952`, `two`, and `NBC`;
- no wrong final answer was emitted.

## Structural acceptance evidence

The token-budget hypothesis is supported:

- verifier invoked: `20/20` trajectory rounds;
- structured generation attempts: `29`;
- `finish_reason=stop`: `29/29`;
- `finish_reason=length`: `0`;
- actual verifier parse failure: `0`;
- `required_hops_malformed`: `0`;
- `topology_update_rejected`: `0`;
- non-finite metrics: `0`;
- final answered unsupported: `0`.

Sentinel bookkeeping also remained safe:

- `sentinel_candidate_ignored` transition events: `10`;
- sentinel candidate-observed/selected transitions: `0`;
- sentinel values retained in candidate state: `0`.

The remaining topology diagnostics are semantic signals rather than malformed
output: `ambiguous_target_mapping` occurred in 13 rounds,
`sentinel_candidate_ignored` in 11 rounds, and `hop_binding_failure` in three
rounds. Nissan still performed exactly one allowlisted
`topology_revision_applied` transition and answered `Nissan Altima` from the
query `What model of Nissan does Mohammed Atta have?`.

## Failure analysis

### 1. `1952`: valid final value, invalid bridge chain

The verifier now parses successfully and recognizes `1952` as a year-shaped
final answer. The final death hop is verified, but the generated topology
still requires unresolved `named_after`, `same_as`, and `governor_of` hops.
It introduces the semantically wrong bridge `Saint Peter -> same_as -> San
Feliciano`, then treats the supported Foligno Cathedral/Foligno hops as hard
conflicts. The round-2 query `Mantua Cathedral named_after` has zero evidence
gain, and the controller safely terminates with
`hard_conflict_blocks_repair_and_answer`.

The lower call count is therefore early conflict termination, not quality
recovery. The next fix belongs in relation decomposition and evidence-to-hop
conflict attribution, not in token budgeting or final-answer safety.

### 2. NBC: country identity does not propagate to program identity

Round 1 recognizes `NBC` as a direct final-answer candidate, but correctly
refuses to bind it while the country chain is incomplete. Later topology state
mixes `country A`, `Moscow`, and `Philippines`: the `country A` node carries a
Moscow identity while its object becomes Philippines, and the final program
subject is fixed as `The Biggest Loser (Philippines version)`. Consequently,
the controller retrieves the Philippines version twice and never establishes
the required country-A-to-program-version identity. Round 3 is zero-gain and
ends at the retrieval budget.

This is a cross-round entity-identity and typed country/network-chain problem.
The larger verifier response is well formed but cannot repair the wrong
semantic binding.

### 3. Arizona Mario: final candidate found, bridge evidence not bound

The previously truncated round now parses and labels `Mario Andretti` as a
direct final-answer candidate. It still leaves the Arizona-largest-city,
Phoenix-hosted-race, and race-winner hops incomplete. The controller therefore
rejects the answer at budget exhaustion. This is safe behavior, but it exposes
an evidence-attribution gap: retrieved Phoenix/race evidence is not converted
into certificates for the intermediate hops.

### 4. Remaining 4-hop failures

- The `two` sample changes its set-elimination anchor from Sony Music
  Entertainment to Universal Music Group but still cannot bind headquarters
  location and the final count; its last call is zero-gain.
- The East Coasting sample retrieves Charles Mingus and his origin-state
  evidence, yet the state continues to mark the first performer hop unresolved
  and emits `hop_binding_failure` in all three rounds. This is a typed
  requirement/evidence binding failure, not lack of verifier output space.

## Claim validation

| Claim | Evidence | Verdict |
| --- | --- | --- |
| 2304 tokens eliminate R15 length truncation | 29/29 attempts stop; zero length/parse failures | supported |
| Safety remains intact | final unsupported 0; no sentinel candidate transition | supported |
| Existing 2-hop recoveries remain intact | 3/3 correct, including Nissan | supported |
| `1952` is restored | still abstains | refuted |
| At least one 4-hop sample is recovered | 0/3 correct | refuted |
| R16 is ready to scale | targeted quality gate fails | refuted |

## Conclusion and decision

Verdict: **partial success; token-budget gate passed; overall R16 gate failed**.

R16 answers its single-variable research question cleanly: 1536 tokens were
insufficient, while 2304 eliminates all observed truncation without weakening
safety and slightly improves retrieval efficiency. However, removing the
formatting bottleneck reveals the next true bottleneck: semantic topology and
cross-round entity/evidence binding. Accuracy and coverage do not improve,
`1952` remains rejected, and 4-hop accuracy remains zero.

Do not run stratified45. The next targeted implementation should keep 2304
tokens fixed and address, in order: (1) the 1952 relation/conflict topology,
(2) NBC country-to-program entity identity, and (3) evidence certificate
binding for Arizona and East Coasting. A new targeted gate must recover
`1952` and at least one 4-hop sample while retaining all current structural and
safety invariants before any scale run is authorized.
