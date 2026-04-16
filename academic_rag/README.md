# 学术论文 RAG 系统

> 你的"第二大脑" - 用多模态AI理解论文图片，智能配图

## 一句话描述

通过PDF解析 + 向量检索 + 多模态图片理解，让你能快速找到论文中解释特定概念的图片，并理解图片背后的研究思想。

## 核心功能

### 1. 智能配图查找

当你学习某个概念时，系统能帮你找到论文中解释这个概念的图片：

```bash
python run_rag.py find-figure "光电导天线辐射原理" --domain optics --subfield terahertz
```

系统会返回：
- 匹配的图表
- 图片的Obsidian引用格式 `![[image.png]]`
- 图片说明和关键发现
- 在论文中的上下文

### 2. 语义搜索

搜索论文内容，支持领域/子领域过滤：

```bash
python run_rag.py search "THz generation by optical rectification" --domain optics --subfield terahertz
```

### 3. PDF索引

将论文索引到向量数据库，同时提取文本和图片：

```bash
python run_rag.py index paper.pdf --domain optics --subfield terahertz
```

## 架构

```
academic_rag/
├── config.py           # 配置（领域分类、路径等）
├── db/
│   └── models.py       # 数据模型 (Paper, Figure, TextChunk)
├── processors/
│   └── pdf_processor.py  # PDF解析（提取文本、图片、元数据）
├── indexer/
│   └── vector_indexer.py # ChromaDB向量索引
├── api/
│   └── search_api.py     # 搜索API
├── cli/
│   └── rag_cli.py        # 命令行工具
└── run_rag.py            # 入口脚本
```

## 领域分类体系

与Obsidian知识树对应：

```
optics (光学)
├── terahertz (太赫兹)
├── metasurface (超表面)
├── quantum_optics (量子光学)
├── fiber_optics (光纤光学)
├── nonlinear_optics (非线性光学)
└── spectroscopy (光谱学)

physics (物理)
├── semiconductor (半导体物理)
├── electromagnetic (电磁场理论)
├── quantum_mechanics (量子力学)
└── statistical_physics (统计物理)

engineering (工程)
├── communication (通信工程)
├── microwave (微波工程)
└── materials (材料工程)
```

## 使用流程

### 第一步：索引论文

```bash
# 索引单个PDF
python run_rag.py index paper.pdf --domain optics --subfield terahertz

# 批量索引目录
python run_rag.py index-dir /path/to/papers --domain optics --subfield terahertz
```

### 第二步：搜索配图

```bash
# 查找解释"光电导天线"的图片
python run_rag.py find-figure "photoconductive antenna" --subfield terahertz

# 搜索论文内容
python run_rag.py search "optical rectification LiNbO3" --subfield terahertz
```

### 第三步：在Obsidian中使用

从搜索结果获取 `obsidian_ref`，直接在笔记中使用：

```markdown
![[path/to/figure.png]]

**图片来源**：Zhang 2022, Optics Letters, Fig. 1
```

## 核心设计思想

### 1. 领域感知

每篇论文和文本块都带有领域/子领域标签，搜索时可以精确过滤。

### 2. 图文关联

文本块和图表通过页码关联，搜索文本时能自动带上相关的图。

### 3. 多模态扩展

图表的 `description` 和 `key_findings` 字段预留给多模态AI填充，未来可以自动分析图片内容。

## 依赖

```
chromadb>=1.0
sentence-transformers>=2.0
pdfplumber>=0.10
PyMuPDF>=1.23
```

安装：
```bash
pip install chromadb sentence-transformers pdfplumber pymupdf
```

## 状态

当前版本实现 Phase 1-3：
- ✅ PDF处理器 - 提取文本和图片
- ✅ 向量索引器 - ChromaDB存储和检索
- ✅ 搜索API - 语义搜索和配图查找
- ⏳ CLI工具 - 命令行接口
- ⏳ 多模态理解 - 用AI分析图片内容

## License

MIT
