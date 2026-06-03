# HANDOFF — Cross-Session Context Bridge

> Updated: 2026-05-31 (Session 20 — 中期报告图注修复 + tex2docx skill 固化)

## Last Task: 中期报告 DOCX 输出 + tex2docx Skill 固化

### 完成内容

#### 1. 中期报告图注修复（Session 前半段）

文件：`DHL/mid_term/mid_term_report.tex` → `mid_term_report.pdf`

- Fig 1 caption 修正：3面板（ICS散射几何/ICS前/ICS后），恢复原始图片 `pra_published_p2_img1.jpeg`
- Fig 2 caption 修正：panel (a) "蓝宝石棱镜耦合线对" → "CdS 纳米线间隙"
- Fig 4/5/6 (APR 纳米线)：图片保持原始提取版，caption 上轮已修正
- 指导教师：童利民 教授、郭欣 教授 — 未改动

#### 2. tex2docx 转换脚本

文件：`DHL/mid_term/tex2docx.py`

三步混合流程：
1. **python-docx 生成 reference.docx** — 匹配 ctexart 样式（A4、2.5cm、宋体/黑体）
2. **pandoc + reference.docx** — 公式→OMML、图片嵌入、交叉引用
3. **python-docx 后处理** — 232个run字体修正、9个图注/表注识别、2个表格booktabs线型、7张图片尺寸限制

输出：`DHL/mid_term/mid_term_report.docx` (2.1 MB)

#### 3. tex2docx Skill 固化

文件：`.claude/skills/tex2docx/SKILL.md`

独立 skill，与 `mid-term-report`（内容撰写）和 `document-skills`（通用文档处理）互补。

#### 4. 文档更新

- `.claude/rules/architecture.md` — Skills 表新增 `tex2docx`
- `memory/learning/tex2docx_skill_20260531.md` — 经验记录
- `memory/MEMORY.md` — 索引新增条目

### 关键经验（pandoc LaTeX→DOCX 陷阱）

1. pandoc 图注用 `Normal` 样式，不是 `Caption` — 需按内容特征识别
2. pandoc 图片用 `wp:anchor` 不是 `wp:inline` — 检测需覆盖两种
3. run 的 rPr 可能没有 `rFonts` 节点 — 需创建而非 set
4. Windows GBK 不兼容 emoji — 需 `io.TextIOWrapper(encoding="utf-8")`
5. "图 N 展示了" 是正文引用不是 caption，需排除

### 待确认

- [ ] 用户验证 DOCX 在 Word 中打开格式是否满意（图注、公式、表格）
- [ ] Fig 4/5/6 (APR 纳米线) caption 因视觉模型格式错误未验证，可能仍需修正

## Previous Sessions

- **Session 19**: 小孔量子化SM扩充 + Obsidian笔记（pandoc OMML修复、PEC镜像法则）
- **Session 18**: 学科基础笔记全面RAG扩充（10个笔记，~3200行新增）
- **Session 17**: 博士毕业论文骨架+关键章节生成测试（zjuthesis, 49页PDF）
