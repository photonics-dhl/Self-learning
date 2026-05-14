# 铁律：修改前先备份到 GitHub

**任何重要改动前，必须先将待修改文件 commit + push 到 GitHub。**

远程仓库: `https://github.com/photonics-dhl/Self-learning.git`

## 重要改动定义（必须备份）

- 修改 `.claude/` 核心配置（settings.json, CLAUDE.md, AGENTS.md）
- 修改 skills/agents/hooks 定义文件
- 修改 `academic_rag/` 系统代码
- 修改 `Obsidian-Claude-Assistant/` 插件代码
- 删除任何文件
- 重构、批量重命名
- 修改 LaTeX 论文源文件

## 无需备份

- 单行 typo 修复
- 创建全新文件（不涉及修改已有文件）
- 纯查询操作

## 备份流程

```bash
git add <files> && git commit -m "backup: 修改前存档" && git push origin master
# 执行修改...
git add <files> && git commit -m "描述修改内容" && git push origin master
```

**禁止等到会话结束才 push。每次重要改动后立即 push。**
