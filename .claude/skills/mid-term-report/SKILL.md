---
name: mid-term-report
description: 博士/硕士中期考核进展报告撰写流程。从材料索引→RAG检索→Markdown撰写→质量检查→LaTeX转换的完整pipeline。
tags:
  - 毕业论文
  - 中期考核
  - 进展报告
---

# Mid-Term Report Skill: 中期考核进展报告

## 概述

学位论文中期考核进展报告撰写技能。覆盖从材料准备到最终LaTeX输出的完整流程。

**适用对象：** 博士、硕士学位论文中期考核

**核心原则：**
- 成果导向：已完成成果占60%+篇幅
- 量化表述：所有成果必须有具体数据支撑
- 问题诚实：存在的问题不回避，但要配解决方案
- RAG先行：撰写前必须先检索知识库

---

## 工作流

### Phase 0: 材料盘点

**输入：** 开题报告PDF + 已发表论文PDF + 准备中论文PDF + 实验进展文档

**操作：**
1. 读取开题报告，提取：研究目标、技术路线、预期成果、时间节点
2. 读取每篇论文，提取：标题、作者、期刊/状态、核心贡献（1-2句）、关键结果
3. 读取实验进展文档，提取：设备参数、当前进度、下一步计划
4. 输出材料摘要表

### Phase 1: RAG索引

**操作：**
```bash
# 索引所有PDF材料到知识库
python academic_rag/run_rag.py index "path/to/paper.pdf" --domain optics --subfield terahertz
# 对每个PDF执行
```

**注意：** 如果PDF已在知识库中，跳过索引步骤（检查`python academic_rag/run_rag.py stats`）。

### Phase 2: RAG检索 + Zotero补充

**操作：**
```bash
# 对每个研究课题检索相关内容
python academic_rag/run_rag.py search "深亚波长约束光场" --top-k 10
python academic_rag/run_rag.py search "逆康普顿散射" --top-k 10
python academic_rag/run_rag.py search "纳米线导波" --top-k 10
python academic_rag/run_rag.py search "太赫兹源" --top-k 10
```

**Zotero MCP补充：**
- `zotero_search_library` 查相关笔记
- `zotero_search_fulltext` 查已有标注和笔记

### Phase 3: Markdown撰写

**加载bishe-guider Rule 3**（毕业论文写作要点）。

#### 结构模板

```markdown
# 中期考核进展报告

## 一、已完成的任务及取得的成果

### 1.1 [课题1名称]
- 研究背景与动机（2-3句）
- 核心方法与创新点
- 关键结果（量化数据）
- 论文发表/投稿状态

### 1.2 [课题2名称]
（同上结构）

### 1.3 [课题3名称]
（同上结构）

...

## 二、尚须完成的任务

### 2.1 [课题1待完成项]
### 2.2 [课题2待完成项]
### 2.3 [课题3待完成项]

## 三、存在的问题

### 3.1 [技术问题]
### 3.2 [理论问题]
### 3.3 [实验问题]

## 四、拟采取的办法

### 4.1 [针对3.1的解决方案]
### 4.2 [针对3.2的解决方案]
### 4.3 [针对3.3的解决方案]
```

#### 字数分配（博士≥6000字）

| 部分 | 目标字数 | 占比 |
|------|---------|------|
| 一、已完成成果 | ~3600字 | 60% |
| 二、尚须完成 | ~1200字 | 20% |
| 三、存在问题 | ~600字 | 10% |
| 四、拟采取办法 | ~600字 | 10% |

#### 写作规范

1. **量化表述**：所有结果必须有具体数字（功率、效率、脉宽、频率等）
2. **人称规范**：使用"本文"、"本研究"，不用"我们"
3. **避免夸张**：不用"首次"、"开创性"、"革命性"，改用"提出了一种"
4. **引用标注**：每篇已发表/准备论文需标注状态（已发表PRA/投稿APR/准备中）
5. **时态一致**：已完成用过去时，计划用将来时
6. **公式规范**：核心公式用LaTeX格式，编号连续
7. **图表引用**：如有实验数据图表，需编号引用

### Phase 4: 质量检查

**加载bishe-guider Rule 1**（去AI痕迹）+ **academic-craft**（六维度质量）。

#### 检查清单

| 检查项 | 工具 | 标准 |
|--------|------|------|
| AI痕迹 | humanizer skill | 29模式检测，0检出 |
| 人称使用 | bishe-guider Rule 1 | 无"我们"，使用"本文" |
| 夸张词汇 | bishe-guider Rule 1 | 无"首次/开创性/革命性" |
| 量化密度 | academic-craft | 每段≥1个具体数字 |
| 成果-计划对齐 | 手动 | 第二部分与第一部分课题对应 |
| 问题-方案对齐 | 手动 | 第三、四部分一一对应 |
| 字数达标 | wc统计 | 博士≥6000字 |

### Phase 5: Markdown → LaTeX转换

**操作：**
1. 使用zjuthesis章节格式
2. 公式用`\begin{equation}`环境
3. 图表用`\begin{figure}[htbp]`
4. 参考文献用`\cite{}`
5. 章节层级：`\section{}` → `\subsection{}` → `\subsubsection{}`

### Phase 6: 编译验证

```bash
xelatex -interaction=batchmode mid_term_report.tex
bibtex mid_term_report
xelatex -interaction=batchmode mid_term_report.tex
```

**验证项：**
- PDF生成成功
- 公式渲染正确
- 参考文献无缺失
- 页数合理（博士≥6页）

---

## 关联Skills

| Skill | 阶段 | 用途 |
|-------|------|------|
| bishe-guider | Phase 3-4 | 写作规范 + 去AI痕迹 |
| academic-craft | Phase 4 | 六维度质量检查 |
| humanizer | Phase 4 | 去AI痕迹29模式 |
| scientific-writing | Phase 3 | 段落级写作工艺 |
| document-skills | Phase 5 | Markdown→LaTeX转换 |
| academic-research | Phase 2 | 文献补充检索 |

---

## 常见陷阱

1. **忘记RAG**：撰写前必须先索引+检索，否则遗漏已有知识
2. **成果罗列式**：不是简单列举论文，要讲清楚每项成果的技术贡献
3. **问题回避**：评审看重问题意识，存在的问题必须诚实陈述
4. **计划空泛**："继续深入研究"不合格，要给出具体时间节点和技术路径
5. **字数不足**：博士6000字是硬性要求，不能少
6. **盲审格式**：中期报告一般无需盲审格式，但确认学校要求
