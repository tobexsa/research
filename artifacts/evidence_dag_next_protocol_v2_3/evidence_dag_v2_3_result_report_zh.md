# Evidence-DAG 下一阶段实验协议 V2.3 结果报告

## 摘要结论

本轮按照 `evidence_dag_next_experiment_protocol_v2_3.md` 在远程服务器 `10.18.19.171` 的隔离 worktree 中完成了安全阶段、机器化 Preflight、P1 结构路线、P4 Retriever Oracle Gate 和可独立执行的 P5 R0 Oracle attribution。最终结论不是“系统已经可上线”，而是获得了一个更精确、可复现的故障边界：

1. SiliconFlow 的 `provider_json_schema` 确实能够在固定复制任务上稳定约束 `Pro/Qwen/Qwen2.5-7B-Instruct`。P0A 216/216 通过；P0B 六类真实 schema 的 Canonical JSON 和 Schema Semantic Match 为 432/432；标准端点 P0C 为 216/216。
2. 上述结果不能外推到真实问题条件下的语义规划。Route A 为 0/60，Route B C2P 为 7/60，Oracle Pairwise C4A 只有 1/60 exact graph。真实输入会触发两类相互独立的失败：83/362 次 whitespace-loop 截断，以及 279 个 schema-valid 输出中的 187 个语义错误。
3. 自动 Span Candidate 召回不够。Normalized 和 Alias-Resolved Recall 均为 68/90（75.56%），未达到 98% 硬门槛，因此 P2B/P2C 的自动 span/binding 路线不能进入候选。
4. 检索器不是当前首要瓶颈。在 corpus/index/target 完全匹配后，BGE dense 的 Gold-query Recall@10 为 182/200（91.0%），All-Steps Recall 为 44/60（73.3%），timeout 为 0，P4 gate 通过。
5. 下游 Oracle 路径部分可用。P5 R0 在 Gold Plan/Query、dense retriever、Oracle extractor/validator 下达到 182/200 resolved steps、178/200 supporting-document recall、50/60 Answer Ready/EM，且 cross-hypothesis mix 为 0。

最终决策：**停止并归档当前 Qwen2.5-7B Planner 候选；不运行 Internal-Holdout-A/B，不解冻 Confirmation-120，不重新启用模型 Extraction/Validation 或 Strong Validator rollout。** 可保留 P4/R0 下游基础设施；只有在 Planner/Span 的前置 gate 被新的、明确冻结的方案真正通过后，才重新进入 holdout。

## 1. 实验范围与可审计边界

- 远程分支：`analysis/evidence-dag-next-protocol-v2-3`
- 隔离 worktree：`/root/worktrees/evidence-dag-next-protocol-v2-3`
- 主要模型：`Pro/Qwen/Qwen2.5-7B-Instruct`
- P0C 匹配端点：`Qwen/Qwen2.5-7B-Instruct`
- API：SiliconFlow Chat Completions
- 温度：0
- 解析策略：严格 JSON、无 malformed repair
- 主开发评估集：Diagnostic-Dev-60，六拓扑各 10 条
- 新增模型 API 调用：1,238 次，包括 12 次 P0 smoke、864 次正式 P0、362 次 P1
- 复用 V1 baseline：D1/C1 和 D2/C2O 各 60 条；未重复调用
- P4/P5：本地 BGE/FAISS 与 deterministic/Oracle 组件，零 LLM 调用
- Internal-Holdout-A/B：仅构造并冻结，未被模型查询
- Confirmation-120：仅用于 exclusion/audit，`confirmation_touched_by_model=false`

协议规定在 Machine Validation 前只能执行 G0、P0、P2A 和 E0；本轮严格遵守。P1 只在 clean-tree Preflight 通过后启动。P4/P5 只运行与失败 Planner 独立的 Oracle 组件切片。

## 2. 实现与机器验证

本轮新增或强化了以下实现：

