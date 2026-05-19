# CLAUDE.md

Personal digital academic brain for an optics PhD researcher. Core: AI-assisted knowledge management, literature review, and academic writing using Obsidian as the knowledge front-end and Claude Code as the intelligence layer. All documentation and code comments in Chinese; physics terminology in English.

## Rules (loaded on demand)

| File | Content |
|------|---------|
| `.claude/rules/backup.md` | Iron rule: backup to GitHub before any important change |
| `.claude/rules/protected-dirs.md` | Directories never to be recursively deleted |
| `.claude/rules/commands.md` | Core commands (literature review, RAG, plugin build, LaTeX, utilities) |
| `.claude/rules/architecture.md` | Skills, agents, hooks inventory and review pipeline |
| `.claude/rules/conventions.md` | Note quality, knowledge dedup, file naming, tags, language, testing |
| `.claude/rules/security.md` | API key security: never hardcode, always read from `.env` |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Knowledge front-end | Obsidian (Electron) with Dataview, Templater, Zotero Integration |
| AI orchestration | Claude Code with custom skills, agents, hooks (`.claude/`) |
| MCP extensions | 10 servers (`.mcp.json`): tavily-search, semantic-scholar, paper-search, zotero, github, mermaid, puppeteer, fetch, memory, context7 |
| RAG / vector search | Python + ChromaDB + `BAAI/bge-m3` embeddings (`academic_rag/`) |
| PDF processing | PyMuPDF (`fitz`) + `pdfplumber` |
| Academic typesetting | TeX Live 2024 (`xelatex`, `bibtex`) |
| Obsidian plugin | TypeScript + esbuild (`Obsidian-Claude-Assistant/`) |
| Visualization | matplotlib + numpy + scipy |

No root-level `requirements.txt` or `package.json`. Python 3.9 in `.venv/`, Node deps only in `Obsidian-Claude-Assistant/`.

## Key Config Files

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Project permissions, hooks, envFile config |
| `.claude/settings.local.json` | Local permission allowlists (gitignored, machine-specific) |
| `.mcp.json` | MCP server definitions |
| `.env` | Environment variables (API keys, gitignored) |

## Key Resource Locations

| Resource | Path | Note |
|----------|------|------|
| LaTeX templates | `Obsidian-Vault/6️⃣ 工具/templates/` | thesis (zjuthesis) + journal (Nature/APS/IEEE) |
| Draft output dir | `DHL/test_paper_draft/` | Paper-writing pipeline outputs |
| RAG database | `academic_rag/chroma_db/` | Never delete (see protected-dirs) |
| Obsidian plugin | `Obsidian-Claude-Assistant/` | `npm run build` to compile |
| Skills | `.claude/skills/<name>/SKILL.md` | All custom skills |
| Agents | `.claude/agents/*.md` | Sub-agent definitions |
| Hooks | `.claude/hooks/*.py` | Session start/end hooks |
| Zotero downloads | `E:\PostGraduate\Science_softwares\Zotero\downloads` | PDF source for indexing |

## Session Continuity

- **HANDOFF.md**: Before `/clear` or session end, write current task state, key decisions, and next steps to `HANDOFF.md`. Read it at session start.
- **Document & Clear**: Write阶段性成果 to files → `/clear` → new session reads files back. Never accumulate all context in chat.
- **Memory**: Cross-session persistent memory at `.claude/projects/.../memory/`. Used automatically for user preferences, feedback, project decisions.

## Compact & Verification

- **Compact triggers**: Task complete, rounds > 20, time > 30min, or context switching. `/compact` immediately.
- **Before declaring done**: Run `/context`. If >73%, `/compact` or `/clear` first.
- **Verification per task type**: Code change → run the script. LaTeX → `xelatex -interaction=batchmode file.tex`. Plugin → `npm run build`. Lit review → output file exists and non-empty.

## First-Principles Thinking

1. If motivation is unclear, stop and discuss. Don't assume.
2. If a clear goal has a shorter path, say so directly.
3. Trace to root cause. No patches. Every decision must answer "why."
4. Output only what changes the decision. Cut everything else.
