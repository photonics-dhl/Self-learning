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
    private buildSystemPrompt;
    private buildMessages;
    private makeHeaders;
    sendRequest(request: ClaudeRequest): Promise<ClaudeResponse>;
    sendRequestStream(request: ClaudeRequest, onToken: (text: string) => void, onDone: (fullText: string) => void, onError: (error: Error) => void): Promise<void>;
    sendVisionRequest(textPrompt: string, imageBase64: string, mediaType: 'image/jpeg' | 'image/png' | 'image/gif' | 'image/webp', systemPrompt?: string): Promise<string>;
    testConnection(): Promise<boolean>;
}
//# sourceMappingURL=zai-client.d.ts.map