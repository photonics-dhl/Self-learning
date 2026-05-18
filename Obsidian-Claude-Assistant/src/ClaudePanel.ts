import { App, MarkdownRenderer, setIcon } from 'obsidian';
import { ZAIClient } from './zai-client';
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
.claude-btn.upload { background: transparent; color: var(--text-muted); border: 1px solid var(--border-color); padding: 8px 10px; position: relative; }
.claude-btn.upload:hover { background: var(--background-secondary); color: var(--text-primary); }
.claude-btn.upload input[type="file"] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.claude-image-preview { display: none; padding: 6px 0; position: relative; }
.claude-image-preview.has-image { display: flex; align-items: center; gap: 8px; }
.claude-image-preview img { max-width: 80px; max-height: 60px; border-radius: 4px; border: 1px solid var(--border-color); object-fit: cover; }
.claude-image-preview .image-info { font-size: 11px; color: var(--text-muted); flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.claude-image-preview .remove-image { background: transparent; border: none; cursor: pointer; font-size: 14px; color: var(--text-muted); padding: 2px; line-height: 1; }
.claude-image-preview .remove-image:hover { color: #ff6b6b; }
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
	private stopBtn: HTMLElement;
	private writeBtn: HTMLElement;
	private modeRow: HTMLElement;
	private statusEl: HTMLElement;
	private infoEl: HTMLElement;
	private modelBadge: HTMLElement;

	private client: ZAIClient;
	private conversation: ConversationEntry[] = [];
	private currentNotePath: string | null = null;
	private currentNoteContent: string = '';
	private selectedText: string = '';
	private lastResponse: string = '';
	private lastWriteActions: ClaudeResponse['write_actions'] = [];
	private isMinimized: boolean = false;
	private writeMode: 'cursor' | 'heading' | 'append' = 'cursor';
	private modeBtns: Map<string, HTMLElement> = new Map();
	private keydownHandler: (e: KeyboardEvent) => void;
	private isGenerating: boolean = false;
	private currentAbortController: AbortController | null = null;

	// Streaming state
	private streamingMsgEl: HTMLElement | null = null;
	private streamingContentEl: HTMLElement | null = null;
	private streamingText: string = '';

	// Image upload state
	private attachedImage: { base64: string; mediaType: string; name: string } | null = null;
	private imagePreviewEl: HTMLElement | null = null;

	constructor(
		private app: App,
		private plugin: any,
		selectedText?: string
	) {
		const settings = plugin.settings || {};
		this.client = new ZAIClient({
			apiKey: settings.apiKey || '',
			model: settings.model || 'glm-5.1',
			maxTokens: settings.maxTokens || 4096
		});
		this.selectedText = selectedText || '';

		// 注入样式
		const styleEl = document.createElement('style');
		styleEl.textContent = styleContent;
		document.head.appendChild(styleEl);

		// 创建面板容器
		this.container = document.createElement('div');
		this.container.className = 'claude-panel';

		this.buildUI();
		this.loadCurrentNote();
		document.body.appendChild(this.container);

		this.keydownHandler = (e: KeyboardEvent) => {
			if (e.key === 'Escape') this.close();
		};
		document.addEventListener('keydown', this.keydownHandler);
	}

	private buildUI() {
		// Header
		const header = document.createElement('div');
		header.className = 'claude-panel-header';
		header.innerHTML = `
			<div class="claude-panel-title">
				<span>Claude Assistant</span>
				<span class="claude-panel-model-badge">${this.client.getModel()}</span>
			</div>
			<div class="claude-panel-controls">
				<button class="btn-minimize" title="最小化">_</button>
				<button class="btn-close" title="关闭">×</button>
			</div>
		`;

		this.modelBadge = header.querySelector('.claude-panel-model-badge')!;
		header.querySelector('.btn-minimize')?.addEventListener('click', () => this.toggleMinimize());
		header.querySelector('.btn-close')?.addEventListener('click', () => this.close());

		// Info bar
		this.infoEl = document.createElement('div');
		this.infoEl.className = 'claude-panel-info';
		this.infoEl.innerHTML = `<span>📄 当前: </span><span class="note-name">未打开笔记</span>`;

		// History area
		this.historyEl = document.createElement('div');
		this.historyEl.className = 'claude-panel-history';

		// Input area
		const inputArea = document.createElement('div');
		inputArea.className = 'claude-panel-input';

		this.inputEl = document.createElement('textarea');
		this.inputEl.className = 'claude-input';
		this.inputEl.placeholder = '输入指令... (支持 Markdown, LaTeX, 快捷键 Enter 发送)';
		this.inputEl.rows = 2;

		// 发送按钮
		this.sendBtn = document.createElement('button');
		this.sendBtn.className = 'claude-btn primary';
		this.sendBtn.textContent = '📤 发送';
		this.sendBtn.addEventListener('click', () => this.sendMessage());

		// 停止按钮（流式生成时显示）
		this.stopBtn = document.createElement('button');
		this.stopBtn.className = 'claude-btn stop';
		this.stopBtn.textContent = '⏹ 停止';
		this.stopBtn.style.display = 'none';
		this.stopBtn.addEventListener('click', () => this.stopGeneration());

		// 图片上传按钮
		const uploadBtn = document.createElement('button');
		uploadBtn.className = 'claude-btn upload';
		uploadBtn.textContent = '📎 图片';
		const fileInput = document.createElement('input');
		fileInput.type = 'file';
		fileInput.accept = 'image/png,image/jpeg,image/gif,image/webp';
		fileInput.title = '上传图片进行分析';
		fileInput.addEventListener('change', (e: Event) => this.handleImageUpload(e));
		uploadBtn.appendChild(fileInput);

		// 图片预览区域
		this.imagePreviewEl = document.createElement('div');
		this.imagePreviewEl.className = 'claude-image-preview';

		// 写入模式选择器
		const modeRow = document.createElement('div');
		modeRow.className = 'claude-write-mode';
		modeRow.style.display = 'none';
		this.modeRow = modeRow;

		const modes: Array<{id: 'cursor' | 'heading' | 'append'; label: string; title: string}> = [
			{ id: 'cursor', label: '⤼ 光标', title: '写入到编辑器光标位置' },
			{ id: 'heading', label: '📑 标题', title: '智能匹配标题后插入' },
			{ id: 'append', label: '⤓ 文末', title: '追加到笔记末尾' }
		];

		for (const mode of modes) {
			const modeBtn = document.createElement('button');
			modeBtn.className = 'claude-write-mode-btn';
			modeBtn.textContent = mode.label;
			modeBtn.title = mode.title;
			modeBtn.addEventListener('click', () => this.setWriteMode(mode.id));
			this.modeBtns.set(mode.id, modeBtn);
			modeRow.appendChild(modeBtn);
		}
		this.setWriteMode('cursor');

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
		btnContainer.appendChild(this.stopBtn);
		btnContainer.appendChild(uploadBtn);
		btnContainer.appendChild(this.writeBtn);

		inputArea.appendChild(this.inputEl);
		inputArea.appendChild(this.imagePreviewEl);
		inputArea.appendChild(modeRow);
		inputArea.appendChild(btnContainer);
		inputArea.appendChild(this.statusEl);

		this.container.appendChild(header);
		this.container.appendChild(this.infoEl);
		this.container.appendChild(this.historyEl);
		this.container.appendChild(inputArea);

		this.inputEl.addEventListener('keydown', (e: KeyboardEvent) => {
			if (e.key === 'Enter' && !e.shiftKey) {
				e.preventDefault();
				this.sendMessage();
			}
		});
	}

	private async loadCurrentNote() {
		this.app.workspace.on('active-leaf-change', () => this.refreshCurrentNote());
		await this.refreshCurrentNote();

		if (this.selectedText) {
			this.inputEl.value = this.selectedText;
		}
	}

	private async refreshCurrentNote() {
		const fileInfo = await getActiveFileContent(this.app);
		if (fileInfo) {
			this.currentNotePath = fileInfo.path;
			this.currentNoteContent = fileInfo.content;
			const fileName = this.currentNotePath.split('/').pop();
			this.infoEl.innerHTML = `<span>📄 当前: </span><span class="note-name">${fileName}</span>`;
		} else {
			this.infoEl.innerHTML = `<span>📄 当前: </span><span class="note-name">未打开笔记</span>`;
		}
	}

	private async sendMessage() {
		const message = this.inputEl.value.trim();
		if ((!message && !this.attachedImage) || this.isGenerating) return;

		await this.refreshCurrentNote();

		// 显示用户消息
		this.addMessage('user', message || '(图片分析)');
		this.conversation.push({ role: 'user', content: message || '(图片分析)', timestamp: Date.now() });

		this.inputEl.value = '';
		this.setGenerating(true);

		// 有图片走 vision 请求
		if (this.attachedImage) {
			await this.sendVisionMessage(message);
			return;
		}

		const validNoteContent = this.currentNoteContent || '';

		const request: ClaudeRequest = {
			action: this.detectAction(message),
			context: {
				current_note: this.currentNotePath || '',
				note_content: compressNoteContent(validNoteContent),
				selected_text: this.selectedText || '',
				conversation_history: this.conversation.slice(-6) // 最近3轮
			},
			options: {
				depth: 'detailed',
				include_formula: true,
				include_visualization: false
			}
		};

		const useStreaming = this.plugin.settings?.streaming !== false;

		if (useStreaming) {
			this.startStreamingMessage();
			this.showStatus('生成中...');

			await this.client.sendRequestStream(
				request,
				(token: string) => this.onStreamToken(token),
				(fullText: string) => this.onStreamDone(fullText),
				(error: Error) => this.onStreamError(error)
			);
		} else {
			this.showStatus('思考中...');
			try {
				const response = await this.client.sendRequest(request);
				this.handleResponse(response);
			} catch (error) {
				this.showError(`调用失败: ${error}`);
				this.setGenerating(false);
			}
		}
	}

	private detectAction(message: string): ClaudeRequest['action'] {
		if (message.startsWith('/visualize')) return 'visualize';
		if (message.startsWith('/cite')) return 'cite';
		if (message.startsWith('/tree')) return 'tree';
		return 'explain';
	}

	// ── Streaming ──

	private startStreamingMessage() {
		this.streamingText = '';

		const msgEl = document.createElement('div');
		msgEl.className = 'claude-message assistant';
		msgEl.innerHTML = `
			<div class="claude-message-header">
				<span>Assistant</span>
				<button class="claude-message-write-btn" title="写入到光标位置">📝</button>
			</div>
			<div class="claude-message-content"></div>
		`;

		this.streamingContentEl = msgEl.querySelector('.claude-message-content') as HTMLElement;
		this.streamingMsgEl = msgEl;
		this.historyEl.appendChild(msgEl);
		this.historyEl.scrollTop = this.historyEl.scrollHeight;
	}

	private onStreamToken(token: string) {
		if (!this.streamingContentEl) return;
		this.streamingText += token;

		// Render accumulated text as Markdown
		this.streamingContentEl.empty();
		// Add cursor indicator
		const cursor = document.createElement('span');
		cursor.className = 'claude-streaming-cursor';
		MarkdownRenderer.renderMarkdown(this.streamingText, this.streamingContentEl, '', this.plugin);
		this.streamingContentEl.appendChild(cursor);

		this.historyEl.scrollTop = this.historyEl.scrollHeight;
	}

	private onStreamDone(fullText: string) {
		if (!this.streamingContentEl || !this.streamingMsgEl) return;

		// Final render without cursor
		this.streamingContentEl.empty();
		MarkdownRenderer.renderMarkdown(fullText, this.streamingContentEl, '', this.plugin);

		// Wire write button
		const writeBtn = this.streamingMsgEl.querySelector('.claude-message-write-btn');
		if (writeBtn) {
			writeBtn.addEventListener('click', (e) => {
				e.stopPropagation();
				this.writeMessageToNote(fullText);
			});
		}

		this.lastResponse = fullText;
		this.conversation.push({ role: 'assistant', content: fullText, timestamp: Date.now() });

		this.streamingMsgEl = null;
		this.streamingContentEl = null;
		this.streamingText = '';

		this.showStatus('');
		this.setGenerating(false);
		this.writeBtn.style.display = 'block';
		this.modeRow.style.display = 'flex';
	}

	private onStreamError(error: Error) {
		if (this.streamingContentEl) {
			this.streamingContentEl.empty();
			this.streamingContentEl.textContent = `生成出错: ${error.message}`;
			this.streamingContentEl.style.color = '#ff6b6b';
		}
		this.streamingMsgEl = null;
		this.streamingContentEl = null;
		this.setGenerating(false);
	}

	private stopGeneration() {
		if (this.currentAbortController) {
			this.currentAbortController.abort();
			this.currentAbortController = null;
		}

		// Save whatever was streamed
		if (this.streamingText) {
			this.lastResponse = this.streamingText;
			this.conversation.push({ role: 'assistant', content: this.streamingText, timestamp: Date.now() });

			// Final render of partial content
			if (this.streamingContentEl) {
				this.streamingContentEl.empty();
				MarkdownRenderer.renderMarkdown(this.streamingText, this.streamingContentEl, '', this.plugin);
			}
		}

		this.streamingMsgEl = null;
		this.streamingContentEl = null;
		this.streamingText = '';
		this.setGenerating(false);
		this.writeBtn.style.display = this.lastResponse ? 'block' : 'none';
		this.modeRow.style.display = this.lastResponse ? 'flex' : 'none';
		this.showStatus('已停止生成');
		setTimeout(() => this.showStatus(''), 2000);
	}

	private setGenerating(value: boolean) {
		this.isGenerating = value;
		this.sendBtn.textContent = value ? '⏳ 生成中' : '📤 发送';
		(this.sendBtn as HTMLButtonElement).disabled = value;
		this.stopBtn.style.display = value ? 'inline-block' : 'none';
		this.inputEl.disabled = value;
	}

	// ── Non-streaming fallback ──

	private handleResponse(response: ClaudeResponse) {
		this.lastResponse = response.response;
		this.lastWriteActions = response.write_actions;

		this.addMessage('assistant', response.response);
		this.conversation.push({ role: 'assistant', content: response.response, timestamp: Date.now() });

		this.showStatus('');
		this.writeBtn.style.display = 'block';
		this.modeRow.style.display = 'flex';
		this.setGenerating(false);
	}

	// ── Message display ──

	private addMessage(role: 'user' | 'assistant', content: string) {
		const msgEl = document.createElement('div');
		msgEl.className = `claude-message ${role}`;
		msgEl.innerHTML = `
			<div class="claude-message-header">
				<span>${role === 'user' ? '你' : 'Assistant'}</span>
				${role === 'assistant' ? '<button class="claude-message-write-btn" title="写入到光标位置">📝</button>' : ''}
			</div>
			<div class="claude-message-content"></div>
		`;

		const contentEl = msgEl.querySelector('.claude-message-content') as HTMLElement;
		MarkdownRenderer.renderMarkdown(content, contentEl, '', this.plugin);

		if (role === 'assistant') {
			const writeBtn = msgEl.querySelector('.claude-message-write-btn');
			if (writeBtn) {
				writeBtn.addEventListener('click', (e) => {
					e.stopPropagation();
					this.writeMessageToNote(content);
				});
			}
		}

		this.historyEl.appendChild(msgEl);
		this.historyEl.scrollTop = this.historyEl.scrollHeight;
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

	// ── Write to note ──

	private writeMessageToNote(content: string) {
		const editor = this.app.workspace.activeEditor?.editor;
		if (!editor) {
			this.showError('未找到活动编辑器');
			return;
		}
		editor.replaceRange('\n' + content + '\n', editor.getCursor());
		this.showStatus('✅ 已写入光标位置');
		setTimeout(() => this.showStatus(''), 2000);
	}

	private async writeToNote() {
		if (!this.lastResponse) {
			this.showError('无回复内容');
			return;
		}

		this.showStatus('正在写入笔记...');

		try {
			const summary = this.generateLocalSummary(this.currentNoteContent, []);

			if (this.writeMode === 'cursor') {
				const editor = this.app.workspace.activeEditor?.editor;
				if (!editor) {
					this.showError('未找到活动编辑器');
					return;
				}
				editor.replaceRange('\n' + summary + '\n', editor.getCursor());
				this.showStatus('✅ 已写入光标位置');

			} else if (this.writeMode === 'append') {
				const activeFile = this.app.workspace.getActiveFile();
				if (!activeFile) {
					this.showError('未找到活动文件');
					return;
				}
				const currentContent = await this.app.vault.read(activeFile);

				if (currentContent.includes(summary.substring(0, 50))) {
					this.showError('内容已存在');
					return;
				}

				await this.app.vault.modify(activeFile, currentContent + '\n' + summary);
				this.showStatus('✅ 已追加到文末');

			} else {
				const activeFile = this.app.workspace.getActiveFile();
				if (!activeFile) {
					this.showError('未找到活动文件');
					return;
				}
				const currentContent = await this.app.vault.read(activeFile);

				if (currentContent.includes(summary.substring(0, 50))) {
					this.showError('内容已存在');
					return;
				}

				const headings = extractHeadings(currentContent);
				const targetHeading = this.findBestMatchingHeading(headings);

				let newContent: string;
				if (targetHeading && headings.length > 0) {
					newContent = insertAfterHeading(currentContent, targetHeading, summary);
				} else {
					newContent = currentContent + '\n' + summary;
				}

				await this.app.vault.modify(activeFile, newContent);
				this.currentNoteContent = newContent;
				this.showStatus(`✅ 已写入「${targetHeading || '文末'}」`);
			}
		} catch (error: any) {
			const errMsg = error?.message || String(error);
			console.error('[ClaudePanel] writeToNote error:', error);
			this.showError(`写入失败: ${errMsg.substring(0, 100)}`);
		}

		setTimeout(() => this.showStatus(''), 2500);
	}

	private findBestMatchingHeading(headings: string[]): string | null {
		if (headings.length === 0) return null;

		const userMessages = this.conversation.filter(c => c.role === 'user');
		const lastUserMsg = userMessages[userMessages.length - 1]?.content || '';

		const stopWords = ['的', '是', '什么', '如何', '怎么', '为什么', '介绍一下', '请', '给我', '解释', '一下', '吗', '呢', '？', '?', ' ', '\n', '\t'];
		let query = lastUserMsg.toLowerCase();
		stopWords.forEach(w => { query = query.replace(new RegExp(w, 'g'), ' '); });
		const queryWords = query.split(/\s+/).filter(w => w.length > 1);

		let bestHeading: string | null = null;
		let bestScore = 0;

		for (const heading of headings) {
			const headingLower = heading.toLowerCase().replace(/[#一二三四五六七八九十\d\.\s]+/g, '');
			let score = 0;
			for (const word of queryWords) {
				if (headingLower.includes(word)) {
					score += word.length;
				}
			}
			if (heading.startsWith('## ')) score *= 1.5;
			else if (heading.startsWith('### ')) score *= 2;
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

	private generateLocalSummary(noteContent: string, headings: string[]): string {
		const userMessages = this.conversation.filter(c => c.role === 'user');
		const assistantMessages = this.conversation.filter(c => c.role === 'assistant');
		const lastUserMsg = userMessages[userMessages.length - 1]?.content || '';
		const lastAssistantMsg = assistantMessages[assistantMessages.length - 1]?.content || '';

		const formulaRegex = /\$[^$]+\$|\$\$[\s\S]+?\$\$/g;
		const formulas = lastAssistantMsg.match(formulaRegex) || [];

		const mermaidRegex = /```mermaid[\s\S]*?```/g;
		const mermaidDiagrams = lastAssistantMsg.match(mermaidRegex) || [];

		let summary = '';
		summary += `> [!abstract]+ 一句话物理图像\n`;
		summary += `> ${this.extractCoreConcept(lastUserMsg, lastAssistantMsg)}\n\n`;
		summary += `> [!tip]+ 核心要点\n`;
		summary += this.extractCorePoints(lastAssistantMsg);
		summary += '\n\n';

		if (formulas.length > 0) {
			summary += `### 公式\n\n`;
			formulas.forEach(f => { summary += `${f}\n\n`; });
		}

		summary += `### 详细解释\n\n`;
		summary += this.formatExplanation(lastAssistantMsg, formulas, mermaidDiagrams);
		summary += '\n\n';

		if (mermaidDiagrams.length > 0) {
			summary += `### 知识图\n\n`;
			mermaidDiagrams.forEach(d => { summary += `${d}\n\n`; });
		}

		return summary;
	}

	private extractCoreConcept(userQuery: string, assistantResponse: string): string {
		const sentences = assistantResponse.split(/[.。!！?？]/).filter(s => s.length > 10 && s.length < 100);
		if (sentences.length > 0) return sentences[sentences.length - 1].trim().substring(0, 80);
		return `与「${userQuery.substring(0, 20)}...」相关的讨论`;
	}

	private extractCorePoints(content: string): string {
		const lines = content.split('\n').filter(l => l.trim().startsWith('-') || l.trim().startsWith('*'));
		if (lines.length >= 2) return lines.slice(0, 3).map(l => `- ${l.replace(/^[-*]\s*/, '')}`).join('\n');
		const sentences = content.split(/[.。!！?？]/).filter(s => s.length > 20 && s.length < 150);
		if (sentences.length >= 2) return sentences.slice(0, 3).map(s => `- ${s.trim()}`).join('\n');
		return '- 详见下方详细解释';
	}

	private formatExplanation(content: string, formulas: string[], diagrams: string[]): string {
		let formatted = content;
		formatted = formatted.replace(/```mermaid[\s\S]*?```/g, '');
		formatted = formatted.replace(/\n{3,}/g, '\n\n').trim();
		return formatted;
	}

	private toggleMinimize() {
		this.isMinimized = !this.isMinimized;
		this.container.classList.toggle('minimized', this.isMinimized);
	}

	private setWriteMode(mode: 'cursor' | 'heading' | 'append') {
		this.writeMode = mode;
		for (const [id, btn] of this.modeBtns) {
			btn.classList.toggle('active', id === mode);
		}
	}


	private handleImageUpload(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		// Validate file type
		const validTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];
		if (!validTypes.includes(file.type)) {
			this.showError('仅支持 PNG, JPG, GIF, WebP 格式');
			return;
		}

		// Validate file size (max 10MB)
		if (file.size > 10 * 1024 * 1024) {
			this.showError('图片不能超过 10MB');
			return;
		}

		const reader = new FileReader();
		reader.onload = () => {
			const base64Full = reader.result as string;
			// Strip data:image/xxx;base64, prefix
			const base64 = base64Full.split(',')[1];
			const mediaType = file.type as 'image/png' | 'image/jpeg' | 'image/gif' | 'image/webp';

			this.attachedImage = { base64, mediaType, name: file.name };
			this.updateImagePreview();
		};
		reader.readAsDataURL(file);

		// Reset input so same file can be re-selected
		input.value = '';
	}

	private removeAttachedImage() {
		this.attachedImage = null;
		this.updateImagePreview();
	}

	private updateImagePreview() {
		if (!this.imagePreviewEl) return;

		if (!this.attachedImage) {
			this.imagePreviewEl.className = 'claude-image-preview';
			this.imagePreviewEl.empty();
			return;
		}

		this.imagePreviewEl.className = 'claude-image-preview has-image';
		this.imagePreviewEl.empty();

		const img = document.createElement('img');
		img.src = `data:${this.attachedImage.mediaType};base64,${this.attachedImage.base64}`;

		const info = document.createElement('span');
		info.className = 'image-info';
		info.textContent = this.attachedImage.name;

		const removeBtn = document.createElement('button');
		removeBtn.className = 'remove-image';
		removeBtn.textContent = '✕';
		removeBtn.title = '移除图片';
		removeBtn.addEventListener('click', () => this.removeAttachedImage());

		this.imagePreviewEl.appendChild(img);
		this.imagePreviewEl.appendChild(info);
		this.imagePreviewEl.appendChild(removeBtn);
	}

	private async sendVisionMessage(userText: string) {
		if (!this.attachedImage) return;

		const prompt = userText || '请详细分析这张图片中的内容，包括其中的物理现象、实验装置、数据图表等。';
		this.showStatus('正在分析图片...');

		try {
			const result = await this.client.sendVisionRequest(
				prompt,
				this.attachedImage.base64,
				this.attachedImage.mediaType as 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp'
			);

			// Clear image after successful send
			this.removeAttachedImage();

			this.lastResponse = result;
			this.conversation.push({ role: 'assistant', content: result, timestamp: Date.now() });
			this.addMessage('assistant', result);

			this.showStatus('');
			this.setGenerating(false);
			this.writeBtn.style.display = 'block';
			this.modeRow.style.display = 'flex';
		} catch (error: any) {
			const errMsg = error?.message || String(error);
			this.showError(`图片分析失败: ${errMsg.substring(0, 100)}`);
			this.setGenerating(false);
		}
	}

	close() {
		this.stopGeneration();
		document.removeEventListener('keydown', this.keydownHandler);
		this.container.remove();
	}
}
