# Evidence-DAG 下一步实验方案 V2.3

> 适用系统：Evidence-DAG V1.1b  
> 当前状态：7B Full Planner Gate 关闭；Oracle Engine 可独立推进  
> 目标：在固定预算和机器可验证冻结条件下，隔离 Decoder、Planner、Span、Binding、Query、Retriever、Extractor、Validator 和 Engine 的独立影响  
> 版本状态：候选冻结协议

---

# 0. V2.3 修订摘要

V2.3 在 V2.2 基础上新增：

1. `G0-Holdout Feasibility Audit`，明确 Strict / Compositional / Lexical Holdout；
2. 预留 `Internal-Holdout-A` 与 `Internal-Holdout-B`；
3. Route B 增加真实链路 `C2P: Predicted Hop → Shape`；
4. Route C 增加预算内 `C4B-Batched` 邻接矩阵输出；
5. Semantic Ontology 拆分为 `EntityType / ArgumentRole / OperationSignature`；
6. 恢复 `CanonicalGraphMatcher` 和 Alternative Valid DAG；
7. Query 实验改为 Relation × Binding 二维因子设计；
8. 区分 Teacher-Forced Step 与 Autoregressive Rollout；
9. 所有 Query Variant 固定检索调用和文档预算；
10. Oracle Ladder 拆成 Extractor 与 Validator 两层；
11. Strong Validator 增加离线候选 Replay 和在线 Rollout；
12. P0B 按真实 Schema 分别运行；
13. Span Oracle 使用 Hard Negatives 和 Alias Sets；
14. Argument Coverage 拆分 Literal / Normalized / Alias-Resolved；
15. 新增 `internal_holdout_freeze_lock.json`；
16. Freeze Lock 增加 Ontology、Graph Matcher、Span Generator、Query Builder、Trigger 等版本；
17. 新增 JSON Schema 和 Preflight 机器校验；
18. 明确所有 Metric 的定义、分母和条件指标。

---

# 1. 数据与独立性

## 1.1 Diagnostic-Dev-60

原 Diagnostic-60 全部归为开发集，可反复运行。

## 1.2 G0-Holdout Feasibility Audit

在构造 Holdout 前输出：

```text
holdout_feasibility_report.md
holdout_overlap_ledger.csv
```

至少统计：

```text
Sample ID overlap
Complete decomposition overlap
Base subquestion ID overlap
Normalized question near-duplicate
Answer entity overlap
Source passage overlap
Topology availability
```

定义三种等级：

| 等级 | 要求 |
|---|---|
| Strict | Base subquestion ID 也不重叠 |
| Compositional | 完整 decomposition 不重叠，但允许部分 Base ID 重叠 |
| Lexical | 仅保证 Sample ID、完整问题和完整 decomposition 不重叠 |

必须在报告中写明实际等级。

## 1.3 Internal-Holdout-A / B

优先各构造：

```text
每种拓扑 6 条
总计 36 条
```

规则：

```text
A 用于第一次正式内部验证
A 失败后不得再次作为无偏 Holdout
新版本正式验证使用 B
```

若只能构造一套 Holdout，失败后的后续结果必须标记 `exploratory_after_holdout`。

## 1.4 Confirmation-120

保持冻结，只在 Confirmation Freeze Lock 后运行一次。

---

# 2. 执行顺序

```text
G0 Holdout Feasibility
P0A Minimal Decoder
P0B-Topology / Hop / Shape / Slot / Query / Validator
P0C Backend Isolation
        ↓
P1 Route A Direct Topology
P1 Route B C1 + C2O + C2P
P1 C4A Oracle Pairwise
        ↓
P2A Span Candidate
P2B Compiler-Owned Slot
P2C C4B-Sequential / C4B-Batched
        ↓
P3 Strong Model / Routing / Budget
        ↓
P4 Retriever Oracle Gate
P4 Relation × Binding Query Factorial
P4 Equal-Budget Rewrite
        ↓
P5 E0 / R0 / R1 / X0A / X0B / X1A / X1B / X2A / X2B / V0 / V1
        ↓
internal_holdout_freeze_lock.json
        ↓
Internal-Holdout-A 一次性运行
        ↓
confirmation_freeze_lock.json
        ↓
Confirmation-120
```

