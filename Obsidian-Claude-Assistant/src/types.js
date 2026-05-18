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

// src/types.ts
var types_exports = {};
__export(types_exports, {
  ZAI_MODELS: () => ZAI_MODELS
});
module.exports = __toCommonJS(types_exports);
var ZAI_MODELS = [
  { id: "glm-5.1", name: "GLM-5.1", desc: "\u65D7\u8230\u6A21\u578B\uFF0C\u6700\u5F3A\u63A8\u7406" },
  { id: "glm-5-turbo", name: "GLM-5-Turbo", desc: "\u5FEB\u901F\u63A8\u7406" },
  { id: "glm-5", name: "GLM-5", desc: "\u6807\u51C6\u6A21\u578B\uFF08\u652F\u6301\u56FE\u7247\uFF09" },
  { id: "glm-4.7", name: "GLM-4.7", desc: "\u9AD8\u6548\u6A21\u578B\uFF08\u652F\u6301\u56FE\u7247\uFF09" },
  { id: "glm-4.6", name: "GLM-4.6", desc: "\u5747\u8861\u6A21\u578B" },
  { id: "glm-4.5", name: "GLM-4.5", desc: "\u8F7B\u91CF\u6A21\u578B" },
  { id: "glm-4.5-air", name: "GLM-4.5-Air", desc: "\u6781\u901F\u6A21\u578B" },
  { id: "glm-4.6v", name: "GLM-4.6V (Vision)", desc: "\u89C6\u89C9\u7406\u89E3\u6A21\u578B" },
  { id: "glm-4.5v", name: "GLM-4.5V (Vision)", desc: "\u89C6\u89C9\u7406\u89E3\u6A21\u578B" }
];
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ZAI_MODELS
});
//# sourceMappingURL=types.js.map
