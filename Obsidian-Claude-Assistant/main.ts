import { App, Plugin, PluginSettingTab, Setting } from 'obsidian';
import { ClaudePanel } from './src/ClaudePanel';

export default class ClaudeAssistantPlugin extends Plugin {
  private panel: ClaudePanel | null = null;
  public claudePath: string = 'claude';

  async onload() {
    console.log('[Claude Assistant] Plugin loading...');

    try {
      // 添加命令：打开悬浮面板
      this.addCommand({
        id: 'open-claude-panel',
        name: 'Open Claude Assistant Panel',
        callback: () => this.togglePanel()
      });

      // 添加命令：快速问答（使用选中文本）
      this.addCommand({
        id: 'quick-ask-claude',
        name: 'Ask Claude (selected text)',
        editorCallback: (editor) => {
          const selected = editor.getSelection();
          if (selected) {
            this.togglePanel(selected);
          }
        }
      });

      // 添加设置标签页
      this.addSettingTab(new ClaudeSettingsTab(this.app, this));

      // 加载设置
      await this.loadSettings();

      console.log('[Claude Assistant] Plugin loaded successfully');
    } catch (error) {
      console.error('[Claude Assistant] Plugin load error:', error);
    }
  }

  onunload() {
    console.log('[Claude Assistant] Plugin unloading...');
    if (this.panel) {
      this.panel.close();
    }
  }

  async loadSettings() {
    const data = await this.loadData();
    if (data?.claudePath) {
      this.claudePath = data.claudePath;
    }
  }

  async saveSettings() {
    await this.saveData({ claudePath: this.claudePath });
  }

  togglePanel(selectedText?: string) {
    if (this.panel) {
      this.panel.close();
      this.panel = null;
    } else {
      this.panel = new ClaudePanel(this.app, this, this.claudePath, selectedText);
    }
  }
}

class ClaudeSettingsTab extends PluginSettingTab {
  constructor(app: App, private plugin: ClaudeAssistantPlugin) {
    super(app, plugin);
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();

    new Setting(containerEl)
      .setName('Claude CLI Path')
      .setDesc('Claude CLI 的路径（默认: claude）')
      .addText(text => text
        .setValue(this.plugin.claudePath)
        .onChange(async (value) => {
          this.plugin.claudePath = value;
          await this.plugin.saveSettings();
        }));
  }
}