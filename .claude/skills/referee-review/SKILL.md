---
name: referee-review
description: |
  审稿人专用技能：系统化审稿流程。7阶段结构化审稿（初评→逐节→统计→可复现→图表→伦理→写作）。
  适用于作为审稿人评价他人稿件，生成标准审稿信。含物理/光学实验特有审查项。
  与 paper-review（自审工具）和 academic-craft（写作诊断）互补。
tags:
  - 审稿
  - referee
  - peer-review
  - 统计审稿
  - 审稿信
  - 光学
  - 物理期刊
allowed-tools: Read Write Edit Bash
license: MIT license (based on K-Dense scientific-agent-skills)
metadata:
  version: "1.0-customized"
  original-author: K-Dense Inc.
  customized-for: optics PhD peer review
---

# Referee Review — 审稿人专用审稿技能

## 定位

作为期刊审稿人（referee）系统评价他人稿件。与以下 skills 互补：
- `paper-review`：投稿前自审工具（检查自己论文格式）
- `academic-craft`：写作质量诊断（6维度 A/B/C 打分）
- `referee-review`（本 skill）：审别人的稿件，生成标准审稿信

## 触发场景

- "帮我审这篇论文" / "作为审稿人评价这篇稿件"
- "生成审稿意见" / "写审稿信"
- "评价这篇论文的方法论/统计分析"
- "审查论文的可复现性"
- Reviewing scientific manuscripts as a referee for journals

## 适用期刊

物理/光学领域常见期刊：PRL, PRA/B/D, Optica, Light: Sci. Appl., APL, IEEE Photonics, Nat. Photonics, Sci. Rep.

---

## Peer Review Workflow

Conduct peer review systematically through the following stages, adapting depth and focus based on the manuscript type and discipline.

### Stage 1: Initial Assessment

Begin with a high-level evaluation to determine the manuscript's scope, novelty, and overall quality.

**Key Questions:**
- What is the central research question or hypothesis?
- What are the main findings and conclusions?
- Is the work scientifically sound and significant?
- Is the work appropriate for the intended venue?
- Are there any immediate major flaws that would preclude publication?

**Output:** Brief summary (2-3 sentences) capturing the manuscript's essence and initial impression.

### Stage 2: Detailed Section-by-Section Review

Conduct a thorough evaluation of each manuscript section, documenting specific concerns and strengths.

#### Abstract and Title
- **Accuracy:** Does the abstract accurately reflect the study's content and conclusions?
- **Clarity:** Is the title specific, accurate, and informative?
- **Completeness:** Are key findings and methods summarized appropriately?
- **Accessibility:** Is the abstract comprehensible to a broad scientific audience?

#### Introduction
- **Context:** Is the background information adequate and current?
- **Rationale:** Is the research question clearly motivated and justified?
- **Novelty:** Is the work's originality and significance clearly articulated?
- **Literature:** Are relevant prior studies appropriately cited?
- **Objectives:** Are research aims/hypotheses clearly stated?

#### Methods
- **Reproducibility:** Can another researcher replicate the study from the description provided?
- **Rigor:** Are the methods appropriate for addressing the research questions?
- **Detail:** Are protocols, reagents, equipment, and parameters sufficiently described?
- **Ethics:** Are ethical approvals, consent, and data handling properly documented?
- **Statistics:** Are statistical methods appropriate, clearly described, and justified?
- **Validation:** Are controls, replicates, and validation approaches adequate?

**Critical elements to verify:**
- Sample sizes and power calculations
- Randomization and blinding procedures
- Inclusion/exclusion criteria
- Data collection protocols
- Computational methods and software versions
- Statistical tests and correction for multiple comparisons

#### Results
- **Presentation:** Are results presented logically and clearly?
- **Figures/Tables:** Are visualizations appropriate, clear, and properly labeled?
- **Statistics:** Are statistical results properly reported (effect sizes, confidence intervals, p-values)?
- **Objectivity:** Are results presented without over-interpretation?
- **Completeness:** Are all relevant results included, including negative results?
- **Reproducibility:** Are raw data or summary statistics provided?

