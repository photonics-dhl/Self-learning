# Core Commands

## Literature Review Pipeline (primary research tool)

```bash
python .claude/hooks/multi_source_academic_writer.py "terahertz generation" -n 20 --paper-type journal_review
python .claude/hooks/openalex_search.py search "subwavelength aperture diffraction"
python .claude/hooks/openalex_search.py doi "10.1103/PhysRevLett.73.122"
python .claude/hooks/zotero_ref.py search "near-field optics"
```

## RAG System (`academic_rag/`)

```bash
pip install chromadb sentence-transformers pdfplumber pymupdf
python academic_rag/run_rag.py index paper.pdf --domain optics --subfield terahertz
python academic_rag/run_rag.py index-dir /path/to/papers --domain optics --subfield terahertz
python academic_rag/run_rag.py search "optical rectification LiNbO3" --top-k 5
python academic_rag/run_rag.py find-figure "photoconductive antenna" --subfield terahertz
python academic_rag/run_rag.py stats
python academic_rag/enhance_figures.py --all
```

## Plugin Build (`Obsidian-Claude-Assistant/`)

```bash
cd Obsidian-Claude-Assistant && npm install && node build.js
cd Obsidian-Claude-Assistant && npm run dev  # Watch mode
```

## LaTeX Compilation

TeX Live 2024 at `/d/Softwares_new/Latex/texlive/2024/bin/windows/`. Ensure in PATH.

```bash
xelatex -interaction=batchmode file.tex
bibtex file
xelatex -interaction=batchmode file.tex
```

## Utilities

```bash
python check_images.py                           # Batch AI figure analysis
python academic_rag/re_extract_figures.py         # Re-extract figures from indexed PDFs
python academic_rag/test_figure_extraction.py     # Test figure extraction pipeline
python academic_rag/batch_index_postdoc.py        # Batch index postdoc papers
python Obsidian-Vault/6️⃣ 工具/scripts/file_convert.py input.pdf -o output.md  # File format conversion
```

## Visualization

```bash
python generate_scientific_diagrams.py   # THz system diagrams → Obsidian-Vault/visualizations/
python .claude/hooks/sync_viz.py --check "topic"
python .claude/hooks/sync_viz.py image.png "topic"
```
