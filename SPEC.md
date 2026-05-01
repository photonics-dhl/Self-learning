# Obsidian-Claude Assistant Plugin

## 1. Objective & Vision

**目标**：在 Obsidian 中创建一个悬浮命令面板，让用户可以直接向 Claude Code 提问，获取知识解释，并将结果实时写入笔记。

**核心体验**：
- 用户选中笔记中的某个概念/术语，发送指令
- 我接收指令，理解上下文（当前笔记内容 + 对话历史）
- 深度回答 + 生成可视化 + 写入 Obsidian 笔记
- 简短多轮对话（2-3轮），每次都是我收到完整上下文

**用户画像**：光学博士研究生，用于实时学习和研究

---

## 2. Commands & Interactions

### 2.1 触发方式

| 触发 | 行为 |
|------|------|
| `Ctrl+Shift+C` | 打开悬浮面板 |
| `Ctrl+Shift+Q` | 快速问答（选中文本作为上下文） |
| 右键菜单 "Ask Claude" | 选中文本发送到面板 |

### 2.2 悬浮面板 UI

```
┌─────────────────────────────────────────────┐
│  🔵 Claude Assistant              [_] [×]   │  ← 标题栏，可拖拽
├─────────────────────────────────────────────┤
│  📄 当前: 03_太赫兹成像.md                   │  ← 当前笔记名（只读）
├─────────────────────────────────────────────┤
│                                             │
│  [对话历史区 - 可折叠]                       │  ← 最近 2-3 轮对话
│  ┌─────────────────────────────────────────┐│
│  │ Q: 什么是光电导天线？                   ││
│  │ A: [回答内容，支持 markdown]            ││
│  └─────────────────────────────────────────┘│
│                                             │
├─────────────────────────────────────────────┤
│  💬 输入指令...                             │  ← 输入框
│                                             │
│  [📤 发送]  [📝 写入笔记]  [🖼 生成图]      │  ← 操作按钮
└─────────────────────────────────────────────┘
```

### 2.3 交互流程

1. **发送消息**
   - 用户在输入框输入，或右键发送选中文本
   - 面板显示 "正在思考..." 状态
   - 调用 CLI 获取回复

2. **显示结果**
   - 回复显示在对话历史区
   - 如果有生成可视化，显示缩略图

3. **写入笔记**（实时）
   - 用户点击 "📝 写入笔记" 或配置自动写入
   - 将当前回复追加/更新到当前笔记的相关位置
   - 可视化图片自动同步到 `Obsidian-Vault/6️⃣ 工具/visualizations/`

### 2.4 快捷指令

| 指令 | 行为 |
|------|------|
| `/explain [概念]` | 解释选中的概念 |
| `/visualize [主题]` | 生成可视化 |
| `/cite` | 搜索 Zotero 引用当前论文 |
| `/tree [主题]` | 生成知识树 Mermaid 图 |
| `/quit` | 关闭面板，清空对话历史 |

---

## 3. Project Structure

```
Obsidian-Claude-Assistant/
├── manifest.json              # Obsidian 插件清单
├── main.ts                    # 插件入口
├── src/
│   ├── ClaudePanel.ts         # 悬浮面板视图
│   ├── ClaudePanel.html       # 面板 HTML 模板
│   ├── ClaudePanel.css        # 面板样式
│   ├── cli.ts                 # Claude CLI 调用封装
│   ├── types.ts               # TypeScript 类型定义
│   └── utils.ts               # 工具函数
├── package.json
├── tsconfig.json
└── README.md
```

---

## 4. Code Style

- **语言**：TypeScript（Obsidian 原生开发语言）
- **框架**：原生 Obsidian API，无其他框架依赖
- **UI 渲染**：HTML/CSS（不使用 React/Vue，保持轻量）
- **CLI 调用**：Windows 用 `cmd /c`，Unix 用 `bash -c`
- **错误处理**：所有 async 操作用 try-catch，错误显示在面板中

---

## 5. Testing Strategy

### 5.1 单元测试
- `cli.ts` - Mock child_process，测试命令构造和解析

### 5.2 集成测试
- 手动测试各个触发方式
- 测试写入笔记的准确性

### 5.3 手动验证清单
- [ ] `Ctrl+Shift+C` 打开面板
- [ ] 输入指令获得回复
- [ ] 回复写入笔记
- [ ] 可视化同步到正确目录
- [ ] 多轮对话（2-3轮）上下文正确传递

---

## 6. Boundaries

### 6.1 必须做到
- 调用本地 `claude` CLI（不依赖网络共享）
- 面板可拖拽、可关闭
- 回复支持 Markdown 渲染
- 图片自动同步到 `visualizations/` 目录

### 6.2 询问确认（不做决定）
- 写入位置冲突时（笔记中已有相关内容）
- 大段内容写入时（超过 500 字）
- 删除已有内容时

### 6.3 绝不做
- 不在服务器 Z: 盘上调用 claude（延迟高）
- 不在面板中缓存完整对话历史（避免内存泄漏）
- 不发送敏感信息到外部 API

---

## 7. Technical Details

### 7.1 CLI 调用协议

**请求 JSON**（通过 stdin 传递）:
```json
{
  "action": "explain",
  "context": {
    "current_note": "03_太赫兹成像.md",
    "note_content": "## 光电导天线\n\n光电导天线是产生太赫兹辐射的核心器件...",
    "selected_text": "光电导天线",
    "conversation_history": [
      {"role": "user", "content": "什么是光电导天线？"},
      {"role": "assistant", "content": "光电导天线是..."}
    ]
  },
  "options": {
    "depth": "detailed",
    "include_formula": true,
    "include_visualization": true
  }
}
```

**响应 JSON**（从 stdout 解析）:
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

### 7.2 上下文传递方式

插件每次请求时传入：
- 当前笔记完整内容（用于理解上下文）
- 最近 2-3 轮对话历史
- 用户选中的文本

我根据这些上下文生成回答，并将写入手柄指令包含在响应中。

### 7.3 写入机制

响应中的 `write_actions` 由插件执行：
- `append`: 追加到笔记末尾
- `insert_after_heading`: 插入到指定标题后
- `replace`: 替换选中内容

### 7.4 可视化同步

生成图片时：
1. 我返回图片的 base64 或临时路径
2. 插件保存到 `Obsidian-Vault/6️⃣ 工具/visualizations/`
3. 插件在笔记中插入 `![[image.png]]` 引用

---

## 8. Implementation Phases

### Phase 1: 基础框架
- 创建 Obsidian 插件骨架
- 实现悬浮面板 UI
- 基本 CLI 调用

### Phase 2: 对话功能
- 支持 Markdown 渲染
- 对话历史传递
- 实时写入笔记

### Phase 3: 增强功能
- 可视化生成和同步
- Zotero 引用
- 知识树生成