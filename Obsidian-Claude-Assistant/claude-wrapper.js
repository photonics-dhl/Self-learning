#!/usr/bin/env node
/**
 * Claude CLI Wrapper for Obsidian Plugin
 * 解释 JSON 请求并调用 Claude Code CLI
 */

const { spawn } = require('child_process');
const readline = require('readline');

async function main() {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  let requestData = '';
  for await (const line of rl) {
    requestData += line;
  }

  let request;
  try {
    request = JSON.parse(requestData);
  } catch (e) {
    console.error(JSON.stringify({ error: 'Invalid JSON' }));
    process.exit(1);
  }

  const { action, context, options } = request;

  // 根据 action 构建不同的 prompt
  let prompt = '';

  if (action === 'write_summary') {
    prompt = buildSummaryPrompt(context);
  } else if (action === 'explain') {
    prompt = buildExplainPrompt(context, options);
  } else if (action === 'cite') {
    prompt = buildCitePrompt(context);
  } else if (action === 'tree') {
    prompt = buildTreePrompt(context);
  } else {
    // 默认：直接对话
    const lastMessage = context.conversation_history.length > 0
      ? context.conversation_history[context.conversation_history.length - 1].content
      : context.selected_text || '请解释';
    prompt = buildChatPrompt(context, lastMessage, options);
  }

  // 调用 Claude Code CLI
  const response = await callClaude(prompt);

  // 输出 JSON 响应
  console.log(JSON.stringify({
    response: response,
    write_actions: action === 'write_summary' ? [{
      type: 'append',
      content: response
    }] : []
  }));
}

function buildSummaryPrompt(context) {
  const history = context.conversation_history.map(
    e => `${e.role === 'user' ? '用户' : 'Claude'}：${e.content}`
  ).join('\n\n');

  return `你是我的学术笔记助手。请将以下对话内容总结成结构化的笔记格式，要求：
1. 提炼核心概念和关键知识点
2. 保留重要公式（用 LaTeX）
3. 添加 Mermaid 知识图（如适用）
4. 使用 Obsidian Callout 语法美化格式
5. 只输出可直接写入笔记的 Markdown 内容，不要解释

对话内容：
${history}

当前笔记：${context.current_note}
笔记已有内容片段：${context.note_content.substring(0, 500)}`;
}

function buildExplainPrompt(context, options) {
  const depth = options?.depth === 'brief' ? '简要' : '详细';
  const topic = context.selected_text || (context.conversation_history.length > 0
    ? context.conversation_history[context.conversation_history.length - 1].content
    : '请解释');

  return `请${depth}解释以下概念，要求：
1. 用一句话物理图像开头
2. 包含核心公式（用 LaTeX）
3. 适当的 Mermaid 图表
4. 具体数值和参数
5. 相关论文引用格式 [[cite:@AuthorYear]]

主题：${topic}`;
}

function buildCitePrompt(context) {
  return `请为以下内容推荐相关论文引用，要求：
1. 推荐 2-3 篇高影响力论文
2. 包含 DOI 或 URL
3. 说明引用理由

主题：${context.selected_text || context.note_content.substring(0, 500)}`;
}

function buildTreePrompt(context) {
  return `请为以下主题构建知识树，要求：
1. 使用 Mermaid mindmap 格式
2. 包含 3-5 个主要分支
3. 每个分支有 2-3 个子节点
4. 只输出 Mermaid 代码

主题：${context.selected_text || context.note_content.substring(0, 500)}`;
}

function buildChatPrompt(context, message, options) {
  const noteContext = context.note_content
    ? `\n\n当前笔记内容：\n${context.note_content.substring(0, 1000)}`
    : '';

  return `你正在 Obsidian 中帮助用户学习。当前笔记：${context.current_note}${noteContext}

用户选中的内容：${context.selected_text || '无'}

用户消息：${message}

请直接回答，可以使用 Markdown 格式（LaTeX 公式、Mermaid 图表）。`;
}

function callClaude(prompt) {
  return new Promise((resolve, reject) => {
    const isWindows = process.platform === 'win32';
    const child = spawn(
      isWindows ? 'cmd' : 'bash',
      isWindows ? ['/c', 'claude'] : ['-c', 'claude'],
      {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, CLAUDE_NO_ANTHROPIC_WARNING: '1' }
      }
    );

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
      // 提取 JSON 如果有
      const lines = stdout.trim().split('\n');
      const jsonLine = lines.find(l => l.trim().startsWith('{'));
      if (jsonLine) {
        try {
          resolve(JSON.parse(jsonLine).response || stdout);
        } catch {
          resolve(stdout);
        }
      } else {
        resolve(stdout);
      }
    });

    child.stdin.write(prompt);
    child.stdin.end();
  });
}

main().catch(e => {
  console.error(JSON.stringify({ error: e.message }));
  process.exit(1);
});