**Common issues to identify:**
- Selective reporting of results
- Inappropriate statistical tests
- Missing error bars or measures of variability
- Over-fitting or circular analysis
- Batch effects or confounding variables
- Missing controls or validation experiments

#### Discussion
- **Interpretation:** Are conclusions supported by the data?
- **Limitations:** Are study limitations acknowledged and discussed?
- **Context:** Are findings placed appropriately within existing literature?
- **Speculation:** Is speculation clearly distinguished from data-supported conclusions?
- **Significance:** Are implications and importance clearly articulated?
- **Future directions:** Are next steps or unanswered questions discussed?

**Red flags:**
- Overstated conclusions
- Ignoring contradictory evidence
- Causal claims from correlational data
- Inadequate discussion of limitations
- Mechanistic claims without mechanistic evidence

#### References
- **Completeness:** Are key relevant papers cited?
- **Currency:** Are recent important studies included?
- **Balance:** Are contrary viewpoints appropriately cited?
- **Accuracy:** Are citations accurate and appropriate?
- **Self-citation:** Is there excessive or inappropriate self-citation?

### Stage 3: Methodological and Statistical Rigor

Evaluate the technical quality and rigor of the research with particular attention to common pitfalls.

**Statistical Assessment:**
- Are statistical assumptions met (normality, independence, homoscedasticity)?
- Are effect sizes reported alongside p-values?
- Is multiple testing correction applied appropriately?
- Are confidence intervals provided?
- Is sample size justified with power analysis?
- Are parametric vs. non-parametric tests chosen appropriately?
- Are missing data handled properly?
- Are exploratory vs. confirmatory analyses distinguished?

**Experimental Design:**
- Are controls appropriate and adequate?
- Is replication sufficient (biological and technical)?
- Are potential confounders identified and controlled?
- Is randomization properly implemented?
- Are blinding procedures adequate?
- Is the experimental design optimal for the research question?

**Computational/Bioinformatics:**
- Are computational methods clearly described and justified?
- Are software versions and parameters documented?
- Is code made available for reproducibility?
- Are algorithms and models validated appropriately?
- Are assumptions of computational methods met?
- Is batch correction applied appropriately?

### Stage 4: Reproducibility and Transparency

Assess whether the research meets modern standards for reproducibility and open science.

**Data Availability:**
- Are raw data deposited in appropriate repositories?
- Are accession numbers provided for public databases?
- Are data sharing restrictions justified (e.g., patient privacy)?
- Are data formats standard and accessible?

**Code and Materials:**
- Is analysis code made available (GitHub, Zenodo, etc.)?
- Are unique materials available or described sufficiently for recreation?
- Are protocols detailed in sufficient depth?

**Reporting Standards:**
- Does the manuscript follow discipline-specific reporting guidelines (PRISMA for systematic reviews)?
- Are all experimental parameters sufficient for replication?
- Are all elements of the appropriate checklist addressed?

### Stage 5: Figure and Data Presentation

Evaluate the quality, clarity, and integrity of data visualization.

**Quality Checks:**
- Are figures high resolution and clearly labeled?
- Are axes properly labeled with units?
- Are error bars defined (SD, SEM, CI)?
- Are statistical significance indicators explained?
- Are color schemes appropriate and accessible (colorblind-friendly)?
- Are scale bars included for images?
- Is data visualization appropriate for the data type?

**Integrity Checks:**
- Are there signs of image manipulation (duplications, splicing, inconsistent scale bars)?
- Are representative images/measurements truly representative?
- Are all conditions shown (no selective presentation)?
- Are spectra/plots showing raw data or only processed results?

