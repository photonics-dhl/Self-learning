---
name: scientific-writing
description: 科研写作工艺——段落/语言层面的写作工具。两阶段写作流程、段落清晰度检查、反向大纲、7条全局原则、段落角色标注、Claim-Evidence映射。当用户需要优化段落质量、改善逻辑流、做语言层面润色时触发。不负责论文结构规划（那是paper-writing）。
---

# Scientific Writing Skill — 科研写作工艺

## 核心定位

写作的**语言层**工具：段落结构、句子清晰度、逻辑流、术语一致性。

**不负责**：论文结构规划（用 `paper-writing`）、中文毕业论文（用 `bishe-guider`）、去AI痕迹（用 `humanizer`）。

## 核心技术

### 1. 两阶段写作流程

**Stage 1: 要点大纲**
- 每段标记主要论点
- 标记关键研究和数据点
- 标记逻辑流向（因果/对比/递进/深化）

**Stage 2: 流畅散文**
- 转换为完整段落
- 整合引用
- 确保逻辑连贯
- 最终稿件不使用项目符号

### 2. 7条全局写作原则

1. **一段一意** — 每段只传达一个信息
2. **首句立题** — 第一句陈述段落主旨
3. **名词自含定义** — 新术语使用前先定义
4. **保持句间连贯** — 因果、对比、结果或深化
5. **对抗性自我审查** — 以怀疑审稿人角度阅读
6. **视觉质量是核心内容** — 非装饰
7. **使用简洁、墨迹最少的表格**

### 3. 段落清晰度检查

#### 外部读者视角
- 段落是否有一个明确信息？
- 首句是否说明段落目的？
- 所有关键名词是否无需隐藏上下文即可理解？
- 每句是否通过清晰关系（因果/对比/结果/深化）连接？

#### 反向大纲
1. 写下每段的主题句（如果找不到 → 段落主旨不清）
2. 检查相邻段主题句之间是否有逻辑递进
3. 标记所有claim，检查每个claim是否有对应evidence
4. 检查映射关系并修订

### 4. 段落角色标注

写作时为每段标注角色，确保段落间有完整叙事：

| 角色 | 功能 | 示例关键词 |
|------|------|-----------|
| 开篇（Opening） | 引入主题 | "The central question is..." |
| 挑战（Challenge） | 指出问题/局限 | "However, this approach fails when..." |
| 方法（Method） | 描述解决方案 | "We address this by..." |
| 优势（Advantage） | 说明方法优点 | "This allows us to..." |
| 论据（Evidence） | 呈现数据/结果 | "Fig. X shows..." |
| 局限（Limitation） | 承认不足 | "This method requires..." |

### 5. Claim-Evidence 映射

每个主要claim必须有对应evidence：

```markdown
| Claim | Evidence | Status |
|-------|----------|--------|
| "Our method achieves λ/50 resolution" | Fig. 3, cross-section measurement | supported |
| "The approach is broadband" | Fig. 4, 0.5-3 THz transmission | supported |
| "The method is robust to misalignment" | [missing — need additional data] | needs evidence |
```

**规则**: 无法用结果支持的论点需弱化或删除。

### 6. 引用格式

| 格式 | 风格 | 适用 |
|------|------|------|
| AMA | 上标编号 | 生物医学 |
| Vancouver | 括号编号 | 物理学 |
| APA | 作者-日期 | 社会科学 |
| IEEE | 方括号编号 | 工程学 |
| Chicago | 脚注 | 人文学科 |

### 7. 报告指南（按研究类型）

| 指南 | 研究类型 |
|------|---------|
| CONSORT | 随机试验 |
| STROBE | 观察性研究 |
| PRISMA | 系统综述 |
| STARD | 诊断准确性 |
| TRIPOD | 预测模型 |

## 段落写作参数

| 指标 | 目标值 |
|------|-------|
| 平均句子长度 | 15-20词 |
| 段落长度 | 4-8句 |
| 首次缩写定义 | 立即定义 |
| 时态一致性 | 方法/结果用过去时 |

## 输出约定

被要求优化段落时返回：

1. **简洁段落提纲** (3-7条)
2. **修订后段落** 标注明确角色（开篇/挑战/方法/优势/论据/局限）
3. **自审清单**：清晰度、流畅性、术语一致性、无依据论点、缺失证据
4. **Claim-Evidence映射表**

## 调用方式

```
请使用 scientific-writing skill 优化这段段落的逻辑流
请使用 scientific-writing skill 对这节做反向大纲检查
请使用 scientific-writing skill 检查claim-evidence一致性
```

组合使用：
```
请使用 paper-writing skill 规划论文结构，再用 scientific-writing skill 优化每段的写作质量
```

## IMRAD Checklist 与期刊格式速查（源自 K-Dense）

### IMRAD 逐节检查清单

**Introduction**
- [ ] 研究背景与重要性是否在首段建立
- [ ] 文献综述是否系统覆盖关键工作（近 5-10 年为主）
- [ ] 知识空白/争议是否明确指出
- [ ] 研究目标/假设是否清晰陈述
- [ ] 研究新颖性与意义是否说明

**Methods**
- [ ] 实验设计可否被他人重复
- [ ] 样本/材料/设备是否完整描述（含型号、厂商）
- [ ] 统计方法是否有据可依（含效应量与置信区间）
- [ ] 伦理审批与知情同意是否注明
- [ ] 参数选择是否有文献或理论支撑

**Results**
- [ ] 逻辑流是否从主要发现到次要发现
- [ ] 是否与图表（Fig/Table）紧密整合
- [ ] 统计显著性是否附效应量（不仅是 p 值）
- [ ] 是否仅客观报告、未掺杂解读
- [ ] 阴性/矛盾结果是否如实报告

**Discussion**
- [ ] 是否回应 Introduction 中的研究问题
- [ ] 是否与已有文献进行定量对比（非仅罗列）
- [ ] 是否承认局限性并量化影响
- [ ] 是否提出机制性解释（非现象描述）
- [ ] 是否给出实践意义与未来方向

### 期刊格式速查

| 要求 | Nature | Science | PRL | Optica |
|------|--------|---------|-----|--------|
| 正文上限 | ~3000 词（不含方法） | ~4500 词 | 3750 词（含 refs） | 8000 词 |
| 摘要 | 200 词，无结构 | 125 词，无结构 | ~600 字符 | 250 词，无结构 |
| 引用格式 | Nature 编号 | Science 编号 | APS 编号 [1] | OSA 编号 |
| 图数 | ≤6（排版后） | ≤6 | ≤8 | ≤10 |
| 方法位置 | 正文后/补充材料 | 正文后/补充材料 | 融入正文 | 融入正文 |
| 补充材料 | 无上限 | 无上限 | ≤2500 词 | 无上限 |
| 特殊要求 | editorial summary + 图形摘要 | summary paragraph | PRL 编辑评分 | emphasise innovation |
| 参考文献上限 | ~50 | ~40 | ~30 | ~50 |
| LaTeX 模板 | nature.tex | science.tex | revtex4-2 | osajnl.cls |
