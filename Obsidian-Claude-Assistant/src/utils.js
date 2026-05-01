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

// src/utils.ts
var utils_exports = {};
__export(utils_exports, {
  appendToNote: () => appendToNote,
  compressNoteContent: () => compressNoteContent,
  extractHeadings: () => extractHeadings,
  getActiveFileContent: () => getActiveFileContent,
  getActiveFilePath: () => getActiveFilePath,
  getFileName: () => getFileName,
  insertAfterHeading: () => insertAfterHeading,
  writeNoteContent: () => writeNoteContent
});
module.exports = __toCommonJS(utils_exports);
function getActiveFilePath(app) {
  var _a, _b, _c, _d, _e, _f, _g, _h;
  const leaves = app.workspace.getLeaves();
  for (const leaf of leaves) {
    if ((_b = (_a = leaf.view) == null ? void 0 : _a.file) == null ? void 0 : _b.path) {
      return leaf.view.file.path;
    }
  }
  const activeLeaf = app.workspace.activeLeaf;
  if ((_d = (_c = activeLeaf == null ? void 0 : activeLeaf.view) == null ? void 0 : _c.file) == null ? void 0 : _d.path) {
    return activeLeaf.view.file.path;
  }
  if ((_e = app.workspace.lastActiveFile) == null ? void 0 : _e.path) {
    return app.workspace.lastActiveFile.path;
  }
  if (typeof app.workspace.getActiveFile === "function") {
    const activeFile = app.workspace.getActiveFile();
    if (activeFile == null ? void 0 : activeFile.path) {
      return activeFile.path;
    }
  }
  console.log("[ClaudePanel] getActiveFilePath: No active file found");
  console.log("[ClaudePanel] workspace leaves:", app.workspace.getLeaves().map((l) => {
    var _a2;
    return { type: l.type, hasFile: !!((_a2 = l.view) == null ? void 0 : _a2.file) };
  }));
  console.log("[ClaudePanel] activeLeaf:", (_g = (_f = activeLeaf == null ? void 0 : activeLeaf.view) == null ? void 0 : _f.file) == null ? void 0 : _g.path);
  console.log("[ClaudePanel] lastActiveFile:", (_h = app.workspace.lastActiveFile) == null ? void 0 : _h.path);
  return null;
}
async function getActiveFileContent(app) {
  var _a;
  const activeFile = app.workspace.getActiveFile();
  if (!activeFile) {
    const leaves = app.workspace.getLeaves();
    for (const leaf of leaves) {
      if ((_a = leaf.view) == null ? void 0 : _a.file) {
        try {
          const content = await app.vault.read(leaf.view.file);
          return { path: leaf.view.file.path, content };
        } catch (e) {
          continue;
        }
      }
    }
    console.log("[ClaudePanel] getActiveFileContent: No active file found");
    return null;
  }
  try {
    const content = await app.vault.read(activeFile);
    return { path: activeFile.path, content };
  } catch (error) {
    console.error("[ClaudePanel] Error reading file:", error);
    return null;
  }
}
function compressNoteContent(content, maxLength = 4e3) {
  let compressed = content.replace(/\s+/g, " ").trim();
  if (compressed.length <= maxLength) {
    return compressed;
  }
  const headLength = Math.floor(maxLength * 0.7);
  const tailLength = maxLength - headLength;
  return compressed.substring(0, headLength) + "\n...[\u5185\u5BB9\u5DF2\u622A\u65AD]...\n" + compressed.slice(-tailLength);
}
function getFileName(path) {
  var _a;
  return ((_a = path.split("/").pop()) == null ? void 0 : _a.split("\\").pop()) || path;
}
function extractHeadings(content) {
  const headings = [];
  const regex = /^#{1,3}\s+(.+)$/gm;
  let match;
  while ((match = regex.exec(content)) !== null) {
    headings.push(match[1]);
  }
  return headings;
}
function insertAfterHeading(content, heading, insertContent) {
  const lines = content.split("\n");
  let insertIndex = lines.length;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === heading || lines[i].trim().startsWith(heading)) {
      insertIndex = i + 1;
      break;
    }
  }
  lines.splice(insertIndex, 0, "", insertContent);
  return lines.join("\n");
}
async function writeNoteContent(app, path, content) {
  const file = app.vault.getAbstractFileByPath(path);
  if (!file) {
    throw new Error(`File not found: ${path}`);
  }
  await app.vault.modify(file, content);
}
async function appendToNote(app, path, content) {
  const file = app.vault.getAbstractFileByPath(path);
  if (!file) {
    throw new Error(`File not found: ${path}`);
  }
  const existing = await app.vault.read(file);
  const newContent = existing + "\n" + content;
  await app.vault.modify(file, newContent);
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  appendToNote,
  compressNoteContent,
  extractHeadings,
  getActiveFileContent,
  getActiveFilePath,
  getFileName,
  insertAfterHeading,
  writeNoteContent
});
//# sourceMappingURL=utils.js.map
