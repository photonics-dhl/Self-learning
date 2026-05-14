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

## API Key Security (Critical)

**Rule:** Always read API keys from `os.environ` / `.env`. Never hardcode into source files.

Hardcoded keys risk locations: `academic_rag/processors/multimodal_analyzer.py`, `.mcp.json` (Zotero API key), `.claude/settings.local.json` (Tavily dev keys). Never add new keys to these files.

Required env vars: `ANTHROPIC_API_KEY`, `TAVILY_API_KEY` (supports rotation of 4+ keys), `GITHUB_TOKEN`, `Zotero_API_KEY`, `Zotero_user_ID`, `OpenAlex_API_KEY`, `DEEPSEEK_API_KEY`.

## First-Principles Thinking

1. If motivation is unclear, stop and discuss. Don't assume.
2. If a clear goal has a shorter path, say so directly.
3. Trace to root cause. No patches. Every decision must answer "why."
4. Output only what changes the decision. Cut everything else.
