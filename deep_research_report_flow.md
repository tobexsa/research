# Agentic RAG 与 Deep Research 汇报稿

> 汇报主题：从 RAG 到 Agentic RAG，再到 Deep Research  
> 汇报框架：RAG 基础 -> RAG 痛点 -> Agentic RAG -> Deep Research -> Deep Research 详细流程与可靠性评估  
> 文件日期：2026-06-22

## 0. 汇报总思路

这次汇报可以围绕一条主线展开：

> 普通 RAG 解决的是“让大模型查资料再回答”；Agentic RAG 进一步解决“查什么、怎么查、查错了怎么办”；Deep Research 则把这种能力扩展成一个完整的研究型 Agent 流程，能够规划任务、浏览网页、读取 PDF、解释图表、运行 Python、综合多源信息，并生成带引用的研究报告。

建议汇报结构：

1. 介绍 RAG。
2. 介绍 RAG 的痛点，引出 Agentic RAG。
3. 介绍 Agentic RAG 与普通 RAG 的不同。
4. 介绍 Deep Research。
5. 详细讲解 Deep Research：
   - Agent 如何根据初步发现调整检索策略；
   - 如何浏览网页、读取 PDF、解释图表、运行 Python、综合多源信息；
   - Research Agent 如何给出引用、处理不确定性、避免编造来源；
   - Deep Research 类产品对学生科研、文献调研、竞品分析的启发；
   - 如何评估一份 Agent 生成研究报告的可靠性。

## 1. 第一部分：介绍 RAG

### 1.1 这一部分要讲什么

这一部分的目标是让听众先理解 RAG 的基本概念：为什么大模型需要外部知识，RAG 如何把“检索”和“生成”结合起来。

### 1.2 可以这样开场

大语言模型本身有两个明显限制：

1. 它的知识来自训练数据，可能过时。
2. 它生成内容时不一定知道自己不知道，容易产生幻觉。

RAG，也就是 Retrieval-Augmented Generation，检索增强生成，就是为了解决这个问题而提出的一类方法。它的核心思想是：在模型回答问题之前，先从外部知识库中检索相关资料，再把这些资料连同用户问题一起输入给大模型，让模型基于检索结果生成答案。

### 1.3 普通 RAG 的基本流程

普通 RAG 的流程可以概括为：

```text
用户问题
  -> 查询改写或向量化
  -> 从知识库中检索 Top-k 文档
  -> 将检索文档拼接到 Prompt
  -> LLM 基于上下文生成答案
```

也可以画成：

```text
Question -> Retriever -> Retrieved Documents -> Generator -> Answer
```

### 1.4 RAG 的关键组成

| 模块 | 作用 |
|---|---|
| 文档库 | 存放外部知识，例如论文、网页、企业文档、FAQ |
| 索引 | 把文档切分并转成可检索形式，例如向量索引、倒排索引 |
| 检索器 | 根据用户问题找出相关片段 |
| 生成器 | 将问题和检索内容输入 LLM，生成最终答案 |
| 引用或来源 | 标明答案依据哪些文档片段 |

### 1.5 RAG 的价值

RAG 的价值主要有三点：

1. **知识更新更方便**  
   不需要重新训练模型，只要更新知识库，就可以让系统回答新内容。

2. **减少幻觉**  
   模型不是只依赖参数记忆，而是可以参考外部文档。

3. **提高可追溯性**  
   如果系统能给出来源，用户就可以检查答案是否真的来自文档。

### 1.6 推荐论文

1. **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks**  
   Patrick Lewis et al., 2020  
   链接：https://arxiv.org/abs/2005.11401  
   用途：RAG 的经典基础论文，提出把参数化知识和非参数化知识结合起来。

2. **Retrieval-Augmented Generation for Large Language Models: A Survey**  
   Yunfan Gao et al., 2023  
   链接：https://arxiv.org/abs/2312.10997  
   用途：系统梳理 Naive RAG、Advanced RAG 和 Modular RAG。

### 1.7 过渡到下一部分

可以这样过渡：

> RAG 确实缓解了大模型知识过时和幻觉的问题，但它并不是万能的。普通 RAG 很大程度上仍然是一个固定流程：检索一次，然后生成一次。对于复杂研究任务，这种固定流程会暴露出很多问题。

## 2. 第二部分：RAG 的痛点，引出 Agentic RAG

