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
//# sourceMappingURL=types.d.ts.map