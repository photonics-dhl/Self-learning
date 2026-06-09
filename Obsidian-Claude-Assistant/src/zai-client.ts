import { requestUrl } from 'obsidian';
import { ClaudeRequest, ClaudeResponse, FallbackChain, FallbackEntry, RoutedResponse, ProviderType } from './types';

const ZAI_BASE_URL = 'https://api.z.ai/api/anthropic';
const DEFAULT_MODEL = 'glm-5.1';

export interface ZAIClientConfig {
	apiKey: string;
	model?: string;
	maxTokens?: number;
	minimaxApiKey?: string;
	deepseekApiKey?: string;
}

/** MiniMax base URL（官方 API） */
const MINIMAX_BASE_URL = 'https://api.minimax.chat/v1';
/** DeepSeek base URL */
const DEEPSEEK_BASE_URL = 'https://api.deepseek.com';

/**
 * 构建 fallback 链路：primary → MiniMax M2.7 → DeepSeek V4 Flash
 * 只包含有可用 API key 的 fallback 节点
 */
function buildFallbackChain(
	primaryModel: string,
	zaiApiKey: string,
	minimaxApiKey: string,
	deepseekApiKey: string
): FallbackChain {
	const primary: FallbackEntry = {
		model: primaryModel,
		provider: 'zai',
		apiFormat: 'anthropic',
		apiKey: zaiApiKey || null,
		baseUrl: ZAI_BASE_URL
	};

	const fallbacks: FallbackEntry[] = [];

	// Fallback 1: MiniMax M2.7
	if (minimaxApiKey) {
		fallbacks.push({
			model: 'MiniMax-M2.7',
			provider: 'minimax',
			apiFormat: 'openai',
			apiKey: minimaxApiKey,
			baseUrl: MINIMAX_BASE_URL
		});
	}

	// Fallback 2: DeepSeek V4 Flash（兜底）
	if (deepseekApiKey) {
		fallbacks.push({
			model: 'deepseek-v4-flash',
			provider: 'deepseek',
			apiFormat: 'openai',
			apiKey: deepseekApiKey,
			baseUrl: DEEPSEEK_BASE_URL
		});
	}

	return { primary, fallbacks };
}

/**
 * 构建 Vision 模型的 fallback 链路
 */
function buildVisionFallbackChain(
	zaiApiKey: string,
	minimaxApiKey: string,
	deepseekApiKey: string
): FallbackChain {
	const primary: FallbackEntry = {
		model: 'glm-4.5v',
		provider: 'zai',
		apiFormat: 'openai',  // z.ai vision 用 OpenAI 兼容端点
		apiKey: zaiApiKey || null,
		baseUrl: 'https://api.z.ai/api/paas/v4'
	};

	const fallbacks: FallbackEntry[] = [];

	// MiniMax 也支持 vision
	if (minimaxApiKey) {
		fallbacks.push({
			model: 'MiniMax-M2.7',
			provider: 'minimax',
			apiFormat: 'openai',
			apiKey: minimaxApiKey,
			baseUrl: MINIMAX_BASE_URL
		});
	}

	// DeepSeek 支持 vision
	if (deepseekApiKey) {
		fallbacks.push({
			model: 'deepseek-v4-flash',
			provider: 'deepseek',
			apiFormat: 'openai',
			apiKey: deepseekApiKey,
			baseUrl: DEEPSEEK_BASE_URL
		});
	}

	return { primary, fallbacks };
}

export class ZAIClient {
	private apiKey: string;
	private minimaxApiKey: string;
	private deepseekApiKey: string;
	private model: string;
	private maxTokens: number;
	private fallbackChain: FallbackChain;
	private visionFallbackChain: FallbackChain;
	/** 最后一次请求实际使用的模型 */
	private lastActualModel: string;
	private lastActualProvider: ProviderType;

	constructor(config: ZAIClientConfig) {
		this.apiKey = config.apiKey;
		this.minimaxApiKey = config.minimaxApiKey || '';
		this.deepseekApiKey = config.deepseekApiKey || '';
		this.model = config.model || DEFAULT_MODEL;
		this.maxTokens = config.maxTokens || 4096;
		this.fallbackChain = buildFallbackChain(
			this.model, this.apiKey, this.minimaxApiKey, this.deepseekApiKey
		);
		this.visionFallbackChain = buildVisionFallbackChain(
			this.apiKey, this.minimaxApiKey, this.deepseekApiKey
		);
		this.lastActualModel = this.model;
		this.lastActualProvider = 'zai';
	}

	setModel(model: string) {
		this.model = model;
		this.fallbackChain = buildFallbackChain(
			model, this.apiKey, this.minimaxApiKey, this.deepseekApiKey
		);
	}

	getModel(): string {
		return this.model;
	}

	/** 获取最后一次请求实际使用的模型 */
	getLastActualModel(): string {
		return this.lastActualModel;
	}

	/** 获取最后一次请求实际使用的 provider */
	getLastActualProvider(): ProviderType {
		return this.lastActualProvider;
	}

	/** 获取完整 fallback 链路（用于 UI 展示） */
	getFallbackChain(): FallbackChain {
		return this.fallbackChain;
	}

	// ─── Anthropic 格式请求（z.ai） ───

