---
name: scientific-writing
description: AI驱动的深度科研写作。两阶段流程：规划→流畅段落，结合文献检索和验证引用。当用户需要科研写作时触发。
---

# Scientific Writing Skill - 科研写作规范

## Overview

AI驱动的深度研究和格式化科研输出，结合文献检索和验证引用生成可发表的手稿。

## 核心要求

1. **始终写完整段落** - 最终稿件中不使用项目符号
2. **两阶段写作流程**：
   - Stage 1: 创建要点大纲，标记主要论点、关键研究、数据点和逻辑流
   - Stage 2: 转换为流畅散文，整合引用，确保逻辑连贯
3. **每篇论文需要图形摘要**
4. **图表要求**：研究论文至少5张图（推荐6-8张）

## IMRAD 结构

标准稿件格式包括：
- Introduction（引言）
- Methods（方法）
- Results（结果）
- And Discussion（讨论）

针对不同类型另有替代结构：
- Reviews（综述）
- Case Reports（病例报告）
- Meta-analyses（荟萃分析）
- Methods Papers（方法论文）

## 引用管理

支持的格式：
- AMA（上标编号）
- Vancouver（括号编号）
- APA（作者-日期）
- Chicago（脚注-参考书目）
- IEEE

## 视觉元素

**图形摘要生成：**
```bash
python scripts/generate_schematic.py "Graphical abstract for [title]" -o figures/graphical_abstract.png
```

**按文档类型的图表要求：**
- 研究论文：至少5张图
- 文献综述：4张图
- 市场研究：20+张图

## 写作流程

1. 确定目标期刊和适用的报告指南
2. 先后写方法、结果、讨论、引言、摘要
3. 先创建图表作为数据故事骨干
4. 每个章节遵循两阶段流程

## 报告指南

根据研究类型应用：
- CONSORT：随机试验
- STROBE：观察性研究
- PRISMA：系统综述
- STARD：诊断准确性
- TRIPOD：预测模型

## 段落写作原则

| 要求 | 说明 |
|------|------|
| 清晰 | 精确语言，首次使用定义缩写 |
| 简洁 | 平均句子长度15-20词 |
| 准确 | 报告精确值，术语一致 |
| 客观 | 无偏地呈现结果 |

## 调用方式

```
请使用 scientific-writing skill 撰写研究论文
```

结合其他skill：
```
请使用 academic-research skill 检索文献，然后使用 scientific-writing skill 撰写论文
```