---

# 3. P0 Decoder 与 Schema Envelope

## 3.1 P0A

每种模式 72 次，总计 216 次：

```text
Plain Text
Plain JSON
Provider JSON Schema
```

每种模式要求：

```text
72/72 Exact
72/72 Stop
0 Length
0 Repetition
```

## 3.2 P0B 按 Schema 分开

分别运行：

```text
P0B-Topology
P0B-Hop
P0B-Shape
P0B-Slot
P0B-Query
P0B-Validator
```

每个 Schema 提供一个完全合法 Canonical Payload。

同时报告：

```text
Byte Exact Match
Canonical JSON Match
Schema Semantic Match
```

主 Gate 使用 Canonical JSON Match 和 Schema Semantic Match，不因空白和 Key 顺序失败。

---

# 4. P1 结构路线

## 4.1 Route A：Direct Topology

主指标：

```text
Macro-F1
Exact Match
Mode-Collapse Rate
Prediction Entropy
```

## 4.2 Route B：Hop + Shape

### C1 Hop Count

报告：

```text
Balanced Accuracy
Macro-F1
Per-Hop Recall
Majority Baseline
```

### C2O Gold Hop → Shape

Oracle 诊断，不代表生产。

2-Hop 只报告 Decoder；3-Hop 二分类；4-Hop 三分类。

### C2P Predicted Hop → Shape

真实 Route B：

```text
Question
→ C1 Predicted Hop
→ 根据 Predicted Hop 构造 Shape 候选
→ Shape Prediction
→ Compile Topology
```

正式 Gate 使用：

```text
End-to-End Topology Match
Macro-F1
Invalid Rate
Calls per Question
```

## 4.3 Route C：Pairwise Graph Recovery

### C4A Oracle Pairwise

输入 Gold Decomposition，仅作局部能力上限。

### C4B-Sequential

逐 Pair 调用，仅作诊断，不进入部署 Gate。

### C4B-Batched

一次输出固定邻接矩阵：

```json
{
  "relations": [
    ["self", "left_to_right", "independent"],
    ["right_to_left", "self", "left_to_right"],
    ["independent", "right_to_left", "self"]
  ]
}
```

确定性检查：

```text
Diagonal=self
Antisymmetry
No cycle
Transitive consistency
Unique answer sink
Allowed six-topology constraint
```

部署 Route C 只使用 Batched 版本。

---

# 5. Canonical Graph Matching

新增模块：

```text
CanonicalGraphMatcher
```

流程：

```text
Remove identity/formatting steps
Normalize operation semantics
Normalize output types
Enumerate all node mappings for 2–4 steps
Score semantic + structural alignment
Choose maximum valid alignment
Compare against Gold DAG and Alternative Valid DAGs
```

Gold 记录：

```python
@dataclass
class GoldGraphSet:
    primary_graph: CanonicalGraph
    alternative_valid_graphs: list[CanonicalGraph]
    ambiguous_gold: bool
```

允许：

```text
Root order swap
Node ID rename
Merge parent order swap
Equivalent relation wording
```

禁止：

```text
Missing required relation
Extra non-identity step
Wrong source type
Wrong merge position
Wrong answer sink
```

所有 Edge F1 和 Exact DAG 必须在对齐后计算。

---

# 6. P2A Span Candidate

## 6.1 Oracle Span Candidates

Oracle Candidate Set 必须包含 Hard Negatives：

```text
相同实体类型
相似长度
同样出现在原问题
同样可能承担关系参数
```

每个 Gold Input 保存：

```json
{
  "acceptable_spans": ["Oxford University", "University of Oxford"],
  "normalized_values": ["university of oxford"],
  "alias_sets": ["Oxford"]
}
```

## 6.2 Automatic Candidates

由 NER + NP Chunking + 规则生成，不得读 Gold。

## 6.3 Gate