### 2.1 这一部分要讲什么

这一部分要说明：普通 RAG 为什么不足以完成复杂研究任务。只有把痛点讲清楚，后面引出 Agentic RAG 才自然。

### 2.2 普通 RAG 的主要痛点

#### 痛点一：一次检索可能检索不到关键资料

普通 RAG 通常根据用户问题直接检索 Top-k 文档。如果用户问题表达不清，或者问题本身需要多个子问题，检索器可能找不到真正关键的资料。

例如用户问：

> Deep Research 对学生科研有什么启发？

这个问题其实包含多个子问题：

- Deep Research 是什么？
- 它和普通搜索有什么不同？
- 它有哪些技术流程？
- 学生科研场景中哪些环节可以被辅助？
- 它有什么风险？

如果只用原始问题检索一次，很可能只找到一些产品介绍，而不是完整的技术和应用分析。

#### 痛点二：复杂问题需要多跳推理

很多研究问题不是一个文档就能回答的，而是需要多步推理。

例如：

> 某个 Deep Research 产品是否适合做文献调研？

要回答这个问题，需要先查产品功能，再查它是否支持引用、PDF、网页浏览、多轮搜索、文件上传、数据分析，还要看它的局限性和评测结果。这不是一次检索可以完成的。

#### 痛点三：检索结果质量无法自动判断

普通 RAG 常常默认检索到的文档是有用的。但实际情况可能是：

- 文档过时；
- 文档只是二手转述；
- 文档和问题只有表面相关；
- 文档之间互相冲突；
- 文档内容本身不可靠。

如果模型不判断检索结果质量，就可能基于错误材料生成看似合理的答案。

#### 痛点四：缺少动态调整能力

普通 RAG 的流程通常比较固定：

```text
检索 -> 生成
```

但真实研究过程往往是：

```text
初步搜索 -> 阅读 -> 发现新线索 -> 改关键词
       -> 再搜索 -> 对比来源 -> 补充验证
       -> 发现冲突 -> 回到原始资料
```

也就是说，复杂研究需要“边查边改策略”。

#### 痛点五：普通 RAG 难以调用多种工具

普通 RAG 通常只会查文本知识库，而 Deep Research 类任务可能需要：

- 浏览网页；
- 读取 PDF；
- 解释图表；
- 提取表格；
- 运行 Python；
- 调用数据库；
- 比较多个来源；
- 生成带引用报告。

这些能力已经超出了传统 RAG 的固定管道。

### 2.3 引出 Agentic RAG

因此，研究者开始把 Agent 的能力引入 RAG。也就是说，不再让 RAG 只是一个固定的检索生成流程，而是让大模型成为一个可以规划、行动、观察和反思的控制器。

可以这样总结：

> 普通 RAG 的问题不只是“检索不够准”，而是它缺少主动研究能力。Agentic RAG 的目标，就是让系统能够自己判断下一步该查什么、是否需要换关键词、是否需要调用工具、是否需要验证来源。



## 3. 第三部分：Agentic RAG 与普通 RAG 的不同

### 3.1 这一部分要讲什么

这一部分要明确区分两个概念：普通 RAG 是固定管道，Agentic RAG 是由 Agent 控制的动态研究流程。

### 3.2 核心区别

| 对比维度 | 普通 RAG | Agentic RAG |
|---|---|---|
| 工作方式 | 固定流程 | 动态决策 |
| 检索次数 | 通常一次或固定多次 | 多轮、按需检索 |
| 查询生成 | 主要来自用户原问题 | Agent 会拆解问题、改写查询、扩展关键词 |
| 工具使用 | 多数只查知识库 | 可调用搜索、浏览器、PDF 解析器、Python、API |
| 信息判断 | 默认检索结果可用 | 会评估来源质量、相关性和冲突 |
| 适用任务 | 简单问答、企业知识库 QA | 多跳研究、调研报告、竞品分析、文献综述 |
| 输出形式 | 答案为主 | 答案、证据链、引用、不确定性说明、研究过程 |

### 3.3 Agentic RAG 的典型循环

Agentic RAG 可以用一个循环表示：

```text
Plan -> Search -> Read -> Reflect -> Revise Query -> Search Again -> Synthesize
```

或者：

