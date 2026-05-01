import { App, MarkdownRenderer, debounce, setIcon } from 'obsidian';
import { ClaudeCLI } from './cli';
import { ClaudeRequest, ClaudeResponse, ConversationEntry } from './types';
import {
  compressNoteContent,
  getActiveFileContent,
  appendToNote,
  insertAfterHeading,
  writeNoteContent,
  extractHeadings
} from './utils';

// 注入 CSS 样式
const styleContent = `
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

export class ClaudePanel {
  private container: HTMLElement;
  private historyEl: HTMLElement;
  private inputEl: HTMLTextAreaElement;
  private sendBtn: HTMLElement;
  private writeBtn: HTMLElement;
  private statusEl: HTMLElement;
  private infoEl: HTMLElement;

  private cli: ClaudeCLI;
  private conversation: ConversationEntry[] = [];
  private currentNotePath: string | null = null;
  private currentNoteContent: string = '';
  private selectedText: string = '';
  private lastResponse: string = '';
  private lastWriteActions: ClaudeResponse['write_actions'] = [];
  private isMinimized: boolean = false;
  private keydownHandler: (e: KeyboardEvent) => void;

  constructor(
    private app: App,
    private plugin: any,
    private cliPath: string = 'claude',
    selectedText?: string
  ) {
    this.cli = new ClaudeCLI(cliPath);
    this.selectedText = selectedText || '';

    // 注入样式
    const styleEl = document.createElement('style');
    styleEl.textContent = styleContent;
    document.head.appendChild(styleEl);

    // 创建面板容器
    this.container = document.createElement('div');
    this.container.className = 'claude-panel';

    this.buildUI();

    // 获取当前笔记信息
    this.loadCurrentNote();

    // 添加到body
    document.body.appendChild(this.container);

    // ESC 关闭
    this.keydownHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        this.close();
      }
    };
    document.addEventListener('keydown', this.keydownHandler);
  }

  private buildUI() {
    // Header
    const header = document.createElement('div');
    header.className = 'claude-panel-header';
    header.innerHTML = `
      <div class="claude-panel-title">Claude Assistant</div>
      <div class="claude-panel-controls">
        <button class="btn-minimize" title="最小化">_</button>
        <button class="btn-close" title="关闭">×</button>
      </div>
    `;

    header.querySelector('.btn-minimize')?.addEventListener('click', () => this.toggleMinimize());
    header.querySelector('.btn-close')?.addEventListener('click', () => this.close());

    // Info bar
    this.infoEl = document.createElement('div');
    this.infoEl.className = 'claude-panel-info';
    this.infoEl.innerHTML = `
      <span>📄 当前: </span>
      <span class="note-name">未打开笔记</span>
    `;

    // History area
    this.historyEl = document.createElement('div');
    this.historyEl.className = 'claude-panel-history';

    // Input area
    const inputArea = document.createElement('div');
    inputArea.className = 'claude-panel-input';

    this.inputEl = document.createElement('textarea');
    this.inputEl.className = 'claude-input';
    this.inputEl.placeholder = '输入指令... (/explain 解释概念, /visualize 生成图, /cite 引用文献)';
    this.inputEl.rows = 2;

    // 发送按钮
    this.sendBtn = document.createElement('button');
    this.sendBtn.className = 'claude-btn primary';
    this.sendBtn.textContent = '📤 发送';
    this.sendBtn.addEventListener('click', () => this.sendMessage());

    // 写入笔记按钮
    this.writeBtn = document.createElement('button');
    this.writeBtn.className = 'claude-btn secondary';
    this.writeBtn.textContent = '📝 写入笔记';
    this.writeBtn.addEventListener('click', () => this.writeToNote());
    this.writeBtn.style.display = 'none';

    // 状态
    this.statusEl = document.createElement('div');
    this.statusEl.className = 'claude-status';

    // 组装
    const btnContainer = document.createElement('div');
    btnContainer.className = 'claude-buttons';
    btnContainer.appendChild(this.sendBtn);
    btnContainer.appendChild(this.writeBtn);

    inputArea.appendChild(this.inputEl);
    inputArea.appendChild(btnContainer);
    inputArea.appendChild(this.statusEl);

    this.container.appendChild(header);
    this.container.appendChild(this.infoEl);
    this.container.appendChild(this.historyEl);
    this.container.appendChild(inputArea);

    // 事件
    this.inputEl.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
  }

  private async loadCurrentNote() {
    // 监听活动笔记变化
    this.app.workspace.on('active-leaf-change', () => {
      this.refreshCurrentNote();
    });

    // 立即获取当前笔记
    await this.refreshCurrentNote();

    // 如果有选中文本，自动作为第一个问题
    if (this.selectedText) {
      this.inputEl.value = this.selectedText;
      this.inputEl.placeholder = '已选中内容可直接发送...';
    }
  }

  /**
   * 刷新当前笔记信息
   */
  private async refreshCurrentNote() {
    const fileInfo = await getActiveFileContent(this.app);
    if (fileInfo) {
      this.currentNotePath = fileInfo.path;
      this.currentNoteContent = fileInfo.content;
      const fileName = this.currentNotePath.split('/').pop();
      this.infoEl.innerHTML = `
        <span>📄 当前: </span>
        <span class="note-name">${fileName}</span>
      `;
    } else {
      this.infoEl.innerHTML = `
        <span>📄 当前: </span>
        <span class="note-name">未打开笔记</span>
      `;
    }
  }

  private async sendMessage() {
    const message = this.inputEl.value.trim();
    if (!message) return;

    // 每次发送前重新获取当前笔记（确保使用户当前打开的笔记）
    await this.refreshCurrentNote();

    // 显示用户消息
    this.addMessage('user', message);
    this.conversation.push({ role: 'user', content: message, timestamp: Date.now() });

    // 清空输入
    this.inputEl.value = '';

    // 显示加载状态
    this.showStatus('正在思考...');

    // 确保笔记内容有效（防止 undefined 导致 JSON 序列化失败）
    const validNoteContent = this.currentNoteContent || '';

    // 构建请求
    const request: ClaudeRequest = {
      action: this.detectAction(message),
      context: {
        current_note: this.currentNotePath || '未打开笔记',
        note_content: compressNoteContent(validNoteContent),
        selected_text: this.selectedText || '',
        conversation_history: this.conversation.slice(-4) // 最近2轮对话
      },
      options: {
        depth: 'detailed',
        include_formula: true,
        include_visualization: false // Phase 1 暂不生成图
      }
    };

    try {
      // 调用 CLI
      const response = await this.cli.sendRequest(request);
      this.handleResponse(response);
    } catch (error) {
      this.showError(`调用失败: ${error}`);
    }
  }

  private detectAction(message: string): ClaudeRequest['action'] {
    if (message.startsWith('/visualize')) return 'visualize';
    if (message.startsWith('/cite')) return 'cite';
    if (message.startsWith('/tree')) return 'tree';
    return 'explain';
  }

  private handleResponse(response: ClaudeResponse) {
    this.lastResponse = response.response;
    this.lastWriteActions = response.write_actions;

    this.addMessage('assistant', response.response);
    this.conversation.push({ role: 'assistant', content: response.response, timestamp: Date.now() });

    this.showStatus('');
    this.writeBtn.style.display = 'block';

    // 如果有可视化，Phase 2 实现
    if (response.visualization) {
      this.addVisualization(response.visualization);
    }
  }

  private addMessage(role: 'user' | 'assistant', content: string) {
    const msgEl = document.createElement('div');
    msgEl.className = `claude-message ${role}`;
    msgEl.innerHTML = `
      <div class="claude-message-header">${role === 'user' ? '你' : 'Claude'}</div>
      <div class="claude-message-content"></div>
    `;

    const contentEl = msgEl.querySelector('.claude-message-content') as HTMLElement;

    // 渲染 Markdown
    MarkdownRenderer.renderMarkdown(content, contentEl, '', this.plugin);

    this.historyEl.appendChild(msgEl);
    this.historyEl.scrollTop = this.historyEl.scrollHeight;
  }

  private addVisualization(vis: {type: string; content: string}) {
    const visEl = document.createElement('div');
    visEl.className = 'claude-message assistant';
    visEl.innerHTML = `
      <div class="claude-message-header">📊 可视化</div>
      <div class="claude-message-content">
        <pre>${vis.content}</pre>
      </div>
    `;
    this.historyEl.appendChild(visEl);
  }

  private showStatus(text: string) {
    if (text) {
      this.statusEl.innerHTML = `<div class="spinner"></div>${text}`;
    } else {
      this.statusEl.innerHTML = '';
    }
  }

  private showError(text: string) {
    this.statusEl.innerHTML = `<span style="color: #ff6b6b;">⚠️ ${text}</span>`;
    setTimeout(() => this.showStatus(''), 3000);
  }

  private async writeToNote() {
    const errors: string[] = [];

    if (!this.lastResponse) {
      errors.push('无回复内容');
    }
    if (!this.currentNotePath) {
      errors.push('未打开笔记');
    }
    if (this.conversation.length < 2) {
      errors.push('对话不完整');
    }

    if (errors.length > 0) {
      this.showError('无法写入: ' + errors.join(', '));
      return;
    }

    this.showStatus('正在写入笔记...');

    try {
      const fileInfo = await getActiveFileContent(this.app);

      if (!fileInfo) {
        this.showError('错误: 无法读取当前笔记 - 请确认笔记已打开');
        return;
      }

      const headings = extractHeadings(fileInfo.content);
      const targetHeading = this.findBestMatchingHeading(headings);
      const summaryContent = this.generateLocalSummary(fileInfo.content, headings);

      if (!summaryContent || summaryContent.trim().length === 0) {
        this.showError('错误: 生成的内容为空');
        return;
      }

      // 检查是否已包含相同内容（防止重复写入）
      if (fileInfo.content.includes(summaryContent.substring(0, 50))) {
        this.showError('内容已存在，无需重复写入');
        setTimeout(() => this.showStatus(''), 2000);
        return;
      }

      const activeFile = this.app.workspace.getActiveFile();

      if (!activeFile) {
        this.showError('错误: 未找到活动文件');
        return;
      }

      let newContent: string;
      if (targetHeading && headings.length > 0) {
        newContent = insertAfterHeading(fileInfo.content, targetHeading, summaryContent);
      } else {
        newContent = fileInfo.content + '\n' + summaryContent;
      }

      await this.app.vault.modify(activeFile, newContent);
      this.currentNoteContent = newContent;

      this.showStatus('✅ 已写入笔记');
      setTimeout(() => this.showStatus(''), 2000);
    } catch (error: any) {
      const errMsg = error?.message || String(error);
      console.error('[ClaudePanel] writeToNote error:', error);
      this.showError(`写入失败: ${errMsg.substring(0, 100)}`);
    }
  }

  /**
   * 根据对话内容找到最匹配的标题
   */
  private findBestMatchingHeading(headings: string[]): string | null {
    if (headings.length === 0) return null;

    const userMessages = this.conversation.filter(c => c.role === 'user');
    const lastUserMsg = userMessages[userMessages.length - 1]?.content || '';

    // 提取用户问题的核心词（去除停用词）
    const stopWords = ['的', '是', '什么', '如何', '怎么', '为什么', '介绍一下', '请', '给我', '解释', '一下', '吗', '呢', '？', '?', ' ', '\n', '\t'];
    let query = lastUserMsg.toLowerCase();
    stopWords.forEach(w => { query = query.replace(new RegExp(w, 'g'), ' '); });
    const queryWords = query.split(/\s+/).filter(w => w.length > 1);

    // 计算每个标题的匹配分数
    let bestHeading: string | null = null;
    let bestScore = 0;

    for (const heading of headings) {
      const headingLower = heading.toLowerCase().replace(/[#一二三四五六七八九十\d\.\s]+/g, '');
      let score = 0;

      for (const word of queryWords) {
        if (headingLower.includes(word)) {
          score += word.length; // 匹配的字越多分数越高
        }
      }

      // 二级标题权重更高（更具体）
      if (heading.startsWith('## ')) {
        score *= 1.5;
      } else if (heading.startsWith('### ')) {
        score *= 2; // 三级标题最具体
      }

      if (score > bestScore) {
        bestScore = score;
        bestHeading = heading;
      }
    }

    // 如果没有匹配，返回最后一个小节标题
    if (!bestHeading && headings.length > 0) {
      // 找最后一个包含内容的小节（非一级标题）
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
  private generateLocalSummary(noteContent: string, headings: string[]): string {
    const userMessages = this.conversation.filter(c => c.role === 'user');
    const assistantMessages = this.conversation.filter(c => c.role === 'assistant');
    const lastUserMsg = userMessages[userMessages.length - 1]?.content || '';
    const lastAssistantMsg = assistantMessages[assistantMessages.length - 1]?.content || '';

    // 提取公式和图表
    const formulaRegex = /\$[^$]+\$|\$\$[\s\S]+?\$\$/g;
    const formulas = lastAssistantMsg.match(formulaRegex) || [];

    const mermaidRegex = /```mermaid[\s\S]*?```/g;
    const mermaidDiagrams = lastAssistantMsg.match(mermaidRegex) || [];

    // 构建符合项目规范的格式
    let summary = '';

    // 一句话物理图像
    summary += `> [!abstract]+ 一句话物理图像\n`;
    summary += `> ${this.extractCoreConcept(lastUserMsg, lastAssistantMsg)}\n\n`;

    // 核心要点
    summary += `> [!tip]+ 核心要点\n`;
    summary += this.extractCorePoints(lastAssistantMsg);
    summary += '\n\n';

    // 公式（如果有）
    if (formulas.length > 0) {
      summary += `### 公式\n\n`;
      formulas.forEach(f => { summary += `${f}\n\n`; });
    }

    // 详细解释
    summary += `### 详细解释\n\n`;
    summary += this.formatExplanation(lastAssistantMsg, formulas, mermaidDiagrams);
    summary += '\n\n';

    // 图表（如果有）
    if (mermaidDiagrams.length > 0) {
      summary += `### 知识图\n\n`;
      mermaidDiagrams.forEach(d => { summary += `${d}\n\n`; });
    }

    return summary;
  }

  /**
   * 提取一句话物理图像
   */
  private extractCoreConcept(userQuery: string, assistantResponse: string): string {
    // 尝试从回答中提取核心概念作为物理图像
    const sentences = assistantResponse.split(/[.。!！?？]/).filter(s => s.length > 10 && s.length < 100);
    if (sentences.length > 0) {
      return sentences[sentences.length - 1].trim().substring(0, 80);
    }
    return `与「${userQuery.substring(0, 20)}...」相关的深入讨论`;
  }

  /**
   * 提取核心要点（bullet points）
   */
  private extractCorePoints(content: string): string {
    // 尝试提取要点
    const lines = content.split('\n').filter(l => l.trim().startsWith('-') || l.trim().startsWith('*'));
    if (lines.length >= 2) {
      return lines.slice(0, 3).map(l => `- ${l.replace(/^[-*]\s*/, '')}`).join('\n');
    }

    // 尝试提取句子
    const sentences = content.split(/[.。!！?？]/).filter(s => s.length > 20 && s.length < 150);
    if (sentences.length >= 2) {
      return sentences.slice(0, 3).map(s => `- ${s.trim()}`).join('\n');
    }

    return '- 详见下方详细解释';
  }

  /**
   * 格式化详细解释
   */
  private formatExplanation(content: string, formulas: string[], diagrams: string[]): string {
    let formatted = content;

    // 移除已有的 mermaid 块（已在知识图中处理）
    formatted = formatted.replace(/```mermaid[\s\S]*?```/g, '');

    // 清理多余空行
    formatted = formatted.replace(/\n{3,}/g, '\n\n').trim();

    return formatted;
  }

  private toggleMinimize() {
    this.isMinimized = !this.isMinimized;
    if (this.isMinimized) {
      this.container.classList.add('minimized');
    } else {
      this.container.classList.remove('minimized');
    }
  }

  close() {
    document.removeEventListener('keydown', this.keydownHandler);
    this.container.remove();
  }
}