**Clarity:**
- Can figures stand alone with their legends?
- Is the message of each figure immediately clear?
- Are there redundant figures or panels?
- Would data be better presented as tables or figures?

### Stage 6: 研究诚信与光学实验特有检查

**研究诚信（通用）：**
- 是否存在数据伪造或篡改的嫌疑？
- 作者署名是否合理？
- 利益冲突是否声明？
- 基金来源是否披露？
- 是否存在抄袭或重复发表？

**光学/物理实验特有审查项：**
- 激光参数是否完整报告？（波长、功率、脉宽、重复频率、光束质量 M²）
- 光学系统校准是否描述？（波长校准、功率计校准、光路对准方法）
- 探测器参数是否明确？（类型、带宽、NEP、响应率、线性范围）
- 实验环境条件是否说明？（温度、湿度、振动隔离、暗室条件）
- 样品制备是否可复现？（材料来源、纯度、厚度、表面处理）
- 数值模拟参数是否完整？（网格分辨率、收敛判据、边界条件、软件版本）
- 误差分析是否系统化？（系统误差 vs 随机误差、不确定度传播、误差棒含义）
- 光谱/图像数据是否提供原始格式？（不只是处理后的图，有无原始数据可用性声明）
- 理论假设的适用范围是否明确讨论？

### Stage 7: Writing Quality and Clarity

Assess the manuscript's clarity, organization, and accessibility.

**Structure and Organization:**
- Is the manuscript logically organized?
- Do sections flow coherently?
- Are transitions between ideas clear?
- Is the narrative compelling and clear?

**Writing Quality:**
- Is the language clear, precise, and concise?
- Are jargon and acronyms minimized and defined?
- Is grammar and spelling correct?
- Are sentences unnecessarily complex?
- Is the passive voice overused?

**Accessibility:**
- Can a non-specialist understand the main findings?
- Are technical terms explained?
- Is the significance clear to a broad audience?

## Structuring Peer Review Reports

Organize feedback in a hierarchical structure that prioritizes issues and provides actionable guidance.

### Summary Statement

Provide a concise overall assessment (1-2 paragraphs):
- Brief synopsis of the research
- Overall recommendation (accept, minor revisions, major revisions, reject)
- Key strengths (2-3 bullet points)
- Key weaknesses (2-3 bullet points)
- Bottom-line assessment of significance and soundness

### Major Comments

List critical issues that significantly impact the manuscript's validity, interpretability, or significance. Number these sequentially for easy reference.

**Major comments typically include:**
- Fundamental methodological flaws
- Inappropriate statistical analyses
- Unsupported or overstated conclusions
- Missing critical controls or experiments
- Serious reproducibility concerns
- Major gaps in literature coverage
- Ethical concerns

**For each major comment:**
1. Clearly state the issue
2. Explain why it's problematic
3. Suggest specific solutions or additional experiments
4. Indicate if addressing it is essential for publication

### Minor Comments

List less critical issues that would improve clarity, completeness, or presentation. Number these sequentially.

**Minor comments typically include:**
- Unclear figure labels or legends
- Missing methodological details
- Typographical or grammatical errors
- Suggestions for improved data presentation
- Minor statistical reporting issues
- Supplementary analyses that would strengthen conclusions
- Requests for clarification

**For each minor comment:**
1. Identify the specific location (section, paragraph, figure)
2. State the issue clearly
3. Suggest how to address it

### Specific Line-by-Line Comments (Optional)

For manuscripts requiring detailed feedback, provide section-specific or line-by-line comments:
- Reference specific page/line numbers or sections
- Note factual errors, unclear statements, or missing citations
- Suggest specific edits for clarity

### Questions for Authors

List specific questions that need clarification:
- Methodological details that are unclear
- Seemingly contradictory results
- Missing information needed to evaluate the work
- Requests for additional data or analyses

## Tone and Approach

Maintain a constructive, professional, and collegial tone throughout the review.