```text
思考：我需要知道什么？
行动：调用搜索或工具。
观察：阅读返回结果。
反思：结果是否足够？是否可靠？是否需要继续查？
调整：改写查询、换来源、调用新工具。
生成：整合证据并回答。
```

### 3.4 一个具体例子

问题：

> Deep Research 类产品对学生科研有什么帮助？

普通 RAG 可能会：

```text
检索 “Deep Research 学生科研”
-> 找到几篇介绍文章
-> 总结成答案
```

Agentic RAG 会：

```text
1. 先拆解问题：
   - Deep Research 是什么？
   - 学生科研有哪些环节？
   - 文献调研、论文阅读、实验复现、写作分别能否被辅助？
   - 风险是什么？

2. 初步搜索：
   - Deep Research official
   - Deep Research agent paper
   - AI web research agent benchmark

3. 阅读后发现还需要引用质量评估：
   - 搜索 ALCE、FActScore、RAGTruth

4. 发现还涉及 PDF 和图表：
   - 搜索 DocVQA、ChartQA、DePlot

5. 最后综合：
   - 给出应用启发；
   - 标注风险；
   - 给出可靠性评估方法。
```

这个例子说明：Agentic RAG 不是简单扩大 Top-k，而是改变了整个研究流程。

### 3.5 推荐论文

1. **Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG**  
   链接：https://arxiv.org/abs/2501.09136  
   用途：系统理解 Agentic RAG 的概念、分类和应用。

2. **Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity**  
   链接：https://arxiv.org/abs/2403.14403  
   用途：说明系统可以根据问题复杂度选择不同检索策略。

3. **Toolformer: Language Models Can Teach Themselves to Use Tools**  
   链接：https://arxiv.org/abs/2302.04761  
   用途：理解大模型如何学习调用外部工具。

## 4. 第四部分：介绍 Deep Research

### 4.1 这一部分要讲什么

这一部分要把 Deep Research 放到 Agentic RAG 之后讲：Deep Research 可以看作 Agentic RAG 在开放网页、多文档、多工具、长任务研究场景中的产品化和系统化。

### 4.2 Deep Research 是什么

Deep Research 指的是一类能够自动完成复杂调研任务的 AI Research Agent。它通常具备以下能力：

- 根据用户问题生成研究计划；
- 使用搜索引擎或网页浏览工具查找信息；
- 打开并阅读网页、PDF、报告和文档；
- 从图表、表格、图片中提取信息；
- 必要时运行 Python 进行计算、清洗数据和绘图；
- 对多个来源进行交叉验证；
- 最后生成带引用的结构化研究报告。

可以用一句话定义：

> Deep Research 是一种面向复杂开放问题的研究型 Agent 系统，它把搜索、阅读、推理、工具调用、证据管理和报告写作整合成一个端到端流程。

### 4.3 Deep Research 与普通搜索、普通 RAG、Agentic RAG 的关系

| 类型 | 主要能力 | 局限 |
|---|---|---|
| 普通搜索 | 返回网页链接 | 用户需要自己筛选、阅读、综合 |
| 普通 RAG | 检索文档后生成答案 | 通常缺少动态研究和多工具能力 |
| Agentic RAG | 动态检索、反思、工具调用 | 偏技术范式，不一定形成完整研究产品 |
| Deep Research | 规划、搜索、阅读、计算、验证、写报告 | 仍可能幻觉、错引、漏检，需要复核 |

### 4.4 Deep Research 相关代表论文

1. **Deep Research: A Systematic Survey**  
   链接：https://arxiv.org/abs/2512.02038  
   用途：最适合作为 Deep Research 全流程的总纲论文。论文将 Deep Research 拆成 query planning、information acquisition、memory management 和 answer generation。

2. **Deep Research Agents: A Systematic Examination And Roadmap**  
   链接：https://arxiv.org/abs/2506.18096  
   用途：从系统架构角度分析 Deep Research Agent，包括动态推理、长期规划、多跳检索、工具使用和结构化报告生成。

3. **DeepResearcher: Scaling Deep Research via Reinforcement Learning in Real-world Environments**  
   链接：https://arxiv.org/abs/2504.03160  
   用途：研究如何在真实网页环境中训练 Deep Research Agent。论文强调真实网页交互、多源交叉验证、自我反思和无法确定时保持诚实。

