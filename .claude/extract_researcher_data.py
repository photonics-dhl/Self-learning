#!/usr/bin/env python
"""
Extract all indexed paper data for a researcher. Outputs structured JSON
with text chunks, figures, and metadata — ready for AI analysis.
"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
import argparse

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from academic_rag.config import config

PROFESSOR_KEYS = [
    "baum", "chang", "gedik", "hommelhoff", "huber", "kaertner",
    "keller", "kling", "krausz", "leone", "lhuillier", "miao",
    "murnane", "nisoli", "ropers",
]


def extract_professor(prof_key):
    """Extract all indexed data for a professor."""
    db_path = Path(config.vector_db_path)
    papers = []

    for meta_file in sorted(db_path.glob("*_metadata.json")):
        try:
            with open(meta_file, encoding='utf-8') as f:
                meta = json.load(f)
        except Exception:
            continue

        pdf_path = meta.get("paper", {}).get("pdf_path", "")
        if f"postdoc/{prof_key}" not in pdf_path.lower().replace('\\', '/'):
            continue

        paper = meta.get("paper", {})
        figures = meta.get("figures", [])
        chunks = meta.get("chunks", [])
        tables = meta.get("tables", [])

        # Summarize content
        abstract = ""
        key_paragraphs = []
        for c in chunks:
            text = c.get("text", "")
            text_type = c.get("text_type", "")
            if text_type == "abstract":
                abstract = text[:800]
            elif len(text) > 200:
                key_paragraphs.append({
                    "heading": c.get("heading", ""),
                    "text": text[:500],
                    "page": c.get("page_num", 0),
                    "type": text_type,
                })

        papers.append({
            "title": paper.get("title", ""),
            "year": paper.get("year", 0),
            "journal": paper.get("journal", ""),
            "authors": paper.get("authors", []),
            "doi": paper.get("doi", ""),
            "paper_id": paper.get("paper_id", ""),
            "file_hash": paper.get("file_hash", ""),
            "num_pages": paper.get("num_pages", 0),
            "abstract": abstract,
            "n_figures": len(figures),
            "n_chunks": len(chunks),
            "n_tables": len(tables),
            "figures": [
                {
                    "figure_id": f.get("figure_id", ""),
                    "label": f.get("figure_label", ""),
                    "caption": f.get("figure_caption", ""),
                    "image_path": f.get("image_path", ""),
                    "page_num": f.get("page_num", 0),
                    "width": f.get("width", 0),
                    "height": f.get("height", 0),
                    "figure_type": f.get("figure_type", ""),
                    "description": f.get("description", ""),
                }
                for f in figures[:12]
            ],
            "key_paragraphs": key_paragraphs[:10],
        })

    return papers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--professor", "-p", required=True)
    parser.add_argument("--output", "-o", default="")
    args = parser.parse_args()

    prof = args.professor
    papers = extract_professor(prof)

    print(f"Professor: {prof}")
    print(f"Papers indexed: {len(papers)}")
    total_figs = sum(p["n_figures"] for p in papers)
    total_chunks = sum(p["n_chunks"] for p in papers)
    print(f"Figures: {total_figs}, Text chunks: {total_chunks}")

    if not papers:
        print("No indexed papers found!")
        return

    result = {
        "professor_key": prof,
        "paper_count": len(papers),
        "total_figures": total_figs,
        "total_chunks": total_chunks,
        "papers": sorted(papers, key=lambda p: p["year"], reverse=True),
    }

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = PROJECT_ROOT / ".claude" / f"{prof}_extracted.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Output: {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
