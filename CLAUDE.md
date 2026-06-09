# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Personal digital academic brain for an optics PhD researcher. AI-assisted knowledge management, literature review, and academic writing. Obsidian = knowledge front-end, Claude Code = intelligence layer. All documentation/comments in Chinese; physics terminology in English.

## Rules (loaded on demand)

| File | Content |
|------|---------|
| `.claude/rules/backup.md` | 🔴 Iron rule: backup to GitHub before any important change |
| `.claude/rules/protected-dirs.md` | Directories never to be recursively deleted |
| `.claude/rules/commands.md` | Core commands (lit review, RAG, plugin build, LaTeX, utilities) |
| `.claude/rules/architecture.md` | Skills, agents, hooks inventory and review pipeline |
| `.claude/rules/conventions.md` | Note quality, knowledge dedup, file naming, tags, language, testing |
| `.claude/rules/security.md` | API key security: never hardcode, always read from `.env` |

## Architecture

```
Zotero (PDFs) ──► academic_rag/ (ChromaDB + bge-m3) ──► semantic search
     │                                                          │
     ▼                                                          ▼
Obsidian-Vault/ ◄── Claude Code (skills + agents + hooks)
     ▲                              │
     │                              ▼
Obsidian-Claude-Assistant/     MCP servers (9: tavily, semantic-scholar,
  (TypeScript plugin)            paper-search, zotero, github, mermaid,
                                 fetch, memory, context7)
```

**Data flow**: Zotero PDFs → `academic_rag/` indexes text+figures into ChromaDB → Claude searches via `run_rag.py`. Literature review pipeline (`multi_source_academic_writer.py` v5.2) synthesizes OpenAlex + Semantic Scholar + RAG into LaTeX/BibTeX outputs.

**Obsidian plugin** (`Obsidian-Claude-Assistant/`): TypeScript + esbuild. Main panel in `ClaudePanel.ts` (~43KB). API client in `zai-client.ts`. Build: `npm run build` or `node build.js`.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Knowledge front-end | Obsidian with Dataview, Templater, Zotero Integration |
| AI orchestration | Claude Code + custom skills/agents/hooks (`.claude/`) |
| RAG / vector search | Python 3.9 + ChromaDB + `BAAI/bge-m3` (`academic_rag/`) |
| PDF processing | PyMuPDF (`fitz`) + `pdfplumber` |
| Academic typesetting | TeX Live 2024 (`xelatex`, `bibtex`) |
| Obsidian plugin | TypeScript + esbuild (`Obsidian-Claude-Assistant/`) |
| Visualization | matplotlib + numpy + scipy |

No root-level `requirements.txt` or `package.json`. Python 3.9+ (system or `.venv/`), Node deps only in `Obsidian-Claude-Assistant/`.

## Key Commands

```bash
# Literature review (primary research tool)
python .claude/hooks/multi_source_academic_writer.py "topic" -n 20 --paper-type journal_review

# RAG system
python academic_rag/run_rag.py index paper.pdf --domain optics --subfield terahertz
python academic_rag/run_rag.py search "query" --top-k 5

# Obsidian plugin
cd Obsidian-Claude-Assistant && npm install && node build.js

# LaTeX
xelatex -interaction=batchmode file.tex && bibtex file && xelatex -interaction=batchmode file.tex
```

Full command reference in `.claude/rules/commands.md`.

## Key Config & Resource Locations

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Project permissions, hooks, envFile |
| `.mcp.json` | 9 MCP server definitions |
| `.env` | API keys (gitignored) — all keys read via `os.environ` |
| `Obsidian-Vault/6️⃣ 工具/templates/` | LaTeX templates (zjuthesis + journal) |
| `academic_rag/chroma_db/` | Vector DB — **never delete** (rebuild = hours) |
| `.claude/skills/<name>/SKILL.md` | Custom skills (36 total) |
| `.claude/agents/*.md` | Sub-agent definitions (9 total) |
| `DHL/` | Active paper drafts (small_hole_qed, thz_nearfield_paper, terahertz_qed, High_power, mid_term) + templates |
| `Obsidian-Vault/1️⃣ 学科基础/` | Foundation notes organized by topic (01 电磁地基–18 拓扑光学) |
| `Obsidian-Vault/2️⃣ 研究方向/` | Research-direction notes |
| `Obsidian-Vault/4️⃣ 文献库/` | Literature notes synced from Zotero |

## Critical Conventions

- **Backup before change**: See `.claude/rules/backup.md`. Git commit + push to GitHub **before** modifying any important file. Push immediately, not at session end.
- **Knowledge dedup**: Before creating any note, scan siblings → classify relationship → output planning card. Use `knowledge-planning` skill.
- **Note quality**: Every note needs: physical intuition (callout), ≥1 Mermaid diagram, core formula (LaTeX), comparison table, ≥2 citations.
- **Review pipeline**: Only extend `multi_source_academic_writer.py` (v5.2). Older versions in `.claude/hooks/` are archival.
- **Protected dirs**: `Obsidian-Vault/`, `academic_rag/chroma_db/`, `DHL/`, `.claude/` — never recursively delete.
- **Language**: All output, comments, docstrings in Chinese. Physics terms, API fields, LaTeX in English.
- **Tags**: `#optics` / `#optics/terahertz` / `#optics/metasurface` / `#paper` / `#method`

## Session Discipline

- **HANDOFF.md** (repo root): Write task state + decisions + next steps before `/clear` or session end. Read at session start. Always check for prior session context.
- **Caveman mode**: Default communication style (terse, no filler). Toggle via `/caveman lite|full|ultra`.
- **Compact triggers**: Task complete, rounds > 20, time > 30min, or context switching → `/compact` immediately.
- **Verification**: Code → run it. LaTeX → compile. Plugin → `npm run build`. Lit review → output file exists + non-empty.
- **First principles**: Unclear motivation → stop and discuss. Root cause only, no patches. Every decision answers "why."

## Git

Remote: `https://github.com/photonics-dhl/Self-learning.git`. Default branch: `master`. Commit messages in English.
