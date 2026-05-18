var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __esm = (fn, res) => function __init() {
  return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/env-loader.ts
var env_loader_exports = {};
__export(env_loader_exports, {
  readZAIKey: () => readZAIKey
});
function readZAIKey() {
  const candidates = [
    path.join(process.cwd(), ".env"),
    path.join(__dirname, "..", ".env"),
    path.join(__dirname, "..", "..", ".env"),
    path.join(__dirname, "..", "..", "..", ".env")
  ];
  for (const envPath of candidates) {
    if (!(0, import_fs.existsSync)(envPath)) continue;
    try {
      const content = (0, import_fs.readFileSync)(envPath, "utf-8");
      const match = content.match(/^ZAI_API_KEY\s*=\s*["']?([^\s"']+)["']?/m);
      if (match) return match[1];
    } catch {
      continue;
    }
  }
  return null;
}
var import_fs, path;
var init_env_loader = __esm({
  "src/env-loader.ts"() {
    import_fs = require("fs");
    path = __toESM(require("path"));
  }
});

// main.ts
var main_exports = {};
__export(main_exports, {
  default: () => ClaudeAssistantPlugin
});
module.exports = __toCommonJS(main_exports);
var import_obsidian3 = require("obsidian");

// src/ClaudePanel.ts
var import_obsidian2 = require("obsidian");

// src/zai-client.ts
var import_obsidian = require("obsidian");
var ZAI_BASE_URL = "https://api.z.ai/api/anthropic";
var DEFAULT_MODEL = "glm-5.1";
var ZAIClient = class {
  constructor(config) {
    this.apiKey = config.apiKey;
    this.model = config.model || DEFAULT_MODEL;
    this.maxTokens = config.maxTokens || 4096;
  }
  setModel(model) {
    this.model = model;
  }
  getModel() {
    return this.model;
  }
  buildSystemPrompt(request) {
    const parts = [];
    parts.push("\u4F60\u662F\u5149\u5B66\u7814\u7A76\u8005\u7684\u5B66\u672F\u52A9\u624B\uFF0C\u8FD0\u884C\u5728 Obsidian \u77E5\u8BC6\u7BA1\u7406\u73AF\u5883\u4E2D\u3002");
    parts.push("\u7528\u4E2D\u6587\u56DE\u7B54\uFF0C\u7269\u7406\u672F\u8BED\u4FDD\u7559\u82F1\u6587\u3002\u8F93\u51FA Markdown \u683C\u5F0F\u3002");
    if (request.context.note_content) {
      parts.push(`
\u5F53\u524D\u7B14\u8BB0\u5185\u5BB9\uFF08\u538B\u7F29\uFF09:
${request.context.note_content}`);
    }
    if (request.options.include_formula) {
      parts.push("\u5305\u542B LaTeX \u516C\u5F0F\uFF08\u884C\u5185 $...$\uFF0C\u884C\u95F4 $$...$$\uFF09\u3002");
    }
    return parts.join("\n");
  }
  buildMessages(request) {
    const messages = [];
    const history = request.context.conversation_history || [];
    for (const entry of history) {
      messages.push({ role: entry.role, content: entry.content });
    }
    return messages;
  }
  makeHeaders() {
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${this.apiKey}`,
      "anthropic-version": "2023-06-01"
    };
  }
  async sendRequest(request) {
    var _a, _b;
    const response = await (0, import_obsidian.requestUrl)({
      url: `${ZAI_BASE_URL}/v1/messages`,
      method: "POST",
      headers: this.makeHeaders(),
      body: JSON.stringify({
        model: this.model,
        max_tokens: this.maxTokens,
        system: this.buildSystemPrompt(request),
        messages: this.buildMessages(request),
        stream: false
      })
    });
    const data = response.json;
    const text = ((_b = (_a = data.content) == null ? void 0 : _a[0]) == null ? void 0 : _b.text) || "";
    return {
      response: text,
      write_actions: []
    };
  }
  async sendRequestStream(request, onToken, onDone, onError) {
    var _a, _b;
    try {
      const response = await (0, import_obsidian.requestUrl)({
        url: `${ZAI_BASE_URL}/v1/messages`,
        method: "POST",
        headers: this.makeHeaders(),
        body: JSON.stringify({
          model: this.model,
          max_tokens: this.maxTokens,
          system: this.buildSystemPrompt(request),
          messages: this.buildMessages(request),
          stream: false
        })
      });
      const data = response.json;
      const fullText = ((_b = (_a = data.content) == null ? void 0 : _a[0]) == null ? void 0 : _b.text) || "";
      const chunkSize = 8;
      for (let i = 0; i < fullText.length; i += chunkSize) {
        onToken(fullText.slice(i, i + chunkSize));
      }
      onDone(fullText);
    } catch (err) {
      onError(err instanceof Error ? err : new Error(String(err)));
    }
  }
  async sendVisionRequest(textPrompt, imageBase64, mediaType, systemPrompt) {
    var _a, _b;
    const response = await (0, import_obsidian.requestUrl)({
      url: `${ZAI_BASE_URL}/v1/messages`,
      method: "POST",
      headers: this.makeHeaders(),
      body: JSON.stringify({
        model: "glm-4.6v",
        max_tokens: this.maxTokens,
        system: systemPrompt || "\u4F60\u662F\u5149\u5B66\u9886\u57DF\u4E13\u5BB6\uFF0C\u5206\u6790\u56FE\u7247\u4E2D\u7684\u7269\u7406\u5185\u5BB9\u3002\u7528\u4E2D\u6587\u56DE\u7B54\u3002",
        messages: [{
          role: "user",
          content: [
            {
              type: "image",
              source: {
                type: "base64",
                media_type: mediaType,
                data: imageBase64
              }
            },
            {
              type: "text",
              text: textPrompt
            }
          ]
        }],
        stream: false
      })
    });
    const data = response.json;
    return ((_b = (_a = data.content) == null ? void 0 : _a[0]) == null ? void 0 : _b.text) || "";
  }
  async testConnection() {
    try {
      const response = await (0, import_obsidian.requestUrl)({
        url: `${ZAI_BASE_URL}/v1/messages`,
        method: "POST",
        headers: this.makeHeaders(),
        body: JSON.stringify({
          model: this.model,
          max_tokens: 32,
          messages: [{ role: "user", content: "Hi" }],
          stream: false
        })
      });
      return response.status >= 200 && response.status < 300;
    } catch {
      return false;
    }
  }
};

// src/utils.ts
async function getActiveFileContent(app) {
  var _a;
  const activeFile = app.workspace.getActiveFile();
  if (!activeFile) {
    const leaves = app.workspace.getLeaves();
    for (const leaf of leaves) {
      if ((_a = leaf.view) == null ? void 0 : _a.file) {
        try {
          const content = await app.vault.read(leaf.view.file);
          return { path: leaf.view.file.path, content };
        } catch (e) {
          continue;
        }
      }
    }
    console.log("[ClaudePanel] getActiveFileContent: No active file found");
    return null;
  }
  try {
    const content = await app.vault.read(activeFile);
    return { path: activeFile.path, content };
  } catch (error) {
    console.error("[ClaudePanel] Error reading file:", error);
    return null;
  }
}
function compressNoteContent(content, maxLength = 4e3) {
  let compressed = content.replace(/\s+/g, " ").trim();
  if (compressed.length <= maxLength) {
    return compressed;
  }
  const headLength = Math.floor(maxLength * 0.7);
  const tailLength = maxLength - headLength;
  return compressed.substring(0, headLength) + "\n...[\u5185\u5BB9\u5DF2\u622A\u65AD]...\n" + compressed.slice(-tailLength);
}
function extractHeadings(content) {
  const headings = [];
  const regex = /^#{1,3}\s+(.+)$/gm;
  let match;
  while ((match = regex.exec(content)) !== null) {
    headings.push(match[1]);
  }
  return headings;
}
function insertAfterHeading(content, heading, insertContent) {
  const lines = content.split("\n");
  let insertIndex = lines.length;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === heading || lines[i].trim().startsWith(heading)) {
      insertIndex = i + 1;
      break;
    }
  }
  lines.splice(insertIndex, 0, "", insertContent);
  return lines.join("\n");
}

// src/ClaudePanel.ts
var styleContent = `
.claude-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 480px;
  height: 600px;
  background: var(--background-primary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1000;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.claude-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: move;
  user-select: none;
}
.claude-panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}
.claude-panel-model-badge {
  font-size: 10px;
  background: rgba(255,255,255,0.2);
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 400;
}
.claude-panel-controls { display: flex; gap: 8px; }
.claude-panel-controls button {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.claude-panel-controls button:hover { background: rgba(255,255,255,0.3); }
.claude-panel-info {
  padding: 8px 16px;
  background: var(--background-secondary);
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--text-muted);
}
.claude-panel-info .note-name { color: var(--text-primary); font-weight: 500; }
.claude-panel-history { flex: 1; overflow-y: auto; padding: 12px 16px; }
.claude-message { margin-bottom: 12px; border-radius: 8px; overflow: hidden; }
.claude-message.user { background: var(--background-secondary); border-left: 3px solid #667eea; }
.claude-message.assistant { background: var(--background-primary); border-left: 3px solid #764ba2; }
.claude-message-header { padding: 6px 10px; font-size: 11px; color: var(--text-muted); background: rgba(0,0,0,0.05); position: relative; display: flex; align-items: center; justify-content: space-between; }
.claude-message-write-btn { background: transparent; border: none; cursor: pointer; font-size: 12px; opacity: 0.4; padding: 2px 6px; border-radius: 3px; color: var(--text-muted); }
.claude-message-write-btn:hover { opacity: 1; background: rgba(102, 126, 234, 0.15); color: #667eea; }
.claude-write-mode { display: flex; gap: 4px; margin-bottom: 8px; }
.claude-write-mode-btn { padding: 4px 10px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--background-primary); color: var(--text-muted); font-size: 11px; cursor: pointer; white-space: nowrap; }
.claude-write-mode-btn.active { background: #667eea; color: white; border-color: #667eea; }
.claude-write-mode-btn:hover:not(.active) { background: var(--background-secondary); }
.claude-message-content { padding: 10px; font-size: 13px; line-height: 1.5; }
.claude-message-content pre { background: var(--background-secondary); padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 12px; }
.claude-message-content code { background: var(--background-secondary); padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }
.claude-streaming-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: #667eea;
  animation: blink-cursor 0.8s step-end infinite;
  vertical-align: text-bottom;
  margin-left: 1px;
}
@keyframes blink-cursor { 50% { opacity: 0; } }
.claude-panel-input { padding: 12px 16px; border-top: 1px solid var(--border-color); background: var(--background-secondary); }
.claude-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--background-primary);
  color: var(--text-primary);
  font-size: 13px;
  resize: none;
  min-height: 40px;
  max-height: 120px;
  font-family: inherit;
  width: 100%;
  box-sizing: border-box;
}
.claude-input:focus { outline: none; border-color: #667eea; }
.claude-buttons { display: flex; gap: 8px; }
.claude-btn { padding: 8px 14px; border: none; border-radius: 6px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
.claude-btn.primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.claude-btn.primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }
.claude-btn.primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.claude-btn.secondary { background: var(--background-primary); color: var(--text-secondary); border: 1px solid var(--border-color); }
.claude-btn.secondary:hover { background: var(--background-secondary); }
.claude-btn.stop { background: #ff6b6b; color: white; }
.claude-btn.stop:hover { background: #ff5252; }
.claude-status { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-muted); margin-top: 8px; }
.claude-status .spinner { width: 12px; height: 12px; border: 2px solid var(--border-color); border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.claude-panel.minimized .claude-panel-history,
.claude-panel.minimized .claude-panel-input { display: none; }
.claude-panel.minimized { height: auto; }
`;
var ClaudePanel = class {
  constructor(app, plugin, selectedText) {
    this.app = app;
    this.plugin = plugin;
    this.conversation = [];
    this.currentNotePath = null;
    this.currentNoteContent = "";
    this.selectedText = "";
    this.lastResponse = "";
    this.lastWriteActions = [];
    this.isMinimized = false;
    this.writeMode = "cursor";
    this.modeBtns = /* @__PURE__ */ new Map();
    this.isGenerating = false;
    this.currentAbortController = null;
    // Streaming state
    this.streamingMsgEl = null;
    this.streamingContentEl = null;
    this.streamingText = "";
    const settings = plugin.settings || {};
    this.client = new ZAIClient({
      apiKey: settings.apiKey || "",
      model: settings.model || "glm-5.1",
      maxTokens: settings.maxTokens || 4096
    });
    this.selectedText = selectedText || "";
    const styleEl = document.createElement("style");
    styleEl.textContent = styleContent;
    document.head.appendChild(styleEl);
    this.container = document.createElement("div");
    this.container.className = "claude-panel";
    this.buildUI();
    this.loadCurrentNote();
    document.body.appendChild(this.container);
    this.keydownHandler = (e) => {
      if (e.key === "Escape") this.close();
    };
    document.addEventListener("keydown", this.keydownHandler);
  }
  buildUI() {
    var _a, _b;
    const header = document.createElement("div");
    header.className = "claude-panel-header";
    header.innerHTML = `
			<div class="claude-panel-title">
				<span>Claude Assistant</span>
				<span class="claude-panel-model-badge">${this.client.getModel()}</span>
			</div>
			<div class="claude-panel-controls">
				<button class="btn-minimize" title="\u6700\u5C0F\u5316">_</button>
				<button class="btn-close" title="\u5173\u95ED">\xD7</button>
			</div>
		`;
    this.modelBadge = header.querySelector(".claude-panel-model-badge");
    (_a = header.querySelector(".btn-minimize")) == null ? void 0 : _a.addEventListener("click", () => this.toggleMinimize());
    (_b = header.querySelector(".btn-close")) == null ? void 0 : _b.addEventListener("click", () => this.close());
    this.infoEl = document.createElement("div");
    this.infoEl.className = "claude-panel-info";
    this.infoEl.innerHTML = `<span>\u{1F4C4} \u5F53\u524D: </span><span class="note-name">\u672A\u6253\u5F00\u7B14\u8BB0</span>`;
    this.historyEl = document.createElement("div");
    this.historyEl.className = "claude-panel-history";
    const inputArea = document.createElement("div");
    inputArea.className = "claude-panel-input";
    this.inputEl = document.createElement("textarea");
    this.inputEl.className = "claude-input";
    this.inputEl.placeholder = "\u8F93\u5165\u6307\u4EE4... (\u652F\u6301 Markdown, LaTeX, \u5FEB\u6377\u952E Enter \u53D1\u9001)";
    this.inputEl.rows = 2;
    this.sendBtn = document.createElement("button");
    this.sendBtn.className = "claude-btn primary";
    this.sendBtn.textContent = "\u{1F4E4} \u53D1\u9001";
    this.sendBtn.addEventListener("click", () => this.sendMessage());
    this.stopBtn = document.createElement("button");
    this.stopBtn.className = "claude-btn stop";
    this.stopBtn.textContent = "\u23F9 \u505C\u6B62";
    this.stopBtn.style.display = "none";
    this.stopBtn.addEventListener("click", () => this.stopGeneration());
    const modeRow = document.createElement("div");
    modeRow.className = "claude-write-mode";
    modeRow.style.display = "none";
    this.modeRow = modeRow;
    const modes = [
      { id: "cursor", label: "\u293C \u5149\u6807", title: "\u5199\u5165\u5230\u7F16\u8F91\u5668\u5149\u6807\u4F4D\u7F6E" },
      { id: "heading", label: "\u{1F4D1} \u6807\u9898", title: "\u667A\u80FD\u5339\u914D\u6807\u9898\u540E\u63D2\u5165" },
      { id: "append", label: "\u2913 \u6587\u672B", title: "\u8FFD\u52A0\u5230\u7B14\u8BB0\u672B\u5C3E" }
    ];
    for (const mode of modes) {
      const modeBtn = document.createElement("button");
      modeBtn.className = "claude-write-mode-btn";
      modeBtn.textContent = mode.label;
      modeBtn.title = mode.title;
      modeBtn.addEventListener("click", () => this.setWriteMode(mode.id));
      this.modeBtns.set(mode.id, modeBtn);
      modeRow.appendChild(modeBtn);
    }
    this.setWriteMode("cursor");
    this.writeBtn = document.createElement("button");
    this.writeBtn.className = "claude-btn secondary";
    this.writeBtn.textContent = "\u{1F4DD} \u5199\u5165\u7B14\u8BB0";
    this.writeBtn.addEventListener("click", () => this.writeToNote());
    this.writeBtn.style.display = "none";
    this.statusEl = document.createElement("div");
    this.statusEl.className = "claude-status";
    const btnContainer = document.createElement("div");
    btnContainer.className = "claude-buttons";
    btnContainer.appendChild(this.sendBtn);
    btnContainer.appendChild(this.stopBtn);
    btnContainer.appendChild(this.writeBtn);
    inputArea.appendChild(this.inputEl);
    inputArea.appendChild(modeRow);
    inputArea.appendChild(btnContainer);
    inputArea.appendChild(this.statusEl);
    this.container.appendChild(header);
    this.container.appendChild(this.infoEl);
    this.container.appendChild(this.historyEl);
    this.container.appendChild(inputArea);
    this.inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  }
  async loadCurrentNote() {
    this.app.workspace.on("active-leaf-change", () => this.refreshCurrentNote());
    await this.refreshCurrentNote();
    if (this.selectedText) {
      this.inputEl.value = this.selectedText;
    }
  }
  async refreshCurrentNote() {
    const fileInfo = await getActiveFileContent(this.app);
    if (fileInfo) {
      this.currentNotePath = fileInfo.path;
      this.currentNoteContent = fileInfo.content;
      const fileName = this.currentNotePath.split("/").pop();
      this.infoEl.innerHTML = `<span>\u{1F4C4} \u5F53\u524D: </span><span class="note-name">${fileName}</span>`;
    } else {
      this.infoEl.innerHTML = `<span>\u{1F4C4} \u5F53\u524D: </span><span class="note-name">\u672A\u6253\u5F00\u7B14\u8BB0</span>`;
    }
  }
  async sendMessage() {
    var _a;
    const message = this.inputEl.value.trim();
    if (!message || this.isGenerating) return;
    await this.refreshCurrentNote();
    this.addMessage("user", message);
    this.conversation.push({ role: "user", content: message, timestamp: Date.now() });
    this.inputEl.value = "";
    this.setGenerating(true);
    const validNoteContent = this.currentNoteContent || "";
    const request = {
      action: this.detectAction(message),
      context: {
        current_note: this.currentNotePath || "",
        note_content: compressNoteContent(validNoteContent),
        selected_text: this.selectedText || "",
        conversation_history: this.conversation.slice(-6)
        // 最近3轮
      },
      options: {
        depth: "detailed",
        include_formula: true,
        include_visualization: false
      }
    };
    const useStreaming = ((_a = this.plugin.settings) == null ? void 0 : _a.streaming) !== false;
    if (useStreaming) {
      this.startStreamingMessage();
      this.showStatus("\u751F\u6210\u4E2D...");
      await this.client.sendRequestStream(
        request,
        (token) => this.onStreamToken(token),
        (fullText) => this.onStreamDone(fullText),
        (error) => this.onStreamError(error)
      );
    } else {
      this.showStatus("\u601D\u8003\u4E2D...");
      try {
        const response = await this.client.sendRequest(request);
        this.handleResponse(response);
      } catch (error) {
        this.showError(`\u8C03\u7528\u5931\u8D25: ${error}`);
        this.setGenerating(false);
      }
    }
  }
  detectAction(message) {
    if (message.startsWith("/visualize")) return "visualize";
    if (message.startsWith("/cite")) return "cite";
    if (message.startsWith("/tree")) return "tree";
    return "explain";
  }
  // ── Streaming ──
  startStreamingMessage() {
    this.streamingText = "";
    const msgEl = document.createElement("div");
    msgEl.className = "claude-message assistant";
    msgEl.innerHTML = `
			<div class="claude-message-header">
				<span>Assistant</span>
				<button class="claude-message-write-btn" title="\u5199\u5165\u5230\u5149\u6807\u4F4D\u7F6E">\u{1F4DD}</button>
			</div>
			<div class="claude-message-content"></div>
		`;
    this.streamingContentEl = msgEl.querySelector(".claude-message-content");
    this.streamingMsgEl = msgEl;
    this.historyEl.appendChild(msgEl);
    this.historyEl.scrollTop = this.historyEl.scrollHeight;
  }
  onStreamToken(token) {
    if (!this.streamingContentEl) return;
    this.streamingText += token;
    this.streamingContentEl.empty();
    const cursor = document.createElement("span");
    cursor.className = "claude-streaming-cursor";
    import_obsidian2.MarkdownRenderer.renderMarkdown(this.streamingText, this.streamingContentEl, "", this.plugin);
    this.streamingContentEl.appendChild(cursor);
    this.historyEl.scrollTop = this.historyEl.scrollHeight;
  }
  onStreamDone(fullText) {
    if (!this.streamingContentEl || !this.streamingMsgEl) return;
    this.streamingContentEl.empty();
    import_obsidian2.MarkdownRenderer.renderMarkdown(fullText, this.streamingContentEl, "", this.plugin);
    const writeBtn = this.streamingMsgEl.querySelector(".claude-message-write-btn");
    if (writeBtn) {
      writeBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        this.writeMessageToNote(fullText);
      });
    }
    this.lastResponse = fullText;
    this.conversation.push({ role: "assistant", content: fullText, timestamp: Date.now() });
    this.streamingMsgEl = null;
    this.streamingContentEl = null;
    this.streamingText = "";
    this.showStatus("");
    this.setGenerating(false);
    this.writeBtn.style.display = "block";
    this.modeRow.style.display = "flex";
  }
  onStreamError(error) {
    if (this.streamingContentEl) {
      this.streamingContentEl.empty();
      this.streamingContentEl.textContent = `\u751F\u6210\u51FA\u9519: ${error.message}`;
      this.streamingContentEl.style.color = "#ff6b6b";
    }
    this.streamingMsgEl = null;
    this.streamingContentEl = null;
    this.setGenerating(false);
  }
  stopGeneration() {
    if (this.currentAbortController) {
      this.currentAbortController.abort();
      this.currentAbortController = null;
    }
    if (this.streamingText) {
      this.lastResponse = this.streamingText;
      this.conversation.push({ role: "assistant", content: this.streamingText, timestamp: Date.now() });
      if (this.streamingContentEl) {
        this.streamingContentEl.empty();
        import_obsidian2.MarkdownRenderer.renderMarkdown(this.streamingText, this.streamingContentEl, "", this.plugin);
      }
    }
    this.streamingMsgEl = null;
    this.streamingContentEl = null;
    this.streamingText = "";
    this.setGenerating(false);
    this.writeBtn.style.display = this.lastResponse ? "block" : "none";
    this.modeRow.style.display = this.lastResponse ? "flex" : "none";
    this.showStatus("\u5DF2\u505C\u6B62\u751F\u6210");
    setTimeout(() => this.showStatus(""), 2e3);
  }
  setGenerating(value) {
    this.isGenerating = value;
    this.sendBtn.textContent = value ? "\u23F3 \u751F\u6210\u4E2D" : "\u{1F4E4} \u53D1\u9001";
    this.sendBtn.disabled = value;
    this.stopBtn.style.display = value ? "inline-block" : "none";
    this.inputEl.disabled = value;
  }
  // ── Non-streaming fallback ──
  handleResponse(response) {
    this.lastResponse = response.response;
    this.lastWriteActions = response.write_actions;
    this.addMessage("assistant", response.response);
    this.conversation.push({ role: "assistant", content: response.response, timestamp: Date.now() });
    this.showStatus("");
    this.writeBtn.style.display = "block";
    this.modeRow.style.display = "flex";
    this.setGenerating(false);
  }
  // ── Message display ──
  addMessage(role, content) {
    const msgEl = document.createElement("div");
    msgEl.className = `claude-message ${role}`;
    msgEl.innerHTML = `
			<div class="claude-message-header">
				<span>${role === "user" ? "\u4F60" : "Assistant"}</span>
				${role === "assistant" ? '<button class="claude-message-write-btn" title="\u5199\u5165\u5230\u5149\u6807\u4F4D\u7F6E">\u{1F4DD}</button>' : ""}
			</div>
			<div class="claude-message-content"></div>
		`;
    const contentEl = msgEl.querySelector(".claude-message-content");
    import_obsidian2.MarkdownRenderer.renderMarkdown(content, contentEl, "", this.plugin);
    if (role === "assistant") {
      const writeBtn = msgEl.querySelector(".claude-message-write-btn");
      if (writeBtn) {
        writeBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.writeMessageToNote(content);
        });
      }
    }
    this.historyEl.appendChild(msgEl);
    this.historyEl.scrollTop = this.historyEl.scrollHeight;
  }
  showStatus(text) {
    if (text) {
      this.statusEl.innerHTML = `<div class="spinner"></div>${text}`;
    } else {
      this.statusEl.innerHTML = "";
    }
  }
  showError(text) {
    this.statusEl.innerHTML = `<span style="color: #ff6b6b;">\u26A0\uFE0F ${text}</span>`;
    setTimeout(() => this.showStatus(""), 3e3);
  }
  // ── Write to note ──
  writeMessageToNote(content) {
    var _a;
    const editor = (_a = this.app.workspace.activeEditor) == null ? void 0 : _a.editor;
    if (!editor) {
      this.showError("\u672A\u627E\u5230\u6D3B\u52A8\u7F16\u8F91\u5668");
      return;
    }
    editor.replaceRange("\n" + content + "\n", editor.getCursor());
    this.showStatus("\u2705 \u5DF2\u5199\u5165\u5149\u6807\u4F4D\u7F6E");
    setTimeout(() => this.showStatus(""), 2e3);
  }
  async writeToNote() {
    var _a;
    if (!this.lastResponse) {
      this.showError("\u65E0\u56DE\u590D\u5185\u5BB9");
      return;
    }
    this.showStatus("\u6B63\u5728\u5199\u5165\u7B14\u8BB0...");
    try {
      const summary = this.generateLocalSummary(this.currentNoteContent, []);
      if (this.writeMode === "cursor") {
        const editor = (_a = this.app.workspace.activeEditor) == null ? void 0 : _a.editor;
        if (!editor) {
          this.showError("\u672A\u627E\u5230\u6D3B\u52A8\u7F16\u8F91\u5668");
          return;
        }
        editor.replaceRange("\n" + summary + "\n", editor.getCursor());
        this.showStatus("\u2705 \u5DF2\u5199\u5165\u5149\u6807\u4F4D\u7F6E");
      } else if (this.writeMode === "append") {
        const activeFile = this.app.workspace.getActiveFile();
        if (!activeFile) {
          this.showError("\u672A\u627E\u5230\u6D3B\u52A8\u6587\u4EF6");
          return;
        }
        const currentContent = await this.app.vault.read(activeFile);
        if (currentContent.includes(summary.substring(0, 50))) {
          this.showError("\u5185\u5BB9\u5DF2\u5B58\u5728");
          return;
        }
        await this.app.vault.modify(activeFile, currentContent + "\n" + summary);
        this.showStatus("\u2705 \u5DF2\u8FFD\u52A0\u5230\u6587\u672B");
      } else {
        const activeFile = this.app.workspace.getActiveFile();
        if (!activeFile) {
          this.showError("\u672A\u627E\u5230\u6D3B\u52A8\u6587\u4EF6");
          return;
        }
        const currentContent = await this.app.vault.read(activeFile);
        if (currentContent.includes(summary.substring(0, 50))) {
          this.showError("\u5185\u5BB9\u5DF2\u5B58\u5728");
          return;
        }
        const headings = extractHeadings(currentContent);
        const targetHeading = this.findBestMatchingHeading(headings);
        let newContent;
        if (targetHeading && headings.length > 0) {
          newContent = insertAfterHeading(currentContent, targetHeading, summary);
        } else {
          newContent = currentContent + "\n" + summary;
        }
        await this.app.vault.modify(activeFile, newContent);
        this.currentNoteContent = newContent;
        this.showStatus(`\u2705 \u5DF2\u5199\u5165\u300C${targetHeading || "\u6587\u672B"}\u300D`);
      }
    } catch (error) {
      const errMsg = (error == null ? void 0 : error.message) || String(error);
      console.error("[ClaudePanel] writeToNote error:", error);
      this.showError(`\u5199\u5165\u5931\u8D25: ${errMsg.substring(0, 100)}`);
    }
    setTimeout(() => this.showStatus(""), 2500);
  }
  findBestMatchingHeading(headings) {
    var _a;
    if (headings.length === 0) return null;
    const userMessages = this.conversation.filter((c) => c.role === "user");
    const lastUserMsg = ((_a = userMessages[userMessages.length - 1]) == null ? void 0 : _a.content) || "";
    const stopWords = ["\u7684", "\u662F", "\u4EC0\u4E48", "\u5982\u4F55", "\u600E\u4E48", "\u4E3A\u4EC0\u4E48", "\u4ECB\u7ECD\u4E00\u4E0B", "\u8BF7", "\u7ED9\u6211", "\u89E3\u91CA", "\u4E00\u4E0B", "\u5417", "\u5462", "\uFF1F", "?", " ", "\n", "	"];
    let query = lastUserMsg.toLowerCase();
    stopWords.forEach((w) => {
      query = query.replace(new RegExp(w, "g"), " ");
    });
    const queryWords = query.split(/\s+/).filter((w) => w.length > 1);
    let bestHeading = null;
    let bestScore = 0;
    for (const heading of headings) {
      const headingLower = heading.toLowerCase().replace(/[#一二三四五六七八九十\d\.\s]+/g, "");
      let score = 0;
      for (const word of queryWords) {
        if (headingLower.includes(word)) {
          score += word.length;
        }
      }
      if (heading.startsWith("## ")) score *= 1.5;
      else if (heading.startsWith("### ")) score *= 2;
      if (score > bestScore) {
        bestScore = score;
        bestHeading = heading;
      }
    }
    if (!bestHeading && headings.length > 0) {
      for (let i = headings.length - 1; i >= 0; i--) {
        if (!headings[i].match(/^#\s/)) return headings[i];
      }
    }
    return bestHeading;
  }
  generateLocalSummary(noteContent, headings) {
    var _a, _b;
    const userMessages = this.conversation.filter((c) => c.role === "user");
    const assistantMessages = this.conversation.filter((c) => c.role === "assistant");
    const lastUserMsg = ((_a = userMessages[userMessages.length - 1]) == null ? void 0 : _a.content) || "";
    const lastAssistantMsg = ((_b = assistantMessages[assistantMessages.length - 1]) == null ? void 0 : _b.content) || "";
    const formulaRegex = /\$[^$]+\$|\$\$[\s\S]+?\$\$/g;
    const formulas = lastAssistantMsg.match(formulaRegex) || [];
    const mermaidRegex = /```mermaid[\s\S]*?```/g;
    const mermaidDiagrams = lastAssistantMsg.match(mermaidRegex) || [];
    let summary = "";
    summary += `> [!abstract]+ \u4E00\u53E5\u8BDD\u7269\u7406\u56FE\u50CF
`;
    summary += `> ${this.extractCoreConcept(lastUserMsg, lastAssistantMsg)}

`;
    summary += `> [!tip]+ \u6838\u5FC3\u8981\u70B9
`;
    summary += this.extractCorePoints(lastAssistantMsg);
    summary += "\n\n";
    if (formulas.length > 0) {
      summary += `### \u516C\u5F0F

`;
      formulas.forEach((f) => {
        summary += `${f}

`;
      });
    }
    summary += `### \u8BE6\u7EC6\u89E3\u91CA

`;
    summary += this.formatExplanation(lastAssistantMsg, formulas, mermaidDiagrams);
    summary += "\n\n";
    if (mermaidDiagrams.length > 0) {
      summary += `### \u77E5\u8BC6\u56FE

`;
      mermaidDiagrams.forEach((d) => {
        summary += `${d}

`;
      });
    }
    return summary;
  }
  extractCoreConcept(userQuery, assistantResponse) {
    const sentences = assistantResponse.split(/[.。!！?？]/).filter((s) => s.length > 10 && s.length < 100);
    if (sentences.length > 0) return sentences[sentences.length - 1].trim().substring(0, 80);
    return `\u4E0E\u300C${userQuery.substring(0, 20)}...\u300D\u76F8\u5173\u7684\u8BA8\u8BBA`;
  }
  extractCorePoints(content) {
    const lines = content.split("\n").filter((l) => l.trim().startsWith("-") || l.trim().startsWith("*"));
    if (lines.length >= 2) return lines.slice(0, 3).map((l) => `- ${l.replace(/^[-*]\s*/, "")}`).join("\n");
    const sentences = content.split(/[.。!！?？]/).filter((s) => s.length > 20 && s.length < 150);
    if (sentences.length >= 2) return sentences.slice(0, 3).map((s) => `- ${s.trim()}`).join("\n");
    return "- \u8BE6\u89C1\u4E0B\u65B9\u8BE6\u7EC6\u89E3\u91CA";
  }
  formatExplanation(content, formulas, diagrams) {
    let formatted = content;
    formatted = formatted.replace(/```mermaid[\s\S]*?```/g, "");
    formatted = formatted.replace(/\n{3,}/g, "\n\n").trim();
    return formatted;
  }
  toggleMinimize() {
    this.isMinimized = !this.isMinimized;
    this.container.classList.toggle("minimized", this.isMinimized);
  }
  setWriteMode(mode) {
    this.writeMode = mode;
    for (const [id, btn] of this.modeBtns) {
      btn.classList.toggle("active", id === mode);
    }
  }
  close() {
    this.stopGeneration();
    document.removeEventListener("keydown", this.keydownHandler);
    this.container.remove();
  }
};

// src/types.ts
var ZAI_MODELS = [
  { id: "glm-5.1", name: "GLM-5.1", desc: "\u65D7\u8230\u6A21\u578B\uFF0C\u6700\u5F3A\u63A8\u7406" },
  { id: "glm-5-turbo", name: "GLM-5-Turbo", desc: "\u5FEB\u901F\u63A8\u7406" },
  { id: "glm-5", name: "GLM-5", desc: "\u6807\u51C6\u6A21\u578B" },
  { id: "glm-4.7", name: "GLM-4.7", desc: "\u9AD8\u6548\u6A21\u578B" },
  { id: "glm-4.6", name: "GLM-4.6", desc: "\u5747\u8861\u6A21\u578B" },
  { id: "glm-4.5", name: "GLM-4.5", desc: "\u8F7B\u91CF\u6A21\u578B" },
  { id: "glm-4.5-air", name: "GLM-4.5-Air", desc: "\u6781\u901F\u6A21\u578B" },
  { id: "glm-4.6v", name: "GLM-4.6V (Vision)", desc: "\u89C6\u89C9\u7406\u89E3\u6A21\u578B" },
  { id: "glm-4.5v", name: "GLM-4.5V (Vision)", desc: "\u89C6\u89C9\u7406\u89E3\u6A21\u578B" }
];

// main.ts
var DEFAULT_SETTINGS = {
  apiKey: "",
  model: "glm-5.1",
  streaming: true,
  maxTokens: 4096
};
var ClaudeAssistantPlugin = class extends import_obsidian3.Plugin {
  constructor() {
    super(...arguments);
    this.panel = null;
    this.settings = DEFAULT_SETTINGS;
  }
  async onload() {
    console.log("[Claude Assistant] Plugin loading...");
    console.log("[Claude Assistant] Obsidian env \u2014 fetch available:", typeof fetch);
    try {
      this.addCommand({
        id: "open-claude-panel",
        name: "Open Claude Assistant Panel",
        callback: () => this.togglePanel()
      });
      this.addCommand({
        id: "quick-ask-claude",
        name: "Ask Claude (selected text)",
        editorCallback: (editor) => {
          const selected = editor.getSelection();
          if (selected) {
            this.togglePanel(selected);
          }
        }
      });
      this.addSettingTab(new ClaudeSettingsTab(this.app, this));
      await this.loadSettings();
      console.log("[Claude Assistant] Loaded \u2014 model:", this.settings.model, "streaming:", this.settings.streaming);
    } catch (error) {
      console.error("[Claude Assistant] Plugin load error:", error);
    }
  }
  onunload() {
    console.log("[Claude Assistant] Plugin unloading...");
    if (this.panel) {
      this.panel.close();
    }
  }
  async loadSettings() {
    const data = await this.loadData();
    if (data) {
      this.settings = Object.assign({}, DEFAULT_SETTINGS, data);
    }
    if (!this.settings.apiKey) {
      try {
        const { readZAIKey: readZAIKey2 } = (init_env_loader(), __toCommonJS(env_loader_exports));
        const key = readZAIKey2();
        if (key) {
          this.settings.apiKey = key;
          await this.saveSettings();
          console.log("[Claude Assistant] API key loaded from .env");
        }
      } catch {
        console.log("[Claude Assistant] No .env file found \u2014 set API key in settings");
      }
    }
  }
  async saveSettings() {
    await this.saveData(this.settings);
  }
  togglePanel(selectedText) {
    if (this.panel) {
      this.panel.close();
      this.panel = null;
    } else {
      this.panel = new ClaudePanel(this.app, this, selectedText);
    }
  }
};
var ClaudeSettingsTab = class extends import_obsidian3.PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }
  display() {
    const { containerEl } = this;
    containerEl.empty();
    new import_obsidian3.Setting(containerEl).setName("ZAI API Key").setDesc("\u667A\u8C31AI Coding Plan API Key\uFF08\u81EA\u52A8\u4ECE .env \u8BFB\u53D6\uFF0C\u4E5F\u53EF\u624B\u52A8\u8BBE\u7F6E\uFF09").addText((text) => text.setValue(this.plugin.settings.apiKey).setPlaceholder("fc8af37e...").onChange(async (value) => {
      this.plugin.settings.apiKey = value;
      await this.plugin.saveSettings();
    }));
    new import_obsidian3.Setting(containerEl).setName("\u6A21\u578B").setDesc("\u9009\u62E9\u8BED\u8A00\u6A21\u578B").addDropdown((dropdown) => {
      for (const m of ZAI_MODELS) {
        dropdown.addOption(m.id, `${m.name} \u2014 ${m.desc}`);
      }
      dropdown.setValue(this.plugin.settings.model).onChange(async (value) => {
        this.plugin.settings.model = value;
        await this.plugin.saveSettings();
      });
    });
    new import_obsidian3.Setting(containerEl).setName("\u6D41\u5F0F\u8F93\u51FA").setDesc("\u5F00\u542F\u540E\u5B9E\u65F6\u663E\u793A\u751F\u6210\u5185\u5BB9\uFF08\u63A8\u8350\uFF09").addToggle((toggle) => toggle.setValue(this.plugin.settings.streaming).onChange(async (value) => {
      this.plugin.settings.streaming = value;
      await this.plugin.saveSettings();
    }));
    new import_obsidian3.Setting(containerEl).setName("\u6700\u5927\u8F93\u51FA\u957F\u5EA6").setDesc("\u5355\u6B21\u56DE\u590D\u6700\u5927 token \u6570").addText((text) => text.setValue(String(this.plugin.settings.maxTokens)).onChange(async (value) => {
      const num = parseInt(value);
      if (!isNaN(num) && num > 0) {
        this.plugin.settings.maxTokens = num;
        await this.plugin.saveSettings();
      }
    }));
  }
};
//# sourceMappingURL=main.js.map
