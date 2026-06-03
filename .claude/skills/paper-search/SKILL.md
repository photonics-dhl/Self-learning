---
name: paper-search
description: |
  学术论文搜索技能，集成多个学术数据库进行文献发现。

  触发条件：
  - 用户需要搜索特定论文
  - 用户需要查找某领域的代表性文献
  - 用户需要按 DOI/标题查找论文

  核心能力：
  - PubMed / ArXiv / Semantic Scholar 联合搜索
  - 按标题匹配查找论文
  - 获取论文引用和参考文献
---

# 论文搜索技能 (Paper Search)

## 能力概览

本技能整合多个学术搜索引擎，帮助快速定位所需文献：

| 数据源 | 优势 | 适用场景 |
|--------|------|----------|
| **Semantic Scholar** | 引用分析强 | 发现高影响力论文、引用网络 |
| **PubMed** | 生物医学权威 | 生命科学、医学相关文献 |
| **ArXiv** | 预印本快速 | 物理、CS、数学最新成果 |
| **OpenAlex** | 开放数据 | 大规模文献计量分析 |

## 搜索策略

### 1. 关键词搜索
```
搜索词设计原则：
- 英文为主，专业术语准确
- 组合关键词：topic + method + application
- 示例："terahertz generation photoconductive antenna"
```

### 2. DOI 精确查找
当已知 DOI 时，直接用 DOI 查询获取完整元数据。

### 3. 标题匹配
当只记得部分标题时，使用标题匹配搜索。

### 4. 引用追踪
- **正向引用**：查找引用了某篇论文的后续工作
- **反向引用**：查找某篇论文的参考文献

## 工作流程

```
用户提出需求
  → 选择搜索源（Semantic Scholar / PubMed / ArXiv）
  → 构建搜索词
  → 执行搜索
  → 筛选排序（按引用数/年份/相关性）
  → 输出文献列表
```

## 输出格式

```markdown
## 文献搜索结果

| 标题 | 作者 | 年份 | 期刊 | 引用 | DOI |
|------|------|------|------|------|-----|
| ... | ... | ... | ... | ... | ... |

### 必读推荐
1. **论文标题** (作者, 年份)
   - 核心贡献：...
   - 引用：[[cite:@AuthorYear]]
```

## 与学术综述技能配合

本技能为 `academic-research` 技能提供文献数据源：
- `paper-search` → 发现论文
- `academic-research` → 综合成 LaTeX 综述

---

*本技能基于真实学术 API，所有论文元数据可溯源。*

## 多数据库并行搜索策略（源自 K-Dense paper-lookup）

### 10 数据库覆盖

| 类别 | 数据库 | 核心能力 | API Key |
|------|--------|----------|---------|
| 生物医学 | **PubMed** | 37M+ 生物医学引用/摘要 | `NCBI_API_KEY`（可选，3→10 req/s） |
| 生物医学全文 | **PMC** | 10M+ 全文（JATS XML）、ID 转换 | 同 NCBI |
| 生物预印本 | **bioRxiv** | 生物学预印本，按日期/DOI 浏览 | 无需 |
| 医学预印本 | **medRxiv** | 健康科学预印本 | 无需 |
| 物理/CS 预印本 | **arXiv** | 物理、数学、CS 预印本（Atom XML） | 无需，1 req/3s |
| 多学科索引 | **OpenAlex** | 250M+ 作品、机构、主题、引用数据 | `OPENALEX_API_KEY`（推荐） |
| DOI 元数据 | **Crossref** | 150M+ DOI 元数据、期刊、基金 | `mailto` 参数加速 |
| 引用图谱 | **Semantic Scholar** | 200M+ 论文、AI TLDR、推荐 | `S2_API_KEY`（可选） |
| OA 全文 | **CORE** | 37M+ OA 仓储全文 | `CORE_API_KEY`（全文必需） |
| OA 检测 | **Unpaywall** | 任意 DOI 的 OA 状态与 PDF 链接 | `email` 参数 |

### 并行查询策略

按用户意图选择数据库组合，**无速率限制冲突时可并行调用**：

| 搜索场景 | 数据库组合 |
|----------|-----------|
| 综合文献检索 | PubMed + OpenAlex + Semantic Scholar |
| 论文全景（元数据+引用+OA） | Crossref + Semantic Scholar + Unpaywall |
| 查找并阅读论文 | PubMed（定位）+ Unpaywall（OA 链接）+ PMC/CORE（全文） |
| 预印本 vs 发表版 | bioRxiv/medRxiv + Crossref |
| 作者概览+引用指标 | Semantic Scholar + OpenAlex |

### 去重方法

1. **DOI 优先归一化**：不同数据库返回相同论文时，以 DOI 为主键合并
2. **标题模糊匹配**：无 DOI 的预印本，用规范化标题（小写+去标点）去重
3. **ID 交叉映射**：利用 PMC ID Converter 在 PMID/PMCID/DOI 间转换，统一标识

### 速率限制与错误恢复

- NCBI 系列（PubMed/PMC）：无 Key 3 req/s，有 Key 10 req/s，顺序调用
- arXiv：1 req/3s，需间隔
- Crossref/Unpaywall：加 `mailto`/`email` 进入快速池
- HTTP 429 → 短暂等待后重试一次；失败则换数据库或换标识符格式
