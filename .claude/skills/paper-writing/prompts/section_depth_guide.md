# Section Depth Guide — 章节撰写质量控制

> 期刊论文的质量控制框架。三个递进层次：先把话说清楚，再确保每条claim能经受审稿人质疑，最后确保全文叙事连贯。

## 三级深度体系

### Level 1: 清晰度层（Clear Communication）
- 每段有明确主题句，首句立题
- 术语首次出现时定义缩写
- 数据展示有统计标注（误差棒、样本量、显著性）
- 图表自足（不看正文也能理解图的核心信息）

### Level 2: 审稿人抗辩层（Reviewer Defense）
- 关键claim后紧跟证据或预判审稿人质疑
- 与文献对比有量化数据（不只说"优于前人"，给出具体%或倍数）
- Gap陈述引用证明gap存在的具体论文
- 方法创新点与经典方法有明确区分

### Level 3: 叙事连贯层（Narrative Coherence）
- 章节间有过渡句连接逻辑
- 全文核心叙事一致（引言的gap在结论中被回答）
- 创新点声明与证据链一一对应
- 讨论部分讲清楚"so what"（对领域的意义）

## 各章节深度要求

| 章节 | 最低深度 | 推荐深度 | 特殊要求 |
|------|---------|---------|---------|
| Abstract | L3 | L3 | 背景-方法-结果-结论，每句对应一个章节 |
| Introduction | L3 | L3 | Gap唯一 + 按技术路线综合文献（不逐篇罗列） |
| Methods | L1 | L2 | 可复现 + 公式配物理上下文 |
| Results | L2 | L3 | 引用图表时引导读者看核心结论 |
| Discussion | L3 | L3 | 量化对比表 + 诚实局限 + 领域意义 |
| Conclusion | L2 | L3 | 回答引言gap + 不过度外推 |

## 深度自检方法

### 反向大纲（Reverse Outline）
写完每节后执行：
1. 写下每段的主题句（如果找不到，说明段落主旨不清）
2. 检查相邻段主题句之间是否有逻辑递进（因果/对比/递进）
3. 标记所有claim，检查每个claim是否有对应evidence

### 审稿人模拟
对每个主要claim，回答：
- "这个claim最弱的环节是什么？"
- "如果审稿人说'证据不足'，我有什么补充？"
- "这个claim是否超出了数据能支撑的范围？"

## 物理公式撰写要求（Methods/Theory）

每个display equation必须包含：
1. **引入语**：说明为什么展示这个方程（"To quantify X, we use..."）
2. **参数定义**：新符号紧跟定义（"where λ is the wavelength and n is the refractive index"）
3. **适用条件**：方程在什么条件下成立或失效

示例（正常期刊论文写法）：
```
The measured spectral intensity can be expressed as
$$I(\omega) = |E(\omega)|^2 \propto \left|\int_{-\infty}^{+\infty} E(t) e^{i\omega t} dt\right|^2$$
where $E(t)$ is the time-domain electric field. This expression shows that the measured spectrum
is the squared magnitude of the Fourier transform — the phase information is entirely lost.
Consequently, the time-domain waveform cannot be uniquely reconstructed from spectral data
alone without additional constraints such as Kramers-Kronig relations.
```

## 图表撰写要求（Results）

每个figure引用必须引导读者：

**错误写法**：
> The results are shown in Fig. 3.

**正确写法**：
> Fig. 3 shows the measured THz transmission spectra through the meta-lens array.
> Note that the resonance at 1.2 THz (dashed line) shifts by 15% when the gap size increases from 5 to 10 μm,
> consistent with the LC circuit model prediction (Eq. 4).

要点：
- 引导读者看**核心结论**，不是"结果见图X"
- 标注**关键特征**（峰值位置、趋势变化、异常点）
- 连接**前文理论**（"consistent with Eq. X"）

## 讨论部分竞争方法对比表

Discussion必须包含一张量化对比表：

```markdown
| Method | Ref. | Key Metric | Advantage | Limitation | vs. This Work |
|--------|------|-----------|-----------|------------|---------------|
| Method A | [1] | X nm resolution | Well-established | Requires vacuum | Our method works in air |
| Method B | [2] | Y% efficiency | High throughput | Narrow bandwidth | Our method: 3× bandwidth |
| **This work** | — | **Z nm** | **Both X and Y** | **Requires alignment** | — |
```

## 引言技术演化叙事

Intro的"研究现状"部分不应是逐篇罗列，而应讲一个技术演化的故事：

**错误（逐篇罗列）**：
> Smith et al. [1] demonstrated X. Jones et al. [2] improved Y. Lee et al. [3] extended Z.

**正确（主题综合）**：
> The resolution of THz imaging has improved through three generations of approaches.
> Early work relied on aperture-based near-field probes [1,2], which achieved λ/20 resolution
> but suffered from low throughput (< 0.1%). The introduction of metasurface lenses [3-5]
> overcame this bottleneck, enabling λ/50 resolution with 10% efficiency.
> However, all current approaches share a common limitation: they require raster scanning,
> which limits imaging speed to ~1 pixel/s. This work eliminates scanning entirely by...

要点：
- 按**技术路线**分组，不按论文时间顺序罗列
- 每组只引核心代表论文（2-3篇）
- 结尾自然过渡到gap（"all current approaches share a common limitation..."）
