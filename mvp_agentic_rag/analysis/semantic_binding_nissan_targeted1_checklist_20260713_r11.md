# Nissan model-chain provenance targeted1 checklist (R11)

- [x] Preserve the R10 method, retrieval, API, and evaluator contract.
- [x] Add regression coverage for topology repair plus model-chain provenance.
- [x] Pass full tests: 560 tests and 27 subtests.
- [x] Pass `python -m compileall -q src`.
- [x] Pass relevant `git diff --check`.
- [x] Create a unique targeted1 config and output path.
- [x] Execute the real SiliconFlow targeted1 run.
- [x] Verify final answer/action and acceptance provenance.
- [x] Verify final unsupported rate remains zero.
- [x] Update the R10 result report and topology diagnostic checklist.
- [x] Decide whether the targeted gate is stable enough to consider a later
  stratified45 run.

Decision: the code-actionable targeted gate is stable. R10 passes Rotterdam,
NBC, Liam, Mickey, and Timor; the post-R10 R11 run passes Nissan with separate
topology-repair and deterministic-binding provenance. Arizona remains an
evaluation-contract audit item. A new stratified45 run may now be planned.
