import { readFileSync, existsSync } from 'fs';
import * as path from 'path';

/**
 * 从 .env 文件读取指定 key 的值
 * Searches: vault root, plugin dir, project root
 */
function readEnvKey(keyName: string): string | null {
	const candidates = [
		path.join(process.cwd(), '.env'),
		path.join(__dirname, '..', '.env'),
		path.join(__dirname, '..', '..', '.env'),
		path.join(__dirname, '..', '..', '..', '.env')
	];

	for (const envPath of candidates) {
		if (!existsSync(envPath)) continue;
		try {
			const content = readFileSync(envPath, 'utf-8');
			const regex = new RegExp(`^${keyName}\\s*=\\s*["']?([^\\s"']+)["']?`, 'm');
			const match = content.match(regex);
			if (match) return match[1];
		} catch {
			continue;
		}
	}
	return null;
}

/**
 * 从 .env 文件读取 ZAI_API_KEY
 */
export function readZAIKey(): string | null {
	return readEnvKey('ZAI_API_KEY');
}

/**
 * 从 .env 文件读取 MINIMAX_API_KEY
 */
export function readMiniMaxKey(): string | null {
	return readEnvKey('MINIMAX_API_KEY');
}

/**
 * 从 .env 文件读取 MINIMAX_BASE_URL，默认 https://api.minimax.chat/v1
 */
export function readMiniMaxBaseUrl(): string {
	return readEnvKey('MINIMAX_BASE_URL') || 'https://api.minimax.chat/v1';
}

/**
 * 从 .env 文件读取 DEEPSEEK_API_KEY
 */
export function readDeepSeekKey(): string | null {
	return readEnvKey('DEEPSEEK_API_KEY');
}

/**
 * 从 .env 文件读取 DEEPSEEK_BASE_URL，默认 https://api.deepseek.com
 */
export function readDeepSeekBaseUrl(): string {
	return readEnvKey('DEEPSEEK_BASE_URL') || 'https://api.deepseek.com';
}

/**
 * 读取所有可用的 fallback 凭证
 */
export interface ProviderCredentials {
	zai: { apiKey: string | null; baseUrl: string };
	minimax: { apiKey: string | null; baseUrl: string };
	deepseek: { apiKey: string | null; baseUrl: string };
}

export function readAllCredentials(): ProviderCredentials {
	return {
		zai: {
			apiKey: readZAIKey(),
			baseUrl: 'https://api.z.ai/api/anthropic'
		},
		minimax: {
			apiKey: readMiniMaxKey(),
			baseUrl: readMiniMaxBaseUrl()
		},
		deepseek: {
			apiKey: readDeepSeekKey(),
			baseUrl: readDeepSeekBaseUrl()
		}
	};
}
