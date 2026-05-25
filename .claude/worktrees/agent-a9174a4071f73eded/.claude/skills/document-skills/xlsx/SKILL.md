# XLSX Skill

Excel 电子表格创建、编辑和分析。

## 核心原则

### 必须使用公式，而非硬编码值

```python
# ❌ 错误 - 硬编码计算值
sheet['B10'] = 5000

# ✅ 正确 - 使用 Excel 公式
sheet['B10'] = '=SUM(A1:A10)'
```

### 颜色编码规范

| 颜色 | 含义 |
|------|------|
| **蓝色文本** (RGB: 0,0,255) | 硬编码输入值 |
| **黑色文本** (RGB: 0,0,0) | 公式和计算 |
| **绿色文本** (RGB: 0,128,0) | 同工作表内的链接 |
| **红色文本** (RGB: 255,0,0) | 外部文件链接 |
| **黄色背景** (RGB: 255,255,0) | 需要关注的假设 |

### 数字格式

- **年份**: 文本格式 "2024" (非 "2,024")
- **货币**: $#,##0 格式，标题中注明单位
- **零值**: 使用 "-" 显示零值
- **百分比**: 0.0% 格式
- **倍数**: 0.0x 格式 (EV/EBITDA 等)

## 工作流程

1. **选择工具**: pandas (数据分析), openpyxl (公式/格式)
2. **创建/加载**: 创建新工作簿或加载现有文件
3. **修改**: 添加/编辑数据、公式、格式
4. **保存**: 写入文件
5. **重新计算** (必需): `python scripts/recalc.py output.xlsx`

## 常用操作

### 创建

```python
from openpyxl import Workbook

wb = Workbook()
sheet = wb.active
sheet['A1'] = 'Hello'
sheet['B2'] = '=SUM(A1:A10)'
wb.save('output.xlsx')
```

### 编辑

```python
from openpyxl import load_workbook

wb = load_workbook('existing.xlsx')
sheet = wb.active
sheet['A1'] = 'New Value'
wb.save('modified.xlsx')
```

## 公式验证

检查错误:
- `#REF!`: 无效的单元格引用
- `#DIV/0!`: 除以零
- `#VALUE!`: 公式中的数据类型错误
- `#NAME?`: 无法识别的公式名称

## 依赖

- pandas
- openpyxl
- LibreOffice (用于公式重新计算)