**Best Practices:**
- **Be constructive:** Frame criticism as opportunities for improvement
- **Be specific:** Provide concrete examples and actionable suggestions
- **Be balanced:** Acknowledge strengths as well as weaknesses
- **Be respectful:** Remember that authors have invested significant effort
- **Be objective:** Focus on the science, not the scientists
- **Be thorough:** Don't overlook issues, but prioritize appropriately
- **Be clear:** Avoid ambiguous or vague criticism

**Avoid:**
- Personal attacks or dismissive language
- Sarcasm or condescension
- Vague criticism without specific examples
- Requesting unnecessary experiments beyond the scope
- Demanding adherence to personal preferences vs. best practices
- Revealing your identity if reviewing is double-blind

## Special Considerations by Manuscript Type

### Original Research Articles
- Emphasize rigor, reproducibility, and novelty
- Assess significance and impact
- Verify that conclusions are data-driven
- Check for complete methods and appropriate controls

### Reviews and Meta-Analyses
- Evaluate comprehensiveness of literature coverage
- Assess search strategy and inclusion/exclusion criteria
- Verify systematic approach and lack of bias
- Check for critical analysis vs. mere summarization
- For meta-analyses, evaluate statistical approach and heterogeneity

### Methods Papers
- Emphasize validation and comparison to existing methods
- Assess reproducibility and availability of protocols/code
- Evaluate improvements over existing approaches
- Check for sufficient detail for implementation

### Short Reports/Letters
- Adapt expectations for brevity
- Ensure core findings are still rigorous and significant
- Verify that format is appropriate for findings

### Preprints
- Recognize that these have not undergone formal peer review
- May be less polished than journal submissions
- Still apply rigorous standards for scientific validity
- Consider providing constructive feedback to help authors improve before journal submission

### Presentations and Slide Decks

**⚠️ CRITICAL: For presentations, NEVER read the PDF directly. ALWAYS convert to images first.**

When reviewing scientific presentations (PowerPoint, Beamer, slide decks):

#### Mandatory Image-Based Review Workflow

**NEVER attempt to read presentation PDFs directly** - this causes buffer overflow errors and doesn't show visual formatting issues.

**Required Process:**
1. Convert PDF to images using Python:
   ```bash
   python skills/scientific-slides/scripts/pdf_to_images.py presentation.pdf review/slide --dpi 150
   # Creates: review/slide-001.jpg, review/slide-002.jpg, etc.
   ```
2. Read and inspect EACH slide image file sequentially
3. Document issues with specific slide numbers
4. Provide feedback on visual formatting and content

**Print when starting review:**
```
[HH:MM:SS] PEER REVIEW: Presentation detected - converting to images for review
[HH:MM:SS] PDF REVIEW: NEVER reading PDF directly - using image-based inspection
```

#### Presentation-Specific Evaluation Criteria

**Visual Design and Readability:**
- [ ] Text is large enough (minimum 18pt, ideally 24pt+ for body text)
- [ ] High contrast between text and background (4.5:1 minimum, 7:1 preferred)
- [ ] Color scheme is professional and colorblind-accessible
- [ ] Consistent visual design across all slides
- [ ] White space is adequate (not cramped)
- [ ] Fonts are clear and professional

**Layout and Formatting (Check EVERY Slide Image):**
- [ ] No text overflow or truncation at slide edges
- [ ] No element overlaps (text over images, overlapping shapes)
- [ ] Titles are consistently positioned
- [ ] Content is properly aligned
- [ ] Bullets and text are not cut off
- [ ] Figures fit within slide boundaries
- [ ] Captions and labels are visible and readable

**Content Quality:**
- [ ] One main idea per slide (not overloaded)
- [ ] Minimal text (3-6 bullets per slide maximum)
- [ ] Bullet points are concise (5-7 words each)
- [ ] Figures are simplified and clear (not copy-pasted from papers)
- [ ] Data visualizations have large, readable labels
- [ ] Citations are present and properly formatted
- [ ] Results/data slides dominate the presentation (40-50% of content)

