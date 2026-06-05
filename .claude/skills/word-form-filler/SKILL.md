---
name: word-form-filler
description: |
  填写 Word (.docx) 表格表单，格式零破坏。完整流程：
  1. 用 python-docx 深度解析文档结构（段落/表格/合并单元格/表单域）
  2. 定位可填写区域（区分指引行 vs. 内容行）
  3. 保留原始格式（rPr/pPr）写入内容
  4. 备份原文件 → 写入 → 验证 → Humanizer 润色

  触发场景：
  - 用户说"帮我填表"、"填写申请表"、"填写 Word 表单"
  - 需要批量或逐格写入 .docx 表格内容
  - 表格有合并单元格、指引行、固定格式模板

  依赖：python-docx（pip install python-docx）
tags:
  - docx
  - word
  - 表格填写
  - python-docx
  - 表单
---

# word-form-filler: Word 表格表单填写

## 概述

在保留原始字体、段落格式、单元格边框的前提下，用 python-docx 精确写入 Word 表格内容。避免直接赋值 `cell.text` 导致的格式清零问题。

---

## Phase 0：分析文档结构（必须先做）

### 0.1 结构探针脚本

```python
from docx import Document
from docx.oxml.ns import qn
from copy import deepcopy

doc = Document("申请表.docx")

# 基本信息
print(f"段落数: {len(doc.paragraphs)}, 表格数: {len(doc.tables)}")
has_fldchar = any(r.find(qn('w:fldChar')) is not None
                  for t in doc.tables for row in t.rows
                  for cell in row.cells for p in cell.paragraphs
                  for r in p.runs)
print(f"表单域: {has_fldchar}")  # True=有 w:fldChar，需特殊处理

# 全表结构输出
tbl = doc.tables[0]
seen = set()
for i, row in enumerate(tbl.rows):
    print(f"\n--- 行{i} ({len(row.cells)}格) ---")
    for j, cell in enumerate(row.cells):
        cid = id(cell)
        if cid in seen:
            continue
        seen.add(cid)
        tc = cell._tc
        hspan = int(tc.get(qn('w:gridSpan'), '1'))
        vmerge = tc.find(qn('w:vMerge'))
        vm = 'restart' if (vmerge is not None and vmerge.get(qn('w:val')) is None) else (
             'cont' if vmerge is not None else '-')
        text_preview = cell.text[:60].replace('\n', '↵')
        print(f"  col{j} span={hspan} vm={vm} | '{text_preview}'")
```

**输出用途**：
- 识别合并单元格位置（hspan>1 或 vm=restart/cont）
- 区分**标签列**（含固定说明文字）vs **值列**（空白待填）
- 找到指引行（只有提示文字，不可修改）

### 0.2 目标行段落结构探针

```python
# 详查某行（以行8为例）
row8 = tbl.rows[8]
seen = set()
for cell in row8.cells:
    if id(cell) in seen: continue
    seen.add(id(cell))
    print(f"Cell text: {repr(cell.text[:100])}")
    for k, p in enumerate(cell.paragraphs):
        print(f"  para{k}: {repr(p.text[:60])}")
        for r in p.runs:
            print(f"    run: {repr(r.text[:40])}")
```

---

## Phase 1：备份

```bash
# 任何写入前必须备份
cp 申请表.docx 申请表_backup.docx
```

---

## Phase 2：核心写入工具函数

### 2.1 单段落覆写（保留原 rPr）

```python
from docx.oxml.ns import qn
from copy import deepcopy
from lxml import etree

def set_cell_text(cell, text):
    """覆写 cell 第一段落文字，保留原始 run 格式（rPr）"""
    para = cell.paragraphs[0]
    rPr = None
    if para.runs:
        rPr = deepcopy(para.runs[0]._r.find(qn('w:rPr')))
    # 清空所有段落的所有 run
    for p in cell.paragraphs:
        for r in p.runs:
            r.text = ''
    run = para.add_run(text)
    if rPr is not None:
        run._r.insert(0, deepcopy(rPr))
```

### 2.2 追加内容到现有段落末尾

```python
def append_to_para(para, text):
    """追加 run 到段落末，复制末尾 run 的 rPr"""
    rPr = None
    if para.runs:
        rPr = deepcopy(para.runs[-1]._r.find(qn('w:rPr')))
    run = para.add_run(text)
    if rPr is not None:
        run._r.insert(0, deepcopy(rPr))
```

### 2.3 向 cell 追加新段落（保留 pPr+rPr）

