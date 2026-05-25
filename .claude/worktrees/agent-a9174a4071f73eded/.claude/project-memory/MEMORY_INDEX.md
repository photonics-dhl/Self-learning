# Self_Learning 项目记忆索引

> ⚠️ **Single Source of Truth**: 本项目的完整记忆存储在 `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\`（由 Claude Code 维护）。此文件仅为桥接索引，供 Kimi Code CLI 在项目工作目录内快速定位。

## 快速导航

| 类别 | C 盘路径 |
|------|----------|
| **总纲** | `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\MEMORY.md` |
| **用户配置** | `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\config\` |
| **项目参考** | `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\reference\` |
| **经验学习** | `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\learning\` |
| **反馈记录** | `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\feedback\` |

## 关键记忆文件

### 配置 (config/)
- `user_role.md` — 用户身份和角色
- `mcp_config_global_to_project.md` — MCP 全局到项目配置经验

### 参考 (reference/)
- `project_optics_brain.md` — 项目概述和架构
- `reference_zotero.md` — Zotero 文献库配置和 RAG 知识库架构
- `skill_routing_20260505.md` — AGENTS.md 路由：bishe-guider 为中文毕业论文首选 skill

### 经验 (learning/)
- `paper_writing_skill_20260424.md` — AI Scientist V2 × 光学大脑论文撰写系统
- `paper_writing_v5_2_update.md` — v5.2 Skills 重构 + LLM humanizer 架构
- `file_convert_skill_20260424.md` — 文件格式转换 (MarkItDown + pandoc)
- `tavily_proxy_20260424.md` — Tavily API 代理配置
- `vscode_extension_issues_20260501.md` — VS Code Extension Host 问题排查

### 反馈 (feedback/)
- `feedback_knowledge_planning.md` — 知识规划前置流程的重要性
- `feedback_mcp_usage.md` — MCP 使用反馈

## 项目结构

```
z:\321\DHL\Self_Learning
├── Obsidian-Claude-Assistant/  # Obsidian 插件（Claude 面板）
├── academic_rag/               # 学术 RAG 系统（Chroma + 论文索引）
├── zotero_import/              # Zotero 导入工具
├── DHL/                        # 论文项目（small_hole_qed, terahertz_qed 等）
├── Obsidian-Vault/             # Obsidian 知识库
├── CLAUDE.md                   # 项目总纲
└── SPEC.md                     # 项目规范
```

## 记忆写入规则

- **新错误** → 记录到 `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\learning\`
- **新经验** → 记录到 `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\learning\`
- **用户反馈** → 记录到 `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\feedback\`
- **配置变更** → 更新 `C:\Users\Mac\.claude\projects\z--321-DHL-Self-Learning\memory\config\`

## 跨项目共享

- **代理**: `http://127.0.0.1:7890`
- **Zotero**: 本地文献库 + RAG 向量化
- **Tavily**: API 搜索（含 key rotation 机制）