- V2.3 ontology、六类 canonical P0 schema、span generator、GoldGraphSet 和 CanonicalGraphMatcher。
- G0 holdout feasibility audit、P0 runner、P1 structural runner、P2A span runner、P4 Retriever Oracle runner、P5 R0 runner。
- `manifest.schema.json`、`freeze_lock.schema.json`、`raw_record.schema.json`、`metrics.schema.json`。
- repository-local Preflight validator，适配远程环境未安装第三方 `jsonschema` 的事实。
- Preflight 除 schema 外还拒绝 placeholder、required null、hash mismatch、dirty tree、holdout reuse、budget mismatch、Gold-policy conflict、unfair comparison、schema/version mismatch。
- 在审查中进一步补上跨产物 identity、raw record count、重复 `request_id` 校验，防止不同实验的合法文件被错误拼接后仍显示通过。
- CanonicalGraphMatcher 的最终 exact gate 现在同时要求结构、relation semantics 和 output/source type；旧实现只看结构，可能错误接受 relation/type 不匹配。

最终测试：focused tests 在最后切片为 34/34，通过完整回归 829/829。所有正式 P0/P1/P4/P5 metrics bundle 均通过机器校验。

## 3. G0：Internal Holdout 可行性

### 3.1 构造结果

| 独立性级别 | 200 次确定性有界构造 | 最少拓扑候选 | 结果 |
|---|---:|---:|---|
| Strict | 4hop2 仅 1/12 | 1 | 未达到配额 |
| Compositional | 六拓扑均 12/12 | 12 | 可行 |
| Lexical | 六拓扑均 12/12 | 12 | 可行 |

因此实际冻结级别为 **Compositional**，不能在报告中称为 Strict。A/B 各 36 条，每个拓扑各 6 条，A/B Sample ID 无交集。

### 3.2 交集审计

| 字段 | pairwise overlap |
|---|---:|
| Sample ID | 0 |
| Complete decomposition | 0 |
| Source passage | 0 |
| Normalized near duplicate | 2 |
| Answer entity | 56 |
| Base subquestion ID | 174 |

结论：MuSiQue 的组件复用使 Strict 独立性在固定有界搜索内不可构造；Compositional 是本轮能诚实声明的最强级别。Strict 的“不可行”是 200 次有界构造结果，不是数学不可能性证明。

## 4. P0：Decoder 与 Schema Envelope

### 4.1 P0A Minimal Decoder（Pro）

| 模式 | N | Task/Canonical/Semantic | Stop | Length | Repetition |
|---|---:|---:|---:|---:|---:|
| Plain Text | 72 | 72/72 | 72/72 | 0 | 0 |
| Plain JSON | 72 | 72/72 | 72/72 | 0 | 0 |
| Provider JSON Schema | 72 | 72/72 | 72/72 | 0 | 0 |
| 合计 | 216 | 216/216 | 216/216 | 0 | 0 |

### 4.2 P0B 六类真实 Schema（Pro）

| Schema | Byte Exact | Canonical JSON | Schema Semantic |
|---|---:|---:|---:|
| Topology | 72/72 | 72/72 | 72/72 |
| Hop | 72/72 | 72/72 | 72/72 |
| Shape | 72/72 | 72/72 | 72/72 |
| Slot | 72/72 | 72/72 | 72/72 |
| Query | 0/72 | 72/72 | 72/72 |
| Validator | 72/72 | 72/72 | 72/72 |
| 合计 | 360/432 | 432/432 | 432/432 |

Query 的 Byte Exact 失败是稳定序列化格式差异；对象内容与 schema semantics 完全一致。因此按协议主 gate，P0B 通过。

### 4.3 P0C Backend/Endpoint Isolation（Standard）

标准端点三种模式均为 72/72，合计 216/216 exact/stop，0 length、0 repetition。固定 payload 任务上没有观察到 Pro 与 Standard 的系统级差异。

### 4.4 P0 回答的问题

- API 是否接受真正的 `json_schema` 请求：**是**。
- API 是否能稳定生成固定合法 schema payload：**是**。
- 因此 Full Planner 失败是否仅由“不支持 json_schema”解释：**否**。
- P0 是否证明真实问题下的语义分类可用：**否，P1 明确反证**。

## 5. P2A：Span Candidate

| 指标 | 全计划分母 | 结果 |
|---|---:|---:|
| Gold annotation resolved | 90 | 89/90（98.89%） |
| Literal span recall | 90 | 60/90（66.67%） |
| Normalized span recall | 90 | 68/90（75.56%） |
| Alias-resolved recall | 90 | 68/90（75.56%） |
| Non-NER phrase recall | 23 | 16/23（69.57%） |

