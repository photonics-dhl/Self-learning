var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
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
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/ClaudePanel.ts
var ClaudePanel_exports = {};
__export(ClaudePanel_exports, {
  ClaudePanel: () => ClaudePanel
});
module.exports = __toCommonJS(ClaudePanel_exports);
var import_obsidian = require("obsidian");

// src/cli.ts
var import_child_process = require("child_process");
var ClaudeCLI = class {
  constructor(cliPath = "node claude-wrapper.js") {
    this.cliPath = cliPath;
  }
  async sendRequest(request) {
    return new Promise((resolve, reject) => {
      const requestStr = JSON.stringify(request);
      const isWindows = process.platform === "win32";
      const child = (0, import_child_process.spawn)(
        isWindows ? "cmd" : "bash",
        isWindows ? ["/c", this.cliPath] : ["-c", this.cliPath],
        {
          stdio: ["pipe", "pipe", "pipe"],
          env: { ...process.env },
          cwd: isWindows ? void 0 : __dirname
        }
      );
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (data) => {
        stdout += data.toString();
      });
      child.stderr.on("data", (data) => {
        stderr += data.toString();
      });
      child.on("error", reject);
      child.on("close", (code) => {
        if (code !== 0 && !stdout) {
          reject(new Error(`CLI exited with code ${code}: ${stderr}`));
          return;
        }
        try {
          const lines = stdout.trim().split("\n");
          const jsonLine = lines.find((l) => l.trim().startsWith("{"));
          if (jsonLine) {
            resolve(JSON.parse(jsonLine));
          } else {
            resolve({
              response: stdout,
              write_actions: []
            });
          }
        } catch (e) {
          resolve({
            response: stdout || stderr,
            write_actions: []
          });
        }
      });
      child.stdin.write(requestStr);
      child.stdin.end();
    });
  }
  async testConnection() {
    try {
      const result = await this.sendRequest({
        action: "explain",
        context: {
          current_note: "test.md",
          note_content: "test",
          selected_text: "test",
          conversation_history: []
        },
        options: {
          depth: "brief",
          include_formula: false,
          include_visualization: false
        }
      });
      return !!result.response;
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
.claude-message-header { padding: 6px 10px; font-size: 11px; color: var(--text-muted); background: rgba(0,0,0,0.05); }
.claude-message-content { padding: 10px; font-size: 13px; line-height: 1.5; }
.claude-message-content pre { background: var(--background-secondary); padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 12px; }
.claude-message-content code { background: var(--background-secondary); padding: 2px 4px; border-radius: 3px; font-family: 'Consolas', monospace; }
.claude-panel-input { padding: 12px 16px; border-top: 1px solid var(--border-color); background: var(--background-secondary); }
.claude-input-row { display: flex; gap: 8px; margin-bottom: 8px; }
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
.claude-status { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-muted); margin-top: 8px; }
.claude-status .spinner { width: 12px; height: 12px; border: 2px solid var(--border-color); border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.claude-panel.minimized .claude-panel-history,
.claude-panel.minimized .claude-panel-input { display: none; }
.claude-panel.minimized { height: auto; }
`;
var ClaudePanel = class {
  constructor(app, plugin, cliPath = "claude", selectedText) {
    this.app = app;
    this.plugin = plugin;
    this.cliPath = cliPath;
    this.conversation = [];
    this.currentNotePath = null;
    this.currentNoteContent = "";
    this.selectedText = "";
    this.lastResponse = "";
    this.lastWriteActions = [];
    this.isMinimized = false;
    this.cli = new ClaudeCLI(cliPath);
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
      if (e.key === "Escape") {
        this.close();
      }
    };
    document.addEventListener("keydown", this.keydownHandler);
  }
  buildUI() {
    var _a, _b;
    const header = document.createElement("div");
    header.className = "claude-panel-header";
    header.innerHTML = `
      <div class="claude-panel-title">Claude Assistant</div>
      <div class="claude-panel-controls">
        <button class="btn-minimize" title="\u6700\u5C0F\u5316">_</button>
        <button class="btn-close" title="\u5173\u95ED">\xD7</button>
      </div>
    `;
    (_a = header.querySelector(".btn-minimize")) == null ? void 0 : _a.addEventListener("click", () => this.toggleMinimize());
    (_b = header.querySelector(".btn-close")) == null ? void 0 : _b.addEventListener("click", () => this.close());
    this.infoEl = document.createElement("div");
    this.infoEl.className = "claude-panel-info";
    this.infoEl.innerHTML = `
      <span>\u{1F4C4} \u5F53\u524D: </span>
      <span class="note-name">\u672A\u6253\u5F00\u7B14\u8BB0</span>
    `;
    this.historyEl = document.createElement("div");
    this.historyEl.className = "claude-panel-history";
    const inputArea = document.createElement("div");
    inputArea.className = "claude-panel-input";
    this.inputEl = document.createElement("textarea");
    this.inputEl.className = "claude-input";
    this.inputEl.placeholder = "\u8F93\u5165\u6307\u4EE4... (/explain \u89E3\u91CA\u6982\u5FF5, /visualize \u751F\u6210\u56FE, /cite \u5F15\u7528\u6587\u732E)";
    this.inputEl.rows = 2;
    this.sendBtn = document.createElement("button");
    this.sendBtn.className = "claude-btn primary";
    this.sendBtn.textContent = "\u{1F4E4} \u53D1\u9001";
    this.sendBtn.addEventListener("click", () => this.sendMessage());
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
    btnContainer.appendChild(this.writeBtn);
    inputArea.appendChild(this.inputEl);
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
    this.app.workspace.on("active-leaf-change", () => {
      this.refreshCurrentNote();
    });
    await this.refreshCurrentNote();
    if (this.selectedText) {
      this.inputEl.value = this.selectedText;
      this.inputEl.placeholder = "\u5DF2\u9009\u4E2D\u5185\u5BB9\u53EF\u76F4\u63A5\u53D1\u9001...";
    }
  }
  /**
   * 刷新当前笔记信息
   */
  async refreshCurrentNote() {
    const fileInfo = await getActiveFileContent(this.app);
    if (fileInfo) {
      this.currentNotePath = fileInfo.path;
      this.currentNoteContent = fileInfo.content;
      const fileName = this.currentNotePath.split("/").pop();
      this.infoEl.innerHTML = `
        <span>\u{1F4C4} \u5F53\u524D: </span>
        <span class="note-name">${fileName}</span>
      `;
    } else {
      this.infoEl.innerHTML = `
        <span>\u{1F4C4} \u5F53\u524D: </span>
        <span class="note-name">\u672A\u6253\u5F00\u7B14\u8BB0</span>
      `;
    }
  }
  async sendMessage() {
    const message = this.inputEl.value.trim();
    if (!message) return;
    await this.refreshCurrentNote();
    this.addMessage("user", message);
    this.conversation.push({ role: "user", content: message, timestamp: Date.now() });
    this.inputEl.value = "";
    this.showStatus("\u6B63\u5728\u601D\u8003...");
    const validNoteContent = this.currentNoteContent || "";
    const request = {
      action: this.detectAction(message),
      context: {
        current_note: this.currentNotePath || "\u672A\u6253\u5F00\u7B14\u8BB0",
        note_content: compressNoteContent(validNoteContent),
        selected_text: this.selectedText || "",
        conversation_history: this.conversation.slice(-4)
        // 最近2轮对话
      },
      options: {
        depth: "detailed",
        include_formula: true,
        include_visualization: false
        // Phase 1 暂不生成图
      }
    };
    try {
      const response = await this.cli.sendRequest(request);
      this.handleResponse(response);
    } catch (error) {
      this.showError(`\u8C03\u7528\u5931\u8D25: ${error}`);
    }
  }
  detectAction(message) {
    if (message.startsWith("/visualize")) return "visualize";
    if (message.startsWith("/cite")) return "cite";
    if (message.startsWith("/tree")) return "tree";
    return "explain";
  }
  handleResponse(response) {
    this.lastResponse = response.response;
    this.lastWriteActions = response.write_actions;
    this.addMessage("assistant", response.response);
    this.conversation.push({ role: "assistant", content: response.response, timestamp: Date.now() });
    this.showStatus("");
    this.writeBtn.style.display = "block";
    if (response.visualization) {
      this.addVisualization(response.visualization);
    }
  }
  addMessage(role, content) {
    const msgEl = document.createElement("div");
    msgEl.className = `claude-message ${role}`;
    msgEl.innerHTML = `
      <div class="claude-message-header">${role === "user" ? "\u4F60" : "Claude"}</div>
      <div class="claude-message-content"></div>
    `;
    const contentEl = msgEl.querySelector(".claude-message-content");
    import_obsidian.MarkdownRenderer.renderMarkdown(content, contentEl, "", this.plugin);
    this.historyEl.appendChild(msgEl);
    this.historyEl.scrollTop = this.historyEl.scrollHeight;
  }
  addVisualization(vis) {
    const visEl = document.createElement("div");
    visEl.className = "claude-message assistant";
    visEl.innerHTML = `
      <div class="claude-message-header">\u{1F4CA} \u53EF\u89C6\u5316</div>
      <div class="claude-message-content">
        <pre>${vis.content}</pre>
      </div>
    `;
    this.historyEl.appendChild(visEl);
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
  async writeToNote() {
    const errors = [];
    if (!this.lastResponse) {
      errors.push("\u65E0\u56DE\u590D\u5185\u5BB9");
    }
    if (!this.currentNotePath) {
      errors.push("\u672A\u6253\u5F00\u7B14\u8BB0");
    }
    if (this.conversation.length < 2) {
      errors.push("\u5BF9\u8BDD\u4E0D\u5B8C\u6574");
    }
    if (errors.length > 0) {
      this.showError("\u65E0\u6CD5\u5199\u5165: " + errors.join(", "));
      return;
    }
    this.showStatus("\u6B63\u5728\u5199\u5165\u7B14\u8BB0...");
    try {
      const fileInfo = await getActiveFileContent(this.app);
      if (!fileInfo) {
        this.showError("\u9519\u8BEF: \u65E0\u6CD5\u8BFB\u53D6\u5F53\u524D\u7B14\u8BB0 - \u8BF7\u786E\u8BA4\u7B14\u8BB0\u5DF2\u6253\u5F00");
        return;
      }
      const headings = extractHeadings(fileInfo.content);
      const targetHeading = this.findBestMatchingHeading(headings);
      const summaryContent = this.generateLocalSummary(fileInfo.content, headings);
      if (!summaryContent || summaryContent.trim().length === 0) {
        this.showError("\u9519\u8BEF: \u751F\u6210\u7684\u5185\u5BB9\u4E3A\u7A7A");
        return;
      }
      if (fileInfo.content.includes(summaryContent.substring(0, 50))) {
        this.showError("\u5185\u5BB9\u5DF2\u5B58\u5728\uFF0C\u65E0\u9700\u91CD\u590D\u5199\u5165");
        setTimeout(() => this.showStatus(""), 2e3);
        return;
      }
      const activeFile = this.app.workspace.getActiveFile();
      if (!activeFile) {
        this.showError("\u9519\u8BEF: \u672A\u627E\u5230\u6D3B\u52A8\u6587\u4EF6");
        return;
      }
      let newContent;
      if (targetHeading && headings.length > 0) {
        newContent = insertAfterHeading(fileInfo.content, targetHeading, summaryContent);
      } else {
        newContent = fileInfo.content + "\n" + summaryContent;
      }
      await this.app.vault.modify(activeFile, newContent);
      this.currentNoteContent = newContent;
      this.showStatus("\u2705 \u5DF2\u5199\u5165\u7B14\u8BB0");
      setTimeout(() => this.showStatus(""), 2e3);
    } catch (error) {
      const errMsg = (error == null ? void 0 : error.message) || String(error);
      console.error("[ClaudePanel] writeToNote error:", error);
      this.showError(`\u5199\u5165\u5931\u8D25: ${errMsg.substring(0, 100)}`);
    }
  }
  /**
   * 根据对话内容找到最匹配的标题
   */
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
      if (heading.startsWith("## ")) {
        score *= 1.5;
      } else if (heading.startsWith("### ")) {
        score *= 2;
      }
      if (score > bestScore) {
        bestScore = score;
        bestHeading = heading;
      }
    }
    if (!bestHeading && headings.length > 0) {
      for (let i = headings.length - 1; i >= 0; i--) {
        if (!headings[i].match(/^#\s/)) {
          return headings[i];
        }
      }
    }
    return bestHeading;
  }
  /**
   * 生成符合项目规范的笔记内容
   */
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
  /**
   * 提取一句话物理图像
   */
  extractCoreConcept(userQuery, assistantResponse) {
    const sentences = assistantResponse.split(/[.。!！?？]/).filter((s) => s.length > 10 && s.length < 100);
    if (sentences.length > 0) {
      return sentences[sentences.length - 1].trim().substring(0, 80);
    }
    return `\u4E0E\u300C${userQuery.substring(0, 20)}...\u300D\u76F8\u5173\u7684\u6DF1\u5165\u8BA8\u8BBA`;
  }
  /**
   * 提取核心要点（bullet points）
   */
  extractCorePoints(content) {
    const lines = content.split("\n").filter((l) => l.trim().startsWith("-") || l.trim().startsWith("*"));
    if (lines.length >= 2) {
      return lines.slice(0, 3).map((l) => `- ${l.replace(/^[-*]\s*/, "")}`).join("\n");
    }
    const sentences = content.split(/[.。!！?？]/).filter((s) => s.length > 20 && s.length < 150);
    if (sentences.length >= 2) {
      return sentences.slice(0, 3).map((s) => `- ${s.trim()}`).join("\n");
    }
    return "- \u8BE6\u89C1\u4E0B\u65B9\u8BE6\u7EC6\u89E3\u91CA";
  }
  /**
   * 格式化详细解释
   */
  formatExplanation(content, formulas, diagrams) {
    let formatted = content;
    formatted = formatted.replace(/```mermaid[\s\S]*?```/g, "");
    formatted = formatted.replace(/\n{3,}/g, "\n\n").trim();
    return formatted;
  }
  toggleMinimize() {
    this.isMinimized = !this.isMinimized;
    if (this.isMinimized) {
      this.container.classList.add("minimized");
    } else {
      this.container.classList.remove("minimized");
    }
  }
  close() {
    document.removeEventListener("keydown", this.keydownHandler);
    this.container.remove();
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ClaudePanel
});
//# sourceMappingURL=ClaudePanel.js.map
