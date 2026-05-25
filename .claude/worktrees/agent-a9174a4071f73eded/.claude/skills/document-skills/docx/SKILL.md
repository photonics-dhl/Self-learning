# DOCX Skill

Word 文档创建、编辑和分析。

## 创建新文档

使用 `docx-js` (npm install -g docx)

### 关键规范

- **页面大小**: 始终显式设置 (docx-js 默认为 A4)
- **字体**: Arial (通用支持)
- **列表**: 使用 `LevelFormat.BULLET`，不使用 unicode 符号
- **表格**: 需要双重宽度设置 (`columnWidths` + cell `width`)
- **图片**: 必须指定 `type` 参数

### 代码模板

```javascript
const { Document, Packer, Paragraph, TextRun } = require('docx');

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 }, // US Letter
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      new Paragraph({
        children: [new TextRun({ text: "Hello World", font: "Arial", size: 24 })]
      })
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => fs.writeFileSync("doc.docx", buffer));
```

## 编辑现有文档

### 步骤

1. **解压**: `python scripts/office/unpack.py document.docx unpacked/`
2. **编辑 XML**: 直接编辑 XML 文件
3. **打包**: `python scripts/office/pack.py unpacked/ output.docx`

## 依赖

- pandoc (文本提取)
- docx (npm install -g docx)
- LibreOffice (PDF 转换)
- Poppler (图片转换)
