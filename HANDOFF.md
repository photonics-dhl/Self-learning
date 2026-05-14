# HANDOFF — Cross-Session Context Bridge

> Read this at session start. Update before `/clear` or session end.

## Last Task
Integrated "图文并茂" (rich illustration) requirement into literature review writing pipeline.
Updated 5 files across 2 skills to make image extraction + semantic matching a DEFAULT behavior.

## Changes Made

### literature-review skill (4 files)
- **SKILL.md**: Added Core Principle #5 (图文并茂), Phase 0 (图表预提取), updated MCP协同 (Zotero image extraction toolchain), added quality gates (>=2 figures per theme)
- **theme_analysis.md**: Added Step 5 (图表语义匹配与利用) with extraction workflow, semantic matching rules, output format, and insertion rules
- **review_template.md**: Added figure placement zones (2.3 图表展示区), data-figure insertion points, updated checklist with figure requirements
- **introduction.md**: Updated 本文目标 paragraph to mention figure extraction, added figure count to call template

### academic-research skill (1 file)
- **SKILL.md**: Added Phase 0 (图表预提取) to pipeline, figure_assets.json output, noted PDF dependency in 已知限制

### Key Design Decisions
- Zotero MCP `get_content` is primary image source; `academic_rag/figure_indexer` is fallback for pre-indexed papers
- Semantic matching: chart type → review section mapping (experimental setup → methods, data plot → tradeoff analysis, etc.)
- Minimum bar: >=2 figures per theme (setup diagram + data plot)
- Every figure must have: Chinese caption + source note + in-text reference

## Next Steps
1. Resume Postdoc researcher profile enhancement (Leone profile next)
2. Apply new 图文并茂 rules when writing any literature review

## Relevant Files
- `.claude/skills/literature-review/SKILL.md` — core skill (updated)
- `.claude/skills/literature-review/prompts/theme_analysis.md` — figure semantic matching (updated)
- `.claude/skills/literature-review/prompts/introduction.md` — intro w/ figure mention (updated)
- `.claude/skills/literature-review/templates/review_template.md` — figure placement zones (updated)
- `.claude/skills/academic-research/SKILL.md` — pipeline w/ figure extraction (updated)
- `Obsidian-Vault/2️⃣ 研究方向/Postdoc方向/Stephen Leone.md` — next profile to enhance