```text
Normalized Span Recall ≥ 98%
Alias-Resolved Recall ≥ 98%
Non-NER Phrase Recall 达到冻结阈值
```

---

# 7. P2B Semantic Planner

## 7.1 Ontology 三层

### EntityType

```text
person
organization
location
date
number
work
event
object
boolean
other
```

### ArgumentRole

例如：

```text
subject_entity
target_entity
character_constraint
network_constraint
time_constraint
location_constraint
comparison_left
comparison_right
```

### OperationSignature

每个 Operation 定义：

```text
operation_id
argument roles
allowed entity types per role
output type
cardinality
relation direction
```

模型不能把 `actor/director/network` 当成 EntityType alias。

## 7.2 T0/T1/T2

### T0

Gold Graph + Gold Source Assignment，只测语义填槽。

### T1

Gold Shape + Predicted Source Assignment。

### T2

Predicted Shape + Predicted Source Assignment，真实 Planner。

## 7.3 Sequential 与 Batched

Sequential 仅作能力上限。

Batched 作为部署候选，固定数组长度和顺序。

## 7.4 Graph Semantic Validator

检查：

```text
Output type → downstream role compatibility
Role assignment completeness
Relation direction
Merge source distinctness
AnswerSpec compatibility
Duplicate/contradictory operation
```

---

# 8. P2C Graph Recovery

C4B 使用通过 Slot Contract 的 Operations。

必须报告：

```text
Operation Alignment Rate
End-to-End Edge F1
Edge F1 Given Correct Operations
Global Consistency
Exact Graph Recovery
Calls per Question
```

正式 Route C Gate 使用 `C4B-Batched`。

---

# 9. Planner Budget

部署候选：

```text
2-Hop Planner Calls ≤ 1
3-Hop Planner Calls ≤ 2
4-Hop Planner Calls ≤ 2
4-Hop Total LLM Calls ≤ 8
Strong Calls ≤ 2
```

报告：

```text
Calls
Prompt tokens
Completion tokens
P50/P90
Projected full-system budget
```

---

# 10. P4 Retriever 与 Query

## 10.1 Retriever Oracle Gate

Gold Query：

```text
Recall@10 ≥ 75%
All-Steps Recall ≥ 60%
Timeout = 0
```

Merge Joint Recall 阈值在 Dev 上冻结。

## 10.2 Relation × Binding 因子设计

| Relation Goal | Binding | 用途 |
|---|---|---|
| Gold | Gold | Query Builder 上限 |
| Predicted | Gold | Relation Goal 损失 |
| Gold | Predicted | Binding 传播损失 |
| Predicted | Predicted | 真实链路 |

同时分别运行：

```text
Teacher-Forced Step Evaluation
Autoregressive DAG Rollout
```

Teacher-Forced 每一步使用正确前序 Binding；Rollout 使用系统自己的中间结果。

## 10.3 Argument Coverage

区分：

```text
Literal Coverage
Normalized Coverage
Alias-Resolved Coverage
```

硬 Gate 使用 Normalized/Alias-Resolved，不要求原字符串逐字出现。

Alias 必须来自运行时可用词典或实体标准化器，不得读取 Gold Alias。

## 10.4 Equal-Budget Rewrite

所有 Query Variant 固定：

```text
Max retrieval calls
Max unique documents
Max passages
Max total top-k slots
```

报告：

```text
Recall per retrieval call
Recall per unique document
Recall–budget curve
MRR–cost curve
```

正式比较使用同文档预算下 Recall。

## 10.5 Runtime Trigger

使用 Hypothesis-Step 级状态：

```text
No new document for hypothesis-step
All top-k documents already evaluated by this step
Duplicate query key
Frozen normalized-score/rank-margin rule
```

---

# 11. P5 完整 Oracle Ladder

## 11.1 E0

Oracle Plan + Oracle Evidence + Oracle Extractor + Oracle Validator。

## 11.2 R0 / R1

```text
R0 = Gold Query + Target Retriever + Oracle Extractor + Oracle Validator
R1 = Deterministic Query + Target Retriever + Oracle Extractor + Oracle Validator
```

