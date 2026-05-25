# 光学博士数字学术大脑 - 使用指南

> 你的 AI 辅助光学研究知识管理系统

---

## 目录

1. [系统概览](#系统概览)
2. [快速开始](#快速开始)
3. [Obsidian 配置](#obsidian-配置)
4. [Zotero 联动](#zotero-联动)
5. [Claude Code 使用](#claude-code-使用)
6. [MCP 扩展](#mcp-扩展)
7. [可视化脚本](#可视化脚本)
8. [日常使用工作流](#日常使用工作流)

---

## 系统概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        你的"数字学术大脑"                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │   Zotero    │◄──►│   Obsidian  │◄──►│   Claude Code (终端)     │ │
│  │  文献管理    │    │   知识中枢   │    │   AI 超级导师            │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 核心功能

- **AI 导师**: Claude Code 作为你的光学知识导师
- **知识管理**: Obsidian 构建个人知识图谱
- **文献联动**: Zotero 管理的论文自动同步到 Obsidian
- **可视化**: 内置光学概念可视化脚本
- **MCP 扩展**: Tavily/知乎/学术搜索增强

---

## 快速开始

### 1. 环境检查

在终端中运行：

```bash
# 检查 Python 依赖
python Obsidian-Vault/6️⃣ 工具/scripts/optics_viz.py --list

# 检查 Vault 路径
ls Obsidian-Vault/
```

### 2. 创建第一篇笔记

```bash
# 方式 1: 直接创建
python Obsidian-Vault/6️⃣ 工具/scripts/new_note.py "高斯光束" --type concept --subfield 波动光学

# 方式 2: 交互式创建
python Obsidian-Vault/6️⃣ 工具/scripts/new_note.py --interactive
```

### 3. 与 Claude Code 对话

```bash
# 进入项目目录
cd z:/321/DHL/Self_Learning

# 启动 Claude Code
claude

# 然后输入你的问题，例如：
# "帮我解释一下高斯光束的束腰概念"
# "构建超表面光学的知识树"
# "搜索一下最近关于几何相位的论文"
```

---

## Obsidian 配置

### 必装插件

在 Obsidian 设置 → 社区插件 中安装：

| 插件名称 | 功能 |
|----------|------|
| **Templater** | 动态模板生成 |
| **Dataview** | 笔记数据库查询 |
| **Mermaid** | 图表渲染 |
| **Admonition** | 特殊提示框 |
| **Excalidraw** | 手绘示意图 |
| **Zotero Integration** | 文献嵌入 (需要 Zotero 6+) |
| **Smart Connections** | AI 检索 [GitHub](https://github.com/brianpetro/obsidian-smart-connections) |

### Smart Connections 配置

1. 安装插件后，在设置中配置：
   - **API Provider**: Anthropic 或 OpenAI
   - **API Key**: 你的 API key
   - **Default Model**: `claude-sonnet-4-6`

2. 使用方式：
   - 按 `Cmd/Ctrl + K` 打开搜索
   - 插件会自动检索你的笔记库

### 模板使用

创建的笔记位于 `Obsidian-Vault/6️⃣ 工具/templates/`

- `concept.md` - 概念笔记模板
- `paper.md` - 论文笔记模板
- `method.md` - 方法笔记模板

### 知识树查看

使用 Dataview 查询：

````dataview
TABLE title, type, status
FROM ""
WHERE field = "optics"
SORT type, title
````

---

## Zotero 联动

### 方式 1: BibTeX 导出 (推荐)

1. **安装 Better BibTeX 插件** (Zotero → 工具 → 附加组件)

2. **创建自动导出**：
   - Zotero → 文件 → 导出库
   - 格式选择: `Better-BibTeX`
   - 勾选: `自动导出`

3. **同步到 Obsidian**：

```bash
# 导出后运行
python Obsidian-Vault/6️⃣ 工具/scripts/sync_zotero.py --bibtex path/to/export.bib

# 或放到默认位置后直接运行
python Obsidian-Vault/6️⃣ 工具/scripts/sync_zotero.py --list  # 预览
python Obsidian-Vault/6️⃣ 工具/scripts/sync_zotero.py          # 同步
```

### 方式 2: Zotero API

1. 获取 API Key：Zotero → 编辑 → 设置 → Feeds/API

2. 设置环境变量：

```bash
# Windows (PowerShell)
$env:ZOTERO_LIBRARY_ID = "your_library_id"
$env:ZOTERO_API_KEY = "your_api_key"

# 或添加到系统环境变量
```

3. 运行同步：

```bash
python Obsidian-Vault/6️⃣ 工具/scripts/sync_zotero.py --zotero
```

### Zotero Integration 插件

安装后可以：
- 在 Obsidian 中直接插入引用
- 快捷键 `Cmd/Ctrl+Shift+Z` 搜索 Zotero 文献
- 嵌入 PDF 和笔记

---

## Claude Code 使用

### 基础对话

```bash
# 进入项目目录
cd z:/321/DHL/Self_Learning

# 启动 Claude Code
claude

# 常用指令：
# "解释一下什么是广义斯涅尔定律"
# "帮我推导一下菲涅尔衍射积分"
# "用 Python 实现一个简单的干涉图样模拟"
```

### 调用子代理

```bash
# 调用光学导师代理深入学习
/optics-mentor
# 然后输入："帮我深入理解超表面光学的相位调控原理"

# 调用文献研究代理
/literature-researcher
# 然后输入："搜索最近关于金属透镜的论文"
```

### 调用 Skills

```bash
# 调用光学学习技能
/optics-learning
# 然后输入："构建傅里叶光学的知识树"

# 调用文献同步技能
/literature-sync
# 然后输入："同步我的 Zotero 文献"
```

### 快捷命令

```bash
# 新建笔记
python Obsidian-Vault/6️⃣ 工具/scripts/new_note.py "笔记标题" -t concept

# 可视化
python Obsidian-Vault/6️⃣ 工具/scripts/optics_viz.py gaussian_beam

# 文献同步
python Obsidian-Vault/6️⃣ 工具/scripts/sync_zotero.py --list
```

---

## MCP 扩展

### 已配置的 MCP Server

#### Tavily Search (网络搜索)

```bash
# 需要设置 API key
export TAVILY_API_KEY=tvly-xxxxx

# 使用方式
/mcp__tavily__search "超表面光学 最新进展"
```

#### Semantic Scholar (学术搜索)

```bash
# 无需 API key
/mcp__semantic-scholar__search_papers "geometric phase metasurface 2024"
```

### 手动添加 MCP Server

```bash
# 添加 GitHub MCP
claude mcp add github -- npx -y @modelcontextprotocol/server-github

# 添加更多 MCP
claude mcp add <name> -- <command>
```

---

## 可视化脚本

### 使用方法

```bash
# 进入脚本目录
cd Obsidian-Vault/6️⃣ 工具/scripts

# 查看所有可用的可视化
python optics_viz.py --list

# 生成高斯光束图
python optics_viz.py gaussian_beam

# 生成超表面相位分布
python optics_viz.py metasurface_phase

# 生成衍射图样 (多缝)
python optics_viz.py diffraction --num_slits 3 --slit_width 30e-6
```

### 可视化类型

| 函数 | 说明 | 参数 |
|------|------|------|
| `gaussian_beam` | 高斯光束传播 | wavelength, w0 |
| `metasurface_phase` | 超表面相位剖面 | period, focal_length |
| `snells_law` | 广义斯涅尔定律 | n1, n2 |
| `diffraction` | 衍射图样 | num_slits, slit_width |
| `plasmon_resonance` | 等离激元共振 | wavelength_range |
| `fresnel` | 菲涅尔方程 | n1, n2 |
| `fourier` | 傅里叶光学 | function_type |

### 在笔记中使用

在 Obsidian 笔记中插入图片：

```markdown
![[gaussian_beam.png]]
```

或在 Mermaid 图中使用：

````markdown
```mermaid
graph LR
    A[入射] --> B[超表面]
    B --> C[相位调控]
    C --> D[聚焦]
```
````

---

## 日常使用工作流

### 场景 1: 学习新概念

1. 向 Claude Code 提问：
   ```
   "帮我理解等离激元共振，用清晰的物理图像解释"
   ```

2. Claude Code 回答后，建议创建笔记：
   ```
   "要不要我帮你创建一篇 Obsidian 笔记？"
   ```

3. 创建笔记：
   ```bash
   python Obsidian-Vault/6️⃣ 工具/scripts/new_note.py "等离激元共振" -t concept -s 等离激元光学
   ```

4. 在 Obsidian 中打开笔记，补充个人理解

### 场景 2: 阅读论文

1. 在 Zotero 中整理论文，添加标签和笔记

2. 同步到 Obsidian：
   ```bash
   python Obsidian-Vault/6️⃣ 工具/scripts/sync_zotero.py --dry-run  # 预览
   python Obsidian-Vault/6️⃣ 工具/scripts/sync_zotero.py             # 同步
   ```

3. 用 Claude Code 总结论文：
   ```
   "帮我总结一下 @Zhang2024 这篇论文的核心贡献"
   ```

### 场景 3: 追踪最新研究

1. 向 Claude Code 请求文献调研：
   ```
   "搜索一下 2024 年关于超构透镜(metalens)的最新进展"
   ```

2. Claude Code 调用 MCP 搜索，返回结果

3. 筛选感兴趣的论文，导入 Zotero

4. 同步到 Obsidian 并创建笔记

### 场景 4: 代码验证

1. 描述需求：
   ```
   "帮我写一个 RCWA 方法的简单实现，用于计算光栅衍射"
   ```

2. Claude Code 生成代码

3. 运行验证：
   ```bash
   python your_code.py
   ```

4. 生成可视化结果

---

## 故障排除

### 常见问题

**Q: 运行脚本报错 "No module named 'xxx'"**
```bash
pip install numpy matplotlib scipy
```

**Q: Smart Connections 不工作**
- 检查 API key 是否正确配置
- 确认 Obsidian 已安装插件

**Q: Zotero 同步失败**
- 检查 BibTeX 文件路径是否正确
- 确认 Better BibTeX 插件已安装并配置自动导出

**Q: Claude Code 无法访问笔记库**
- 检查当前工作目录是否在 `z:/321/DHL/Self_Learning`
- 确认 `CLAUDE.md` 中的 `Obsidian-Vault` 路径配置正确

### 联系方式

如有更多问题，可以在 Claude Code 中输入：
```
"帮助：如何[具体问题]"
```

---

## 更新日志

- **2024-04-14**: 初始系统搭建完成
  - Obsidian Vault 结构
  - Python 脚本工具
  - Claude Code 代理和技能
  - MCP 配置

---

*此系统将随着你的使用不断进化，形成真正的"数字学术大脑"*
