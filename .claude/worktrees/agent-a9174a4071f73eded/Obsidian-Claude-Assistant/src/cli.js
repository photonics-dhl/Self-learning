"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ClaudeCLI = void 0;
const child_process_1 = require("child_process");
class ClaudeCLI {
    constructor(cliPath = 'node claude-wrapper.js') {
        this.cliPath = cliPath;
    }
    async sendRequest(request) {
        return new Promise((resolve, reject) => {
            const requestStr = JSON.stringify(request);
            const isWindows = process.platform === 'win32';
            const child = (0, child_process_1.spawn)(isWindows ? 'cmd' : 'bash', isWindows ? ['/c', this.cliPath] : ['-c', this.cliPath], {
                stdio: ['pipe', 'pipe', 'pipe'],
                env: { ...process.env },
                cwd: isWindows ? undefined : __dirname
            });
            let stdout = '';
            let stderr = '';
            child.stdout.on('data', (data) => { stdout += data.toString(); });
            child.stderr.on('data', (data) => { stderr += data.toString(); });
            child.on('error', reject);
            child.on('close', (code) => {
                if (code !== 0 && !stdout) {
                    reject(new Error(`CLI exited with code ${code}: ${stderr}`));
                    return;
                }
                try {
                    // 尝试解析 JSON 响应
                    const lines = stdout.trim().split('\n');
                    const jsonLine = lines.find(l => l.trim().startsWith('{'));
                    if (jsonLine) {
                        resolve(JSON.parse(jsonLine));
                    }
                    else {
                        resolve({
                            response: stdout,
                            write_actions: []
                        });
                    }
                }
                catch (e) {
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
                action: 'explain',
                context: {
                    current_note: 'test.md',
                    note_content: 'test',
                    selected_text: 'test',
                    conversation_history: []
                },
                options: {
                    depth: 'brief',
                    include_formula: false,
                    include_visualization: false
                }
            });
            return !!result.response;
        }
        catch {
            return false;
        }
    }
}
exports.ClaudeCLI = ClaudeCLI;
//# sourceMappingURL=cli.js.map