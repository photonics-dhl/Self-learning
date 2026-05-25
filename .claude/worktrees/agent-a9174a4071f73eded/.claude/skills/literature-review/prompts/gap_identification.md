# Gap Identification Prompt

## 目的
从文献分析中系统性地识别研究空白（Research Gap）。

## 什么是 Research Gap？

**定义**: 在某一研究领域内，尚未被充分研究或尚未解决的问题。

**Gap 不是**:
- ❌ "这个方向很重要"（泛泛而谈）
- ❌ "未来需要更多研究"（没有具体方向）
- ❌ "没有人研究过X"（如果没有证据支持，只是猜测）

**Gap 应该是**:
- ✅ "Zhang (2015) 实现了 2.5 THz 带宽（LiNbO3，倾斜脉冲前），但没有研究探索有机晶体 DAST 在相同泵浦条件下是否能突破 5 THz 带宽同时保持 >100 μJ 输出"
- ✅ "文献中普遍报道了空气等离子体在 2-5 THz 范围的产生，但 10 THz 以上超宽带产生的系统性数据几乎空白（证据：仅 3 篇论文涉及 >10 THz，且条件不一致）"

## Gap 类型分类

### 类型 1: 方法空白（Methodological Gap）
**定义**: 某种技术方法尚未被尝试应用于该问题。

**识别信号**:
- "X method has been used for [application A], but not for [application B]"
- "While [technique] achieved good results in [field 1], its potential in [field 2] remains unexplored"

**示例**:
"光整流在 LiNbO3 中已实现 mJ 级输出（文献X），但有机晶体 DAST 尚未在相同泵浦条件下进行系统性对比研究。"

### 类型 2: 参数空白（Parameter Gap）
**定义**: 某个关键参数区间尚未被探索。

**识别信号**:
- "Most studies focused on [parameter range A], but [range B] remains largely unexplored"
- "The effect of [parameter] on [outcome] has not been systematically studied"

**示例**:
"现有空气等离子体研究多集中在 0.1-5 mJ 泵浦能量范围，>10 mJ 条件下的转换效率 scaling 关系尚缺乏系统性数据（文献Y、Z 仅做了 2-3 个能量点）。"

### 类型 3: 比较空白（Comparative Gap）
**定义**: 两种或多种方法在相同条件下的直接对比缺失。

**识别信号**:
- "[Method A] and [Method B] have both shown promise, but no direct comparison under identical conditions exists"
- "Previous studies compared [method] with [method], but the comparison did not control for [variable]"

**示例**:
"LiNbO3（倾斜脉冲前）与 GaSe（斜向相位匹配）都宣称实现 >2 THz 带宽，但两者在相同泵浦条件（800nm，1mJ，10Hz）下的直接对比研究尚未见报道。"

### 类型 4: 理论空白（Theoretical Gap）
**定义**: 现象已被观测到，但缺乏理论解释或机制研究。

**识别信号**:
- "Although [phenomenon] has been observed, the underlying mechanism remains unclear"
- "[Theory] predicts [result], but experiments show [different result], suggesting [unknown factor]"

**示例**:
"空气等离子体产生 THz 的效率随泵浦波长变化呈现非单调关系（文献X），但缺乏统一的物理解释——电子碰撞频率与等离子体密度的耦合模型尚未建立。"

### 类型 5: 条件空白（Condition Gap）
**定义**: 在某种特定条件下的研究缺失。

**识别信号**:
- "Under [specific condition], [method] has not been studied"
- "[Application] in [environment] remains unexplored"

**示例**:
"现有 THz 产生研究多在实验室条件（干燥空气、室温）下进行，但实际大气环境（湿度 >50%、湍流）下的传输效率数据几乎空白。"

## Gap Identification 流程

### Step 1: 整理已有知识

对每个主题，列出：
- 已解决的问题（Consensus）
- 技术路线及其性能边界
- 已有研究的参数范围

### Step 2: 寻找"未填满的格子"

对照性能矩阵，找出：
- 哪些参数组合尚未被研究？
- 哪些技术路线之间没有直接比较？
- 哪些应用场景尚未被探索？

### Step 3: 验证 Gap 的存在

每个声称的 Gap 必须有文献证据：
- 直接证据: "To the best of our knowledge, no study has..."
- 间接证据: 最高引用论文只做了 X，没有做 Y，可以推算出 Y 尚未被研究
- 反面证据: 某方向只有 1-2 篇论文，且都指出需要进一步研究

### Step 4: 评估 Gap 的重要性

每个 Gap 需要评估：
- **科学意义**: 填补这个 Gap 对理解基础物理有何帮助？
- **应用价值**: 填补这个 Gap 对实际应用有何推动？
- **可操作性**: 在现有技术条件下，这个 Gap 是否可以被填补？

## 输出格式

```
## [主题名称] - Gap Identification

### Gap 1: [名称]
- **类型**: [方法/参数/比较/理论/条件]
- **描述**: [具体缺失内容]
- **文献证据**:
  - [证据1]: 文献X（年份）发现/指出/承认了...
  - [证据2]: 文献Y（年份）指出...
- **重要性**:
  - 科学意义: [说明]
  - 应用价值: [说明]
- **可能的填补路径**: [需要什么技术突破或研究方向]

### Gap 2: ...

### Gap 3: ...
```

## 常见错误

❌ **错误**: "This is an important research area."
**原因**: 没有具体指出缺失什么

❌ **错误**: "More research is needed."
**原因**: 没有指出具体需要研究什么

❌ **错误**: "No one has studied X."
**原因**: 未经充分搜索就断言，可能是搜索覆盖不足

✅ **正确**: "While Zhang (2015) achieved 2.5 THz with LiNbO3, our search reveals no systematic study comparing DAST under identical pump conditions. The only DAST study (Wang 2018) used different pump wavelengths (1.5μm vs 800nm), preventing direct comparison."

## 调用方式
```
Identify research gaps for [主题] based on:
- Papers analyzed: [列表]
- Technical routes identified: [列表]
- Consensus points: [列表]
- Gaps found: [数量]

Use systematic gap classification (methodological, parameter, comparative, theoretical, condition).
Each gap must have literature evidence.
```