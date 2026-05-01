import { App } from 'obsidian';
export declare class ClaudePanel {
    private app;
    private plugin;
    private cliPath;
    private container;
    private historyEl;
    private inputEl;
    private sendBtn;
    private writeBtn;
    private statusEl;
    private infoEl;
    private cli;
    private conversation;
    private currentNotePath;
    private currentNoteContent;
    private selectedText;
    private lastResponse;
    private lastWriteActions;
    private isMinimized;
    private keydownHandler;
    constructor(app: App, plugin: any, cliPath?: string, selectedText?: string);
    private buildUI;
    private loadCurrentNote;
    /**
     * 刷新当前笔记信息
     */
    private refreshCurrentNote;
    private sendMessage;
    private detectAction;
    private handleResponse;
    private addMessage;
    private addVisualization;
    private showStatus;
    private showError;
    private writeToNote;
    /**
     * 根据对话内容找到最匹配的标题
     */
    private findBestMatchingHeading;
    /**
     * 生成符合项目规范的笔记内容
     */
    private generateLocalSummary;
    /**
     * 提取一句话物理图像
     */
    private extractCoreConcept;
    /**
     * 提取核心要点（bullet points）
     */
    private extractCorePoints;
    /**
     * 格式化详细解释
     */
    private formatExplanation;
    private toggleMinimize;
    close(): void;
}
//# sourceMappingURL=ClaudePanel.d.ts.map