4. **Deep Research Bench: Evaluating AI Web Research Agents**  
   链接：https://arxiv.org/abs/2506.06287  
   用途：评估 AI Web Research Agent 的多步网页研究能力、幻觉、工具使用和遗忘问题。

### 4.5 过渡到第五部分

可以这样过渡：

> 接下来我们不只把 Deep Research 当成一个产品功能，而是拆开看它背后的完整流程：它如何决定查什么，如何处理网页、PDF、图表和数据，如何生成引用，如何处理不确定性，以及我们应该如何评估它生成的报告是否可靠。

## 5. 第五部分：详细讲解 Deep Research

## 5.1 Agent 如何根据初步发现调整检索策略

### 5.1.1 这一部分要讲什么

这里要说明 Deep Research 与普通搜索最大的不同：它不是一次性搜索，而是根据已经读到的信息不断改变检索策略。

### 5.1.2 典型流程

```text
用户提出研究目标
  -> Agent 拆解问题
  -> 生成初始查询
  -> 搜索并阅读初步来源
  -> 判断信息是否足够、是否可靠、是否冲突
  -> 生成新的查询或切换来源
  -> 重复搜索和阅读
  -> 汇总证据并形成结论
```

### 5.1.3 查询策略如何调整

Agent 调整检索策略通常有几种方式：

1. **从宽泛查询到精确查询**  
   例如先搜 `Deep Research AI agent`，再搜 `Deep Research Bench Evaluating AI Web Research Agents`。

2. **从产品介绍转向论文和评测**  
   如果初步搜索大多是新闻或博客，Agent 会进一步查 arXiv、官方文档、benchmark。

3. **从概念查询转向具体实体**  
   例如查到 DeepResearcher 之后，继续查它的 GitHub、作者、实验设置、benchmark。

4. **从单一关键词扩展到相关模块**  
   例如研究 Deep Research 时，会进一步查：
   - Agentic RAG；
   - tool use；
   - citation evaluation；
   - chart understanding；
   - factuality evaluation。

5. **根据冲突信息进行反查**  
   如果两个来源对同一功能描述不同，Agent 应优先回到官方文档或原论文。

### 5.1.4 可放 PPT 的例子

研究问题：

> Deep Research 类产品如何保证报告可靠？

Agent 的检索路径可能是：

```text
Deep Research official
  -> 发现产品强调 citations 和 web browsing
  -> 搜索 AI web research agent benchmark
  -> 找到 Deep Research Bench
  -> 发现问题包括 hallucination、tool use、forgetting
  -> 搜索 citation evaluation LLM
  -> 找到 ALCE
  -> 搜索 factual precision long form generation
  -> 找到 FActScore
  -> 最后形成“引用 + 事实核查 + 多源交叉验证”的评估框架
```

### 5.1.5 推荐论文

1. **ReAct**  
   https://arxiv.org/abs/2210.03629  
   关键词：reasoning and acting。

2. **IRCoT**  
   https://arxiv.org/abs/2212.10509  
   关键词：interleaving retrieval and reasoning。

3. **Self-RAG**  
   https://arxiv.org/abs/2310.11511  
   关键词：retrieve、generate、critique。

4. **DeepResearcher**  
   https://arxiv.org/abs/2504.03160  
   关键词：真实网页环境、强化学习、多源交叉验证、自我反思。

## 5.2 浏览网页、读取 PDF、解释图表、运行 Python、综合多源信息的流程

### 5.2.1 这一部分要讲什么

这一部分要把 Deep Research 的“研究动作”讲具体。它不是抽象地说“查资料”，而是分成网页、PDF、图表、Python 和多源综合几个步骤。

### 5.2.2 浏览网页

浏览网页时，Agent 不应该只看搜索结果摘要，而应该实际打开网页并判断：

- 这个网页是不是一手来源？
- 发布时间是什么？
- 是否过时？
- 是否只是转述？
- 是否有数据、表格或原始报告？
- 页面中的结论是否和其他来源一致？

网页浏览的关键不是“打开页面”，而是“判断页面是否值得信任”。

### 5.2.3 读取 PDF

PDF 通常包括论文、白皮书、技术报告、财报、政策文件。Agent 需要识别：

- 标题和摘要；
- 方法部分；
- 实验设置；
- 结果表格；
- 图表和图注；
- limitations；
- references。

