import { readFileSync, existsSync } from 'fs';
import * as path from 'path';

/**
 * 从 .env 文件读取 ZAI_API_KEY
 * Searches: vault root, plugin dir, project root
 */
export function readZAIKey(): string | null {
	// Try common .env locations
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
			const match = content.match(/^ZAI_API_KEY\s*=\s*["']?([^\s"']+)["']?/m);
			if (match) return match[1];
		} catch {
			continue;
		}
	}
	return null;
}
