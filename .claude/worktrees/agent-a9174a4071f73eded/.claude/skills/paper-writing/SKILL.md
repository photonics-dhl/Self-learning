---
name: paper-writing
description: 英文期刊论文AI辅助撰写。从Gap识别到定稿的全流程pipeline，整合三源文献、Gap-driven规划、审稿人友好写作、反AI痕迹。当用户需要写英文期刊论文时触发。中文毕业论文请用bishe-guider。
---

# Paper Writing Skill — 英文期刊论文撰写

## 核心定位

英文期刊论文的完整撰写系统。覆盖从Gap识别、文献调研、结构规划到分章节撰写和定稿审查的全流程。

**中文毕业论文** → 使用 `bishe-guider` skill（不使用本skill）

## 与其他 Skill 的边界

| 需求 | 使用 | 不使用 |
|------|------|--------|
| 英文期刊论文撰写 | **paper-writing**（本skill） | — |
| 段落/语言层面优化 | scientific-writing | paper-writing |
| 中文学位论文 | bishe-guider | paper-writing |
| 文献综述章节 | literature-review + academic-research | paper-writing |
| 去AI写作痕迹 | humanizer | paper-writing |
| 论文质量审查 | paper-review | paper-writing |

## 期刊论文质量标准

| 维度 | 要求 | 详细指导 |
|------|------|---------|
| 公式规范性 | 每个display equation配物理上下文（为什么展示、参数含义、失效条件） | `prompts/paper_draft.md` |
| 图表引用 | 引用图表时引导读者看核心结论（不只是"results shown in Fig.X"） | `prompts/paper_draft.md` |
| Discussion对比 | 与竞争方法量化对比表 | `prompts/paper_draft.md` |
| Intro文献综合 | 按技术路线分组综合，不逐篇罗列 | `prompts/anti_ai_patterns.md` |
| Gap驱动 | 每篇论文回答一个具体空白，gap不可跨章节重复 | `agents/paper-planner.md` |
| 局限性诚实 | 量化局限+物理原因，不是空泛"future work" | `prompts/paper_draft.md` |
| 反AI痕迹 | 消除审稿人一眼识别的模板句式 | `prompts/anti_ai_patterns.md` |

## 六阶段工作流程

```
Stage 0: 素材准备
    │ 四层收集: 用户实验数据 → Zotero文献 → RAG图表 → Obsidian笔记
    │ 用户实验数据为最高优先级，所有其他素材围绕实验数据展开
    │ 详见 prompts/material_prep.md
    │ 输出: 素材就绪报告（实验数据 + 文献清单 + 图表清单 + 知识点汇总）
    ↓
Stage 1: 规划
    │ 调用 paper-planner agent
    │ 输出: 论文规划卡（Gap + 结构 + Claim-Evidence映射）
    ↓
Stage 2: 文献调研
    │ 基于 Stage 0 素材 + 补充外部搜索
    │ 优先使用已收集素材，外部搜索补充遗漏
    │ 输出: 结构化文献综述 + 真实引用列表
    ↓
Stage 3: 大纲生成
    │ Gap-driven大纲 + 审稿人视角检查
    │ 输出: 每节主题句 + Claim预映射 + 图表规划
    ↓
Stage 4: 分章节撰写
    │ 每节走两阶段: 提纲 → 流畅段落
    │ 应用深度指南 + 反AI模式
    ↓
Stage 5: 定稿审查
    │ 5a: academic-craft 6维度诊断（主题综合/批判评价/实验证据/Gap具体性/焦点控制/研究连接）
    │ 5b: 反向大纲 + Claim-Evidence验证
    │ 5c: humanizer润色
    │ 任一维度C级 → 强制修订后再继续
    │ 输出: 质量门检查清单（6维度全B级以上方可定稿）
```

### 用户审核节点

1. **素材确认** — Stage 0完成后，用户确认素材是否充足（新增）
2. **规划卡确认** — Stage 1完成后，用户确认Gap和创新点
3. **大纲确认** — Stage 3完成后，用户确认结构
4. **各章节初稿** — Stage 4每节完成后
5. **完整草稿** — Stage 5完成后

## 撰写原则

### 通用原则
1. **一段一意** — 每段只传达一个信息
2. **首句立题** — 第一句陈述段落主旨
3. **Gap驱动** — 每篇论文必须回答"填补了什么空白"
4. **保守陈述** — 创新点来自用户实验，不夸大

### Gap唯一性规则
- Introduction gap: 领域层面空白（为什么这个方向重要但未解决）
- Methods gap: 技术层面空白（现有方法做不到什么）
- Results gap: 数据层面空白（哪些参数区间未被探索）
- Discussion gap: 理解层面空白（现象已知但机理未知）
- **同一gap不可在2+章节重复使用**

### Intro-Body非重叠规则
- Intro路线图只命名章节主题，不解释内容
- 详细解释只在正文对应章节出现
- 如果Intro已提到某信息，正文必须增加深度而非重复

## 文件结构

```
paper-writing/
├── SKILL.md                       # 本文件（主skill定义）
├── prompts/
│   ├── material_prep.md           # Stage 0 素材准备prompt
│   ├── literature_review.md       # 文献调研prompt
│   ├── knowledge_graph.md         # 知识整合prompt
│   ├── paper_outline.md           # 大纲生成prompt
│   ├── paper_draft.md             # 各章节撰写prompt（核心）
│   ├── section_depth_guide.md     # 章节深度控制
│   ├── anti_ai_patterns.md        # 反AI写作模式
│   ├── figure_generation.md       # 图表生成prompt
│   └── citation_check.md          # 引用审查prompt
```

LaTeX 模板位置：`Obsidian-Vault/6️⃣ 工具/templates/`
- `thesis_templates/zjuthesis/` — 浙大博士论文
- `reference_templates/journal_template.tex` — 期刊论文通用模板

## MCP 协同

| MCP | 用途 | 优先级 |
|-----|------|--------|
| `semantic-scholar` | 学术论文搜索 | 高 |
| `tavily-search` | 深度网络搜索 | 高 |
| `zotero` | 个人文献引用 | 高 |
| `mermaid` | 引用图谱/流程图 | 中 |
| `paper-search` | 预印本搜索 | 中 |

## 质量保证

### 防止幻觉引用
- 仅使用 Zotero 验证过的真实引用
- 外部文献需双重确认存在性
- 引用格式统一

### 反AI痕迹
- 参见 `prompts/anti_ai_patterns.md` 三级模式
- 完成后调用 `humanizer` skill 终审

### 6维度质量诊断（academic-craft）
- Stage 5a 强制执行 `academic-craft` skill 的6维度诊断
- 主题综合(A/B/C)、批判评价、实验证据、Gap具体性、焦点控制、研究连接
- 任一维度C级 → 执行对应修订策略后再进入5b/5c
- 详见 `.claude/skills/academic-craft/SKILL.md`

### 深度自检
- 参见 `prompts/section_depth_guide.md` 三级深度
- 每节至少达到该章最低深度要求

## 使用方式

```
"帮我写一篇关于 {{主题}} 的期刊论文，目标投 {{期刊名}}"
"基于实验数据撰写论文的 {{章节}} 部分"
"帮我改进论文引言的Gap陈述"
"审查论文草稿的claim-evidence一致性"
```