对于论文 PDF，不能只读摘要，因为很多限制和实验细节在正文、表格或附录里。

### 5.2.4 解释图表

图表理解需要至少检查：

- 图表标题；
- 横轴和纵轴含义；
- 单位；
- 图例；
- 趋势；
- 异常点；
- 作者在图注中的解释；
- 图表能支持什么结论，不能支持什么结论。

例如，一个柱状图显示某方法在某 benchmark 上得分更高，只能说明该 benchmark 上的结果更好，不能直接推出它在所有场景都更好。

### 5.2.5 运行 Python

Python 在 Deep Research 中常用于：

| 场景 | Python 的作用 |
|---|---|
| 表格整理 | 合并多个来源的数据 |
| 数据清洗 | 统一单位、时间、币种、字段名 |
| 统计计算 | 计算增长率、均值、比例、排名 |
| 可视化 | 生成趋势图、对比图、分布图 |
| 复核结论 | 检查报告中的数字是否算对 |

例如竞品分析中，不同产品价格可能按月、按年、按 token、按席位计费。Agent 需要把这些口径统一后，才能进行合理比较。

### 5.2.6 综合多源信息

多源综合不是简单拼接来源，而是要解决五个问题：

1. 哪些结论被多个来源支持？
2. 哪些来源之间存在冲突？
3. 哪些来源更权威？
4. 哪些信息已经过时？
5. 哪些结论只是推断，不能写成事实？

可以用证据表组织：

| 结论 | 支持来源 | 来源类型 | 可信度 | 备注 |
|---|---|---|---|---|
| Deep Research 可用于多步网页研究 | 官方文档、系统论文 | 官方/论文 | 高 | 需注明产品版本和日期 |
| Deep Research 报告仍可能有幻觉 | 官方限制说明、评测论文 | 官方/论文 | 高 | 需要人类复核 |
| 某产品一定优于另一产品 | 单篇博客 | 博客 | 低 | 不应作为确定结论 |

### 5.2.7 推荐论文

1. **DocVQA: A Dataset for VQA on Document Images**  
   https://arxiv.org/abs/2007.00398  
   用途：文档图像理解。

2. **MMDocIR: Benchmarking Multi-Modal Retrieval for Long Documents**  
   https://arxiv.org/abs/2501.08828  
   用途：长文档、多模态检索。

3. **ChartQA: A Benchmark for Question Answering about Charts**  
   https://arxiv.org/abs/2203.10244  
   用途：图表问答。

4. **DePlot: One-shot Visual Language Reasoning by Plot-to-Table Translation**  
   https://arxiv.org/abs/2212.10505  
   用途：把图表转换为表格后推理。

5. **Toolformer**  
   https://arxiv.org/abs/2302.04761  
   用途：工具调用。

6. **Gorilla**  
   https://arxiv.org/abs/2305.15334  
   用途：API 调用和工具使用。

## 5.3 Research Agent 如何给出引用、处理不确定性、避免编造来源

### 5.3.1 为什么引用很重要

Deep Research 报告看起来通常很完整，但报告是否可靠不取决于文字是否流畅，而取决于每个关键结论是否可以追溯到真实来源。

因此，引用不是装饰，而是可靠性的核心。

### 5.3.2 好引用应该是什么样

好的引用应该满足：

1. 来源真实存在。
2. 链接可以打开。
3. 来源内容确实支持这句话。
4. 关键事实尽量引用一手来源。
5. 对数字、日期、产品功能、论文结论等具体信息给出精确来源。

可以分三层：

| 层级 | 含义 | 例子 |
|---|---|---|
| 来源级引用 | 标明用了哪些资料 | 报告末尾列出论文和网页 |
| 段落级引用 | 某段分析对应几个来源 | 一段产品分析后放 2-3 个来源 |
| 主张级引用 | 每个关键事实都有来源 | 某产品发布时间、功能、价格、benchmark 分数 |

最可靠的是主张级引用。

### 5.3.3 如何处理不确定性

Deep Research 中的不确定性主要有四类：

| 不确定性类型 | 例子 | 正确处理方式 |
|---|---|---|
| 证据不足 | 没找到官方说明 | 写“未找到公开证据” |
| 来源冲突 | 不同来源给出不同日期 | 列出冲突，优先官方来源 |
| 信息过时 | 产品功能和价格变化 | 标注访问日期 |
| 推断不确定 | 从多个迹象推测技术路线 | 明确写“推测”或“可能” |