只在 89 个 resolved annotation 上计算的 conditional recall 为 68/89（76.40%），仍远低于 98%。最终 gate 使用全计划分母，不能用 conditional 口径掩盖失败。

按拓扑看，2hop 为 100%，而 4hop1/4hop2/4hop3 分别为 50%/65%/70%。结论：当前 question-only NER/NP/rule generator 不能支撑 P2B 自动 slot/binding。

## 6. E0：Canonical Matcher 与不变量

E0 覆盖了六拓扑的 node ID rename、root order、merge-parent order、identity removal、alternative valid DAG，以及以下拒绝条件：missing relation semantics、extra non-identity step、wrong source/output type、wrong merge、invalid answer sink。

该切片在 focused suite 中通过，完整回归也通过。它支持“评估器与 deterministic graph invariants 可用”，但不代表模型能够生成正确图。

## 7. P1：真实结构路线

P1 在 clean-tree Preflight 后运行。C1/D1 和 C2O/D2 从完全匹配的 V1 Diagnostic-60 baseline 附加复用；Route A、C2P、C4A 新调用 362 次。

| 路线 | 主结果 | Invalid | 其他 |
|---|---:|---:|---|
| Route A Direct Topology | 0/60（0%） | 50/60 | Macro-F1 0；多数基线 10/60 |
| C1 Hop Count（attached） | 24/60（40%） | 8/60 | 2/3/4 分类 |
| C2O Gold-Hop Shape，3/4-hop | 7/50（14%） | 31/50 | Oracle diagnostic |
| C2P Predicted Hop→Shape | 7/60（11.67%） | 18/60 | Macro-F1 0.0751；1.8667 calls/question |
| C4A Oracle Pairwise | 85/250（34%） | 23/250 | 2/60 globally consistent |
| C4A Exact Graph | 1/60（1.67%） | — | Mean Edge F1 0.025 |

### 7.1 Decoder failure与 semantic failure 分离

362 次新调用全部 transport success，因此不是网络失败。

- 83/362 次 `finish=length`。
- 原始输出不是普通词语重复，而是在 `{` 或一个合法字段后持续生成空格、换行和制表符，直至 128-token 上限；lexical repeated-token detector 为 0，但 raw head/tail 明确显示 whitespace loop。
- 279 次 schema-valid 输出中有 187 次 valid-but-semantically-wrong。

因此只提高 `max_tokens` 最多影响 whitespace-loop 截断，不能解决大量合法但错误的分类。P0 的固定复制成功和 P1 的语义失败可以同时成立。

### 7.2 P1 决策

Route A、Route B 和 Pairwise Route C 的局部上限均不可用。没有任何候选可进入 Internal Holdout。该结论使用所有计划样本，不对 parse-valid 子集做选择性汇报。

## 8. P4：Retriever Oracle Gate

### 8.1 被排除的数据契约事故

第一次 P4 使用了旧的 6,000-passage corpus/index，Diagnostic-60 的 200 个 Gold target 只有 11 个存在于该 index，得到的 9/200 Recall@10 无效。该运行已保留在 `p4_retriever_oracle_dense_invalid_contract`，但从最终指标中排除。

修复没有改变模型或 top-k：使用相同本地 BGE snapshot 对冻结的 3,720-passage Diagnostic corpus 重建 FAISS index，并在 runner 中加入 fail-closed contract：corpus IDs 必须等于 index IDs，且 Gold targets 必须覆盖 200/200。

### 8.2 有效结果

| 指标 | 结果 | Gate |
|---|---:|---:|
| Step Recall@10 | 182/200（91.0%） | ≥75%，通过 |
| All-Steps Recall | 44/60（73.3%） | ≥60%，通过 |
| Timeout | 0/200 | 必须为 0，通过 |
| Merge Joint Recall | 21/30（70.0%） | Dev 描述性冻结 |
| MRR@10 | 0.6658 | 描述性 |

按拓扑的 All-Steps Recall：2hop 90%、3hop1 90%、3hop2 90%、4hop1 50%、4hop2 50%、4hop3 70%。检索仍对长链/merge 有损失，但在 Gold-query 条件下通过正式门槛，不能解释 Planner 近零的结构准确率。

## 9. P5 R0：Oracle Ladder

R0 使用 Gold Plan、Gold relation/query template、运行时 Gold prior binding、contract-matched BGE top-10、ExplicitValueExtractor 和 deterministic Oracle validation，零 LLM 调用。

