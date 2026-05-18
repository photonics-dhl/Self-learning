export interface ClaudeRequest {
	action: 'explain' | 'visualize' | 'cite' | 'tree' | 'write_summary';
	context: {
		current_note: string;
		note_content: string;
		selected_text: string;
		conversation_history: Array<{role: 'user' | 'assistant'; content: string}>;
	};
	options: {
		depth: 'brief' | 'detailed';
		include_formula: boolean;
		include_visualization: boolean;
	};
}

export interface ClaudeResponse {
	response: string;
	visualization?: {
		type: 'mermaid' | 'image';
		content: string;
	};
	write_actions: Array<{
		type: 'append' | 'insert_after_heading' | 'replace';
		target: string;
		content: string;
		heading?: string;
	}>;
}

export interface ConversationEntry {
	role: 'user' | 'assistant';
	content: string;
	timestamp: number;
}

export const ZAI_MODELS = [
	{ id: 'glm-5.1', name: 'GLM-5.1', desc: '旗舰模型，最强推理' },
	{ id: 'glm-5-turbo', name: 'GLM-5-Turbo', desc: '快速推理' },
	{ id: 'glm-5', name: 'GLM-5', desc: '标准模型' },
	{ id: 'glm-4.7', name: 'GLM-4.7', desc: '高效模型' },
	{ id: 'glm-4.6', name: 'GLM-4.6', desc: '均衡模型' },
	{ id: 'glm-4.5', name: 'GLM-4.5', desc: '轻量模型' },
	{ id: 'glm-4.5-air', name: 'GLM-4.5-Air', desc: '极速模型' },
	{ id: 'glm-4.6v', name: 'GLM-4.6V (Vision)', desc: '视觉理解模型' },
	{ id: 'glm-4.5v', name: 'GLM-4.5V (Vision)', desc: '视觉理解模型' }
] as const;

export type ZAIModelId = typeof ZAI_MODELS[number]['id'];
