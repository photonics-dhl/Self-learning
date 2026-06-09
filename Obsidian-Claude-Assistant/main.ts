import { App, Plugin, PluginSettingTab, Setting } from 'obsidian';
import { ClaudePanel } from './src/ClaudePanel';
import { ZAI_MODELS, ZAIModelId } from './src/types';

interface PluginSettings {
	apiKey: string;
	minimaxApiKey: string;
	deepseekApiKey: string;
	model: ZAIModelId;
	streaming: boolean;
	maxTokens: number;
}

const DEFAULT_SETTINGS: PluginSettings = {
	apiKey: '',
	minimaxApiKey: '',
	deepseekApiKey: '',
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
			console.log('[Claude Assistant] Keys — ZAI:', !!this.settings.apiKey, 'MiniMax:', !!this.settings.minimaxApiKey, 'DeepSeek:', !!this.settings.deepseekApiKey);
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

		// Auto-load API keys from .env if not set
		let needsSave = false;
		try {
			const { readZAIKey, readMiniMaxKey, readDeepSeekKey } = require('./src/env-loader');

			if (!this.settings.apiKey) {
				const key = readZAIKey();
				if (key) {
					this.settings.apiKey = key;
					needsSave = true;
					console.log('[Claude Assistant] ZAI API key loaded from .env');
				}
			}
			if (!this.settings.minimaxApiKey) {
				const key = readMiniMaxKey();
				if (key) {
					this.settings.minimaxApiKey = key;
					needsSave = true;
					console.log('[Claude Assistant] MiniMax API key loaded from .env');
				}
			}
			if (!this.settings.deepseekApiKey) {
				const key = readDeepSeekKey();
				if (key) {
					this.settings.deepseekApiKey = key;
					needsSave = true;
					console.log('[Claude Assistant] DeepSeek API key loaded from .env');
				}
			}

			if (needsSave) {
				await this.saveSettings();
			}
		} catch {
			console.log('[Claude Assistant] No .env file found — set API keys in settings');
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
			.setName('MiniMax API Key')
			.setDesc('MiniMax API Key — Fallback 1，主模型不可用时自动切换（自动从 .env 读取）')
			.addText(text => text
				.setValue(this.plugin.settings.minimaxApiKey)
				.setPlaceholder('sk-cp-...')
				.onChange(async (value) => {
					this.plugin.settings.minimaxApiKey = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('DeepSeek API Key')
			.setDesc('DeepSeek API Key — Fallback 2（兜底），自动从 .env 读取')
			.addText(text => text
				.setValue(this.plugin.settings.deepseekApiKey)
				.setPlaceholder('sk-...')
				.onChange(async (value) => {
					this.plugin.settings.deepseekApiKey = value;
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
