"""
Re-extract figures from all indexed PDFs using improved rendering method.
Replaces old low-quality extractions (embedded-image-only) with full-layer renders.
Processes one PDF at a time, closes after each, gc.collect() to avoid OOM.

Usage:
    python academic_rag/re_extract_figures.py              # all papers
    python academic_rag/re_extract_figures.py --paper-id X # single paper
"""

import gc
import json
import shutil
import sys
import io
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from academic_rag.config import config
from academic_rag.processors.pdf_processor import PDFProcessor
# Heavy imports deferred to re_index_clip() to avoid loading sentence-transformers
# during figure extraction phase


def re_extract_all(processor: PDFProcessor) -> list[dict]:
    """Re-extract figures + tables for all indexed papers. Returns summary list."""
    db_path = config.vector_db_path
    meta_files = sorted(db_path.glob("*_metadata.json"))
    summary = []

    for i, meta_file in enumerate(meta_files):
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        pdf_path = meta["paper"]["pdf_path"]
        paper_id = meta["paper"]["paper_id"]
        title = meta["paper"]["title"][:60]
        old_fig_count = len(meta.get("figures", []))
        old_tab_count = len(meta.get("tables", []))

        print(f"[{i+1}/{len(meta_files)}] {paper_id[:8]} | {title}")

        pdf = Path(pdf_path)
        if not pdf.exists():
            print(f"  SKIP: PDF not found: {pdf_path}")
            summary.append({"paper_id": paper_id, "old_fig": old_fig_count, "new_fig": 0,
                           "old_tab": old_tab_count, "new_tab": 0, "error": "pdf missing"})
            continue

        # Delete old figure/table files
        old_dir = config.visualizations / paper_id[:8]
        if old_dir.exists():
            for f in old_dir.iterdir():
                try:
                    f.unlink()
                except OSError:
                    pass

        # Re-extract figures
        try:
            figures = processor._extract_figures(pdf, paper_id)
        except Exception as e:
            print(f"  FIG ERROR: {e}")
            summary.append({"paper_id": paper_id, "old_fig": old_fig_count, "new_fig": 0,
                           "old_tab": old_tab_count, "new_tab": 0, "error": str(e)[:100]})
            gc.collect()
            continue

        # Re-extract tables
        try:
            tables = processor._extract_tables(pdf, paper_id)
        except Exception as e:
            print(f"  TAB ERROR: {e}")
            tables = []

        # Update metadata
        meta["figures"] = [f.to_dict() for f in figures]
        meta["tables"] = tables
        meta["paper"]["num_figures"] = len(figures)
        meta["paper"]["num_tables"] = len(tables)

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"  Figs: {old_fig_count} → {len(figures)} | Tables: {old_tab_count} → {len(tables)}")
        summary.append({"paper_id": paper_id, "old_fig": old_fig_count, "new_fig": len(figures),
                        "old_tab": old_tab_count, "new_tab": len(tables)})

        del figures, tables, meta
        gc.collect()

    return summary


def re_index_clip(summary: list[dict]) -> None:
    """Re-index CLIP embeddings for papers that have figures."""
    from academic_rag.indexer.vector_indexer import VectorIndexer
    from academic_rag.indexer.figure_indexer import FigureIndexer
    from academic_rag.db.models import Paper, Figure

    print("\nRe-indexing CLIP figure embeddings...")
    figure_indexer = FigureIndexer()
    indexer = VectorIndexer(figure_indexer=figure_indexer)
    db_path = config.vector_db_path

    papers_with_figs = [s for s in summary if s.get("new_fig", s.get("new", 0)) > 0]
    for i, s in enumerate(papers_with_figs):
        meta_file = db_path / f"{s['paper_id']}_metadata.json"
        if not meta_file.exists():
            continue

        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        paper = Paper.from_dict(meta["paper"])
        figures = [Figure.from_dict(fd) for fd in meta.get("figures", [])]

        if figures:
            n = indexer.index_paper_figures(paper, figures)
            print(f"  [{i+1}/{len(papers_with_figs)}] {paper.paper_id[:8]}: {n} CLIP embeddings")

        del paper, figures, meta
        gc.collect()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Re-extract figures from indexed PDFs")
    parser.add_argument("--paper-id", help="Re-extract specific paper only")
    args = parser.parse_args()

    print("Loading PDF processor (image_dpi=300)...")
    processor = PDFProcessor(extract_images=True, image_dpi=300, enhance=True)
    print("Ready.\n")

    if args.paper_id:
        # Single paper mode
        db_path = config.vector_db_path
        meta_file = db_path / f"{args.paper_id}_metadata.json"
        if not meta_file.exists():
            print(f"No metadata found for {args.paper_id}")
            return
        # Temporarily rename other metadata files so loop only processes one
        all_metas = sorted(db_path.glob("*_metadata.json"))
        others = [m for m in all_metas if m.name != meta_file.name]
        for m in others:
            m.rename(m.with_suffix(".json.bak"))
        try:
            summary = re_extract_all(processor)
        finally:
            for m in others:
                bak = m.with_suffix(".json.bak")
                if bak.exists():
                    bak.rename(m)
    else:
        summary = re_extract_all(processor)

    old_fig_total = sum(r.get("old_fig", r.get("old", 0)) for r in summary)
    new_fig_total = sum(r.get("new_fig", r.get("new", 0)) for r in summary)
    old_tab_total = sum(r.get("old_tab", 0) for r in summary)
    new_tab_total = sum(r.get("new_tab", 0) for r in summary)
    errors = [r for r in summary if "error" in r]

    print(f"\n{'='*60}")
    print(f"RE-EXTRACTION COMPLETE")
    print(f"  Papers: {len(summary)}")
    print(f"  Figures: {old_fig_total} → {new_fig_total}")
    print(f"  Tables:  {old_tab_total} → {new_tab_total}")
    print(f"  Errors: {len(errors)}")
    print(f"{'='*60}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e['paper_id'][:8]}: {e['error']}")

    # Re-index CLIP embeddings
    if new_total > 0:
        print()
        re_index_clip(summary)

    print("\nAll done.")


if __name__ == "__main__":
    main()
