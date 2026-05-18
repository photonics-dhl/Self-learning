# Anti-AI Writing Patterns — 论文写作AI痕迹消除指南

> 从 humanizer skill 35种模式中提取论文写作最关键的12种，按审稿人识别风险分级。

## Tier 1: 必须消除（审稿人一眼识别）

| AI模式 | 常见位置 | 替代写法 |
|--------|---------|---------|
| "has attracted significant attention" | Intro L1 | 引用3+篇具体论文说明谁在关注什么问题 |
| "plays an important/vital role" | Intro L1 | 说明具体应用场景+量化指标 |
| "despite significant progress" | Intro L2 | 列举2-3项具体进展+具体遗留问题 |
| "promising applications" | Abstract/Conclusion | 列举具体应用+所需性能指标 |
| "comprehensive study" | Abstract | 说明具体覆盖了什么范围 |
| "groundbreaking/revolutionary" | 任何位置 | 删除。用数据和对比说话 |

### 替换示例

**AI味**：
> Terahertz radiation has attracted significant attention in recent years due to its promising applications in spectroscopy and imaging.

**人类写法**：
> Terahertz radiation (0.1–10 THz) excites vibrational modes in polar molecules [1-3] and penetrates most dielectrics [4], enabling spectroscopic identification of concealed substances [5] and nondestructive testing of composite materials [6].

要点：每个形容词用具体论文或数据替代。

## Tier 2: 应当弱化（减少但不完全消除）

| AI模式 | 问题 | 替代写法 |
|--------|------|---------|
| "significantly improved" | 无量化 | "improved by X%" 或 "improved from A to B" |
| "remarkably/unprecedented" | 主观夸大 | 删除或给出客观对比 |
| "in-depth/comprehensive analysis" | 空洞 | 描述具体分析了什么 |
| "it is worth noting that" | 凑字 | 删除，直接陈述 |
| "sheds light on" | 隐喻过度 | "reveals" 或 "demonstrates" |
| "paves the way for" | 模板化 | 具体说明下一步能做什么 |

## Tier 3: 物理写作特有（学科相关）

### 公式处理

| 问题 | 后果 | 规则 |
|------|------|------|
| display equation后无解释 | 审稿人跳过公式 | 每个display equation后接一句话物理含义 |
| 参数第一次出现不定义 | 读者无法理解 | 新符号立即用括号定义 |
| 公式堆砌无叙事 | 读起来像教科书 | 公式之间用文字串联物理逻辑 |

### 图表引用

| 问题 | 后果 | 规则 |
|------|------|------|
| "as shown in Fig. X" 无引导 | 审稿人不知道看什么 | "Fig. X shows [结论]. Note that [关键特征]." |
| 图注只是label | 图不自足 | caption包含：标题+描述+关键信息 |
| 方法部分只引用综述 | 审稿人无法判断创新性 | 简述经典方法+明确本文改进点 |

### 讨论部分

| 问题 | 后果 | 规则 |
|------|------|------|
| "future work will..." | 空洞承诺 | 改为"open question"（具体指出什么条件下能解决）|
| 局限性写"样本量不够" | 不够诚实 | 量化局限（"方法在X条件下精度降低Y%，原因是Z"）|
| 只与自己的前作对比 | 审稿人质疑 | 必须与≥3种竞争方法量化对比 |

## Intro写作反模式（v5.2实测问题）

### 反模式1: "取得了显著进展"

**AI味**（中文）：
> 近年来，太赫兹成像技术取得了显著进展，在生物医学、无损检测等领域具有重要应用前景。

**人类写法**（中文）：
> 太赫兹成像的空间分辨率在2010-2024年间从 λ/2 提升到 λ/50 [1-3]，但现有系统仍需逐点扫描，成像速度限制在 ~1 pixel/s [4,5]。

### 反模式2: "国内外研究现状"逐篇罗列

**AI味**：
> Smith等[1]提出了一种方法。Jones等[2]改进了该方法的精度。Lee等[3]将其拓展到新领域。Wang等[4]...

**人类写法**（主题综合）：
> 提高太赫兹成像分辨率有三条技术路线：孔径近场探针（~λ/20, <0.1%效率）[1,2]、超表面透镜（~λ/50, ~10%效率）[3-5]、和光栅耦合方案（~λ/30, ~5%效率）[6]。三种路线的共同瓶颈是逐点扫描导致成像速度慢。

### 反模式3: Intro-Body内容重复

**AI味**（Intro路线图过于详细）：
> 本文第2章介绍太赫兹波在非线性晶体中的产生原理，包括光整流效应和光学参量过程；第3章展示实验结果...

**人类写法**（只列主题不解释）：
> 本文组织如下：Section II 建立理论框架；Section III 报告实验结果；Section IV 讨论物理机制。各章开头的引导句说明该章目标。

## 自检清单

写完每节后，搜索以下关键词，如果出现则需修改：
- [ ] "significant attention" → 替换为具体引用
- [ ] "important role" → 替换为具体应用
- [ ] "significant progress" → 替换为具体进展
- [ ] "promising" → 替换为具体指标
- [ ] "groundbreaking/revolutionary" → 删除
- [ ] "paves the way" → 替换为具体下一步
- [ ] 连续3+篇论文逐篇罗列 → 合并为主题综合
- [ ] "as shown in Fig." 后无引导句 → 添加读图引导
- [ ] display equation后无物理解释 → 添加一句话