**Structure and Flow:**
- [ ] Clear narrative arc (introduction → methods → results → discussion)
- [ ] Logical progression between slides
- [ ] Slide count appropriate for talk duration (~1 slide per minute)
- [ ] Title slide includes authors, affiliation, date
- [ ] Introduction cites relevant background literature (3-5 papers)
- [ ] Discussion cites comparison papers (3-5 papers)
- [ ] Conclusions slide summarizes key findings
- [ ] Acknowledgments/funding slide at end

**Scientific Content:**
- [ ] Research question clearly stated
- [ ] Methods adequately summarized (not excessive detail)
- [ ] Results presented logically with clear visualizations
- [ ] Statistical significance indicated appropriately
- [ ] Conclusions supported by data shown
- [ ] Limitations acknowledged where appropriate
- [ ] Future directions or broader impact discussed

**Common Presentation Issues to Flag:**

**Critical Issues (Must Fix):**
- Text overflow making content unreadable
- Font sizes too small (<18pt)
- Element overlaps obscuring data
- Insufficient contrast (text hard to read)
- Figures too complex or illegible
- No citations (completely unsupported claims)
- Slide count drastically mismatched to duration

**Major Issues (Should Fix):**
- Inconsistent design across slides
- Too much text (walls of text, not bullets)
- Poorly simplified figures (axis labels too small)
- Cramped layout with insufficient white space
- Missing key structural elements (no conclusion slide)
- Poor color choices (not colorblind-safe)
- Minimal results content (<30% of slides)

**Minor Issues (Suggestions for Improvement):**
- Could use more visuals/diagrams
- Some slides slightly text-heavy
- Minor alignment inconsistencies
- Could benefit from more white space
- Additional citations would strengthen claims
- Color scheme could be more modern

#### Review Report Format for Presentations

**Summary Statement:**
- Overall impression of presentation quality
- Appropriateness for target audience and duration
- Key strengths (visual design, content, clarity)
- Key weaknesses (formatting issues, content gaps)
- Recommendation (ready to present, minor revisions, major revisions)

**Layout and Formatting Issues (By Slide Number):**
```
Slide 3: Text overflow - bullet point 4 extends beyond right margin
Slide 7: Element overlap - figure overlaps with caption text
Slide 12: Font size - axis labels too small to read from distance
Slide 18: Alignment - title not centered
```

**Content and Structure Feedback:**
- Adequacy of background context and citations
- Clarity of research question and objectives
- Quality of methods summary
- Effectiveness of results presentation
- Strength of conclusions and implications

**Design and Accessibility:**
- Overall visual appeal and professionalism
- Color contrast and readability
- Colorblind accessibility
- Consistency across slides

**Timing and Scope:**
- Whether slide count matches intended duration
- Appropriate level of detail for talk type
- Balance between sections

#### Example Image-Based Review Process

```
[14:30:00] PEER REVIEW: Starting review of presentation
[14:30:05] PEER REVIEW: Presentation detected - converting to images
[14:30:10] PDF REVIEW: Running pdf_to_images.py on presentation.pdf
[14:30:15] PDF REVIEW: Converted 25 slides to images in review/ directory
[14:30:20] PDF REVIEW: Inspecting slide 1/25 - title slide
[14:30:25] PDF REVIEW: Inspecting slide 2/25 - introduction
...
[14:35:40] PDF REVIEW: Inspecting slide 25/25 - acknowledgments
[14:35:45] PDF REVIEW: Completed image-based review
[14:35:50] PEER REVIEW: Found 8 layout issues, 3 content issues
[14:35:55] PEER REVIEW: Generating structured feedback by slide number
```

**Remember:** For presentations, the visual inspection via images is MANDATORY. Never attempt to read presentation PDFs as text - it will fail and miss all visual formatting issues.

