---
name: literature-review
description: 系统性文献综述撰写。整合 Pautasso (2013) 综述写作规则和 C-C-C 结构原则。当用户需要写文献综述时触发。
---

# Literature Review Writing Skill - 系统性文献综述撰写技能

## 概述

这是一个基于学术规范的文献综述撰写系统，整合了 Pautasso (2013) 的"Ten Simple Rules for Writing a Literature Review"和 Mensah (2019) 的"Ten Simple Rules for Structuring Papers"中的 C-C-C 结构原则。

**核心定位**: 帮助研究者撰写真正有深度的学术文献综述，而非简单的论文堆砌或拼接。

---

## 核心原则

### 1. Thematic Synthesis（主题综合）而非 Paper-by-Paper 列举

**错误方式**（当前v4 pipeline的问题）:
```
Smith (2005) 做了xxx
Jones (2008) 做了yyy
Wang (2012) 做了zzz
→ 没有任何分析，只是罗列
```

**正确方式**:
```
主题: 光整流晶体的效率-带宽权衡
问题: 为什么高非线性系数材料往往损伤阈值低？
分析: 
  - LiNbO3: 相位匹配好(d=25 pm/V)但损伤阈值高(1 GW/cm²)→ 能量输出高但带宽受限
  - DAST: 非线性系数极高(d=490 pm/V)但损伤阈值低(0.1 GW/cm²)→ 带宽宽但能量输出低
  - 权衡点: 目前缺乏同时满足 >5 THz带宽 AND >100 μJ 能量输出的晶体方案
→ 这是一个有深度的 Gap 分析，不是简单罗列
```

### 2. C-C-C 结构（每段必须遵循）

每段必须包含：
- **Context（上下文）**: 这个问题在什么背景下出现？为何重要？
- **Content（内容）**: 具体说了什么？数据、发现、分析
- **Conclusion/Gap（结论/Gap）**: 这意味着什么？文献中缺少什么？

### 3. Gap-Driven 写作（研究空白驱动）

每个主题必须明确回答：
1. 这个领域已经解决了什么问题？
2. 当前的主要争议/权衡是什么？
3. **文献中缺失什么**（具体、量化、可验证的 Gap）？

### 4. 跨论文综合（不是单篇摘要拼接）

综合分析必须：
- 识别论文之间的**模式**（patterns）
- 讨论**一致性**和**争议**
- 追踪**技术演进**（谁在谁的基础上改进）
- 比较**性能边界**（最优结果 vs. 理论极限）

### 5. 图文并茂（Rich Illustration） 🔴 强制执行

**综述必须充分利用图表来解释复杂概念和关键数据。** 不能用纯文字堆砌。

每篇关键论文（引用>50 或领域里程碑）必须提取并利用其 PDF 中的图表：
- **实验装置图** → 解释技术方法时插入，比纯文字描述直观 10 倍
- **关键数据图** → 讨论性能指标时引用，用真实数据显示趋势/对比
- **原理示意图** → 解释物理机制时放置，帮助建立物理图像
- **对比表格** → 方法对比时使用，一目了然

**图表来源优先级**:
1. Zotero MCP `get_content` — 从 PDF 提取图片（最直接）
2. `academic_rag/figure_indexer.py` — 从已索引论文获取图表及语义描述
3. `academic_rag/enhance_figures.py` — AI 增强图表分析
4. 论文官方 DOI 页面 — 获取公开图表

**每张图表必须包含**:
- 清晰的图题（Figure N: 描述）
- 来源标注（Adapted from [Author, Year]）
- 与正文的语义关联（"如图 X 所示，..."）

---

## 写作流程

### Phase 0: 图表预提取（Image Pre-fetch） 🔴 写综述前必做

**目标**: 在动笔之前，先收集所有关键论文的图表资产。

```
对每篇关键论文（引用>50 或主题核心论文）:
1. 调用 Zotero MCP get_content(itemKey=论文key, include={pdf: true})
   → 提取 PDF 全文和嵌入图片
2. 调用 Zotero MCP search_fulltext(q="figure", itemKeys=[论文key])
   → 搜索论文中的图表提及
3. 调用 academic_rag figure_indexer 获取已索引图表及 AI 语义描述
4. 建立 图表→主题 语义映射表
```

