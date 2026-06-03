---
name: document-skills
description: |
  文档处理技能集（增强版）。支持多格式输入转换、PDF操作、Office文档创建/编辑。
  输入：PDF, DOCX, XLSX, PPTX, HTML, EPUB, CSV, JSON, 图片(OCR), 音频(转录)。
  输出：Markdown, DOCX, PPTX, XLSX, PDF。
  基于 K-Dense markitdown/pdf/docx/pptx/xlsx/liteparse skills 增强。
tags:
  - 文档处理
  - 格式转换
  - PDF
  - DOCX
  - PPTX
  - XLSX
  - OCR
  - markitdown
  - pandoc
---

# Document Skills — 文档处理技能集（增强版）

## 格式覆盖

### 输入格式（→ Markdown）

| 格式 | 工具 | 备注 |
|------|------|------|
| **PDF** | MarkItDown / PyMuPDF | 电子版直接提取，扫描版需 OCR |
| **DOCX** | MarkItDown / pandoc | 表格/格式保持好 |
| **PPTX** | MarkItDown | 幻灯片文字+备注 |
| **XLSX** | MarkItDown / openpyxl | 表格数据提取 |
| **HTML** | MarkItDown | 清理标签 |
| **EPUB** | MarkItDown | 全文提取 |
| **CSV/TSV** | MarkItDown / pandas | 表格格式 |
| **JSON** | MarkItDown | 结构化展示 |
| **Images** | MarkItDown + OCR | EXIF + OCR（需 tesseract） |
| **Audio** | MarkItDown | 元数据 + 转录（需 whisper） |

### 输出格式（创建/编辑）

| 格式 | 工具 | 备注 |
|------|------|------|
| **Markdown** | 所有输入格式 | 中间格式 |
| **DOCX** | python-docx / pandoc | 保留标题/表格/图片 |
| **PDF** | pandoc / PyMuPDF / LaTeX | 学术排版用 LaTeX |
| **PPTX** | python-pptx | 幻灯片创建 |
| **XLSX** | openpyxl | 表格/公式/格式 |

---

## 子技能矩阵

| 技能 | 用途 | 关键库 |
|------|------|--------|
| 格式转换 | 万能格式 → Markdown | `markitdown[all]` |
| PDF 操作 | 读/写/合并/拆分/水印/旋转 | `pypdf`, `PyMuPDF` |
| DOCX 创建 | 标题/表格/图片/TOC | `python-docx`, `pandoc` |
| PPTX 创建 | 幻灯片/模板/备注 | `python-pptx` |
| XLSX 创建 | 公式/格式/数据分析 | `openpyxl`, `pandas` |
| OCR | 扫描版PDF/图片文字识别 | `tesseract` (可选) |
| LaTeX→DOCX | 学术论文格式保持 | pandoc + python-docx（tex2docx skill） |

---

## 安装依赖

```bash
# 核心依赖（已安装）
pip install markitdown[all] pypdf PyMuPDF python-docx openpyxl pandas

# 可选依赖
pip install pytesseract pillow  # OCR（需安装 tesseract-ocr）
```

---

## 通用原则

1. **字体**: 中文用宋体/黑体，英文用 Arial/Times New Roman
2. **模板**: 编辑现有文件时保留原有格式
3. **验证**: 创建后必须验证文件可打开且格式正确
4. **编码**: 始终指定 UTF-8
5. **备份**: 修改重要文件前先备份

---

## 触发场景

- "将这个文件转换成 Markdown" / "把这个 PDF 转成 Word"
- "合并 PDF" / "拆分 PDF" / "给 PDF 加水印"
- "创建一个 Excel 表格" / "生成 PPT"
- "OCR 这个扫描版文件"
- "处理 Office 文档"
- "将论文转换为 Word"

---

## 快速参考命令

### 格式转换（→ Markdown）

```bash
# 万能转换（CLI）
markitdown document.pdf > output.md
markitdown spreadsheet.xlsx > output.md
markitdown presentation.pptx > output.md

# Python API
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

### PDF 操作

```python
from pypdf import PdfReader, PdfWriter

# 合并 PDF
writer = PdfWriter()
for f in ["a.pdf", "b.pdf"]:
    for page in PdfReader(f).pages:
        writer.add_page(page)
writer.write("merged.pdf")

# 拆分 PDF
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    w = PdfWriter(); w.add_page(page)
    w.write(f"page_{i+1}.pdf")

# 旋转页面
page = PdfReader("input.pdf").pages[0]
page.rotate(90)

# 提取元数据
meta = PdfReader("doc.pdf").metadata
```

### DOCX 创建

```python
from docx import Document
doc = Document()
doc.add_heading("标题", level=1)
doc.add_paragraph("正文内容")
doc.add_table(rows=3, cols=2, data=[["A","B"],["C","D"]])
doc.save("output.docx")
```

### PPTX 创建

```python
from pptx import Presentation
prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[1])  # 标题+内容
slide.shapes.title.text = "标题"
slide.placeholders[1].text = "内容"
prs.save("output.pptx")
```

### XLSX 创建

```python
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "数据"
ws.append(["列1", "列2", "列3"])
ws.append([1, 2, 3])
wb.save("output.xlsx")
```

---

## 与其他 Skill 的关系

```
tex2docx           → LaTeX → DOCX 专用（三步法，格式保持更好）
document-skills    → 通用文档处理（本 skill）
academic-research  → 调用本 skill 的格式转换能力
literature-sync    → 调用 PDF 提取能力
```

---

## 注意事项

- **OCR 质量**: tesseract 对中文数学公式效果有限，物理文献建议用 PyMuPDF 直接提取电子版
- **PPTX → MD**: 只提取文字，视觉布局丢失
- **大文件**: MarkItDown 支持 `convert_stream()` 流式处理
- **中文字体**: DOCX/PPTX 创建时需显式设置中文字体（宋体/黑体）

---

*增强自 K-Dense markitdown/pdf/docx/pptx/xlsx/liteparse skills*
*保留原有 pandoc + python-docx 工作流*