## 11.3 X0A / X0B

```text
X0A = Oracle Passages + 7B Extractor + Oracle Validator
X0B = Oracle Passages + 7B Extractor + Standard Validator
```

## 11.4 X1A / X1B

```text
X1A = Gold-Query Retrieved Passages + 7B Extractor + Oracle Validator
X1B = Gold-Query Retrieved Passages + 7B Extractor + Standard Validator
```

## 11.5 X2A / X2B

```text
X2A = Deterministic-Query Retrieved Passages + 7B Extractor + Oracle Validator
X2B = Deterministic-Query Retrieved Passages + 7B Extractor + Standard Validator
```

## 11.6 Validator Replay

### V0 Offline Paired Replay

固定同一批 Candidate：

```text
Frozen Candidate Set
→ Standard Validator
→ Strong Validator
```

测纯 Validator 差异。

### V1 Online Rollout

Strong Validator 进入真实控制流，测系统级收益。

## 11.7 因果归因

```text
E0 → R0       Retriever Loss
R0 → R1       Query Builder Loss
E0 → X0A      Extractor Loss
X0A → X0B     Standard Validator Loss
X0A → X1A     Retriever-Induced Extraction Loss
X1A → X2A     Query-Induced Extraction Loss
V0            Pure Validator Gain
X2B → V1      Online System Gain
```

---

# 12. Strong Validator 指标

```text
Acceptance Precision
Acceptance Recall
False Accept
False Reject
Merge Validation Accuracy
Final Validation Accuracy
Conflict Adjudication Accuracy
Answer Ready
Answer F1
```

通过条件：

```text
False Accept 显著下降
且 Acceptance Recall 下降不超过冻结容忍值
```

---

# 13. Internal Holdout Freeze

在运行 Holdout 前生成：

```text
internal_holdout_freeze_lock.json
```

冻结：

```text
candidate variants
prompt/schema/model/backend
ontology hash
graph matcher version
span generator version
query builder version
trigger config hash
retriever/index
budget
git commit
exact command
environment hash
```

Holdout 后不得修改同一候选。

---

# 14. Confirmation Freeze

Confirmation Lock 必须引用：

```text
candidate_configuration_sha256
internal_holdout_freeze_lock_sha256
```

每个 Variant 独立冻结配置。

---

# 15. Machine Validation

新增：

```text
manifest.schema.json
freeze_lock.schema.json
raw_record.schema.json
metrics.schema.json
```

Preflight：

```bash
python scripts/validate_experiment_preflight.py \
  --manifest manifest.json \
  --freeze-lock internal_holdout_freeze_lock.json
```

必须拒绝：

```text
Unresolved placeholders
Required nulls
Hash mismatch
Dirty git tree
Holdout already used
Budget mismatch
Gold policy conflict
Unverified fair comparison
Schema/version mismatch
```

---

# 16. 统计与报告

所有 Rate 保存：

```json
{"numerator": 54, "denominator": 60, "rate": 0.9}
```

主指标包含所有计划样本。

条件指标明确命名：

```text
Conditional-on-Parse
Conditional-on-Correct-Operation
Conditional-on-Executable
Conditional-on-Valid-Planner
```

---

# 17. Confirmation 端到端指标

```text
Answer EM/F1
Planner Valid
Structural Complete
Evidence Complete
Answer Ready
Merge Accuracy
Cross-Hypothesis Mix
Incomplete-DAG Answer
Abstention
Retrieval Calls
LLM Calls
Strong Calls
P50/P90
Runtime Gold Violations
```

报告视图：

```text
Pure DAG
DAG + Fallback
Conditional Valid Planner
Overall Including Planner Failure
```

---

# 18. 当前安全执行范围

在 V2.3 机器校验完成前，可执行：

```text
G0 Holdout Feasibility
P0A
P0B 各 Schema
P0C
P2A 数据标注和 Candidate Generator
E0 Fixture / Invariant / Property Tests
```

其余阶段必须通过 Preflight 后执行。
