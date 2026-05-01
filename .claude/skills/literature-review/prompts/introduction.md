# 引言段落 Prompt

## 目的
生成符合 C-C-C 结构的引言段落，遵循 Pautasso (2013) 和 Mensah (2019) 的学术规范。

## 输入
- 研究主题
- 已发现的关键 Gap（来自 Gap Identification）
- 检索到的论文数量和分布

## 输出结构

### Paragraph 1: Context（领域重要性）
```
太赫兹(THz)波段位于微波与红外之间，是连接电子学与光学的桥梁，在[具体应用领域]展现出重要应用前景。
然而，[核心难点]一直是该领域核心技术难题，制约着相关应用的发展。
```
- 范围：1-2 句
- 引用：领域重要性的奠基性文献（1-2篇）

### Paragraph 2: 已有进展与问题
```
近年来，[技术路线A]在[具体指标]方面取得了显著进展（文献X、Y）。
[技术路线B]则通过[具体方法]实现了[具体性能]，为该领域提供了新的思路。
然而，这些方案在[关键维度]上仍面临不可兼得的困境：[具体矛盾]。
```
- 必须指出具体的进展和局限
- 用数据说话（带具体指标）

### Paragraph 3: Gap Identification（研究空白）
```
【研究空白】通过系统性文献调研，我们发现现有文献存在以下不足：

- [Gap 1]: [具体缺失]。文献X和Y虽然解决了[问题A]，但对于[问题B]的研究仍然空白。
  具体表现在：...[量化描述]。

- [Gap 2]: [具体缺失]。现有研究多聚焦于[方面]，而对[另一方面]缺乏系统性的[研究/对比/理论分析]。
  证据：文献Z在此方向只进行了[有限探索]，尚未有研究[具体做什么]。

- [Gap 3]: [具体缺失]。在[特定条件/参数范围]下，[现象/方法/理论]尚未被研究。
```
- 每个 Gap 必须有文献依据
- 引用具体论文，不能泛泛而谈

### Paragraph 4: 本文目标
```
本综述基于[数据库]检索的[N]篇相关论文，对[N]个主题方向进行系统性的主题综合。
我们将从[维度A]、[维度B]、[维度C]三个角度分析各技术路线的核心权衡，
并识别各主题的研究空白，为[具体应用场景]下的THz源选择提供参考依据。
```
- 明确说明检索范围和方法
- 预告综述结构

## 注意事项

1. **Context 要具体**: "THz radiation is important" 太泛；"THz imaging enables label-free tissue diagnosis with 100 μm resolution" 更具体
2. **Gap 要可验证**: "lack of research on X" 不够；"while Zhang (2015) achieved 2.5 THz bandwidth, no study has explored whether DAST can exceed 5 THz under same pump conditions" 更好
3. **避免泛泛而谈**: 不用 "recent years many researchers have studied..." 而用具体人名和年份
4. **C-C-C 每段都要有**: 不能只有 Context 和 Content，必须有 Conclusion（哪怕是隐含的）

## 错误示例（避免）
❌ "Terahertz technology is very important and has many applications. Many researchers have studied this topic. In this review, we will discuss various methods."

✅ "THz radiation (0.1-10 THz) enables label-free imaging with 100 μm spatial resolution, showing promise for biological tissue diagnosis [cite]. However, the low conversion efficiency of practical THz sources remains the critical bottleneck: state-of-the-art optical rectification in LiNbO3 achieves only 0.1% efficiency at 1 μm pump [cite, cite]. We identify three specific gaps in the literature..."

## 调用方式
```
Write introduction paragraphs for [主题] with [N] papers found, covering [主题列表].
Gaps identified: [Gap1], [Gap2], [Gap3].
Target audience: [具体领域] researchers.
```