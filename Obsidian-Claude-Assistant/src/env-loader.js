var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
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
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/env-loader.ts
var env_loader_exports = {};
__export(env_loader_exports, {
  readAllCredentials: () => readAllCredentials,
  readDeepSeekBaseUrl: () => readDeepSeekBaseUrl,
  readDeepSeekKey: () => readDeepSeekKey,
  readMiniMaxBaseUrl: () => readMiniMaxBaseUrl,
  readMiniMaxKey: () => readMiniMaxKey,
  readZAIKey: () => readZAIKey
});
module.exports = __toCommonJS(env_loader_exports);
var import_fs = require("fs");
var path = __toESM(require("path"));
function readEnvKey(keyName) {
  const candidates = [
    path.join(process.cwd(), ".env"),
    path.join(__dirname, "..", ".env"),
    path.join(__dirname, "..", "..", ".env"),
    path.join(__dirname, "..", "..", "..", ".env")
  ];
  for (const envPath of candidates) {
    if (!(0, import_fs.existsSync)(envPath)) continue;
    try {
      const content = (0, import_fs.readFileSync)(envPath, "utf-8");
      const regex = new RegExp(`^${keyName}\\s*=\\s*["']?([^\\s"']+)["']?`, "m");
      const match = content.match(regex);
      if (match) return match[1];
    } catch {
      continue;
    }
  }
  return null;
}
function readZAIKey() {
  return readEnvKey("ZAI_API_KEY");
}
function readMiniMaxKey() {
  return readEnvKey("MINIMAX_API_KEY");
}
function readMiniMaxBaseUrl() {
  return readEnvKey("MINIMAX_BASE_URL") || "https://api.minimax.chat/v1";
}
function readDeepSeekKey() {
  return readEnvKey("DEEPSEEK_API_KEY");
}
function readDeepSeekBaseUrl() {
  return readEnvKey("DEEPSEEK_BASE_URL") || "https://api.deepseek.com";
}
function readAllCredentials() {
  return {
    zai: {
      apiKey: readZAIKey(),
      baseUrl: "https://api.z.ai/api/anthropic"
    },
    minimax: {
      apiKey: readMiniMaxKey(),
      baseUrl: readMiniMaxBaseUrl()
    },
    deepseek: {
      apiKey: readDeepSeekKey(),
      baseUrl: readDeepSeekBaseUrl()
    }
  };
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  readAllCredentials,
  readDeepSeekBaseUrl,
  readDeepSeekKey,
  readMiniMaxBaseUrl,
  readMiniMaxKey,
  readZAIKey
});
//# sourceMappingURL=env-loader.js.map