可靠的 Research Agent 应该敢于说：

```text
目前证据不足，无法确认。
公开资料中没有找到直接支持。
不同来源存在冲突，需要以官方文档为准。
以下是基于现有来源的推断，而不是确定事实。
```

### 5.3.4 如何避免编造来源

避免编造来源可以用这几条规则：

1. **只引用实际打开并检查过的来源。**
2. **不凭模型记忆编论文名、作者、年份或 DOI。**
3. **引用前检查来源是否真的支持当前句子。**
4. **优先引用原论文、官方文档、原始数据。**
5. **不要把搜索结果摘要当作证据。**
6. **对关键结论做交叉验证。**
7. **保留检索轨迹和访问日期。**

### 5.3.5 推荐论文

1. **ALCE: Enabling Large Language Models to Generate Text with Citations**  
   https://arxiv.org/abs/2305.14627  
   用途：评估带引用长文本生成。

2. **FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation**  
   https://arxiv.org/abs/2305.14251  
   用途：把长文本拆成原子事实逐条验证。

3. **RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models**  
   https://arxiv.org/abs/2401.00396  
   用途：说明 RAG 系统仍可能生成不被检索内容支持的幻觉。

4. **Deep Research Bench**  
   https://arxiv.org/abs/2506.06287  
   用途：评估 AI Web Research Agent 的幻觉、工具使用和长任务表现。

## 5.4 Deep Research 类产品对学生科研、文献调研、竞品分析的启发

### 5.4.1 对学生科研的启发

Deep Research 对学生科研最重要的启发不是“让 AI 代写论文”，而是把 AI 当作研究流程加速器。

它可以帮助学生：

1. **快速建立领域地图**  
   找出一个方向中的核心概念、代表论文、常用数据集、评价指标和主流方法。

2. **做文献初筛**  
   把论文按任务、方法、数据集、年份、贡献和局限性分类。

3. **发现研究空白**  
   总结多篇论文的 limitations，找到共同问题。

4. **准备复现实验**  
   查找代码仓库、数据集、baseline、依赖环境和实验设置。

5. **辅助写作结构**  
   帮助整理 related work、实验对比表、研究问题和论文大纲。

但必须强调：

> Deep Research 可以辅助科研流程，但不能替代学生阅读原文、判断贡献、设计实验和承担学术责任。

### 5.4.2 对文献调研的启发

传统文献调研依赖人工关键词搜索和滚雪球式查找。Deep Research 的启发是：文献调研可以变成一个更系统的流程。

可以采用：

```text
确定主题
  -> 找 survey 和代表论文
  -> 提取关键词、作者、数据集、方法名
  -> 追踪引用和被引用
  -> 建立文献矩阵
  -> 总结方法演进和研究空白
```

文献矩阵可以包括：

| 论文 | 年份 | 任务 | 方法 | 数据集 | 指标 | 贡献 | 局限 | 是否有代码 |
|---|---|---|---|---|---|---|---|---|

这样比单纯堆论文摘要更适合做综述。

### 5.4.3 对竞品分析的启发

竞品分析中，信息往往来自多个来源：

- 官方网站；
- 价格页；
- 产品文档；
- 新闻报道；
- 用户评价；
- 第三方评测；
- 财报或公告；
- API 文档。

Deep Research 可以把竞品分析组织成：

```text
确定竞品集合
  -> 确定比较维度
  -> 收集官方资料
  -> 补充第三方评测和用户反馈
  -> 统一价格、功能和时间口径
  -> 生成对比表
  -> 标注不确定信息
```

比较维度可以包括：

| 维度 | 示例 |
|---|---|
| 功能 | 是否支持网页浏览、文件上传、PDF、图表、Python |
| 成本 | 订阅价格、API 价格、使用限制 |
| 质量 | 引用质量、报告深度、覆盖范围 |
| 速度 | 生成报告所需时间 |
| 可控性 | 是否能修改研究计划、限定来源 |
| 企业能力 | 权限、隐私、内部知识库连接 |

需要提醒：

> 竞品分析中的产品功能、价格和限制变化很快，所以必须标注查询日期，不能把旧信息当成当前事实。

## 5.5 如何评估一份 Agent 生成研究报告的可靠性

### 5.5.1 评估原则

