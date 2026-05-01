/**
 * 获取当前打开的笔记路径
 */
export declare function getActiveFilePath(app: any): string | null;
/**
 * 获取当前笔记内容
 */
export declare function getActiveFileContent(app: any): Promise<{
    path: string;
    content: string;
} | null>;
/**
 * 压缩笔记内容以传递给 CLI
 */
export declare function compressNoteContent(content: string, maxLength?: number): string;
export declare function getFileName(path: string): string;
export declare function extractHeadings(content: string): string[];
export declare function insertAfterHeading(content: string, heading: string, insertContent: string): string;
export declare function writeNoteContent(app: any, path: string, content: string): Promise<void>;
export declare function appendToNote(app: any, path: string, content: string): Promise<void>;
//# sourceMappingURL=utils.d.ts.map