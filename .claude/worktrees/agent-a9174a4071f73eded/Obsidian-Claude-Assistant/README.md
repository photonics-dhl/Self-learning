# Obsidian Claude Assistant

在 Obsidian 中集成 Claude Code，直接提问并自动写入笔记。

## 功能

- 🎯 **悬浮面板**: `Ctrl+Shift+C` 打开 Claude 助手
- 📝 **上下文感知**: 自动获取当前笔记内容作为上下文
- ✍️ **实时写入**: 回复可一键写入当前笔记
- 🔍 **快捷指令**: `/explain`, `/visualize`, `/cite`, `/tree`
- 🎨 **Markdown 渲染**: 支持完整的 Markdown 格式

## 安装

### 方式一：手动安装（推荐用于开发）

1. 克隆/复制 `Obsidian-Claude-Assistant` 文件夹到 Obsidian 插件目录：
   ```
   vault_name/.obsidian/plugins/Obsidian-Claude-Assistant/
   ```

2. 进入插件目录，安装依赖并编译：
   ```bash
   cd Obsidian-Claude-Assistant
   npm install
   npm run build
   ```

3. 在 Obsidian 中启用插件：
   - 设置 → 第三方插件 → 启用 "Claude Assistant"

### 方式二：BRAT（测试版）

1. 安装 BRAT 插件
2. 添加 beta repository: `https://github.com/YOUR_USERNAME/Obsidian-Claude-Assistant`

## 配置

### Claude CLI 路径

在插件设置中配置 `claude` CLI 的路径，默认值为 `claude`（假设已在 PATH 中）。

Windows 示例: `C:\Users\Mac\AppData\Local\Programs\Claude\Claude.exe`
macOS 示例: `/usr/local/bin/claude`

### 环境要求

- Obsidian v0.15.0+
- Node.js 16+
- Claude Code CLI (需配置 API Key)

## 使用方法

### 打开面板

| 方式 | 操作 |
|------|------|
| 快捷键 | `Ctrl+Shift+C` |
| 命令面板 | `Ctrl+P` → "Open Claude Assistant Panel" |

### 快速问答

1. 在笔记中选中文本
2. `Ctrl+Shift+Q` 或 右键 → "Ask Claude"
3. 选中的文本会自动填入输入框

### 发送指令

在输入框输入内容，按 `Enter` 或点击「📤 发送」。

### 快捷指令

| 指令 | 说明 |
|------|------|
| `/explain [概念]` | 解释选中的概念 |
| `/visualize [主题]` | 生成可视化（Phase 2） |
| `/cite` | 搜索 Zotero 引用（Phase 2） |
| `/tree [主题]` | 生成知识树（Phase 2） |
| `/quit` | 关闭面板 |

### 写入笔记

点击「📝 写入笔记」将 Claude 的回答追加到当前笔记末尾。

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│  Obsidian                                           │
│  ┌─────────────────┐    ┌─────────────────────────┐ │
│  │  Claude Panel   │───▶│  Claude CLI (child_proc)│ │
│  │  (浮动窗口)     │    │  - send JSON via stdin  │ │
│  │                 │◀───│  - receive JSON via     │ │
│  │                 │    │    stdout               │ │
│  └─────────────────┘    └─────────────────────────┘ │
│         │                                                  │
│         ▼                                                  │
│  ┌─────────────────┐                                     │
│  │  Obsidian Vault │                                     │
│  │  (写入笔记)      │                                     │
│  └─────────────────┘                                     │
└─────────────────────────────────────────────────────────┘
```

### CLI 协议

**请求格式** (通过 stdin 传递):
```json
{
  "action": "explain",
  "context": {
    "current_note": "03_太赫兹成像.md",
    "note_content": "...",
    "selected_text": "光电导天线",
    "conversation_history": [
      {"role": "user", "content": "解释这个概念"},
      {"role": "assistant", "content": "这是..."}
    ]
  },
  "options": {
    "depth": "detailed",
    "include_formula": true,
    "include_visualization": false
  }
}
```

**响应格式** (从 stdout 解析):
```json
{
  "response": "## 解释内容（Markdown）",
  "visualization": {
    "type": "mermaid",
    "content": "graph TD\n  A-->B"
  },
  "write_actions": [
    {"type": "append", "target": "03_太赫兹成像.md", "content": "..."}
  ]
}
```

## 开发

### 项目结构

```
Obsidian-Claude-Assistant/
├── manifest.json          # 插件清单
├── main.ts                # 插件入口
├── package.json
├── tsconfig.json
└── src/
    ├── cli.ts             # CLI 调用封装
    ├── types.ts           # TypeScript 类型
    ├── utils.ts           # 工具函数
    └── ClaudePanel.ts     # 面板组件
```

### 编译

```bash
npm run build    # 编译一次
npm run dev      # 监听模式（修改自动编译）
```

### 测试

1. 启动 Obsidian
2. 打开任意笔记
3. `Ctrl+Shift+C` 打开面板
4. 输入问题，观察 CLI 调用和响应

## Phase 2 计划

- [ ] 可视化生成（Mermaid 图）
- [ ] Zotero 文献引用
- [ ] 图片自动同步到 visualizations 目录
- [ ] 多语言支持

## 问题排查

### CLI 调用失败

1. 检查 `claude` 是否在 PATH 中
2. 在插件设置中填写完整路径
3. 测试: 打开命令行，输入 `claude --version`

### 笔记未找到

确保先打开一个笔记文件，再使用插件。

## License

MIT