	private async sendAnthropicRequest(
		entry: FallbackEntry,
		systemPrompt: string,
		messages: Array<{role: string; content: string | any[]}>,
		stream: boolean
	): Promise<string> {
		const body: any = {
			model: entry.model,
			max_tokens: this.maxTokens,
			messages: messages,
			stream: false
		};

		// Anthropic 格式：system 是顶层字段
		if (systemPrompt) {
			body.system = systemPrompt;
		}

		const response = await requestUrl({
			url: `${entry.baseUrl}/v1/messages`,
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${entry.apiKey}`,
				'anthropic-version': '2023-06-01'
			},
			body: JSON.stringify(body)
		});

		const data = response.json;
		return data.content?.[0]?.text || '';
	}

	// ─── OpenAI 格式请求（MiniMax / DeepSeek） ───

	private async sendOpenAIRequest(
		entry: FallbackEntry,
		systemPrompt: string,
		messages: Array<{role: string; content: string | any[]}>,
		stream: boolean
	): Promise<string> {
		// OpenAI 格式：system prompt 作为第一条消息
		const openaiMessages: Array<{role: string; content: string | any[]}> = [];
		if (systemPrompt) {
			openaiMessages.push({ role: 'system', content: systemPrompt });
		}
		openaiMessages.push(...messages);

		const response = await requestUrl({
			url: `${entry.baseUrl}/chat/completions`,
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'Authorization': `Bearer ${entry.apiKey}`
			},
			body: JSON.stringify({
				model: entry.model,
				max_tokens: this.maxTokens,
				messages: openaiMessages,
				stream: false
			})
		});

		const data = response.json;
		return data.choices?.[0]?.message?.content || '';
	}

	// ─── 通用请求（带 fallback） ───

	private async sendWithFallback(
		chain: FallbackChain,
		systemPrompt: string,
		messages: Array<{role: string; content: string | any[]}>,
		stream: boolean
	): Promise<RoutedResponse> {
		const allEntries = [chain.primary, ...chain.fallbacks];
		const errors: string[] = [];

		for (const entry of allEntries) {
			if (!entry.apiKey) {
				errors.push(`${entry.provider}/${entry.model}: no API key — skipped`);
				continue;
			}

			try {
				console.log(`[ZAIClient] Trying ${entry.provider}/${entry.model}...`);
				let text: string;

				if (entry.apiFormat === 'anthropic') {
					text = await this.sendAnthropicRequest(entry, systemPrompt, messages, stream);
				} else {
					text = await this.sendOpenAIRequest(entry, systemPrompt, messages, stream);
				}

				console.log(`[ZAIClient] ✓ ${entry.provider}/${entry.model} succeeded`);
				this.lastActualModel = entry.model;
				this.lastActualProvider = entry.provider;
				return {
					response: text,
					actualModel: entry.model,
					actualProvider: entry.provider
				};
			} catch (err: any) {
				const status = err?.status || err?.code || 'unknown';
				const msg = `${entry.provider}/${entry.model}: ${status} — ${err?.message || err}`;
				console.warn(`[ZAIClient] ✗ ${msg}`);
				errors.push(msg);
				// 继续尝试下一个 fallback
			}
		}

		// 所有 fallback 都失败
		throw new Error(`All models failed:\n${errors.join('\n')}`);
	}

	// ─── 公共 API ───

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

	async sendRequest(request: ClaudeRequest): Promise<ClaudeResponse> {
		const systemPrompt = this.buildSystemPrompt(request);
		const messages = this.buildMessages(request);

		const routed = await this.sendWithFallback(
			this.fallbackChain,
			systemPrompt,
			messages,
			false
		);

		return {
			response: routed.response,
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
			const systemPrompt = this.buildSystemPrompt(request);
			const messages = this.buildMessages(request);

			const routed = await this.sendWithFallback(
				this.fallbackChain,
				systemPrompt,
				messages,
				false
			);

			const fullText = routed.response;

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

	// ─── Vision 请求（带 fallback） ───

	async sendVisionRequest(
		textPrompt: string,
		imageBase64: string,
		mediaType: 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp',
		systemPrompt?: string
	): Promise<string> {
		const dataUrl = `data:${mediaType};base64,${imageBase64}`;

		const messages: Array<{role: string; content: any[]}> = [
			{
				role: 'user',
				content: [
					{
						type: 'image_url',
						image_url: { url: dataUrl }
					},
					{
						type: 'text',
						text: textPrompt
					}
				]
			}
		];

		const defaultSystem = systemPrompt || '你是光学领域专家，分析图片中的物理内容。用中文回答，物理术语保留英文。' +
			'公式用 UTF-8 Unicode 符号直接输出，不要用 LaTeX。' +
			'例如：用 E=mc² 不用 $E=mc^2$；用 λ=hc/E 不用 $\\lambda=hc/E$；' +
			'用 ∫、∑、∂、∇、≈、≤、→ 等 Unicode 数学符号。' +
			'分数用 a/b 或 a÷b，不用 \\frac{a}{b}。';

		// Vision 统一用 OpenAI 格式（所有 providers 都支持）
		const routed = await this.sendWithFallback(
			this.visionFallbackChain,
			defaultSystem,
			messages as any,
			false
		);

		return routed.response;
	}

	async testConnection(): Promise<boolean> {
		try {
			// 测试主模型连接
			const entry = this.fallbackChain.primary;
			if (!entry.apiKey) return false;

			const response = await requestUrl({
				url: `${entry.baseUrl}/v1/messages`,
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${entry.apiKey}`,
					'anthropic-version': '2023-06-01'
				},
				body: JSON.stringify({
					model: entry.model,
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
