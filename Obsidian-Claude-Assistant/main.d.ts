import { Plugin } from 'obsidian';
export default class ClaudeAssistantPlugin extends Plugin {
    private panel;
    claudePath: string;
    onload(): Promise<void>;
    onunload(): void;
    loadSettings(): Promise<void>;
    saveSettings(): Promise<void>;
    togglePanel(selectedText?: string): void;
}
//# sourceMappingURL=main.d.ts.map