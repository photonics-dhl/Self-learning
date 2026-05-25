# PDF Skill

PDF 文档处理和分析。

## Python 库

| 库 | 用途 |
|---|------|
| **pypdf** | 合并、分割、旋转、提取元数据 |
| **pdfplumber** | 文本和表格提取 |
| **reportlab** | 创建新 PDF |
| **pytesseract** | OCR 识别 |

## 命令行工具

| 工具 | 用途 |
|------|------|
| **pdftotext** | 提取文本 |
| **qpdf** | 合并、分割、旋转 |
| **poppler-utils** | PDF 处理 |

## 常用操作

### 提取文本

```bash
pdftotext document.pdf output.txt
```

### 合并 PDF

```bash
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf
```

### 表格转 Excel

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            # 处理表格
            pass
```

## 注意事项

- 使用 `<sub>` 和 `<super>` 标签代替 Unicode 下标/上标
- qpdf 的 `--decrypt` 标志可移除密码保护
