# 光学博士数字学术大脑 - 完整方案

> 2024-04-14 | 版本 1.0

---

## 一、系统概览

为光学专业博士构建的 **AI 辅助知识管理系统**，实现：
- Obsidian 本地知识库 + Claude Code AI 导师
- Zotero 文献自动同步
- 光学概念可视化
- MCP 知识库扩展搜索

```
┌─────────────────────────────────────────────────────────────────────┐
│                        数字学术大脑架构                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │   Zotero    │◄──►│   Obsidian  │◄──►│   Claude Code (终端)     │ │
│  │  文献管理    │    │   知识中枢   │    │   AI 超级导师            │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
│         │                  │                      │                │
│         ▼                  ▼                      ▼                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │ Better      │    │ Smart       │    │   MCP Server 扩展        │ │
│  │ BibTeX      │    │ Connections │    │   (Tavily/学术搜索)      │ │
│  │ + ZotFile    │    │ (RAG检索)   │    └─────────────────────────┘ │
│  └─────────────┘    └─────────────┘                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、已搭建完成的系统

### 2.1 文件结构

```
Self_Learning/
├── CLAUDE.md                    # 项目配置 (Claude Code 读取)
├── README.md                    # 使用指南
├── .mcp.json                    # MCP Server 配置
│
├── .claude/                     # Claude Code 配置
│   ├── settings.json            # 项目设置
│   ├── agents/                  # 子代理
│   │   ├── optics-mentor.md     # 光学导师代理
│   │   └── literature-researcher.md  # 文献研究代理
│   ├── skills/                  # 技能
│   │   ├── optics-learning/     # 光学学习技能
│   │   └── literature-sync/     # 文献同步技能
│   └── hooks/                   # 钩子
│       └── session-summary.py   # 会话总结
│
└── Obsidian-Vault/              # Obsidian 知识库
    ├── 0️⃣ Inbox/                # 灵感入口
    ├── 1️⃣ 学科基础/              # 基础理论
    ├── 2️⃣ 研究方向/              # 超表面光学等
    ├── 3️⃣ 方法论/                # 研究方法
    ├── 4️⃣ 文献库/                # Zotero 同步
    ├── 5️⃣ 项目/                  # 项目
    └── 6️⃣ 工具/                  # 脚本和模板
        ├── scripts/
        │   ├── new_note.py      # 新建笔记
        │   ├── sync_zotero.py   # Zotero 同步
        │   └── optics_viz.py    # 可视化
        └── templates/           # 笔记模板
            ├── concept.md
            ├── paper.md
            └── method.md
```

### 2.2 核心组件

| 组件 | 功能 | 状态 |
|------|------|------|
| CLAUDE.md | 项目配置 | ✅ |
| README.md | 使用指南 | ✅ |
| .mcp.json | MCP 配置 (Tavily, Semantic Scholar) | ✅ |
| optics-mentor | 光学导师代理 | ✅ |
| literature-researcher | 文献研究代理 | ✅ |
| optics-learning | 光学学习技能 | ✅ |
| literature-sync | 文献同步技能 | ✅ |
| new_note.py | 笔记创建脚本 | ✅ |
| sync_zotero.py | Zotero 同步脚本 | ✅ |
| optics_viz.py | 可视化脚本库 | ✅ |
| 笔记模板 | concept/paper/method | ✅ |

---

## 三、Obsidian 配置

### 必装插件

| 插件 | 来源 | 功能 |
|------|------|------|
| **Templater** | 社区 | 动态模板 |
| **Dataview** | 社区 | 笔记查询 |
| **Mermaid** | 社区 | 图表渲染 |
| **Admonition** | 社区 | 提示框 |
| **Excalidraw** | 社区 | 手绘示意 |
| **Zotero Integration** | 社区 | 文献嵌入 |
| **Smart Connections** | [GitHub](https://github.com/brianpetro/obsidian-smart-connections) | AI 检索 |

### Smart Connections 安装

1. 下载 [obsidian-smart-connections](https://github.com/brianpetro/obsidian-smart-connections)
2. 将 `main.js` 和 `manifest.json` 放入 `.obsidian/plugins/smart-connections/`
3. 在 Obsidian 设置中启用
4. 配置 API key (支持 Claude/GPT)

---

## 四、使用指南

### 4.1 快速开始

```bash
# 1. 进入项目目录
cd z:/321/DHL/Self_Learning

# 2. 启动 Claude Code
claude

# 3. 开始对话
"帮我解释高斯光束的束腰概念"
"构建超表面光学的知识树"
"搜索最近关于几何相位的论文"
```

### 4.2 新建笔记

```bash
# 方式 1: 命令行
python Obsidian-Vault/6️⃣ 工具/scripts/new_note.py "笔记标题" -t concept -s 子领域

# 方式 2: Claude Code
"帮我创建一篇关于 [主题] 的笔记"
```

### 4.3 Zotero 同步

```bash
# 1. 在 Zotero 中安装 Better BibTeX
# 2. 配置自动导出到 Self_Learning/Zotero/export.bib
# 3. 运行同步
python Obsidian-Vault/6️⃣ 工具/scripts/sync_zotero.py --bibtex Zotero/export.bib
```

### 4.4 可视化

```bash
# 列出所有可视化
python Obsidian-Vault/6️⃣ 工具/scripts/optics_viz.py --list

# 生成图表
python Obsidian-Vault/6️⃣ 工具/scripts/optics_viz.py gaussian_beam
python Obsidian-Vault/6️⃣ 工具/scripts/optics_viz.py diffraction --num_slits 3
```

---

## 五、模型选择策略

| 场景 | 模型 | 原因 |
|------|------|------|
| 快速概念解释 | gpt-5-thinking | 快速、便宜 |
| 深度公式推导 | claude-sonnet-4-6 | 强推理 |
| 代码生成 | claude-sonnet-4-6 | 编程能力强 |
| 文献综述 | claude-sonnet-4-6 + Tavily | 搜索 + 总结 |

---

## 六、MCP Server 配置

已在 `.mcp.json` 中配置：

```json
{
  "tavily-search": "网络搜索 (需要 TAVILY_API_KEY)",
  "semantic-scholar": "学术论文搜索",
  "github": "GitHub 访问"
}
```

### 使用示例

```
/mcp__tavily__search "超表面光学 最新进展"
/mcp__semantic-scholar__search_papers "geometric phase metasurface"
```

---

## 七、下一步行动

### 立即可做
- [ ] 在 Obsidian 中安装 Smart Connections 插件
- [ ] 配置 Zotero Better BibTeX 自动导出
- [ ] 设置 TAVILY_API_KEY 环境变量
- [ ] 运行 `python new_note.py "测试笔记" -t idea` 创建第一篇笔记

### 持续使用
- [ ] 每次学习新概念时创建 Obsidian 笔记
- [ ] 用 Claude Code 定期回顾和扩展知识树
- [ ] 阅读论文后同步到 Zotero 并导入 Obsidian

---

## 八、参考资源

- [Smart Connections](https://github.com/brianpetro/obsidian-smart-connections)
- [Obsidian 插件市场](obsidian.md/plugins)
- [Better BibTeX](https://retorque.re/zotero-better-bibtex/)
- [Zotero Integration](https://github.com/vanakat/zotero-integration)

---

*系统已完整搭建，立即开始你的"数字学术大脑"之旅！*
