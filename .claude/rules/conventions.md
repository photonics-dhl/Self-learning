# Key Conventions

## Note Quality Requirements

Every note must contain: one-sentence physical intuition (callout), >=1 Mermaid diagram, core formula (LaTeX), comparison table, schematic (MCP image gen or matplotlib), >=2 paper citations (`[[cite:@Author2024]]`), quantified parameters.

## Knowledge Deduplication

Before creating a note: scan siblings → classify relationship (`DUPLICATE`/`SUBSUMED`/`CONTAINS`/`OVERLAPS`/`INDEPENDENT`) → output planning card → then write.

## File Naming (Obsidian Vault)

`NN_Title.md` or `📁 NN CategoryName/`. Internal links use `[[Title]]` (no number prefix — frontmatter `title` handles this).

## Tag System

`#optics` / `#optics/terahertz` / `#optics/metasurface` / `#paper` / `#method`

## Language

All output, comments, docstrings in Chinese. Physics terms, API fields, LaTeX in English.

## Testing

No formal test framework. Manual verification per component:
- Obsidian plugin: `Ctrl+Shift+C` → submit query → verify Markdown → click "写入笔记" → check insertion
- Python scripts: Run with real data, check output
- RAG: `academic_rag/test_figure_extraction.py` for figure extraction
- LaTeX: Compile with `xelatex -interaction=batchmode`, verify PDF