## Resources

This skill includes reference materials to support comprehensive peer review:

### references/reporting_standards.md
Guidelines for major reporting standards across disciplines (CONSORT, PRISMA, ARRIVE, MIAME, STROBE, etc.) to evaluate completeness of methods and results reporting.

### references/common_issues.md
Catalog of frequent methodological and statistical issues encountered in peer review, with guidance on identifying and addressing them.

## Final Checklist

Before finalizing the review, verify:

- [ ] Summary statement clearly conveys overall assessment
- [ ] Major concerns are clearly identified and justified
- [ ] Suggested revisions are specific and actionable
- [ ] Minor issues are noted but properly categorized
- [ ] Statistical methods have been evaluated
- [ ] Reproducibility and data availability assessed
- [ ] Ethical considerations verified
- [ ] Figures and tables evaluated for quality and integrity
- [ ] Writing quality assessed
- [ ] Tone is constructive and professional throughout
- [ ] Review is thorough but proportionate to manuscript scope
- [ ] Recommendation is consistent with identified issues

---

## 审稿信模板（中英双语）

审稿信是审稿人给编辑和作者的正式意见。使用以下模板，按需填写。

### English Template

```
Referee Report
Manuscript: [Title]
Journal: [Journal Name]
Date: [YYYY-MM-DD]

=== Summary ===
[2-3 sentences summarizing the paper's contribution]

=== General Assessment ===
Recommendation: [Accept / Minor Revision / Major Revision / Reject]

Strengths:
1. [Key strength]
2. [Key strength]

Weaknesses:
1. [Key weakness]
2. [Key weakness]

=== Major Comments ===
1. [Specific issue with location and suggested fix]
2. ...

=== Minor Comments ===
1. [Specific issue with location]
2. ...

=== Questions for Authors ===
1. [Clarification needed]
2. ...
```

### 中文模板

```
审稿意见
稿件: [标题]
期刊: [期刊名]
日期: [YYYY-MM-DD]

=== 概述 ===
[2-3 句话概括论文贡献]

=== 总体评价 ===
建议: [接收 / 小修 / 大修 / 拒稿]

优点:
1. [核心优点]
2. [核心优点]

不足:
1. [核心问题]
2. [核心问题]

=== 主要意见 ===
1. [具体问题，标注位置和修改建议]
2. ...

=== 次要意见 ===
1. [具体问题，标注位置]
2. ...

=== 致作者的问题 ===
1. [需要澄清的问题]
2. ...
```

---

## 光学/物理期刊特有审稿要点

### PRL (Physical Review Letters) 审稿关注
- 是否解释了对广泛物理学界的重要性（broad interest）
- 创新性是否足以支撑 Letter 级别
- 理论推导是否自洽，假设是否合理
- 实验证据是否支持核心结论
- 长度限制内是否完整表达了关键信息

### Optica/Light: Science & Applications 审稿关注
- 光学工程/应用价值是否明确
- 与现有技术的定量对比是否充分
- 实验方案是否考虑了实际应用场景
- 是否讨论了技术局限性和改进方向

### APL (Applied Physics Letters) 审稿关注
- 应用量子物理/光学的新颖性
- 实验可复现性（参数是否充分）
- 与理论预测的对比是否定量
- 实际器件/系统性能指标是否完整

### 统计审稿快速检查（物理实验适用）
- [ ] 误差棒含义是否说明（SD / SEM / 95% CI）
- [ ] 样本量/测量次数是否足够
- [ ] 是否报告了效应量（不只是 p-value）
- [ ] 多重比较是否校正（如适用）
- [ ] 拟合参数是否有不确定度
- [ ] 理论曲线与实验数据的残差是否展示
- [ ] 系统误差是否讨论

---

*定制化自 K-Dense scientific-agent-skills peer-review skill*
*适配光学 PhD 审稿需求 — v1.0-customized*