# 光学博士数字学术大脑 - 项目配置

## 项目概览

- **名称**: Optics Digital Brain (光学数字学术大脑)
- **类型**: 知识管理系统 / 个人知识库
- **用户身份**: 光学专业博士研究生
- **核心功能**: AI 辅助学习、Zotero 文献联动、可视化概念验证
- **技术栈**: Obsidian + Claude Code + MCP + Python 可视化

## ⚡ 全自动工作模式（默认）

```
你提问 → 我回答 → 自动存笔记 → 自动关联 → 自动溯源 → 自动可视化
```

### 核心原则

1. **知识不重复** - 每次创建笔记前检查是否已存在
2. **深入清晰** - 一次把问题讲透，不碎片化
3. **自动同步** - 对话结束自动生成笔记并关联知识树
4. **文献溯源** - 引用论文时自动关联 Zotero

### 你需要做的

**只需在 IDE 窗口跟我对话**，我会自动处理：

| 你说 | 我做 |
|------|------|
| "解释 XXX" | 深度解释 + 物理图像 + 存入笔记 |
| "帮我理解这篇论文" | 搜索 Zotero + 生成引用 + 更新关联 |
| "生成可视化" | 生成图表 + 自动同步到 Obsidian |
| "构建知识树" | 创建完整知识树 + Mermaid 图 + 关联已有笔记 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        你的"数字学术大脑"                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  你 (IDE 窗口) ────────────────────────────────────────────────     │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  Claude Code (我)                                           │  │
│  │  • 理解问题                                                 │  │
│  │  • 深度回答 + 物理图像                                       │  │
│  │  • 自动创建/更新 Obsidian 笔记                              │  │
│  │  • 自动关联已有知识树                                        │  │
│  │  • 自动引用 Zotero 文献                                     │  │
│  │  • 自动生成可视化                                            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│       │                                                           │
│       ▼                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │   Zotero    │◄──►│   Obsidian  │◄──►│   MCP Servers          │ │
│  │  文献库      │    │   知识中枢   │    │   Tavily/学术搜索      │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
Self_Learning/
├── CLAUDE.md                    # 本文件 - 项目配置
├── README.md                    # 使用指南
│
├── .claude/                     # Claude Code 配置
│   ├── settings.json            # 项目设置 (含 hooks)
│   ├── agents/                  # 子代理定义
│   │   ├── optics-mentor.md
│   │   └── literature-researcher.md
│   ├── skills/                  # 技能定义
│   │   ├── optics-learning/
│   │   └── literature-sync/
│   ├── hooks/                   # 自动化钩子
│   │   ├── session-end-hook.py   # 会话结束自动存笔记
│   │   ├── sync_viz.py          # 可视化自动同步
│   │   └── zotero_ref.py        # Zotero 文献引用
│   └── discussion_log.json       # 当前会话日志
│
├── Obsidian-Vault/              # Obsidian 知识库
│   ├── 0️⃣ Inbox/               # 自动收集的讨论摘要
│   ├── 1️⃣ 学科基础/             # 理论知识
│   ├── 2️⃣ 研究方向/             # 研究领域
│   │   └── 太赫兹技术/          # 太赫兹知识树
│   ├── 3️⃣ 方法论/               # 研究方法
│   ├── 4️⃣ 文献库/               # 论文笔记
│   ├── 5️⃣ 项目/                 # 项目
│   └── 6️⃣ 工具/                 # 工具
│       ├── scripts/              # 脚本
│       ├── templates/            # 模板
│       └── visualizations/      # 自动同步的可视化
│
└── .mcp.json                   # MCP 服务器配置
```

---

## 环境变量

```bash
# Zotero (已配置)
ZOTERO_API_KEY=gKXxzW93bZAWlbs0DCN0KVbj
ZOTERO_user_ID=20242032

# API Keys
TAVILY_API_KEY=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
```

---

## 自动化机制

### 1. 会话结束钩子 (SessionEnd Hook)

**触发**: 会话结束（你说"再见"、窗口关闭等）

**执行**:
1. 扫描本次讨论的所有主题
2. 检查是否已有相关笔记 → **避免重复**
3. 生成结构化摘要
4. 创建/追加到 Obsidian 笔记
5. 自动关联已有知识树

**钩子脚本**: `.claude/hooks/session-end-hook.py`

### 2. 可视化同步

**触发**: 我生成可视化图表时

**执行**:
1. 生成图表保存到临时位置
2. 自动复制到 `Obsidian-Vault/6️⃣ 工具/visualizations/`
3. 在对应笔记中插入 `![[image.png]]` 引用

**CLI 命令**:
```bash
python .claude/hooks/sync_viz.py --check "主题"  # 检查是否已有
python .claude/hooks/sync_viz.py image.png "主题"  # 同步新图
```

### 3. Zotero 文献引用

**触发**: 我引用论文时

**执行**:
1. 搜索本地 Zotero SQLite 数据库
2. 搜索 Better BibTeX 导出文件
3. 生成 `[[cite:@Author2024]]` 格式引用
4. 在笔记中附带完整引用信息

**CLI 命令**:
```bash
python .claude/hooks/zotero_ref.py search "keywords"  # 搜索文献
```

---

## AI 模型选择策略

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 快速概念解释 | gpt-5-thinking | 快速、便宜 |
| 深度公式推导 | claude-sonnet-4-6 | 强推理能力 |
| 代码生成 | claude-sonnet-4-6 | 编程能力强 |
| 文献综述 | claude-sonnet-4-6 + Tavily | 搜索 + 总结 |

---

## 使用规范

### 笔记结构

```
topic.md (概念笔记)
├── frontmatter: type, status, prerequisites, related, children
├── 一句话物理图像
├── 核心公式 (LaTeX)
├── 详细解释
├── Mermaid 知识树图
├── 引用文献 [[cite:@Author2024]]
└── 相关链接 [[other_topic]]
```

### 知识去重规则

| 情况 | 处理方式 |
|------|---------|
| 新主题 | 创建新笔记 |
| 已存在笔记的延伸 | 追加到已有笔记，更新关联 |
| 完全重复 | 更新 existing 笔记，不创建新的 |

### 标签系统

- `#optics` - 光学通用
- `#optics/terahertz` - 太赫兹
- `#optics/metasurface` - 超表面
- `#paper` - 论文笔记
- `#method` - 研究方法

---

## MCP Server 配置

```json
{
  "tavily-search": "网络搜索 (已连接)",
  "semantic-scholar": "学术搜索 (已连接)",
  "github": "GitHub (已连接)"
}
```

---

## CLI 工具

| 命令 | 用途 |
|------|------|
| `python .claude/hooks/session-end-hook.py` | 测试会话结束钩子 |
| `python .claude/hooks/sync_viz.py --list` | 列出已同步可视化 |
| `python .claude/hooks/sync_viz.py --check "主题"` | 检查某主题是否已有可视化 |
| `python .claude/hooks/zotero_ref.py search "关键词"` | 搜索 Zotero 文献 |

---

## 你如何跟我对话

### 直接说你的需求

```
"帮我深入理解 QCL 的工作原理"
"构建太赫兹成像的知识树"
"生成光电导天线原理的可视化"
"搜索最近关于超构透镜的论文"
```

### 我会自动完成

1. 深度回答（物理图像 + 公式 + 代码）
2. 创建/更新 Obsidian 笔记
3. 关联到知识树
4. 引用 Zotero 文献
5. 生成可视化并同步

---

*这个系统会随着你的使用不断进化，形成真正的"数字学术大脑"*
