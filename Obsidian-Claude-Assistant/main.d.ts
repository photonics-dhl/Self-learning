import { Plugin } from 'obsidian';
import { ZAIModelId } from './src/types';
interface PluginSettings {
    apiKey: string;
    model: ZAIModelId;
    streaming: boolean;
    maxTokens: number;
}
export default class ClaudeAssistantPlugin extends Plugin {
    private panel;
    settings: PluginSettings;
    onload(): Promise<void>;
    onunload(): void;
    loadSettings(): Promise<void>;
    saveSettings(): Promise<void>;
    togglePanel(selectedText?: string): void;
}
export {};
//# sourceMappingURL=main.d.ts.map