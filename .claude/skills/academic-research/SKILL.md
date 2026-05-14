---
name: academic-research
description: |
  智能学术研究技能 v2.0 - 数据驱动的可验证文献综述生成

  触发条件：
  - 用户需要文献调研并生成可验证的学术综述
  - 用户需要"帮我写一篇关于X的综述"
  - 用户需要基于真实文献的LaTeX论文

  核心工作流：
  1. OpenAlex 论文发现（按相关性排序）
  2. 多字段关键词分组（PCA/OR/等离子体/超表面等）
  3. LaTeX + BibTeX 导出
  4. 引用图谱生成

  数据保证：所有论文信息（作者/年份/期刊/引用数/DOI）均来自真实API响应，
  摘要从 inverted_index 重建，数值可溯源。
---

# 智能学术研究技能 v2.0

## 核心原则：**数据驱动，每句话有文献支撑**

### 质量保证
- 每篇论文的作者、年份、期刊、引用数来自 OpenAlex API 原始数据
- 摘要从 `abstract_inverted_index` 字段重建，非训练知识
- 分组基于 title + abstract + concepts 多字段关键词匹配
- LaTeX 输出可编译，BibTeX 可直接导入 Zotero

---

## 自动化工作流

```
用户: "帮我写一篇关于太赫兹产生的综述"

助手执行:
1. 调用 review_pipeline.py discover "terahertz generation" --n 30
   → 按 relevance_score 排序，返回 30 篇真实论文元数据

2. 自动分组（多字段匹配）:
   - 光电导天线 PCA: title/abstract/concepts 包含 "photoconductive" 等
   - 光整流 OR: 包含 "optical rectification" 等
   - 等离子体/空气: 包含 "plasma", "filament", "two-color" 等
   - 超表面/元表面: 包含 "metasurface", "plasmonic" 等

3. 🔴 图表预提取（图文并茂 — Phase 0）:
   对引用>50 或各主题核心论文:
   - Zotero MCP get_content(itemKey=key, include={pdf: true}) → 提取图片
   - academic_rag figure_indexer 查询已索引图表
   - 图表→主题语义匹配（embedding cosine similarity）
   - 输出 figure_assets.json

4. 调用 review_pipeline.py full "terahertz generation" --n 30
   → 生成 LaTeX 综述 + BibTeX + Mermaid 引用图 + 图表嵌入

5. 输出文件:
   - DHL/review_terahertz_generation.tex (可编译，含图表)
   - DHL/review_terahertz_generation.bib
   - DHL/review_terahertz_generation.md (引用图)
   - figure_assets.json (图表资产清单)
```

---

## 使用命令

### 发现论文
```bash
python .claude/hooks/review_pipeline.py discover "<主题>" [--n N] [--year Y]
```
- `--n N`: 返回 N 篇（默认 20）
- `--year Y`: 只返回 Y 年之后的论文

### 完整生成（发现 + 分析 + LaTeX）
```bash
python .claude/hooks/review_pipeline.py full "<主题>" [--n N]
```

### 导出 BibTeX/DOI
```bash
python .claude/hooks/openalex_search.py export "<主题>" --bibtex --file refs.bibtex
```

---

## 论文分组方法

| 方法 | 关键词 |
|------|--------|
| 光电导天线 PCA | photoconductive, photo-conductive, PCA, THz antenna |
| 光整流 OR | optical rectification, laser rectification |
| 等离子体/空气 | air plasma, laser plasma, filamentation, two-color |
| 量子级联激光器 | quantum cascade, QCL, THz laser |
| 非线性晶体 | lithium niobate, LiNbO3, ZnTe, GaSe, DAST |
| 超表面/元表面 | metasurface, metamaterial, plasmonic, nanoantenna |

---

## 输出格式

### LaTeX 综述结构
```
\section{引言}
  领域重要性 + 经典工作引用（基于高引用论文）

\section{方法与结果}
  \subsection{光电导天线 PCA}
    - 高引用工作列表（作者年 期刊 \cite{RefX}）
    - 摘要方法描述（来自真实论文 abstract）
    - 引用次数（真实数据）

  \subsection{光整流 OR}
    ...

\section{讨论}
  总结 + 未来方向

\appendix
  表\ref{tab:papers} 完整论文列表
```

### BibTeX 格式
```bibtex
@article{Ref1,
  title   = {Real paper title},
  author  = {Lastname1, Firstname1 and Lastname2, Firstname2},
  journal = {Journal Name},
  year    = {2024},
  volume  = {123},
  number  = {4},
  pages   = {456--789},
  doi     = {https://doi.org/10.xxxx/xxxxx}
}
```

---

## 质量对比

| 项目 | v1.0 (不可用) | v2.0 (当前) |
|------|---------------|-------------|
| 论文数据 | AI 训练知识（可能虚构） | OpenAlex 真实 API 响应 |
| 引用次数 | 估算 | 真实 `cited_by_count` |
| 摘要 | 无或虚构 | 从 `abstract_inverted_index` 重建 |
| 期刊信息 | 泛泛而谈 | 真实卷期页码 |
| 分组准确性 | 低（仅 title 匹配） | 高（多字段关键词） |
| LaTeX 输出 | 无 | 可编译 .tex + .bib |
| 公式溯源 | 无 | 需配合 paper-review skill |

---

## 已知限制

1. **分组依赖关键词**：可能存在分类不准确的情况，需人工审核
2. **摘要长度限制**：仅截取前 500 字符，非完整摘要
3. **公式溯源缺失**：公式与文献的映射需后续 paper-review skill 补充
4. **无批判性分析**：当前仅整理客观信息，批判性综述需人工撰写
5. **图表依赖 PDF 可获取性**：关键论文需在 Zotero 中有 PDF 全文才能提取图表；仅有元数据的论文无法提取图表

---

## 协作流程

```
review_pipeline.py (数据层)
    ↓ 真实论文数据 + LaTeX
paper-review skill (审查层)
    ↓ 修改建议
用户 → 最终论文
```

