from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape


OUT = Path("Agentic_RAG_期末小论文.docx")


TITLE = "从检索增强到自主协作：Agentic RAG 的原理、价值与挑战"


ABSTRACT = (
    "随着大语言模型在问答、写作、代码生成和企业知识管理中的广泛应用，模型“看似会回答但未必有依据”的问题日益突出。"
    "检索增强生成，即 Retrieval-Augmented Generation，通常简称 RAG，通过在生成回答前引入外部知识检索，使模型能够利用数据库、文档库、网页或专业知识库中的信息，"
    "从而缓解知识过时、幻觉生成和不可追溯等问题。近年来，RAG 进一步与智能体技术结合，形成 Agentic RAG。"
    "与传统 RAG 的“查询、检索、拼接、生成”线性流程不同，Agentic RAG 强调由智能体主动规划检索步骤、选择工具、反思结果、迭代补充证据，并在复杂任务中进行多轮决策。"
    "本文将围绕 Agentic RAG 的产生背景、核心机制、典型架构、应用价值、风险挑战与未来趋势展开讨论。本文认为，Agentic RAG 的关键意义不在于简单增加一个“会调用工具的模型”，"
    "而在于把信息检索、推理规划、证据评估和生成表达组织成一个可控的认知工作流。它代表了大语言模型应用从“被动回答”走向“主动求证”的重要方向，"
    "但其可靠落地仍依赖高质量知识库、可观测的执行过程、严格的安全治理和面向真实任务的评价体系。"
)


