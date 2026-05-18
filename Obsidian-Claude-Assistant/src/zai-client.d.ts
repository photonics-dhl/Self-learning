import { ClaudeRequest, ClaudeResponse } from './types';
export interface ZAIClientConfig {
    apiKey: string;
    model?: string;
    maxTokens?: number;
}
export declare class ZAIClient {
    private apiKey;
    private model;
    private maxTokens;
    constructor(config: ZAIClientConfig);
    setModel(model: string): void;
    getModel(): string;
    /**
     * Build system prompt from request context
     */
    private buildSystemPrompt;
    /**
     * Build Anthropic Messages API messages array from conversation
     */
    private buildMessages;
    /**
     * Non-streaming request — returns full response
     */
    sendRequest(request: ClaudeRequest): Promise<ClaudeResponse>;
    /**
     * Streaming request — calls onToken for each text delta, onDone when complete
     */
    sendRequestStream(request: ClaudeRequest, onToken: (text: string) => void, onDone: (fullText: string) => void, onError: (error: Error) => void): Promise<void>;
    /**
     * Vision request — send image + text to vision model
     */
    sendVisionRequest(textPrompt: string, imageBase64: string, mediaType: 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp', systemPrompt?: string): Promise<string>;
    /**
     * Test API connectivity
     */
    testConnection(): Promise<boolean>;
}
//# sourceMappingURL=zai-client.d.ts.map