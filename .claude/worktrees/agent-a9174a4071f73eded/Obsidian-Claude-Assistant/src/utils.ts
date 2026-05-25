/**
 * 获取当前打开的笔记路径
 */
export function getActiveFilePath(app: any): string | null {
  // 获取所有 leaf
  const leaves = app.workspace.getLeaves();

  // 遍历所有 leaf 查找 markdown 视图
  for (const leaf of leaves) {
    if (leaf.view?.file?.path) {
      return leaf.view.file.path;
    }
  }

  // 尝试 activeLeaf
  const activeLeaf = app.workspace.activeLeaf;
  if (activeLeaf?.view?.file?.path) {
    return activeLeaf.view.file.path;
  }

  // 尝试 lastActiveFile
  if (app.workspace.lastActiveFile?.path) {
    return app.workspace.lastActiveFile.path;
  }

  // 尝试 getActiveFile()
  if (typeof app.workspace.getActiveFile === 'function') {
    const activeFile = app.workspace.getActiveFile();
    if (activeFile?.path) {
      return activeFile.path;
    }
  }

  console.log('[ClaudePanel] getActiveFilePath: No active file found');
  console.log('[ClaudePanel] workspace leaves:', app.workspace.getLeaves().map(l => ({ type: l.type, hasFile: !!l.view?.file })));
  console.log('[ClaudePanel] activeLeaf:', activeLeaf?.view?.file?.path);
  console.log('[ClaudePanel] lastActiveFile:', app.workspace.lastActiveFile?.path);

  return null;
}

/**
 * 获取当前笔记内容
 */
export async function getActiveFileContent(app: any): Promise<{path: string; content: string} | null> {
  // 获取活动文件（TFile对象）
  const activeFile = app.workspace.getActiveFile();
  if (!activeFile) {
    // 尝试从 leaves 中获取
    const leaves = app.workspace.getLeaves();
    for (const leaf of leaves) {
      if (leaf.view?.file) {
        try {
          const content = await app.vault.read(leaf.view.file);
          return { path: leaf.view.file.path, content };
        } catch (e) {
          continue;
        }
      }
    }
    console.log('[ClaudePanel] getActiveFileContent: No active file found');
    return null;
  }

  try {
    const content = await app.vault.read(activeFile);
    return { path: activeFile.path, content };
  } catch (error) {
    console.error('[ClaudePanel] Error reading file:', error);
    return null;
  }
}

/**
 * 压缩笔记内容以传递给 CLI
 */
export function compressNoteContent(content: string, maxLength: number = 4000): string {
  let compressed = content.replace(/\s+/g, ' ').trim();
  if (compressed.length <= maxLength) {
    return compressed;
  }
  const headLength = Math.floor(maxLength * 0.7);
  const tailLength = maxLength - headLength;
  return compressed.substring(0, headLength) + '\n...[内容已截断]...\n' + compressed.slice(-tailLength);
}

export function getFileName(path: string): string {
  return path.split('/').pop()?.split('\\').pop() || path;
}

export function extractHeadings(content: string): string[] {
  const headings: string[] = [];
  const regex = /^#{1,3}\s+(.+)$/gm;
  let match;
  while ((match = regex.exec(content)) !== null) {
    headings.push(match[1]);
  }
  return headings;
}

export function insertAfterHeading(content: string, heading: string, insertContent: string): string {
  const lines = content.split('\n');
  let insertIndex = lines.length;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === heading || lines[i].trim().startsWith(heading)) {
      insertIndex = i + 1;
      break;
    }
  }
  lines.splice(insertIndex, 0, '', insertContent);
  return lines.join('\n');
}

export async function writeNoteContent(app: any, path: string, content: string): Promise<void> {
  const file = app.vault.getAbstractFileByPath(path);
  if (!file) {
    throw new Error(`File not found: ${path}`);
  }
  await app.vault.modify(file, content);
}

export async function appendToNote(app: any, path: string, content: string): Promise<void> {
  // 通过路径获取 TFile 对象
  const file = app.vault.getAbstractFileByPath(path);
  if (!file) {
    throw new Error(`File not found: ${path}`);
  }
  const existing = await app.vault.read(file);
  const newContent = existing + '\n' + content;
  await app.vault.modify(file, newContent);
}