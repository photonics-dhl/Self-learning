import { requestUrl } from 'obsidian';
import { ClaudeRequest, ClaudeResponse } from './types';

const ZAI_BASE_URL = 'https://api.z.ai/api/anthropic';
const DEFAULT_MODEL = 'glm-5.1';

export interface ZAIClientConfig {
	apiKey: string;
	model?: string;
	maxTokens?: number;
}

export class ZAIClient {
	private apiKey: string;
	private model: string;
	private maxTokens: number;

	constructor(config: ZAIClientConfig) {
		this.apiKey = config.apiKey;
		this.model = config.model || DEFAULT_MODEL;
		this.maxTokens = config.maxTokens || 4096;
	}

	setModel(model: string) {
		this.model = model;
	}

	getModel(): string {
		return this.model;
	}

	private buildSystemPrompt(request: ClaudeRequest): string {
		const parts: string[] = [];

		parts.push('你是光学研究者的学术助手，运行在 Obsidian 知识管理环境中。');
		parts.push('用中文回答，物理术语保留英文。输出 Markdown 格式。');

		if (request.context.note_content) {
			parts.push(`\n当前笔记内容（压缩）:\n${request.context.note_content}`);
		}

		if (request.options.include_formula) {
			parts.push('包含 LaTeX 公式（行内 $...$，行间 $$...$$）。');
		}

		return parts.join('\n');
	}

	private buildMessages(request: ClaudeRequest): Array<{role: 'user' | 'assistant'; content: string | any[]}> {
		const messages: Array<{role: 'user' | 'assistant'; content: string | any[]}> = [];
		const history = request.context.conversation_history || [];

		for (const entry of history) {
			messages.push({ role: entry.role, content: entry.content });
		}

		return messages;
	}

	private makeHeaders(): Record<string, string> {
		return {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${this.apiKey}`,
			'anthropic-version': '2023-06-01'
		};
	}

	async sendRequest(request: ClaudeRequest): Promise<ClaudeResponse> {
		const response = await requestUrl({
			url: `${ZAI_BASE_URL}/v1/messages`,
			method: 'POST',
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
		const text = data.content?.[0]?.text || '';
		return {
			response: text,
			write_actions: []
		};
	}

	async sendRequestStream(
		request: ClaudeRequest,
		onToken: (text: string) => void,
		onDone: (fullText: string) => void,
		onError: (error: Error) => void
	): Promise<void> {
		try {
			const response = await requestUrl({
				url: `${ZAI_BASE_URL}/v1/messages`,
				method: 'POST',
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
			const fullText = data.content?.[0]?.text || '';

			// Simulate streaming by sending text in chunks
			const chunkSize = 8;
			for (let i = 0; i < fullText.length; i += chunkSize) {
				onToken(fullText.slice(i, i + chunkSize));
			}

			onDone(fullText);
		} catch (err) {
			onError(err instanceof Error ? err : new Error(String(err)));
		}
	}

	async sendVisionRequest(
		textPrompt: string,
		imageBase64: string,
		mediaType: 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp',
		systemPrompt?: string
	): Promise<string> {
		const response = await requestUrl({
			url: `${ZAI_BASE_URL}/v1/messages`,
			method: 'POST',
			headers: this.makeHeaders(),
			body: JSON.stringify({
				model: 'glm-5',
				max_tokens: this.maxTokens,
				system: systemPrompt || '你是光学领域专家，分析图片中的物理内容。用中文回答。',
				messages: [{
					role: 'user',
					content: [
						{
							type: 'image',
							source: {
								type: 'base64',
								media_type: mediaType,
								data: imageBase64
							}
						},
						{
							type: 'text',
							text: textPrompt
						}
					]
				}],
				stream: false
			})
		});

		const data = response.json;
		console.log('[ZAIClient] Vision API response:', JSON.stringify(data).substring(0, 500));
		console.log('[ZAIClient] Vision response status:', response.status);

		// 兼容多种返回格式
		if (data.content?.[0]?.text) {
			return data.content[0].text;
		}
		// 有些 API 直接返回 { text: "..." } 或 { choices: [...] }
		if (data.text) return data.text;
		if (data.choices?.[0]?.message?.content) return data.choices[0].message.content;
		if (data.output) return typeof data.output === 'string' ? data.output : JSON.stringify(data.output);

		console.warn('[ZAIClient] Vision response empty or unknown format:', JSON.stringify(data));
		return '';
	}

	async testConnection(): Promise<boolean> {
		try {
			const response = await requestUrl({
				url: `${ZAI_BASE_URL}/v1/messages`,
				method: 'POST',
				headers: this.makeHeaders(),
				body: JSON.stringify({
					model: this.model,
					max_tokens: 32,
					messages: [{ role: 'user', content: 'Hi' }],
					stream: false
				})
			});
			return response.status >= 200 && response.status < 300;
		} catch {
			return false;
		}
	}
}
