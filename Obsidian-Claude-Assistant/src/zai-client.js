var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/zai-client.ts
var zai_client_exports = {};
__export(zai_client_exports, {
  ZAIClient: () => ZAIClient
});
module.exports = __toCommonJS(zai_client_exports);
var import_obsidian = require("obsidian");
var ZAI_BASE_URL = "https://api.z.ai/api/anthropic";
var DEFAULT_MODEL = "glm-5.1";
var MINIMAX_BASE_URL = "https://api.minimax.chat/v1";
var DEEPSEEK_BASE_URL = "https://api.deepseek.com";
function buildFallbackChain(primaryModel, zaiApiKey, minimaxApiKey, deepseekApiKey) {
  const primary = {
    model: primaryModel,
    provider: "zai",
    apiFormat: "anthropic",
    apiKey: zaiApiKey || null,
    baseUrl: ZAI_BASE_URL
  };
  const fallbacks = [];
  if (minimaxApiKey) {
    fallbacks.push({
      model: "MiniMax-M2.7",
      provider: "minimax",
      apiFormat: "openai",
      apiKey: minimaxApiKey,
      baseUrl: MINIMAX_BASE_URL
    });
  }
  if (deepseekApiKey) {
    fallbacks.push({
      model: "deepseek-v4-flash",
      provider: "deepseek",
      apiFormat: "openai",
      apiKey: deepseekApiKey,
      baseUrl: DEEPSEEK_BASE_URL
    });
  }
  return { primary, fallbacks };
}
function buildVisionFallbackChain(zaiApiKey, minimaxApiKey, deepseekApiKey) {
  const primary = {
    model: "glm-4.5v",
    provider: "zai",
    apiFormat: "openai",
    // z.ai vision 用 OpenAI 兼容端点
    apiKey: zaiApiKey || null,
    baseUrl: "https://api.z.ai/api/paas/v4"
  };
  const fallbacks = [];
  if (minimaxApiKey) {
    fallbacks.push({
      model: "MiniMax-M2.7",
      provider: "minimax",
      apiFormat: "openai",
      apiKey: minimaxApiKey,
      baseUrl: MINIMAX_BASE_URL
    });
  }
  if (deepseekApiKey) {
    fallbacks.push({
      model: "deepseek-v4-flash",
      provider: "deepseek",
      apiFormat: "openai",
      apiKey: deepseekApiKey,
      baseUrl: DEEPSEEK_BASE_URL
    });
  }
  return { primary, fallbacks };
}
var ZAIClient = class {
  constructor(config) {
    this.apiKey = config.apiKey;
    this.minimaxApiKey = config.minimaxApiKey || "";
    this.deepseekApiKey = config.deepseekApiKey || "";
    this.model = config.model || DEFAULT_MODEL;
    this.maxTokens = config.maxTokens || 4096;
    this.fallbackChain = buildFallbackChain(
      this.model,
      this.apiKey,
      this.minimaxApiKey,
      this.deepseekApiKey
    );
    this.visionFallbackChain = buildVisionFallbackChain(
      this.apiKey,
      this.minimaxApiKey,
      this.deepseekApiKey
    );
    this.lastActualModel = this.model;
    this.lastActualProvider = "zai";
  }
  setModel(model) {
    this.model = model;
    this.fallbackChain = buildFallbackChain(
      model,
      this.apiKey,
      this.minimaxApiKey,
      this.deepseekApiKey
    );
  }
  getModel() {
    return this.model;
  }
  /** 获取最后一次请求实际使用的模型 */
  getLastActualModel() {
    return this.lastActualModel;
  }
  /** 获取最后一次请求实际使用的 provider */
  getLastActualProvider() {
    return this.lastActualProvider;
  }
  /** 获取完整 fallback 链路（用于 UI 展示） */
  getFallbackChain() {
    return this.fallbackChain;
  }
  // ─── Anthropic 格式请求（z.ai） ───
  async sendAnthropicRequest(entry, systemPrompt, messages, stream) {
    var _a, _b;
    const body = {
      model: entry.model,
      max_tokens: this.maxTokens,
      messages,
      stream: false
    };
    if (systemPrompt) {
      body.system = systemPrompt;
    }
    const response = await (0, import_obsidian.requestUrl)({
      url: `${entry.baseUrl}/v1/messages`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${entry.apiKey}`,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify(body)
    });
    const data = response.json;
    return ((_b = (_a = data.content) == null ? void 0 : _a[0]) == null ? void 0 : _b.text) || "";
  }
  // ─── OpenAI 格式请求（MiniMax / DeepSeek） ───
  async sendOpenAIRequest(entry, systemPrompt, messages, stream) {
    var _a, _b, _c;
    const openaiMessages = [];
    if (systemPrompt) {
      openaiMessages.push({ role: "system", content: systemPrompt });
    }
    openaiMessages.push(...messages);
    const response = await (0, import_obsidian.requestUrl)({
      url: `${entry.baseUrl}/chat/completions`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${entry.apiKey}`
      },
      body: JSON.stringify({
        model: entry.model,
        max_tokens: this.maxTokens,
        messages: openaiMessages,
        stream: false
      })
    });
    const data = response.json;
    return ((_c = (_b = (_a = data.choices) == null ? void 0 : _a[0]) == null ? void 0 : _b.message) == null ? void 0 : _c.content) || "";
  }
  // ─── 通用请求（带 fallback） ───
  async sendWithFallback(chain, systemPrompt, messages, stream) {
    const allEntries = [chain.primary, ...chain.fallbacks];
    const errors = [];
    for (const entry of allEntries) {
      if (!entry.apiKey) {
        errors.push(`${entry.provider}/${entry.model}: no API key \u2014 skipped`);
        continue;
      }
      try {
        console.log(`[ZAIClient] Trying ${entry.provider}/${entry.model}...`);
        let text;
        if (entry.apiFormat === "anthropic") {
          text = await this.sendAnthropicRequest(entry, systemPrompt, messages, stream);
        } else {
          text = await this.sendOpenAIRequest(entry, systemPrompt, messages, stream);
        }
        console.log(`[ZAIClient] \u2713 ${entry.provider}/${entry.model} succeeded`);
        this.lastActualModel = entry.model;
        this.lastActualProvider = entry.provider;
        return {
          response: text,
          actualModel: entry.model,
          actualProvider: entry.provider
        };
      } catch (err) {
        const status = (err == null ? void 0 : err.status) || (err == null ? void 0 : err.code) || "unknown";
        const msg = `${entry.provider}/${entry.model}: ${status} \u2014 ${(err == null ? void 0 : err.message) || err}`;
        console.warn(`[ZAIClient] \u2717 ${msg}`);
        errors.push(msg);
      }
    }
    throw new Error(`All models failed:
${errors.join("\n")}`);
  }
  // ─── 公共 API ───
  buildSystemPrompt(request) {
    const parts = [];
    parts.push("\u4F60\u662F\u5149\u5B66\u7814\u7A76\u8005\u7684\u5B66\u672F\u52A9\u624B\uFF0C\u8FD0\u884C\u5728 Obsidian \u77E5\u8BC6\u7BA1\u7406\u73AF\u5883\u4E2D\u3002");
    parts.push("\u7528\u4E2D\u6587\u56DE\u7B54\uFF0C\u7269\u7406\u672F\u8BED\u4FDD\u7559\u82F1\u6587\u3002\u8F93\u51FA Markdown \u683C\u5F0F\u3002");
    if (request.context.note_content) {
      parts.push(`
\u5F53\u524D\u7B14\u8BB0\u5185\u5BB9\uFF08\u538B\u7F29\uFF09:
${request.context.note_content}`);
    }
    if (request.options.include_formula) {
      parts.push("\u5305\u542B LaTeX \u516C\u5F0F\uFF08\u884C\u5185 $...$\uFF0C\u884C\u95F4 $$...$$\uFF09\u3002");
    }
    return parts.join("\n");
  }
  buildMessages(request) {
    const messages = [];
    const history = request.context.conversation_history || [];
    for (const entry of history) {
      messages.push({ role: entry.role, content: entry.content });
    }
    return messages;
  }
  async sendRequest(request) {
    const systemPrompt = this.buildSystemPrompt(request);
    const messages = this.buildMessages(request);
    const routed = await this.sendWithFallback(
      this.fallbackChain,
      systemPrompt,
      messages,
      false
    );
    return {
      response: routed.response,
      write_actions: []
    };
  }
  async sendRequestStream(request, onToken, onDone, onError) {
    try {
      const systemPrompt = this.buildSystemPrompt(request);
      const messages = this.buildMessages(request);
      const routed = await this.sendWithFallback(
        this.fallbackChain,
        systemPrompt,
        messages,
        false
      );
      const fullText = routed.response;
      const chunkSize = 8;
      for (let i = 0; i < fullText.length; i += chunkSize) {
        onToken(fullText.slice(i, i + chunkSize));
      }
      onDone(fullText);
    } catch (err) {
      onError(err instanceof Error ? err : new Error(String(err)));
    }
  }
  // ─── Vision 请求（带 fallback） ───
  async sendVisionRequest(textPrompt, imageBase64, mediaType, systemPrompt) {
    const dataUrl = `data:${mediaType};base64,${imageBase64}`;
    const messages = [
      {
        role: "user",
        content: [
          {
            type: "image_url",
            image_url: { url: dataUrl }
          },
          {
            type: "text",
            text: textPrompt
          }
        ]
      }
    ];
    const defaultSystem = systemPrompt || "\u4F60\u662F\u5149\u5B66\u9886\u57DF\u4E13\u5BB6\uFF0C\u5206\u6790\u56FE\u7247\u4E2D\u7684\u7269\u7406\u5185\u5BB9\u3002\u7528\u4E2D\u6587\u56DE\u7B54\uFF0C\u7269\u7406\u672F\u8BED\u4FDD\u7559\u82F1\u6587\u3002\u516C\u5F0F\u7528 UTF-8 Unicode \u7B26\u53F7\u76F4\u63A5\u8F93\u51FA\uFF0C\u4E0D\u8981\u7528 LaTeX\u3002\u4F8B\u5982\uFF1A\u7528 E=mc\xB2 \u4E0D\u7528 $E=mc^2$\uFF1B\u7528 \u03BB=hc/E \u4E0D\u7528 $\\lambda=hc/E$\uFF1B\u7528 \u222B\u3001\u2211\u3001\u2202\u3001\u2207\u3001\u2248\u3001\u2264\u3001\u2192 \u7B49 Unicode \u6570\u5B66\u7B26\u53F7\u3002\u5206\u6570\u7528 a/b \u6216 a\xF7b\uFF0C\u4E0D\u7528 \\frac{a}{b}\u3002";
    const routed = await this.sendWithFallback(
      this.visionFallbackChain,
      defaultSystem,
      messages,
      false
    );
    return routed.response;
  }
  async testConnection() {
    try {
      const entry = this.fallbackChain.primary;
      if (!entry.apiKey) return false;
      const response = await (0, import_obsidian.requestUrl)({
        url: `${entry.baseUrl}/v1/messages`,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${entry.apiKey}`,
          "anthropic-version": "2023-06-01"
        },
        body: JSON.stringify({
          model: entry.model,
          max_tokens: 32,
          messages: [{ role: "user", content: "Hi" }],
          stream: false
        })
      });
      return response.status >= 200 && response.status < 300;
    } catch {
      return false;
    }
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ZAIClient
});
//# sourceMappingURL=zai-client.js.map