```python
def add_para_to_cell(cell, text, ref_para_idx=0):
    """在 cell 末尾追加新段落，格式从 ref_para_idx 段落复制"""
    from docx.oxml import OxmlElement
    ref_para = cell.paragraphs[ref_para_idx]
    
    new_p = OxmlElement('w:p')
    
    # 复制段落格式 pPr
    pPr = ref_para._p.find(qn('w:pPr'))
    if pPr is not None:
        new_p.insert(0, deepcopy(pPr))
    
    # 新 run
    new_r = OxmlElement('w:r')
    rPr = None
    if ref_para.runs:
        rPr = ref_para.runs[0]._r.find(qn('w:rPr'))
    if rPr is not None:
        new_r.append(deepcopy(rPr))
    new_t = OxmlElement('w:t')
    new_t.text = text
    new_t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    new_r.append(new_t)
    new_p.append(new_r)
    
    cell._tc.append(new_p)
```

### 2.4 修改段落内特定文字（汇总填空类）

```python
def replace_para_text(para, old_text, new_text):
    """替换段落内文字，保留原 run 格式"""
    if old_text not in para.text:
        return False
    full = para.text
    new_full = full.replace(old_text, new_text)
    # 清空旧 runs
    for r in para.runs:
        r.text = ''
    # 写入第一个 run
    if para.runs:
        para.runs[0].text = new_full
    else:
        rPr = None
        run = para.add_run(new_full)
    return True
```

---

## Phase 3：合并单元格去重

python-docx 对合并区域会返回同一 cell 对象多次，必须去重：

```python
seen_cells = set()
for row in tbl.rows:
    for cell in row.cells:
        if id(cell) in seen_cells:
            continue
        seen_cells.add(id(cell))
        # ... 处理 cell
```

---

## Phase 4：区分指引行 vs. 内容行

常见表单结构：
- **指引行**：含固定提示文字如"（请填写……）"、"（限500字）"，**绝对不改**
- **标题行**：节标题如"一、……"，**不改**
- **内容行**：含空白 para 或 `[  ]` 占位符，**这里写内容**

判断方法：
```python
def is_hint_row(cell_text):
    hint_markers = ['（请', '（简述', '（说明', '见备注', '限', '字以内']
    return any(m in cell_text for m in hint_markers)
```

---

## Phase 5：验证

写入后立即验证，输出到临时文件再用 Read 工具查看（避免终端乱码）：

```python
doc2 = Document(output_path)
with open('/tmp/verify.txt', 'w', encoding='utf-8') as f:
    tbl = doc2.tables[0]
    seen = set()
    for i, row in enumerate(tbl.rows):
        for cell in row.cells:
            if id(cell) in seen: continue
            seen.add(id(cell))
            if cell.text.strip():
                f.write(f"[行{i}] {cell.text[:200]}\n")
```

在 Claude Code 中：用 `Read` 工具读 `/tmp/verify.txt`，**不要用 bash cat**（Windows 终端 GBK 编码会乱码）。

---

## Phase 6：Humanizer 润色（中文表单必做）

填完中文叙述段落后，调用 `humanizer skill (mode=chinese-academic)` 处理：
- 删除"首次"、"显著"、"重大突破"等夸张词
- 打散三连并列结构
- 去除通用正面结论（"未来前景广阔"类）
- 具体数字替换模糊副词

---

## 常见陷阱

| 陷阱 | 原因 | 解决 |
|------|------|------|
| `cell.text = "xxx"` 清空格式 | 底层重建 XML，所有 run 格式丢失 | 用 `set_cell_text()` 保留 rPr |
| 合并格写入多次 | python-docx 返回同一对象多次 | `seen_cells` 集合去重 |
| bash cat 中文乱码 | Windows PowerShell/CMD 默认 GBK | 写 `/tmp/file.txt` → Read 工具读 |
| 指引行被覆写 | 未区分提示行和内容行 | 先解析结构，建白名单 |
| para 无 runs 时追加失败 | 纯 XML text 节点，无 `<w:r>` | 先清空再 `para.add_run()` |
| 表单域 w:fldChar 存在 | 旧式 Word 表单，需 `fldChar` API | 先 `has_fldchar` 检测，换路径 |

---

## 调用范式

```
用户："帮我填写 path/to/form.docx，基本信息在 CV.docx 里"

执行顺序：
1. Phase 0：读两个文件，输出结构到 /tmp/structure.txt，Read 查看
2. grill-me（若字段含义不确定）
3. 备份原文件
4. Phase 2-4：逐行填入
5. Phase 5：验证写入
6. Humanizer 润色中文段落
7. 告知用户在 Word 中打开验证视觉效果
```

---

## 依赖安装

```bash
pip install python-docx lxml
```
