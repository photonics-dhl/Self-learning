# Paper Writing Skill - 学术论文AI辅助撰写

## 概述

本技能整合 AI Scientist V2 的论文撰写能力与光学大脑的知识管理系统，帮助用户基于实验数据、个人文献库（Zotero）和知识库（Obsidian）自动撰写符合学术规范的论文。

**核心定位**: 替代 AI Scientist V2 的实验执行模块，替换为实验数据分析；三源搜索替代单一 Semantic Scholar 搜索。

---

## 核心能力

### 1. 三源文献调研
```
用户输入研究主题
    ↓
┌──────────────────────────────────────┐
│ 1. Obsidian 知识库（优先）            │
│    → 已理解的笔记 → 标记"已知"       │
│ 2. Zotero 个人文献库                 │
│    → 个人收藏 → 真实引用              │
│ 3. Semantic Scholar + Tavily（扩展） │
│    → 最新论文 → 高引用论文           │
└──────────────────────────────────────┘
    ↓
结构化文献综述 + 引用图谱
```

### 2. 知识整合与大纲生成
```
实验数据 + 文献综述
    ↓
关联理论框架
    ↓
构建叙事："我的实验 → 验证/挑战已有理论"
    ↓
IMRAD 结构论文大纲
```

### 3. 论文撰写
- 支持格式：毕业论文 (LaTeX/Word)、期刊论文 (LaTeX)、草稿 (Markdown)
- 各章节独立生成，可迭代修改
- 自动插入图表和引用

### 4. 引用管理
- Zotero 真实引用插入
- 多格式参考文献（Nature/Science/ACS/IEEE）
- 幻觉引用检测

### 5. 图表生成
- 概念图：技术原理示意图
- 数据图：实验结果可视化

---

## 工作流程

```
┌──────────────────────────────────────────────────────────────┐
│                     论文撰写完整流程                           │
└──────────────────────────────────────────────────────────────┘

Step 1: 文献调研
    │
    ├─ 收集 Obsidian 相关笔记
    ├─ 收集 Zotero 相关文献
    ├─ 外部论文搜索（Semantic Scholar / Tavily）
    └─ 输出: 文献综述 + 引用列表

Step 2: 知识整合
    │
    ├─ 导入实验数据描述
    ├─ 关联理论框架
    └─ 输出: 论文大纲（IMRAD）

Step 3: 论文撰写
    │
    ├─ Introduction
    ├─ Theory/Methods
    ├─ Results
    ├─ Discussion
    └─ Conclusion

Step 4: 图表生成
    │
    ├─ 原理示意图
    └─ 数据可视化

Step 5: 引用整理
    │
    ├─ Zotero 插入引用
    ├─ 格式规范化
    └─ 输出: 完整论文 LaTeX/Word
```

---

## 使用方式

### 触发论文撰写
```
"帮我写一篇关于 {{主题}} 的期刊论文"
"基于我的实验数据撰写毕业论文"
"帮我生成论文草稿"
```

### 提供信息
用户应提供：
- 研究主题/方向
- 实验数据（文件路径或描述）
- 目标期刊/格式要求
- 特殊创新点说明

---

## MCP 协同

| MCP | 用途 | 优先级 |
|-----|------|--------|
| `semantic-scholar` | 学术论文搜索 | 高 |
| `tavily-search` | 网络深度搜索 | 高 |
| `zotero` | 个人文献引用 | 高 |
| `image-generation` | 图表生成 | 高 |
| `mermaid` | 引用图谱绘制 | 中 |
| `paper-search` | 预印本搜索 | 中 |

---

## 质量保证

### 防止幻觉引用
- 仅使用 Zotero 验证过的真实引用
- 外部文献需双重确认存在性

### 用户审核节点
- 大纲生成后需用户确认
- 创新点声明需用户审核
- 参考文献列表需用户确认完整性

### 格式规范
- 不同期刊/学位格式模板
- 自动单位转换检查
- 图表编号规范

---

## 文件结构

```
paper-writing/
├── SKILL.md                    # 本文件
├── prompts/
│   ├── literature_review.md    # 文献调研 prompt
│   ├── knowledge_graph.md      # 知识整合 prompt
│   ├── paper_outline.md        # 大纲生成 prompt
│   ├── paper_draft.md          # 各章节撰写 prompt
│   ├── figure_generation.md   # 图表生成 prompt
│   └── citation_check.md       # 引用审查 prompt
└── templates/
    ├── thesis_templates/zjuthesis/  # 浙江大学博士论文模板
    └── journal_templates/
        ├── optica/             # Optica (OSA) 通用模板
        ├── aps/                # APS REVTeX (需手动下载)
        ├── nature/            # Springer Nature (需手动下载)
        └── ieee/              # IEEE (需手动下载)
```

## 模板位置

| 模板类型 | 位置 | 状态 |
|---------|------|------|
| 浙大博士论文 | `.../thesis_templates/zjuthesis/` | ✅ 已下载 |
| Optica 期刊 | `.../journal_templates/optica/` | ✅ 已下载 |
| APS/PRL | `.../journal_templates/aps/` | ⏳ 需手动下载 |
| Springer Nature | `.../journal_templates/nature/` | ⏳ 需手动下载 |
| IEEE | `.../journal_templates/ieee/` | ⏳ 需手动下载 |

详见: `.../journal_templates/README.md`

---

## 借鉴 AI Scientist V2

| 功能 | AI Scientist V2 | 本系统适配 |
|-----|---------------|----------|
| 文献搜索 | Semantic Scholar | 三源搜索 |
| 创新点生成 | AI 自主生成 | 用户主导 + AI 辅助 |
| 实验执行 | 运行代码 | 分析已有数据 |
| 论文撰写 | 模板-free | 模板引导 |
| 图表优化 | VLM 反馈 | 保留 |

---

*本技能是 AI Scientist V2 与光学大脑的深度融合，专为光学领域实验科学设计。*
