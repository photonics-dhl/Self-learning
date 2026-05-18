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
var ZAIClient = class {
  constructor(config) {
    this.apiKey = config.apiKey;
    this.model = config.model || DEFAULT_MODEL;
    this.maxTokens = config.maxTokens || 4096;
  }
  setModel(model) {
    this.model = model;
  }
  getModel() {
    return this.model;
  }
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
  makeHeaders() {
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${this.apiKey}`,
      "anthropic-version": "2023-06-01"
    };
  }
  async sendRequest(request) {
    var _a, _b;
    const response = await (0, import_obsidian.requestUrl)({
      url: `${ZAI_BASE_URL}/v1/messages`,
      method: "POST",
      headers: this.makeHeaders(),
      body: JSON.stringify({
        model: this.model,
        max_tokens: this.maxTokens,
        system: this.buildSystemPrompt(request),
        messages: this.buildMessages(request),
        stream: false
      })
    });
    const data = response.json;
    const text = ((_b = (_a = data.content) == null ? void 0 : _a[0]) == null ? void 0 : _b.text) || "";
    return {
      response: text,
      write_actions: []
    };
  }
  async sendRequestStream(request, onToken, onDone, onError) {
    var _a, _b;
    try {
      const response = await (0, import_obsidian.requestUrl)({
        url: `${ZAI_BASE_URL}/v1/messages`,
        method: "POST",
        headers: this.makeHeaders(),
        body: JSON.stringify({
          model: this.model,
          max_tokens: this.maxTokens,
          system: this.buildSystemPrompt(request),
          messages: this.buildMessages(request),
          stream: false
        })
      });
      const data = response.json;
      const fullText = ((_b = (_a = data.content) == null ? void 0 : _a[0]) == null ? void 0 : _b.text) || "";
      const chunkSize = 8;
      for (let i = 0; i < fullText.length; i += chunkSize) {
        onToken(fullText.slice(i, i + chunkSize));
      }
      onDone(fullText);
    } catch (err) {
      onError(err instanceof Error ? err : new Error(String(err)));
    }
  }
  async sendVisionRequest(textPrompt, imageBase64, mediaType, systemPrompt) {
    var _a, _b, _c;
    const VISION_BASE_URL = "https://api.z.ai/api/paas/v4";
    const dataUrl = `data:${mediaType};base64,${imageBase64}`;
    const response = await (0, import_obsidian.requestUrl)({
      url: `${VISION_BASE_URL}/chat/completions`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        model: "glm-4.6v-flash",
        max_tokens: this.maxTokens,
        messages: [
          {
            role: "system",
            content: systemPrompt || "\u4F60\u662F\u5149\u5B66\u9886\u57DF\u4E13\u5BB6\uFF0C\u5206\u6790\u56FE\u7247\u4E2D\u7684\u7269\u7406\u5185\u5BB9\u3002\u7528\u4E2D\u6587\u56DE\u7B54\uFF0C\u7269\u7406\u672F\u8BED\u4FDD\u7559\u82F1\u6587\u3002"
          },
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
        ],
        stream: false
      })
    });
    const data = response.json;
    console.log("[ZAIClient] Vision response:", JSON.stringify(data).substring(0, 500));
    return ((_c = (_b = (_a = data.choices) == null ? void 0 : _a[0]) == null ? void 0 : _b.message) == null ? void 0 : _c.content) || "";
  }
  async testConnection() {
    try {
      const response = await (0, import_obsidian.requestUrl)({
        url: `${ZAI_BASE_URL}/v1/messages`,
        method: "POST",
        headers: this.makeHeaders(),
        body: JSON.stringify({
          model: this.model,
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
