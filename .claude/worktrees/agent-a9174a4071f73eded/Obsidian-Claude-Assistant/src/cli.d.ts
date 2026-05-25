import { ClaudeRequest, ClaudeResponse } from './types';
export declare class ClaudeCLI {
    private cliPath;
    constructor(cliPath?: string);
    sendRequest(request: ClaudeRequest): Promise<ClaudeResponse>;
    testConnection(): Promise<boolean>;
}
//# sourceMappingURL=cli.d.ts.map