| 指标 | 结果 |
|---|---:|
| Evaluated | 60/60 |
| Resolved steps | 182/200（91.0%） |
| Supporting-document recall in executed path | 178/200（89.0%） |
| Answer Ready | 50/60（83.33%） |
| Answer EM/F1 | 50/60（83.33%） |
| Cross-hypothesis mix | 0/60 |
| Physical retrieval calls | 192 |

相对于 pure Oracle Engine 六 fixture 的 6/6，R0 的 10/60 Answer loss 表明真实 retrieval/extraction coverage 仍造成可测损失；但 R0 是上限诊断，不能替代 production Planner。

## 10. 总 Gate 矩阵

| 阶段 | 状态 | 决策 |
|---|---|---|
| G0 Holdout feasibility | 通过，Compositional | A/B 已保留但未使用 |
| Machine Validation | 通过 | 允许在冻结配置下运行 P1+ |
| P0A Minimal Decoder | 通过 | 固定 payload decoder 可用 |
| P0B Schema Envelope | 通过 | 六 schema canonical/semantic 432/432 |
| P0C Endpoint Isolation | 通过 | fixed-copy 无明显 endpoint 差异 |
| E0 Matcher/Invariant | 通过 | 评估器与 invariants 可用 |
| P2A Span Candidate | **失败** | 阻断 P2B/P2C automatic span/binding |
| P1 Route A | **失败** | 不可提升 |
| P1 Route B C2P | **失败** | 低于多数基线，不可提升 |
| P1 C4A Oracle Pairwise | **失败** | 1/60 exact，不可提升 |
| P3 Strong Model | Blocked | 未冻结/授权精确 comparator；未替换 |
| P4 Retriever Oracle | 通过 | Gold-query retrieval 不是首要瓶颈 |
| P5 E0/R0 | E0 通过；R0 部分支持 | 仅 component upper bound |
| P4 Query factorial | Blocked | Predicted relation/binding prerequisite 失败 |
| P5 R1/X0/X1/X2/V0/V1 | Blocked/Skipped | production Planner/Span 与 strong validator 前置条件不满足 |
| Internal Holdout A/B | 未运行 | 无合格候选，保持一次性预算 |
| Confirmation-120 | 未运行 | 保持冻结，未被模型触碰 |

## 11. Claim Ledger

### 11.1 稳定支持

- SiliconFlow 对该模型支持可执行的 `json_schema` fixed-payload envelope。
- 机器化 manifest/freeze/raw/metrics gate 能拒绝主要不安全状态。
- Canonical matcher 和六拓扑 invariants 在 fixture/property tests 上成立。
- Contract-matched BGE 在 Gold-query 条件下通过 P4 gate。
- Oracle Engine/R0 保持 cross-hypothesis isolation，且 downstream upper bound 明显高于 Planner 路线。

### 11.2 部分支持

- Compositional holdout 可构造；Strict 只得到有界搜索的失败证据。
- R0 Answer Ready/EM 为 83.3%，说明下游大部分可执行，但不是完美。
- Retriever 在总体 gate 上通过，但 4hop1/4hop2 All-Steps 仅 50%。

### 11.3 明确反证

- “只要 provider 支持 json_schema，7B Planner 就会可用”：反证。
- Direct Topology、Hop→Shape、Oracle Pairwise 能产生可提升候选：反证。
- 当前 automatic span generator 达到生产 gate：反证。
- 当前失败只是 transport 或普通 lexical repetition：反证。

### 11.4 未决与阻断

- 失败中模型权重、provider guided-decoding backend、量化/服务实现各占多少：未决；provider 不披露 revision/backend。
- 更强模型是否越过结构/语义边界：未决；没有精确冻结的 strong comparator。
- 本地 grammar-constrained decoding 能否消除 whitespace loop：未测；即使消除也不能自动解决 187 个 valid-but-wrong。
- model Extractor/Validator 和 Strong Validator 的真实收益：因 Planner gate 关闭而未运行。
- Internal Holdout 和 Confirmation 的端到端指标：有意未运行。

## 12. 局限性

