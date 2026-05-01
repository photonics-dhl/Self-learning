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

// src/cli.ts
var cli_exports = {};
__export(cli_exports, {
  ClaudeCLI: () => ClaudeCLI
});
module.exports = __toCommonJS(cli_exports);
var import_child_process = require("child_process");
var ClaudeCLI = class {
  constructor(cliPath = "node claude-wrapper.js") {
    this.cliPath = cliPath;
  }
  async sendRequest(request) {
    return new Promise((resolve, reject) => {
      const requestStr = JSON.stringify(request);
      const isWindows = process.platform === "win32";
      const child = (0, import_child_process.spawn)(
        isWindows ? "cmd" : "bash",
        isWindows ? ["/c", this.cliPath] : ["-c", this.cliPath],
        {
          stdio: ["pipe", "pipe", "pipe"],
          env: { ...process.env },
          cwd: isWindows ? void 0 : __dirname
        }
      );
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (data) => {
        stdout += data.toString();
      });
      child.stderr.on("data", (data) => {
        stderr += data.toString();
      });
      child.on("error", reject);
      child.on("close", (code) => {
        if (code !== 0 && !stdout) {
          reject(new Error(`CLI exited with code ${code}: ${stderr}`));
          return;
        }
        try {
          const lines = stdout.trim().split("\n");
          const jsonLine = lines.find((l) => l.trim().startsWith("{"));
          if (jsonLine) {
            resolve(JSON.parse(jsonLine));
          } else {
            resolve({
              response: stdout,
              write_actions: []
            });
          }
        } catch (e) {
          resolve({
            response: stdout || stderr,
            write_actions: []
          });
        }
      });
      child.stdin.write(requestStr);
      child.stdin.end();
    });
  }
  async testConnection() {
    try {
      const result = await this.sendRequest({
        action: "explain",
        context: {
          current_note: "test.md",
          note_content: "test",
          selected_text: "test",
          conversation_history: []
        },
        options: {
          depth: "brief",
          include_formula: false,
          include_visualization: false
        }
      });
      return !!result.response;
    } catch {
      return false;
    }
  }
};
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  ClaudeCLI
});
//# sourceMappingURL=cli.js.map
