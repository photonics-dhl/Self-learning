export interface ClaudeRequest {
    action: 'explain' | 'visualize' | 'cite' | 'tree' | 'write_summary';
    context: {
        current_note: string;
        note_content: string;
        selected_text: string;
        conversation_history: Array<{
            role: 'user' | 'assistant';
            content: string;
        }>;
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
export declare const ZAI_MODELS: readonly [{
    readonly id: "glm-5.1";
    readonly name: "GLM-5.1";
    readonly desc: "旗舰模型，最强推理";
}, {
    readonly id: "glm-5-turbo";
    readonly name: "GLM-5-Turbo";
    readonly desc: "快速推理";
}, {
    readonly id: "glm-5";
    readonly name: "GLM-5";
    readonly desc: "标准模型";
}, {
    readonly id: "glm-4.7";
    readonly name: "GLM-4.7";
    readonly desc: "高效模型";
}, {
    readonly id: "glm-4.6";
    readonly name: "GLM-4.6";
    readonly desc: "均衡模型";
}, {
    readonly id: "glm-4.5";
    readonly name: "GLM-4.5";
    readonly desc: "轻量模型";
}, {
    readonly id: "glm-4.5-air";
    readonly name: "GLM-4.5-Air";
    readonly desc: "极速模型";
}, {
    readonly id: "glm-4.6v";
    readonly name: "GLM-4.6V (Vision)";
    readonly desc: "视觉理解模型";
}, {
    readonly id: "glm-4.5v";
    readonly name: "GLM-4.5V (Vision)";
    readonly desc: "视觉理解模型";
}];
export type ZAIModelId = typeof ZAI_MODELS[number]['id'];
//# sourceMappingURL=types.d.ts.map