"""
批量索引 Postdoc 15位教授的 PDF 论文到 RAG 系统
Usage: python academic_rag/batch_index_postdoc.py [--professor name] [--start-from name]
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from academic_rag.processors.pdf_processor import PDFProcessor, BatchProcessor
from academic_rag.indexer.vector_indexer import VectorIndexer
from academic_rag.indexer.figure_indexer import FigureIndexer
from academic_rag.db.models import Paper, Figure

PROFESSOR_FIELDS = {
    "krausz": ("optics", "attosecond"),
    "lhuillier": ("optics", "attosecond"),
    "keller": ("optics", "attosecond"),
    "nisoli": ("optics", "attosecond"),
    "ropers": ("optics", "ultrafast"),
    "murnane": ("optics", "extreme_ultraviolet"),
    "kaertner": ("optics", "ultrafast"),
    "baum": ("optics", "ultrafast"),
    "kling": ("optics", "attosecond"),
    "hommelhoff": ("optics", "ultrafast"),
    "huber": ("optics", "terahertz"),
    "chang": ("optics", "attosecond"),
    "leone": ("optics", "attosecond"),
    "gedik": ("optics", "condensed_matter"),
    "miao": ("optics", "imaging"),
}

PAPERS_ROOT = Path(__file__).parent / "papers" / "postdoc"


def index_figures_only(indexer, professor=None):
    """Re-index CLIP embeddings for papers already in the text index.

    Loads paper + figures from chroma_db metadata files (no PDF re-extraction).
    """
    import json
    from academic_rag.config import config

    db_path = config.vector_db_path
    meta_files = sorted(db_path.glob("*_metadata.json"))
    if not meta_files:
        print("No metadata files found in chroma_db.")
        return []

    summary = []
    for meta_file in meta_files:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        paper = Paper.from_dict(meta["paper"])
        figures = [Figure.from_dict(fd) for fd in meta.get("figures", [])]

        if professor:
            prof_segment = Path("postdoc") / professor
            if str(prof_segment) not in paper.pdf_path:
                continue
        if not figures:
            continue

        n = indexer.index_paper_figures(paper, figures)
        summary.append({"paper_id": paper.paper_id, "title": paper.title[:60], "figures_indexed": n})
        print(f"  CLIP figs: {paper.title[:60]} → {n} embeddings")

    return summary


def index_professor(name, domain, subfield, processor, indexer):
    pdf_dir = PAPERS_ROOT / name
    if not pdf_dir.exists():
        return {"professor": name, "total": 0, "indexed": 0, "error": "dir not found"}

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        return {"professor": name, "total": 0, "indexed": 0}

    print(f"\n{'='*60}")
    print(f"Indexing {name} ({domain}/{subfield}): {len(pdfs)} PDFs")
    print(f"{'='*60}")

    batch = BatchProcessor(processor)
    results = batch.process_directory(pdf_dir, domain=domain, subfield=subfield, recursive=False)

    success = 0
    fail = 0

    for paper, figures, chunks, tables in results:
        paper_id = paper.paper_id
        try:
            if indexer._is_paper_indexed(paper_id):
                print(f"  SKIP: {paper.title[:60]}")
                continue
            if indexer.index_paper(paper, figures, chunks):
                success += 1
                print(f"  OK: {paper.title[:60]} [{len(chunks)} chunks, {len(figures)} figs]")
                if indexer.figure_indexer and figures:
                    n_fig = indexer.index_paper_figures(paper, figures)
                    print(f"       CLIP: {n_fig} figure embeddings")
            else:
                fail += 1
                print(f"  FAIL: {paper.title[:60]}")
        except Exception as e:
            fail += 1
            print(f"  ERROR: {paper.title[:60]} — {e}")

    print(f"  Result: {success}/{len(pdfs)} indexed, {fail} failed")
    return {"professor": name, "total": len(pdfs), "indexed": success, "failed": fail}


def main():
    parser = argparse.ArgumentParser(description="Batch index postdoc professor PDFs")
    parser.add_argument("--professor", "-p", help="Index specific professor only")
    parser.add_argument("--start-from", help="Start from this professor (alphabetical)")
    parser.add_argument("--figures-only", action="store_true", help="Only index CLIP figure embeddings (skip text)")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    prof_names = sorted(PROFESSOR_FIELDS.keys())
    if args.start_from and args.start_from in PROFESSOR_FIELDS:
        idx = prof_names.index(args.start_from)
        prof_names = prof_names[idx:]
    if args.professor and args.professor in PROFESSOR_FIELDS:
        prof_names = [args.professor]

    print(f"Loading models once (shared across all professors)...")
    figure_indexer = FigureIndexer()
    processor = PDFProcessor(extract_images=True, image_dpi=300)
    indexer = VectorIndexer(figure_indexer=figure_indexer)
    print(f"Models loaded.")

    if args.figures_only:
        print(f"FIGURES-ONLY mode: re-indexing CLIP embeddings for existing papers")
        start_time = time.time()
        summary = index_figures_only(indexer, professor=args.professor)
        elapsed = time.time() - start_time
        total_figs = sum(r["figures_indexed"] for r in summary)
        print(f"\n{'='*60}")
        print(f"CLIP FIGURE INDEX COMPLETE")
        print(f"  Papers: {len(summary)}")
        print(f"  Figure embeddings: {total_figs}")
        print(f"  Time: {elapsed:.1f}s")
        print(f"{'='*60}")
        return

    print(f"Processing {len(prof_names)} professor(s).")

    start_time = time.time()
    summary = []

    for name in prof_names:
        domain, subfield = PROFESSOR_FIELDS[name]
        result = index_professor(name, domain, subfield, processor, indexer)
        summary.append(result)

    elapsed = time.time() - start_time
    total_indexed = sum(r["indexed"] for r in summary)
    total_pdfs = sum(r["total"] for r in summary)

    print(f"\n{'='*60}")
    print(f"BATCH INDEX COMPLETE")
    print(f"  Professors: {len(summary)}")
    print(f"  PDFs: {total_indexed}/{total_pdfs} indexed")
    print(f"  Time: {elapsed:.1f}s")
    print(f"{'='*60}")

    for r in summary:
        status = "OK" if r["indexed"] == r["total"] else f"{r['indexed']}/{r['total']}"
        print(f"  {r['professor']}: {status}")


if __name__ == "__main__":
    main()
