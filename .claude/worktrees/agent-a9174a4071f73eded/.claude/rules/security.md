# API Key Security

**Rule:** Always read API keys from `os.environ` / `.env`. Never hardcode into source files.

## Risk Locations (do not add keys here)

- `academic_rag/processors/multimodal_analyzer.py`
- `.mcp.json` (Zotero API key)
- `.claude/settings.local.json` (Tavily dev keys)

## Required Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API access |
| `TAVILY_API_KEY` | Web search (supports rotation of 4+ keys) |
| `GITHUB_TOKEN` | GitHub API operations |
| `Zotero_API_KEY` | Zotero library access |
| `Zotero_user_ID` | Zotero user identification |
| `OpenAlex_API_KEY` | OpenAlex academic search |
| `DEEPSEEK_API_KEY` | DeepSeek model access |
