# Architecture: Skills, Agents, Hooks

## Skills

Skills live in `.claude/skills/<name>/SKILL.md`. Key skills:

| Skill | Purpose |
|-------|---------|
| `bishe-guider` | **Top priority** for Chinese thesis writing — 5 rule modules, P0/P1/P2 checks, 50+ regex de-AI rules |
| `knowledge-planning` | **Mandatory before creating any note** — scan siblings, output planning card, prevent duplicates |
| `knowledge-structure` | Note causal chain and four-layer understanding model |
| `academic-research` | Data-driven literature review generation (OpenAlex → LaTeX/BibTeX) |
| `literature-review` | Systematic review with thematic synthesis |
| `paper-writing` | IMRAD paper writing workflow |
| `humanizer` | Remove AI writing traces (29+ pattern types) |
| `research-paper-writing` | Reviewer-friendly rewriting |
| `scientific-writing` | Two-phase writing: plan → fluent paragraphs |
| `paper-review` | Dual-agent paper quality review |
| `beautiful-notes` | Obsidian callout-based note formatting |
| `optics-learning` | Optics domain knowledge tree builder, physics formula derivation, simulation code |
| `literature-sync` | Sync literature from Zotero to Obsidian vault with structured metadata |
| `last30days` | Hot discussion aggregation from web |
| `superpowers` | Meta-skill: mandatory skill reading + red flag checklist |
| `document-skills` | Document format conversion (MarkItDown + pandoc) |
| `diagram-generator` | DrawIO / Excalidraw technical diagram generation |
| `paper-search` | Multi-source academic paper search |

## Agents

Sub-agents in `.claude/agents/*.md` — invoke via `Agent` tool:

| Agent | Purpose |
|-------|---------|
| `optics-mentor` | Optics domain expert, physics formulas, simulation code |
| `literature-researcher` | Search, read, organize academic literature |
| `literature-curator` | Batch paper metadata enrichment + DB ingestion |
| `note-planner` | Pre-note knowledge planning (duplicate check) |
| `note-generator` | Generate Obsidian notes from sources |
| `note-reviewer` | Quality review of generated notes |
| `paper-writer` | AI Scientist v2 paper writing |
| `paper-planner` | Paper outline planning (planning-driven writing) |
| `researcher-profiler` | Deep researcher profile generation (postdoc-interview depth) |

## Hooks

- `SessionStart` → `python .claude/hooks/session-start-hook.py`
- `SessionEnd` → `python .claude/hooks/session-end-hook.py`
- Config in `.claude/settings.json` → `hooks` section

## Review Pipeline

Current active: `multi_source_academic_writer.py` (v5.2). Older versions in `.claude/hooks/` are archival — do not extend.