评估 Agent 研究报告时，不能只看语言是否流畅，也不能只看结构是否完整。真正重要的是：

```text
结论是否有证据？
证据是否真实？
引用是否支持结论？
是否覆盖关键来源？
是否处理冲突和不确定性？
是否可以被复核？
```

### 5.5.2 可靠性评分表

可以用 100 分评分：

| 维度 | 分值 | 检查问题 |
|---|---:|---|
| 来源真实性 | 15 | 链接是否存在？是否能打开？来源是否真实？ |
| 引用支撑度 | 20 | 每个关键结论是否被引用直接支持？ |
| 来源质量 | 15 | 是否优先使用论文、官方文档、原始数据？ |
| 覆盖完整性 | 15 | 是否覆盖主流观点、反例、最新进展和关键竞品？ |
| 冲突处理 | 10 | 遇到来源冲突时是否说明？ |
| 不确定性表达 | 10 | 是否区分事实、推断、假设和未知？ |
| 方法透明度 | 10 | 是否说明检索范围、时间、筛选标准？ |
| 可复现性 | 5 | 他人能否按来源和方法复核报告？ |

### 5.5.3 五步复核法

实际使用中，可以用五步快速复核：

1. **抽查关键事实**  
   随机抽 10 个关键事实，包括数字、日期、论文结论、产品功能。

2. **打开引用链接**  
   检查链接是否真实存在，内容是否支持报告中的说法。

3. **查找遗漏来源**  
   看报告是否漏掉重要论文、官方文档、主流竞品或反方证据。

4. **检查冲突处理**  
   如果不同来源说法不一致，报告是否明确说明。

5. **要求证据表**  
   让 Agent 输出“结论-证据-来源-可信度-备注”表格。

### 5.5.4 低可靠报告的信号

如果一份 Agent 生成报告出现以下情况，要特别警惕：

- 引用链接打不开；
- 引用内容和结论无关；
- 大量使用“有研究表明”但不说明研究是谁；
- 把博客当成论文证据；
- 没有访问日期；
- 对快速变化的信息给出确定结论；
- 只给支持证据，不给反例或限制；
- 没有说明哪些结论不确定；
- 文风很流畅，但没有证据表。

### 5.5.5 推荐论文

1. **Deep Research Bench: Evaluating AI Web Research Agents**  
   https://arxiv.org/abs/2506.06287  
   用途：评估 Web Research Agent 的多步研究能力、幻觉、工具使用和遗忘。

2. **GAIA: a benchmark for General AI Assistants**  
   https://arxiv.org/abs/2311.12983  
   用途：评估真实世界问题中的网页浏览、工具使用、多步推理和多模态能力。

3. **FActScore**  
   https://arxiv.org/abs/2305.14251  
   用途：原子事实级别的事实核查。

4. **ALCE**  
   https://arxiv.org/abs/2305.14627  
   用途：评估引用质量。

## 6. PPT 建议页结构

### 第 1 页：标题

```text
从 RAG 到 Agentic RAG，再到 Deep Research
```

副标题：

```text
检索增强、研究型 Agent 与可信报告生成
```

### 第 2 页：RAG 是什么

讲：

- 大模型知识过时和幻觉问题；
- RAG 的基本思想；
- RAG 流程图。

图：

```text
Question -> Retriever -> Documents -> LLM -> Answer
```

### 第 3 页：普通 RAG 的痛点

讲：

- 一次检索可能找不到关键资料；
- 复杂问题需要多跳推理；
- 检索结果质量难判断；
- 缺少动态调整；
- 难以调用网页、PDF、Python 等工具。

### 第 4 页：Agentic RAG 的出现

讲：

- Agent 成为控制器；
- 可以规划、检索、观察、反思、再检索；
- 从固定管道变成动态研究流程。

图：

```text
Plan -> Search -> Read -> Reflect -> Revise -> Search Again -> Answer
```

### 第 5 页：Agentic RAG vs 普通 RAG

放对比表：

| 普通 RAG | Agentic RAG |
|---|---|
| 固定流程 | 动态决策 |
| 一次检索 | 多轮检索 |
| 查知识库 | 调用多工具 |
| 答案为主 | 答案 + 证据链 |

### 第 6 页：Deep Research 是什么

讲：

