#!/usr/bin/env python
"""
Researcher Profile Enrichment with Figures
===========================================
Reads indexed papers from ChromaDB, extracts figures, enriches Obsidian notes.

Usage:
    python .claude/enrich_profiles.py --professor baum
    python .claude/enrich_profiles.py --all
    python .claude/enrich_profiles.py --professor baum --dry-run
"""

import json
import sys
import io
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from academic_rag.indexer.vector_indexer import VectorIndexer
from academic_rag.config import config

POSTDOC_DIR = PROJECT_ROOT / "Obsidian-Vault" / "2️⃣ 研究方向" / "Postdoc方向"
PROFESSOR_NAMES = {
    "baum": "Peter Baum",
    "chang": "Zenghu Chang",
    "gedik": "Nuh Gedik",
    "hommelhoff": "Peter Hommelhoff",
    "huber": "Rupert Huber",
    "kaertner": "Franz X Kärtner",
    "keller": "Ursula Keller",
    "kling": "Matthias Kling",
    "krausz": "Ferenc Krausz",
    "leone": "Stephen Leone",
    "lhuillier": "Anne L'Huillier",
    "miao": "Jianwei Miao",
    "murnane": "Margaret Murnane",
    "nisoli": "Mauro Nisoli",
    "ropers": "Claus Ropers",
}


def load_indexed_papers_for_professor(indexer, prof_key):
    """Load all papers indexed for a professor from ChromaDB."""
    # Load all metadata files and filter by path
    db_path = config.vector_db_path
    papers = []
    for meta_file in sorted(db_path.glob("*_metadata.json")):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            pdf_path = meta.get("paper", {}).get("pdf_path", "")
            if f"postdoc/{prof_key}" in pdf_path.lower() or f"postdoc\\{prof_key}" in pdf_path.lower():
                papers.append(meta)
        except Exception:
            continue
    return papers


def build_figure_gallery(meta, max_figs=8):
    """Build a markdown figure gallery from paper metadata."""
    paper = meta.get("paper", {})
    figures = meta.get("figures", [])
    chunks = meta.get("chunks", [])

    lines = []
    title = paper.get("title", "Unknown")
    year = paper.get("year", "?")
    authors = ", ".join(paper.get("authors", [])[:3])

    lines.append(f"\n### 📄 {title} ({year})")
    lines.append(f"*{authors} — {paper.get('journal', '?')}*\n")

    # Show key findings from text chunks
    abstract_chunks = [c for c in chunks if c.get("text_type") == "abstract"]
    if abstract_chunks:
        lines.append(f"> [!abstract]- Abstract")
        lines.append(f"> {abstract_chunks[0]['text'][:500]}...")
        lines.append("")

    # Figure gallery
    if figures:
        lines.append(f"**Figures ({len(figures)} extracted):**\n")
        for fig in figures[:max_figs]:
            img_path = fig.get("image_path", "")
            if img_path:
                rel_path = Path(img_path).as_posix()
                fig_label = fig.get("figure_label", "Figure")
                caption = fig.get("figure_caption", "")[:200]
                lines.append(f"![[{rel_path}|{fig_label}]]")
                lines.append(f"*{fig_label}: {caption}*\n")

    return "\n".join(lines)


def generate_enrichment(prof_key, dry_run=False):
    """Generate enrichment content for a researcher profile."""
    indexer = VectorIndexer()
    name = PROFESSOR_NAMES.get(prof_key, prof_key)

    # Load papers
    papers = load_indexed_papers_for_professor(indexer, prof_key)
    print(f"\n{'='*60}")
    print(f"{name}: {len(papers)} indexed papers found")
    print(f"{'='*60}")

    if not papers:
        print("  No indexed papers! Run batch_index_postdoc.py first.")
        return

    # Build enrichment content
    enriched = []
    enriched.append(f"\n---\n")
    enriched.append(f"## 📊 论文内容提取与图表（RAG 自动生成 {len(papers)} 篇）\n")
    enriched.append(f"> 以下内容由 RAG 系统从已索引 PDF 中自动提取。图表直接从论文渲染。\n")

    total_figs = 0
    for meta in papers:
        paper = meta.get("paper", {})
        title = paper.get("title", "?")
        n_figs = len(meta.get("figures", []))
        n_chunks = len(meta.get("chunks", []))
        total_figs += n_figs
        print(f"  {title[:70]}... — {n_chunks} chunks, {n_figs} figures")

        gallery = build_figure_gallery(meta)
        enriched.append(gallery)

    enriched.append(f"\n---\n")
    enriched.append(f"> **统计**: {len(papers)} 篇论文, {total_figs} 张图表已提取\n")

    enrichment_text = "\n".join(enriched)

    if dry_run:
        print(f"\n{'='*60}")
        print(f"DRY RUN — would write {len(enrichment_text)} chars to {name}.md")
        print(f"{'='*60}")
        print(enrichment_text[:2000])
        return

    # Read existing profile
    profile_path = POSTDOC_DIR / f"{name}.md"
    if not profile_path.exists():
        print(f"  Profile not found: {profile_path}")
        return

    with open(profile_path, "r", encoding="utf-8") as f:
        existing = f.read()

    # Check if enrichment already exists (avoid duplicate)
    marker = "## 📊 论文内容提取与图表"
    if marker in existing:
        # Replace existing enrichment
        parts = existing.split(marker)
        existing = parts[0]

    # Append enrichment
    updated = existing.rstrip() + "\n" + enrichment_text

    # Update paper count
    import re
    updated = re.sub(r"paper_count: \d+", f"paper_count: {len(papers)}", updated)
    updated = re.sub(r"modified: \d{4}-\d{2}-\d{2}", f"modified: 2026-05-16", updated)

    with open(profile_path, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"  Updated: {profile_path}")
    print(f"  Added: {len(enrichment_text)} chars, {total_figs} figures")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--professor", "-p", help="Professor key")
    parser.add_argument("--all", action="store_true", help="All professors")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()

    if args.all:
        for key in sorted(PROFESSOR_NAMES.keys()):
            try:
                generate_enrichment(key, dry_run=args.dry_run)
            except Exception as e:
                print(f"  ERROR {key}: {e}")
    elif args.professor:
        generate_enrichment(args.professor, dry_run=args.dry_run)
    else:
        print("Usage: --professor NAME or --all")
        print(f"Available: {', '.join(sorted(PROFESSOR_NAMES.keys()))}")


if __name__ == "__main__":
    main()
