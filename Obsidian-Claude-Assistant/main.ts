import { App, Plugin, PluginSettingTab, Setting } from 'obsidian';
import { ClaudePanel } from './src/ClaudePanel';
import { ZAI_MODELS, ZAIModelId } from './src/types';

interface PluginSettings {
	apiKey: string;
	model: ZAIModelId;
	streaming: boolean;
	maxTokens: number;
}

const DEFAULT_SETTINGS: PluginSettings = {
	apiKey: '',
	model: 'glm-5.1',
	streaming: true,
	maxTokens: 4096
};

export default class ClaudeAssistantPlugin extends Plugin {
	private panel: ClaudePanel | null = null;
	public settings: PluginSettings = DEFAULT_SETTINGS;

	async onload() {
		console.log('[Claude Assistant] Plugin loading...');
		console.log('[Claude Assistant] Obsidian env — fetch available:', typeof fetch);

		try {
			this.addCommand({
				id: 'open-claude-panel',
				name: 'Open Claude Assistant Panel',
				callback: () => this.togglePanel()
			});

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

			this.addSettingTab(new ClaudeSettingsTab(this.app, this));
			await this.loadSettings();

			console.log('[Claude Assistant] Loaded — model:', this.settings.model, 'streaming:', this.settings.streaming);
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
		if (data) {
			this.settings = Object.assign({}, DEFAULT_SETTINGS, data);
		}

		// Auto-load API key from .env if not set
		if (!this.settings.apiKey) {
			try {
				const { readZAIKey } = require('./src/env-loader');
				const key = readZAIKey();
				if (key) {
					this.settings.apiKey = key;
					await this.saveSettings();
					console.log('[Claude Assistant] API key loaded from .env');
				}
			} catch {
				console.log('[Claude Assistant] No .env file found — set API key in settings');
			}
		}
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}

	togglePanel(selectedText?: string) {
		if (this.panel) {
			this.panel.close();
			this.panel = null;
		} else {
			this.panel = new ClaudePanel(this.app, this, selectedText);
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
			.setName('ZAI API Key')
			.setDesc('智谱AI Coding Plan API Key（自动从 .env 读取，也可手动设置）')
			.addText(text => text
				.setValue(this.plugin.settings.apiKey)
				.setPlaceholder('fc8af37e...')
				.onChange(async (value) => {
					this.plugin.settings.apiKey = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('模型')
			.setDesc('选择语言模型')
			.addDropdown(dropdown => {
				for (const m of ZAI_MODELS) {
					dropdown.addOption(m.id, `${m.name} — ${m.desc}`);
				}
				dropdown
					.setValue(this.plugin.settings.model)
					.onChange(async (value) => {
						this.plugin.settings.model = value as ZAIModelId;
						await this.plugin.saveSettings();
					});
			});

		new Setting(containerEl)
			.setName('流式输出')
			.setDesc('开启后实时显示生成内容（推荐）')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.streaming)
				.onChange(async (value) => {
					this.plugin.settings.streaming = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('最大输出长度')
			.setDesc('单次回复最大 token 数')
			.addText(text => text
				.setValue(String(this.plugin.settings.maxTokens))
				.onChange(async (value) => {
					const num = parseInt(value);
					if (!isNaN(num) && num > 0) {
						this.plugin.settings.maxTokens = num;
						await this.plugin.saveSettings();
					}
				}));
	}
}