- Deep Research 是研究型 Agent；
- 可以规划、搜索、阅读、计算、验证、写报告；
- 是 Agentic RAG 在复杂开放研究任务中的产品化。

### 第 7 页：Deep Research 全流程

放流程图：

```text
Task -> Plan -> Search -> Browse -> Read PDF/Charts
     -> Python Analysis -> Cross-check -> Evidence Memory
     -> Report with Citations -> Reliability Review
```

### 第 8 页：动态检索策略

讲：

- 从宽泛查询到精确查询；
- 从新闻/博客转向论文/官方文档；
- 根据冲突信息回查原始来源；
- 根据发现扩展新关键词。

### 第 9 页：网页、PDF、图表、Python

讲：

- 网页：判断来源质量；
- PDF：读方法、实验、表格、局限；
- 图表：看坐标轴、单位、趋势；
- Python：清洗数据、计算、绘图、复核数字。

### 第 10 页：引用与不确定性

讲：

- 引用要支撑具体主张；
- 区分事实、推断、未知；
- 来源冲突要说明；
- 不足证据不能硬答。

### 第 11 页：对科研、文献调研、竞品分析的启发

讲：

- 学生科研：建立领域地图、筛论文、找空白；
- 文献调研：文献矩阵、引用追踪、方法演进；
- 竞品分析：功能、价格、质量、限制、访问日期。

### 第 12 页：如何评估可靠性

放评分表：

- 来源真实性；
- 引用支撑度；
- 来源质量；
- 覆盖完整性；
- 冲突处理；
- 不确定性表达；
- 方法透明度；
- 可复现性。

### 第 13 页：论文推荐

按类别列：

- RAG：Lewis 2020, Gao Survey；
- Agentic RAG：ReAct, IRCoT, Self-RAG, CRAG；
- Deep Research：Deep Research Survey, DeepResearcher, Deep Research Bench；
- 引用与事实性：ALCE, FActScore, RAGTruth；
- 多模态文档：DocVQA, ChartQA, DePlot。

### 第 14 页：总结

可直接放 PPT：

```text
RAG 让大模型能够基于外部知识回答问题；
Agentic RAG 让系统能够主动规划、检索、反思和调用工具；
Deep Research 则把这些能力组合成完整研究流程，
能够完成网页浏览、PDF 阅读、图表理解、Python 分析、
多源综合和带引用报告生成。

但 Deep Research 不是自动真理机。
它的可靠性必须通过来源、引用、交叉验证、
不确定性说明和人类复核来保证。
```

## 7. 最小论文阅读清单

如果时间有限，建议重点读 8 篇：

1. **Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks**  
   https://arxiv.org/abs/2005.11401  
   RAG 基础。

2. **Retrieval-Augmented Generation for Large Language Models: A Survey**  
   https://arxiv.org/abs/2312.10997  
   RAG 综述。

3. **ReAct: Synergizing Reasoning and Acting in Language Models**  
   https://arxiv.org/abs/2210.03629  
   Agent 推理与行动。

4. **Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection**  
   https://arxiv.org/abs/2310.11511  
   检索、生成和自我批评。

5. **Deep Research: A Systematic Survey**  
   https://arxiv.org/abs/2512.02038  
   Deep Research 全流程总览。

6. **DeepResearcher: Scaling Deep Research via Reinforcement Learning in Real-world Environments**  
   https://arxiv.org/abs/2504.03160  
   真实网页环境中的 Deep Research Agent。

7. **Deep Research Bench: Evaluating AI Web Research Agents**  
   https://arxiv.org/abs/2506.06287  
   Deep Research Agent 评估。

8. **FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation**  
   https://arxiv.org/abs/2305.14251  
   长报告事实性评估。

## 8. 汇报结尾可以这样说

> 从 RAG 到 Agentic RAG，再到 Deep Research，本质上是从“检索增强回答”走向“自动化研究流程”。  
>  
> 普通 RAG 解决的是让模型参考外部知识；Agentic RAG 解决的是让模型主动决定如何查、查什么、是否需要修正；Deep Research 则进一步把网页浏览、PDF 阅读、图表理解、Python 分析、多源综合和引用报告整合起来。  
>  
> 但越像研究助理，就越需要严格评估。我们不能只看报告是否流畅，而要看证据链是否真实、引用是否支撑结论、是否处理不确定性，以及人类是否能够复核。