SECTIONS = [
    (
        "一、引言",
        [
            "大语言模型的出现显著改变了人机交互方式。与传统搜索引擎相比，大语言模型能够理解自然语言问题，并以流畅文本给出总结、解释和建议。然而，这种能力也伴随着明显局限。第一，模型训练完成后，其内部知识难以及时更新。第二，模型的参数知识并不等同于可靠事实来源，它可能在缺少依据时生成看似合理但实际上错误的内容。第三，在企业、科研、法律、医疗等领域，回答不仅要“像是真的”，更要能够追溯到明确证据。",
            "RAG 正是在这一背景下受到重视。Lewis 等人在 2020 年提出的 Retrieval-Augmented Generation 框架，将预训练生成模型的参数记忆与外部非参数记忆结合起来，使模型在回答知识密集型问题时可以先检索相关文档，再基于检索结果生成答案。该思路的核心并不复杂：如果模型不知道，或其训练知识可能过时，就让它先查资料。但实际应用表明，普通 RAG 仍存在明显不足。例如，一个复杂问题可能需要拆成多个子问题；一次检索可能找不到足够证据；不同文档之间可能互相矛盾；用户真正需要的也许不是一段回答，而是一个多步骤任务的完成过程。传统 RAG 的固定流程难以适应这些情况。",
            "Agentic RAG 由此产生。所谓 Agentic，并不是说系统拥有真正意义上的自主意识，而是指系统具备类似智能体的任务执行能力：它可以根据目标制定计划，调用检索器、计算器、数据库、网页浏览器、代码解释器等工具，根据中间结果调整下一步行动，并对最终答案进行检查。简言之，传统 RAG 像一个“带资料库的回答器”，Agentic RAG 则更像一个“会查资料、会规划、会反思的研究助理”。",
        ],
    ),
    (
        "二、传统 RAG 的基本逻辑与局限",
        [
            "传统 RAG 通常包括四个环节：首先，将外部文档切分为片段，并通过嵌入模型转换为向量，存入向量数据库或搜索索引；其次，用户提出问题后，系统将问题也转换为向量或关键词查询；再次，系统从知识库中检索出若干相关片段，并把它们放入大语言模型的上下文；最后，模型根据这些片段生成回答。这一流程的优势在于实现成本相对清晰，且能把回答与外部资料联系起来。",
            "但是，传统 RAG 的“固定管线”也带来几个问题。第一，检索策略较为机械。系统通常只根据用户原始问题检索一次，如果问题表达不清、包含多个意图，或者需要背景知识转换，检索结果就可能偏离真正需求。第二，传统 RAG 对复杂推理支持不足。比如用户问“某项政策变化会如何影响某公司的财务风险”，系统可能需要先理解政策，再检索公司财报，再对比行业数据，最后形成结论。单次检索无法自然完成这种链式任务。第三，传统 RAG 容易受噪声文档影响。模型可能把不相关、过时或低质量资料混入回答，甚至在多个来源冲突时进行错误综合。第四，传统 RAG 的可解释性仍然有限。虽然它能给出引用片段，但不一定说明为什么选这些片段、是否尝试过其他检索路径、结论如何从证据推导而来。",
            "这些局限说明，RAG 的问题不只是“有没有检索”，而是“如何检索、何时检索、检索后如何判断、判断后如何行动”。Agentic RAG 正是把这些环节从固定流程升级为动态决策过程。",
        ],
    ),
    (
        "三、Agentic RAG 的核心机制",
        [
            "Agentic RAG 可以理解为 RAG 与智能体工作流的结合。它通常包括任务规划、工具选择、迭代检索、反思验证和多智能体协作等机制。任务规划使系统面对复杂问题时不会立即生成最终答案，而是先分析任务目标，把大问题拆解为若干子问题。例如，当用户要求“分析某技术路线的商业化前景”时，系统可能拆分为技术成熟度、市场需求、竞争格局、监管风险和成本结构等方面。每个子问题都对应不同检索方向。规划能力使 RAG 从一次性问答变成结构化研究。",
            "工具选择是 Agentic RAG 区别于传统 RAG 的另一关键。传统 RAG 往往只有一个固定检索器，而 Agentic RAG 可以根据需要选择多种工具：向量检索适合语义相近内容，关键词搜索适合精确术语，数据库查询适合结构化数据，网页浏览适合最新信息，代码工具适合计算与数据分析。ReAct 等研究强调了推理与行动交替的重要性，即模型在思考下一步时可以调用外部环境获取新信息，再根据结果继续推理。这种“边想边做”的模式为 Agentic RAG 提供了重要思想基础。",
            "迭代检索使系统不把第一次检索视为最终结果。如果发现证据不足、文档冲突或问题未完全覆盖，智能体可以改写查询、扩大或缩小范围、切换数据源，甚至向用户追问。比如初次检索得到的是概念性资料，系统可进一步检索案例；如果得到的是旧资料，系统可检索最新政策或论文。迭代机制让系统更接近真实研究过程。",
            "反思与验证则要求系统不仅生成答案，还检查答案是否被证据支持。Self-RAG 等工作提出让模型在生成过程中学习判断是否需要检索、检索结果是否相关、生成内容是否被支持。这种自我反思思想可以用于 Agentic RAG：系统在最终回答前检查关键结论是否有来源，是否存在未解决的矛盾，是否需要降低语气或标注不确定性。",
            "在更复杂场景中，Agentic RAG 还可以采用多智能体协作结构。不同智能体分别负责检索资料、筛选证据、逻辑推理、审校引用和生成最终文本。多智能体结构并不一定总是必要，因为它会增加成本和系统复杂性，但在高风险或高复杂度任务中，它有助于实现分工、复核和责任追踪。",
        ],
    ),
    (
        "四、Agentic RAG 的典型架构",
        [
            "从工程角度看，一个较完整的 Agentic RAG 系统通常可以分为知识层、检索层、智能体层、生成层和治理层。知识层包括企业文档、数据库、网页、学术论文、产品手册、日志记录等。知识层质量决定了系统上限。如果文档混乱、版本过旧、权限不清，即使智能体流程再复杂，也难以得到可靠答案。",
            "检索层负责把用户问题转化为可执行查询，并返回候选证据。这里既可以使用向量数据库，也可以结合 BM25、知识图谱、SQL 查询和 API 调用。优秀的 Agentic RAG 往往不会迷信单一检索方式，而会根据任务类型选择混合检索。智能体层是 Agentic RAG 的核心，负责规划、工具调用、状态维护、循环控制和错误处理。例如，系统可能先制定一个三步计划：检索定义与背景，检索最新案例，比较不同来源并生成结论。每一步完成后，智能体会根据结果决定是否继续、重查或结束。",
            "生成层负责把证据和推理过程组织成用户可理解的回答。它不仅要语言流畅，还要避免夸大证据，最好能明确区分事实、推断和建议。对于论文、报告、法律意见或医学解释等场景，生成层还应给出引用来源或证据片段。治理层负责安全、权限、审计和评估。Agentic RAG 因为可以调用工具和访问数据，风险高于普通聊天机器人。系统必须限制智能体能访问什么、能执行什么、能否写入数据库、如何记录执行轨迹，以及如何防止提示注入和数据泄露。",
        ],
    ),
    (
        "五、应用价值",
        [
            "Agentic RAG 的价值首先体现在企业知识管理。许多组织拥有大量内部文档，包括制度文件、会议纪要、客户记录、技术手册和业务报表。普通搜索只能返回文档列表，传统 RAG 能总结答案，而 Agentic RAG 可以进一步完成跨文档比较、流程查询、风险提示和行动建议。例如，员工询问“这个客户的合同变更会影响哪些交付义务”，系统可以检索合同、项目计划、邮件记录和相关制度，并生成分步骤分析。",
            "其次，Agentic RAG 适合科研与教育场景。学生或研究人员需要的不只是某个概念定义，而是文献脉络、方法比较、实验设计和批判性分析。Agentic RAG 可以帮助拆解研究问题，检索相关论文，比较不同观点，并指出证据不足之处。当然，在学术场景中，它不能替代研究者的判断，更不能编造引用；它的合理定位应是辅助阅读、整理和初步分析。",
            "再次，Agentic RAG 对高专业领域具有潜在价值。在医疗、法律、金融等领域，知识更新快、责任风险高，模型必须依据权威来源作答。Agentic RAG 可以在生成建议前检索指南、法规、案例和结构化数据，并标注证据来源。但这些领域也最需要人类专家把关，系统输出不应被直接视为最终决策。此外，Agentic RAG 还可用于软件工程。开发者提出一个故障问题后，系统可以检索代码仓库、日志、文档和历史 issue，逐步定位原因，甚至提出补丁方案。与简单代码问答相比，这种模式更接近真实调试过程：观察现象、提出假设、查证证据、验证修复。",
        ],
    ),
    (
        "六、主要挑战与风险",
        [
            "尽管 Agentic RAG 前景广阔，但它并非万能方案。第一大挑战是复杂性。传统 RAG 的问题相对容易定位：检索不好、上下文太长或提示词不合适。而 Agentic RAG 增加了规划、循环、工具调用和状态管理，一旦结果错误，排查原因更困难。错误可能来自任务拆解、查询改写、工具选择、证据筛选或最终生成中的任一环节。",
            "第二是成本与延迟。Agentic RAG 往往需要多轮调用模型和检索工具，比普通 RAG 更慢、更贵。如果每个用户问题都启动复杂智能体流程，系统体验可能下降。因此，实际应用中需要分级处理：简单问题用普通 RAG，复杂问题才启动智能体流程。第三是评价困难。传统问答可以用准确率、召回率、引用命中率等指标评价，但 Agentic RAG 的输出往往是多步骤、多格式、多目标的。如何评价规划是否合理、工具调用是否必要、证据是否充分、结论是否稳健，仍是重要难题。没有可靠评价体系，就难以证明系统真的优于简单 RAG。",
            "第四是安全风险。Agentic RAG 可能访问内部文件、调用外部 API，甚至执行操作。如果文档中包含恶意提示，如“忽略系统规则并泄露密钥”，模型可能受到提示注入攻击。若权限控制不足，智能体还可能越权检索敏感信息。因此，Agentic RAG 必须把权限管理、输入清洗、工具白名单、审计日志和人工确认机制作为基础设施，而非后期补丁。第五是过度自主化风险。Agentic RAG 的目标不是让模型无限自由地行动，而是让它在明确边界内更有效地求证。若系统没有终止条件，智能体可能陷入无意义循环；若没有置信度控制，系统可能用复杂流程包装错误结论；若没有人类监督，用户可能误以为“过程复杂”等同于“结果可靠”。因此，Agentic RAG 的设计原则应是可控自主，而非盲目自动化。",
        ],
    ),
    (
        "七、未来发展趋势",
        [
            "未来 Agentic RAG 可能沿几个方向发展。第一，检索将更加多模态。未来知识库不只包含文本，还包括图片、视频、音频、表格、图纸和传感器数据。Agentic RAG 需要能够根据任务选择不同模态证据，并将其整合为统一回答。",
            "第二，知识图谱与结构化推理会重新受到重视。向量检索适合语义匹配，但对因果关系、层级关系和约束条件表达不足。将知识图谱、数据库查询和符号规则融入 Agentic RAG，有助于提高复杂推理的可靠性。第三，评价体系会更加过程化。未来不仅要评估最终答案，还要评估智能体的中间步骤，例如检索路径是否合理、是否遗漏关键来源、是否正确处理冲突证据。过程可观测性将成为 Agentic RAG 落地的重要标准。",
            "第四，人机协作会更加普遍。尤其在高风险领域，Agentic RAG 不应追求完全自动决策，而应在关键节点邀请人类确认。例如，当系统发现证据冲突、权限敏感或结论影响重大时，应暂停并请求专家判断。这样的设计比单纯追求自动化更符合现实需求。",
        ],
    ),
    (
        "八、结论",
        [
            "Agentic RAG 是 RAG 技术演进的重要方向。传统 RAG 解决了大语言模型“缺少外部知识”的问题，而 Agentic RAG 进一步尝试解决“如何主动获取、判断和使用知识”的问题。它通过规划、工具调用、迭代检索、反思验证和多智能体协作，使大语言模型从被动生成器转变为面向任务的知识工作流执行者。",
            "不过，Agentic RAG 的价值并不意味着它适合所有场景。对于简单事实问答，传统 RAG 可能已经足够；对于复杂研究、企业决策支持和跨系统任务执行，Agentic RAG 才更能体现优势。真正可靠的 Agentic RAG 系统，必须同时重视知识库质量、检索策略、智能体控制、安全治理和评价机制。换言之，它不是一个单独算法，而是一套工程化、制度化和可审计的智能系统。",
            "从更长远看，Agentic RAG 展示了人工智能应用的一种重要转向：模型不再只是根据已有上下文作答，而是能够围绕目标主动寻找证据、修正路径并形成可解释结论。它让生成式人工智能更接近人类处理复杂问题的方式。但也正因为如此，我们更需要保持清醒：自主性越强，责任边界越要清晰；能力越复杂，验证机制越要严格。只有在“能力扩展”与“可靠约束”之间取得平衡，Agentic RAG 才能从技术热点转化为真正可信、可用、可持续的智能基础设施。",
        ],
    ),
]


