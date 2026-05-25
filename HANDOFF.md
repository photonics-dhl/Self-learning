# HANDOFF — Cross-Session Context Bridge

> Updated: 2026-05-21 (Session 18 — 学科基础笔记全面RAG扩充)

## Last Task: 学科基础笔记全面RAG扩充（10个笔记）

### 完成内容

对所有学科基础笔记进行推导详细化、物理图像清晰化扩充。总计新增约 3200 行。

| 笔记 | 原始 | 扩充后 | 核心新增 |
|------|------|--------|---------|
| 01 电磁场理论基础 | 394 | ~700 | 矢量分析恒等式、标矢势推导、规范自由度、多极展开/Larmor、Green函数/推迟势、Drude色散 |
| 03 波动光学 | 409 | ~550 | 基尔霍夫衍射积分、FP干涉(Airy函数+细度推导)、薄膜/Newton环、Jones+Stokes、相干性深入 |
| 04 光学原理 | 344 | **723** | 程函方程(从Helmholtz推导)、ABCD矩阵5种+成像条件、厚透镜、Fresnel公式完整推导 |
| 05 傅里叶光学 | 349 | **786** | 角谱理论、透镜FT精确推导、4f系统、OTF/MTF、Zernike相衬显微镜 |
| 06 量子光学 | 808 | **1135** | Quadrature+Homodyne、场量子化逐步推导、Wigner函数/相空间、g^(2)四种态推导、Casimir/Lamb |
| 07 激光物理 | 411 | ~620 | 四能级速率方程+阈值、高斯光束+ABCD定律、锁模几何级数推导+KLM、Schawlow-Townes线宽 |
| 07 腔QED | 540 | 540 | 已全面，未改 |
| 08 半导体物理 | 551 | **907** | Kronig-Penney+Bloch定理、PN结Poisson+Shockley、载流子输运/Einstein、量子阱/QCL |
| 10 纳米光学 | 388 | **767** | SPP色散推导、LSPR+消光截面+Frohlich条件、光学天线、近场增强+SERS |
| 11 超表面 | 429 | **717** | 广义Snell定律推导、超原子设计(6种)、metalens设计、12类应用表 |

### 工作方式

- 主线程直接编辑：01, 03, 07_激光, 06_量子光学(第二轮)
- Agent并行处理：04, 05, 08, 10+11（4个agent同时运行）
- 已RAG扩充（前一轮）：02_麦克斯韦, 09_近场, 12_微波, 13_无线通信, 14_半导体工艺

### RAG使用情况

- 搜索了 electromagnetic field, diffraction, laser cavity, plasmon 等主题
- 主要RAG来源：Scully1997量子光学教材、THz Roadmap 2017、Dressel2015时空代数
- 新增引用标记："RAG 库收录" 附在 Scully1997, Dressel2015, Born1999 等

## Next Task: DFT/TDDFT 学习

用户希望学习 **密度泛函理论 (DFT)** 和 **含时密度泛函理论 (TDDFT)**。

### 预期方向

1. 在学科基础中创建新的 DFT/TDDFT 笔记
2. 内容可能包括：
   - Hohenberg-Kohn 定理（DFT理论基础）
   - Kohn-Sham 方程（实际计算框架）
   - 交换关联泛函（LDA, GGA, hybrid）
   - TDDFT（Runge-Gross 定理, 线性响应）
   - 常用软件（VASP, QE, GPAW, Octopus）
   - 与光学/THz研究的关联（材料光学性质计算）

### 相关现有笔记

- [[量子光学]] — 多体量子力学基础
- [[半导体物理]] — 能带结构是DFT的核心应用
- [[电磁场理论基础]] — 量子力学前驱知识

## Previous Sessions

- **Session 17**: 博士毕业论文骨架+关键章节生成测试（zjuthesis, 49页PDF）
- **Session 16**: academic-craft 写作诊断skill + 草稿修订
- **Session 15**: paper-writing Stage 0 四层素材准备pipeline
- **Session 14**: 论文写作skill 4→2+1架构重组