1. Diagnostic-Dev-60 规模有限，每拓扑 10 条；它适合诊断与 gate，不适合宣称广泛泛化。
2. Internal Holdout 只能达到 Compositional，不具备 Strict 的所有隔离属性。
3. 模型服务 revision、量化、guided-decoding backend 和 seed 不可见，因此结果是 SiliconFlow endpoint/system-level 证据，不是纯模型权重结论。
4. P0 是固定复制任务，只回答 schema envelope，不测语义理解。
5. P2A Gold span annotation 由 Gold decomposition 辅助算法产生，并非双人独立人工标注。
6. P4/R0 使用 Gold queries/values，是组件上限，不是 production end-to-end。
7. Strong model、model extractor、standard/strong validator 没有满足冻结与前置 gate，不能对其收益做正负推断。
8. 本轮未运行 Internal Holdout/Confirmation，因此不能报告任何 holdout/confirmation answer metric。

## 13. 最终建议与重开条件

### 13.1 当前动作

**停止并归档当前 `Pro/Qwen/Qwen2.5-7B-Instruct` Planner 路线。** 保留 P4/R0 检索与 Engine 资产，不再对当前 prompt 做微调式迭代，不消费一次性 holdout/confirmation。

### 13.2 推荐的下一实现路线

优先级从高到低：

1. 若必须继续同一模型，先在本地或明确披露的服务中使用真正 grammar-constrained decoding，针对 whitespace-only continuation 做独立 decoder 诊断；同时保持严格 parser 作为最终 gate。
2. 不把 grammar 修复当作语义修复。只有在真实问题上的 Route A/B/C 或新的 typed DSL 达到明显高于多数基线、低 invalid、稳定 macro-F1 后，才重开候选。
3. 将自动 span generator 的全计划 Normalized/Alias Recall 提升到 ≥98%，并保留 non-NER hard negatives；未达标前不进入 P2B/P2C。
4. 若改用强模型，必须先明确模型全名、endpoint/backend、预算和 freeze lock；禁止静默替换。
5. 只有当 Diagnostic gate 同时满足结构路线、span/binding、预算和机器校验时，才一次性运行 Internal-Holdout-A；候选通过后再冻结 Internal-Holdout-B/Confirmation 流程。

### 13.3 不应重复的工作

- 不再证明 API 是否接受 fixed `json_schema`；P0 已有 864 次正式调用证据。
- 不重复当前 Route A/B/C prompt；全分母负结果已稳定。
- 不把 P4 第一次 9/200 的无效结果带入任何比较。
- 不使用 Confirmation-120 调 prompt 或选择候选。

## 14. 关键产物与复现

主目录：`analysis/evidence_dag_next_protocol_v2_3/`

- `PLAN.md` / `CHECKLIST.md`：执行边界、冻结与进度。
- `g0_holdout_feasibility/`：A/B、corpus、feasibility report、overlap ledger。
- `preflight/`：P0/P1/P2A/P4/P5 manifests 和 freeze locks。
- `p0a_pro/`、`p0b_pro/`、`p0c_standard/`：raw JSONL 与 metrics。
- `p2a_span_candidates/`：automatic/oracle candidates、evaluation 和 metrics。
- `p1_structural_pro/`：362 条 raw、C2P/C4A evaluation、error analysis、claim validation。
- `p4_retriever_oracle_dense_invalid_contract/`：保留但排除的 data-contract incident run。
- `p4_retriever_oracle_dense/`：有效 200-step records、metrics 与 gate report。
- `p5_r0_gold_query_dense_oracle_extractor/`：R0 records、metrics 与报告。
- `post_preflight_decision.md`、`post_p1_decision.md`、`p4_data_contract_incident.md`：关键决策与故障历史。

主要提交链从 `40b56c1` 开始，当前结果提交为 `93c9d68`，最终报告将在其后单独提交。完整测试命令最终结果：`829 passed`。

## 15. 最终状态

- 协议中当前可执行且前置条件满足的实验：已完成。
- 协议中依赖失败 gate 或缺失明确授权的实验：已明确 blocked/skipped。
- Internal Holdout：已构造、未消费。
- Confirmation-120：冻结、未查询。
- 当前候选是否可进入 end-to-end smoke/holdout：**否**。
- 当前最可靠的科学结论：**固定 schema decoder 可用，但真实语义 Planner 不可用；Gold-query retrieval 与 Oracle downstream 大部分可用，瓶颈主要位于 Planner/Span/语义结构层。**