**图表-主题语义匹配**:
```
对每张提取的图表:
1. 用图表标题/上下文生成 embedding
2. 与综述各主题描述计算余弦相似度
3. 将图表分配到最相关的主题章节
4. 标记: [实验装置] / [数据图] / [原理图] / [对比表]
```

**输出**: 图表资产清单 `figure_assets.json`
```json
{
  "theme_name": {
    "figures": [
      {
        "paper_id": "Hoffmann2007",
        "figure_number": "Fig. 3",
        "type": "experimental_setup",
        "description": "TPF excitation scheme for LiNbO3",
        "semantic_match": "光整流技术路线 > LiNbO3倾斜脉冲前",
        "caption_zh": "LiNbO3倾斜脉冲前激发THz的实验装置示意图",
        "source_note": "Adapted from Hoffmann et al. (2007)"
      }
    ]
  }
}
```

### Phase 1: 深读论文（不是摘要堆砌）

**每篇论文必须提取**:
1. **研究问题**: 作者想解决什么问题？
2. **技术方法**: 具体怎么做的（不是"用了激光器"而是"用800nm、100fs激光器通过tilted pulse front在LiNbO3中产生THz"）
3. **核心发现**: 关键数据、结论
4. **局限性**: 作者自己承认的不足
5. **与其他论文的关系**: 与同类工作比较，结果更好/更差/有差异的原因

**数据来源优先级**:
1. 论文全文（PDF/Zotero）> 摘要（OpenAlex）
2. 优先读取高引用论文（领域奠基性工作）
3. 对于缺失摘要的论文，尝试从 Zotero 获取 PDF 进行深度分析

### Phase 2: 主题综合（Thematic Synthesis）

**每个主题的分析维度**:

```
主题: [主题名称]
├── 核心科学问题: [该领域最根本的科学问题是什么？]
├── 技术路线对比:
│   ├── 路线A: [方法] → [性能] → [优势/局限]
│   ├── 路线B: [方法] → [性能] → [优势/局限]
│   └── 对比结论: [两者之间的权衡关系]
├── 核心权衡/张力:
│   ├── 权衡1: [矛盾双方] → [如何平衡] 或 [无法兼得]
│   └── 权衡2: ...
├── 领域共识:
│   └── [大家都认可的观点]
├── 主要争议:
│   └── [尚未解决的分歧]
└── 研究空白（Gap）:
    ├── Gap 1: [具体缺失] → [为什么重要] → [如何填补]
    ├── Gap 2: ...
    └── Gap 3: ...
```

### Phase 3: 撰写（按 C-C-C 结构）

**引言写作模板**:
```
[Paragraph 1: Context - 领域重要性]
太赫兹波段在XXX领域有重要应用前景。然而，高效THz辐射的产生一直是核心技术难题。

[Paragraph 2: 已有进展 - 但存在问题]
近年来，[技术路线A]在[方面]取得了进展（如文献X、Y），但[关键问题仍未解决]。

[Paragraph 3: 研究空白 - Gap Identification]
【Gap Identification】现有文献存在以下不足：
  - Gap 1: [具体缺失]
  - Gap 2: [具体缺失]
  （每个Gap必须基于已发表的论文/数据，不能凭空编造）

[Paragraph 4: 本文目标]
本综述对[范围]篇文献进行系统性主题综合，识别各技术路线的核心权衡与研究空白。
```

**主题章节写作模板**:
```
### [主题名称]

【研究问题】该领域的核心科学问题是：XXX

【背景】[2-3句介绍背景，引用2-3篇奠基性工作]

【跨论文综合】
在[具体技术路线]上，有三类代表性方案：
  - 方案A（文献X）: [具体方法] → [具体性能]（优势：XXX，局限：XXX）
  - 方案B（文献Y）: [具体方法] → [具体性能]（优势：XXX，局限：XXX）
  - 方案C（文献Z）: [具体方法] → [具体性能]（优势：XXX，局限：XXX）

【核心权衡】
这三类方案在[维度A]上表现相近，但在[维度B]上差异显著：
  - [权衡1]: 方案A的XXX特性 → 导致方案B的YYY局限性
  - [权衡2]: ...

【共识】
目前领域内公认：[共识陈述]，证据来自文献X、Y、Z的交叉验证。

【争议】
但在XXX问题上存在分歧：[争议1]（文献X认为...，文献Y认为...）

【研究空白】
基于上述分析，该领域存在以下尚未被充分研究的问题：
  - Gap 1: [具体缺失]（现有论文如X在此问题上只做了YYY，未考虑ZZZ）
  - Gap 2: ...

【未来方向】
未来研究应重点关注：如何解决Gap 1...（需要XXX方向的技术突破）
```

