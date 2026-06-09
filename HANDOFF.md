# HANDOFF — Cross-Session Context Bridge

> Updated: 2026-06-07 (Session 26 — Obsidian 插件 Fallback 路由修复)

## Last Task: Claude Assistant 插件多模型 Fallback 路由

### 已完成

**Fallback 链路**: `glm-5.1` (z.ai, Anthropic) → `MiniMax-M2.7` (MiniMax, OpenAI) → `deepseek-v4-flash` (DeepSeek, OpenAI)

| 文件 | 改动 |
|------|------|
| `src/env-loader.ts` | 新增 `readMiniMaxKey()`, `readDeepSeekKey()`, `readMiniMaxBaseUrl()`, `readDeepSeekBaseUrl()`, `readAllCredentials()` |
| `src/types.ts` | 新增 Fallback 模型条目、`ProviderType`, `ApiFormat`, `FallbackEntry`, `FallbackChain`, `RoutedResponse` 类型 |
| `src/zai-client.ts` | 核心重写：`buildFallbackChain()`, `buildVisionFallbackChain()`, `sendAnthropicRequest()`, `sendOpenAIRequest()`, `sendWithFallback()`, Vision fallback |
| `src/ClaudePanel.ts` | `updateModelBadge()` 显示实际模型+降级高亮；构造函数传递 fallback API keys |
| `main.ts` | `PluginSettings` 扩展 miniMax/deepSeek keys；设置 UI 三个 key 字段；从 .env 自动加载；诊断日志 |

### 错误修复历程

1. **MiniMax 400**: model ID `minimax-m2.7` → `MiniMax-M2.7`（官方 API 大小写）
2. **DeepSeek model 名**: `deepseek-chat` → `deepseek-v4-flash`（用户指定）
3. **Key 未传入**: 原架构 `zai-client.ts` 运行时调 `readAllCredentials()` → `fs` 在 Electron renderer 上下文失败。改为 `main.ts` 启动时加载所有 key → `ClaudePanel` → `ZAIClient` 构造器注入
4. **设置 UI 缺 MiniMax/DeepSeek 字段**: 本次 session 补齐

### 关键设计决策

- **双 API 格式**: z.ai 用 Anthropic Messages API（`/v1/messages`, system 顶层字段），MiniMax/DeepSeek 用 OpenAI Chat Completions API（`/v1/chat/completions`, system 作为第一条 message）
- **Vision 独立 fallback 链**: z.ai vision 端点 `https://api.z.ai/api/paas/v4/chat/completions`（OpenAI 格式），fallback 同 MiniMax/DeepSeek
- **Key 加载时机**: `main.ts` → `loadSettings()` → `require('./src/env-loader')`（esbuild 内联）→ 读 .env → 存入 settings → `saveData()` 持久化到 data.json
- **设置 UI**: 三个 API Key 字段全部可见，自动从 .env 读取，用户可覆盖

### 待验证

- [ ] MiniMax `MiniMax-M2.7` 在官方 `api.minimax.chat/v1/chat/completions` 上是否有效（之前配的可能是第三方聚合）
- [ ] DeepSeek `deepseek-v4-flash` 在 `api.deepseek.com` 上是否有效（官方仅 `deepseek-chat` + `deepseek-reasoner`）
- [ ] 完整 fallback 端到端测试（断掉 z.ai 验证 MiniMax 接管，断掉 MiniMax 验证 DeepSeek 接管）

### 下一步可选方向

- 验证 MiniMax 官方 API endpoint（可能是 `/v1/text/chatcompletion_v2` 而非 `/v1/chat/completions`）
- 若 DeepSeek 报 400，改 model ID 为 `deepseek-chat`
- 插件流式输出需改 `sendRequestStream()` 支持真正的 SSE streaming（目前是 simulate streaming by chunking）

## Previous Sessions

- **Session 25**: 小孔量子化 Obsidian 笔记优化（1453→1676行, +15%）
- **Session 24**: 学科基础笔记全面优化（19篇全部达标）+ 学习路径更新
- **Session 23**: 新建3篇笔记(16/17/18) + 学习路径更新
