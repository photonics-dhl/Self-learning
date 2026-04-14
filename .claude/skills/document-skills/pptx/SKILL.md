# PPTX Skill

PowerPoint 演示文稿创建和编辑。

## 创建新演示文稿

使用 `pptxgenjs` (npm install -g pptxgenjs)

### 设计原则

1. **配色**: 选择主题相关的配色方案，不要默认蓝色
2. **字体**: 标题用有个性的字体 (Georgia, Arial Black)，正文用清洁字体 (Calibri)
3. **布局**: 每页必须有视觉元素，避免纯文字幻灯片
4. **间距**: 保持 0.5" 最小边距

### 配色方案

| 主题 | 配色 |
|------|------|
| Midnight Executive | 海军/冰蓝 |
| Forest & Moss | 森林/苔藓/奶油 |
| Coral Energy | 珊瑚/金色/海军 |
| Ocean Gradient | 深蓝/青/午夜 |

### 字体大小

| 类型 | 大小 |
|------|------|
| 标题 | 36-44pt |
| 章节标题 | 20-24pt |
| 正文 | 14-16pt |
| 注释 | 10-12pt |

## 读取内容

```bash
python -m markitdown presentation.pptx
```

## 转换为图片

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

## 依赖

- markitdown (with pptx support)
- Pillow
- pptxgenjs (npm)
- LibreOffice
- Poppler