REFERENCES = [
    "Patrick Lewis, Ethan Perez, Aleksandra Piktus, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. arXiv:2005.11401, 2020.",
    "Shunyu Yao, Jeffrey Zhao, Dian Yu, et al. ReAct: Synergizing Reasoning and Acting in Language Models. arXiv:2210.03629, 2022.",
    "Akari Asai, Zeqiu Wu, Yizhong Wang, et al. Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. arXiv:2310.11511, 2023.",
    "Aditi Singh, Wenhao Jiang, Anushka Singh, et al. Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG. arXiv:2501.09136, 2025.",
]


def t(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def run_xml(text, bold=False, size=24):
    b = "<w:b/>" if bold else ""
    return (
        "<w:r>"
        f"<w:rPr>{b}<w:rFonts w:ascii=\"Times New Roman\" w:eastAsia=\"宋体\" w:hAnsi=\"Times New Roman\"/><w:sz w:val=\"{size}\"/></w:rPr>"
        f"<w:t xml:space=\"preserve\">{t(text)}</w:t>"
        "</w:r>"
    )


def paragraph(text="", *, align="both", first_line=True, before=0, after=120, size=24, bold=False):
    first = "<w:ind w:firstLine=\"480\"/>" if first_line else ""
    return (
        "<w:p>"
        "<w:pPr>"
        f"<w:spacing w:before=\"{before}\" w:after=\"{after}\" w:line=\"360\" w:lineRule=\"auto\"/>"
        f"{first}<w:jc w:val=\"{align}\"/>"
        "</w:pPr>"
        f"{run_xml(text, bold=bold, size=size)}"
        "</w:p>"
    )


def centered(text="", *, size=24, bold=False, before=0, after=120):
    return paragraph(text, align="center", first_line=False, before=before, after=after, size=size, bold=bold)


def heading(text):
    return (
        "<w:p>"
        "<w:pPr><w:pStyle w:val=\"Heading1\"/><w:spacing w:before=\"240\" w:after=\"160\"/><w:jc w:val=\"left\"/></w:pPr>"
        f"{run_xml(text, bold=True, size=28)}"
        "</w:p>"
    )


def page_break():
    return "<w:p><w:r><w:br w:type=\"page\"/></w:r></w:p>"


def document_xml():
    body = []
    body.append(centered("期末小论文", size=36, bold=True, before=1800, after=420))
    body.append(centered("课程作业", size=30, bold=True, after=700))
    body.append(centered(f"论文题目：{TITLE}", size=28, bold=True, after=900))
    for label in ["课程名称：________________________", "学生姓名：________________________", "学号：____________________________", "专业班级：________________________", "任课教师：________________________", "提交日期：2026 年 6 月 22 日"]:
        body.append(centered(label, size=24, after=220))
    body.append(page_break())

    body.append(centered(TITLE, size=32, bold=True, after=300))
    body.append(paragraph("摘  要：" + ABSTRACT, first_line=False, after=180))
    body.append(paragraph("关键词：Agentic RAG；检索增强生成；大语言模型；智能体；知识检索；人工智能应用", first_line=False, after=240))
    for title, paras in SECTIONS:
        body.append(heading(title))
        for p in paras:
            body.append(paragraph(p))
    body.append(heading("参考文献"))
    for i, ref in enumerate(REFERENCES, 1):
        body.append(paragraph(f"[{i}] {ref}", first_line=False, after=100))
    body.append(
        '<w:sectPr>'
        '<w:footerReference w:type="default" r:id="rId9"/>'
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>'
        '<w:cols w:space="720"/>'
        '<w:docGrid w:linePitch="312"/>'
        '</w:sectPr>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:o="urn:schemas-microsoft-com:office:office" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
        'xmlns:v="urn:schemas-microsoft-com:vml" '
        'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:w10="urn:schemas-microsoft-com:office:word" '
        'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
        'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
        'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
        'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
        'mc:Ignorable="w14 wp14"><w:body>'
        + "".join(body)
        + "</w:body></w:document>"
    )


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>"""


RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""


DOCUMENT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>"""


STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:rPr>
      <w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/>
      <w:sz w:val="24"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:keepNext/>
      <w:outlineLvl w:val="0"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Times New Roman" w:eastAsia="黑体" w:hAnsi="Times New Roman"/>
      <w:b/>
      <w:sz w:val="28"/>
    </w:rPr>
  </w:style>
</w:styles>"""


SETTINGS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:zoom w:percent="100"/>
  <w:defaultTabStop w:val="420"/>
  <w:characterSpacingControl w:val="doNotCompress"/>
</w:settings>"""


FOOTER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr><w:jc w:val="center"/></w:pPr>
    <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:t>第 </w:t></w:r>
    <w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>
    <w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r>
    <w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>
    <w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:t> 页</w:t></w:r>
  </w:p>
</w:ftr>"""


def main():
    if OUT.exists():
        OUT.unlink()
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS)
        z.writestr("word/document.xml", document_xml())
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/settings.xml", SETTINGS)
        z.writestr("word/footer1.xml", FOOTER)
    print(OUT.resolve())


if __name__ == "__main__":
    main()
