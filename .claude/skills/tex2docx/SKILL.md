---
name: tex2docx
description: |
  LaTeX (ctexart) → DOCX 格式保持转换。三步流程：
  1. python-docx 生成匹配 ctexart 样式的 reference.docx 模板
  2. pandoc + reference.docx 执行转换（公式→OMML、图片嵌入）
  3. python-docx 后处理（中文字体、图注识别、表格线型、图片尺寸）

  触发场景：
  - 用户需要将 LaTeX 文件转为 Word 文档并保持格式
  - 用户说"转 docx"、"输出 Word 版本"、"转成 Word"
  - 中期报告、论文等需要提交 DOCX 格式时

  依赖：python-docx、pandoc 3.x
tags:
  - latex
  - docx
  - pandoc
  - 格式转换
---

# tex2docx: LaTeX → DOCX 格式保持转换

## 概述

将 ctexart 格式的 LaTeX 文档转为格式保持的 Word (.docx) 文件。通过三步混合流程（模板生成 + pandoc 转换 + 后处理微调），保留页面布局、中文字体、标题样式、表格线型、图片尺寸和数学公式。

## 适用范围

- **源格式**：ctexart 文档（A4、12pt、宋体/黑体）
- **输出格式**：Word 2007+ (.docx)
- **典型场景**：中期报告、开题报告、论文等需要同时提交 PDF 和 DOCX 的情况

## 依赖

| 工具 | 用途 | 安装 |
|------|------|------|
| pandoc ≥ 3.0 | LaTeX→DOCX 核心转换 | `winget install pandoc` |
| python-docx ≥ 1.0 | 模板生成 + 后处理 | `pip install python-docx` |

## 转换脚本

核心脚本：`DHL/mid_term/tex2docx.py`

```bash
# 运行转换（自动三步流程）
python DHL/mid_term/tex2docx.py
```

## 三步流程详解

### Step 1: 创建 reference.docx 模板

用 python-docx 生成匹配 ctexart 样式的 Word 模板：

| 属性 | ctexart 默认值 | DOCX 对应 |
|------|--------------|----------|
| 页面 | A4 | `sections.page_width/height` |
| 边距 | 2.5cm 四边 | `margins` |
| 正文 | 12pt 宋体 | `Normal` style: SimSun 12pt, eastAsia=宋体 |
| 一级标题 | 黑体 三号 | `Heading 1`: SimHei 16pt, 加粗 |
| 二级标题 | 黑体 四号 | `Heading 2`: SimHei 14pt, 加粗 |
| 图注/表注 | 宋体 五号 | `Caption`: SimSun 10.5pt, 居中 |
| 行距 | 1.3 倍 | `line_spacing = 1.3` |
| 首行缩进 | ~2 字符 | `first_line_indent = 0.74cm` |

### Step 2: pandoc 转换

```bash
pandoc input.tex -o output.docx \
  --from latex --to docx \
  --reference-doc=reference.docx \
  --resource-path=figures/
```

pandoc 自动处理：
- LaTeX 公式 → OMML（Word 原生公式）
- `\includegraphics` → 嵌入图片
- `\ref{}` → 交叉引用文字
- `\begin{itemize}` → Word 列表

### Step 3: python-docx 后处理

| 后处理项 | 方法 |
|----------|------|
| 中文字体 | 检测含中文的 run，强制设置 `eastAsia=宋体` |
| 图注识别 | 按内容特征（子面板 `(a)/(b)`、"引自"、表注关键词）识别 Caption 段落 |
| 表格线型 | 模拟 booktabs：顶底线粗（sz=12）、表头下线细（sz=6） |
| 图片尺寸 | 限制宽度 ≤ 页面可用宽 85%（13.6cm），按比例缩放 |
| 标题缩进 | Heading 1/2 去除首行缩进 |

## 图注识别规则

pandoc 不保留 `\caption` 样式，需按内容特征识别：

**识别为 Caption：**
- 以 "图 N" / "表 N" 开头
- 含子面板描述 `(a)/(b)/(c)` + "引自"
- 含表注关键词（"技术指标"、"时间安排"）且段落 < 30 字
- 含 "引自" 且段落 < 150 字

**排除（非 Caption）：**
- "图 N 展示了..." / "图 N 所示..." — 正文引用
- 以小节编号开头（"4.5 时间安排"） — 标题

## 复用到其他 LaTeX 文件

如需转换其他 ctexart 文件，修改 `tex2docx.py` 中的路径配置：

```python
BASE_DIR = "目标目录"
TEX_FILE = os.path.join(BASE_DIR, "input.tex")
DOCX_OUT = os.path.join(BASE_DIR, "output.docx")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")
```

或直接命令行：
```bash
python tex2docx.py --input paper.tex --output paper.docx --figures fig/
```

## 质量验证

转换后需检查：

| 检查项 | 方法 |
|--------|------|
| 页面设置 | Word → 布局 → 页面设置：A4、2.5cm |
| 中文字体 | 选中中文文字 → 查看字体：宋体 |
| 图片完整 | 逐页滚动，确认 7 张图片全部嵌入 |
| 公式显示 | 双击公式 → Word 公式编辑器可编辑 |
| 表格线型 | 查看表格：顶底线粗、无竖线 |
| 图注居中 | 查看图注段落：五号字、居中 |

## 关联 Skills

| Skill | 关系 |
|-------|------|
| `mid-term-report` | 上游：写完 LaTeX 报告后用本 skill 转 DOCX |
| `document-skills` | 同类：通用文档处理 |
| `bishe-guider` | 上游：毕业论文 LaTeX 编写规范 |

## 已知限制

1. **pandoc 丢 LaTeX 特有排版**：`\textbf{}` 嵌套、复杂 tabularx 对齐可能不完全保留
2. **公式复杂度**：多行公式（`\begin{aligned}`）可能渲染不完美，需手动微调
3. **参考文献**：`\cite{}` 转为纯文字，Word 端无自动引用管理
4. **非 ctexart**：如用 zjuthesis/ctexbook 等类，需调整 reference.docx 样式

---

*本 skill 基于中期报告 tex2docx.py 实战经验固化，三步流程经过 7 图 + 2 表 + 9 图注的完整验证。*