---

## 质量标准

### 必须满足的条件

1. **每个主题**有 >= 3篇论文支撑
2. **每个 Gap** 有文献依据，不是凭空编造
3. **每段**遵循 C-C-C 结构
4. **方法描述**具体到技术细节（不是"用了激光"而是"800nm、100fs Ti:Sa激光器"）
5. **性能指标**带单位（THz、mJ、GW/cm²等）
6. **引用数量**对于高影响力论文准确
7. 🔴 **每主题 >= 2张图表** — 实验装置图、数据图、原理图、对比表均可；纯文字不合规
8. 🔴 **每张图表有完整标注** — 图题 + 来源 + 正文引用

### 避免的问题

❌ "Recent years, many researchers have studied..."（泛泛而谈）
❌ "Smith did X. Jones did Y. Wang did Z."（罗列无分析）
❌ "This is very important for future research."（无具体内容）
❌ "Table 1 shows the comparison of methods."（只给表没有分析）
❌ 🔴 纯文字综述，零图表 — 违反"图文并茂"原则，打回重写

✅ "We identify a gap in the literature: while Zhang (2015) achieved 2.5 THz bandwidth with LiNbO3 using tilted pulse front, no study has explored whether organic crystal DAST can exceed 5 THz while maintaining >100 μJ output under same pump conditions."

---

## MCP 协同

| MCP | 用途 | 使用时机 |
|-----|------|---------|
| `zotero` | 获取 PDF 全文 + **提取图表** + 深度分析 | 🔴 关键论文（引用>50）必须调用；先 `get_content` 提取图片，再分析文字 |
| `semantic-scholar` | 论文元数据、引用数、摘要 | 批量筛选和排序 |
| `tavily` | 搜索最新进展、补充信息 | 验证 Gap、分析争议时 |
| `paper-search` | 预印本搜索 | 找最新但未正式发表的工作 |
| `academic_rag` | 已索引论文图表获取、AI 语义描述 | 论文已索引时优先使用（比 Zotero 快） |

### 图表提取工具链

```
Zotero MCP get_content          → PDF 原始图片提取
    ↓
academic_rag/enhance_figures    → AI 增强图表分析（颜色标注、关键区域识别）
    ↓
academic_rag/figure_indexer     → 图表语义索引 + embedding 匹配
    ↓
综述撰写                          → 图表按主题分配合并到正文
```

---

## 质量审查门禁

在生成最终输出前，必须通过以下审查：

**Gate 1: 论文相关性**
- Top 10 论文的相关性分数 > 50

**Gate 2: 摘要质量**
- >= 60% 论文有有效摘要（长度>100字符）

**Gate 3: 分组均衡性**
- >= 3 个主题各有 >= 3 篇论文

**Gate 4: Gap 有文献支撑**
- 每个声称的 Gap 必须能找到至少 1 篇论文明确指出该问题

**Gate 5: 方法提取完整性**
- >= 80% 的论文提取到具体技术方法（非"---"）

---

## 调用方式

```
"帮我写一篇关于 [主题] 的文献综述"
"基于 OpenAlex 搜索生成 [主题] 的系统性综述"
"用 thematic synthesis 方法分析 [主题] 的研究现状"
```

---

## 文件结构

```
literature-review/
├── SKILL.md              # 本文件 - 核心技能定义
├── prompts/
│   ├── introduction.md   # 引言段落 prompt
│   ├── theme_analysis.md # 主题综合分析 prompt
│   └── gap_identification.md # Gap 识别 prompt
└── templates/
    └── review_template.md # 综述撰写模板
```

---

## 参考文献

1. Pautasso, M. (2013). Ten Simple Rules for Writing a Literature Review. PLoS Comput Biol 9(7): e1003149.
2. Mensah, B. & Kording, K. (2019). Ten simple rules for structuring papers. PLoS Comput Biol 15(9): e1005619.
3. Thomas, J. & Harden, A. (2008). Methods for the thematic synthesis of qualitative research in systematic reviews. BMC Medical Research Methodology, 8:45.

---

*本技能基于学术规范设计，确保生成的文献综述具有真正的学术价值*