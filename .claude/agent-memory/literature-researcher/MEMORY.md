# Literature Researcher Agent - Memory Index

## Search Sessions
- [optical_engineering_reviews_20260520.md](optical_engineering_reviews_20260520.md) - Optical engineering & photonic engineering highly-cited review papers search (9 topics, 2026-05-20)

## Search Patterns
- Semantic Scholar bulk endpoint (`/paper/search/bulk`) is more reliable than regular search endpoint, handles rate limiting better
- Regular search endpoint (`/paper/search`) returns 429 errors frequently; need 3-5 second delays between calls
- Web search (Tavily) had API errors during this session; Semantic Scholar was the primary source
- Many older DOIs (pre-2000) return 404 on Semantic Scholar; these papers may need manual DOI lookup
