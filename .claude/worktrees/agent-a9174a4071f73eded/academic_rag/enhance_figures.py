#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
学术论文 RAG 系统 - 批量增强图表
使用多模态AI分析图表内容，支持并发处理和重索引
"""

import io
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 stdout to avoid GBK codec errors on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Load .env
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(str(_env_path))

from academic_rag.config import config
from academic_rag.db.models import Figure
from academic_rag.processors.multimodal_analyzer import MultimodalAnalyzer, FigureEnhancer
from academic_rag.indexer.vector_indexer import VectorIndexer

_print_lock = Lock()


def _progress(msg: str):
    with _print_lock:
        print(msg, flush=True)


def _enhance_single_paper(paper_info: dict, reindex: bool):
    """Single paper enhancement (runs in worker thread).
    Only creates MultimodalAnalyzer — no model loading needed.
    """
    paper_id = paper_info["paper_id"]
    figures_data = paper_info["figures"]
    meta_file = paper_info["meta_file"]

    analyzer = MultimodalAnalyzer()
    enhancer = FigureEnhancer(analyzer)

    # Reconstruct Figure objects from stored data
    figures = [Figure.from_dict(fd) for fd in figures_data]
    undescribed = [f for f in figures if not f.description]

    enhanced = []
    for fig in undescribed:
        try:
            analysis = enhancer.enhance_figure(fig, {
                "title": paper_info.get("title", ""),
                "authors": paper_info.get("authors", []),
                "year": paper_info.get("year", 0),
            })
            if analysis and analysis.description:
                enhanced.append(analysis)
                _progress(f"  [{paper_id[:12]}] {fig.figure_label}: OK "
                          f"({len(enhanced)}/{len(undescribed)})")
        except Exception as e:
            _progress(f"  [{paper_id[:12]}] {fig.figure_label}: FAIL — {e}")

    if not enhanced:
        return {"paper_id": paper_id, "enhanced": 0, "failed": len(undescribed)}

    # Update metadata JSON
    if meta_file:
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        fig_map = {fig.figure_id: fig for fig in enhanced}
        for i, fig_data in enumerate(metadata.get("figures", [])):
            fid = fig_data["figure_id"]
            if fid in fig_map:
                e = fig_map[fid]
                metadata["figures"][i]["description"] = e.description
                metadata["figures"][i]["key_findings"] = e.key_findings
                metadata["figures"][i]["related_concepts"] = e.related_concepts
                metadata["figures"][i]["figure_type"] = e.figure_type
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {"paper_id": paper_id, "enhanced": len(enhanced),
            "failed": len(undescribed) - len(enhanced)}


def enhance_all_figures(domain: str = "", subfield: str = "", workers: int = 4,
                         reindex: bool = True):
    """并发增强所有已索引论文的图表"""
    indexer = VectorIndexer()
    papers = indexer.list_papers(domain=domain, subfield=subfield)

    # Pre-load all figure data from metadata JSONs (no model loading per worker)
    paper_tasks = []
    total_undescribed = 0
    for paper in papers:
        meta_file = config.vector_db_path / f"{paper.paper_id}_metadata.json"
        if not meta_file.exists():
            continue
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        figures_data = metadata.get("figures", [])
        undescribed = sum(1 for fd in figures_data if not fd.get("description"))
        if undescribed > 0:
            total_undescribed += undescribed
            paper_tasks.append({
                "paper_id": paper.paper_id,
                "title": paper.title,
                "authors": paper.authors,
                "year": paper.year,
                "figures": figures_data,
                "meta_file": meta_file,
            })

    if total_undescribed == 0:
        print("All figures already enhanced. Nothing to do.")
        return

    print(f"Found {len(papers)} papers, {total_undescribed} undescribed figures")
    print(f"Using {workers} workers\n")

    t0 = time.time()
    done = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_enhance_single_paper, task, reindex): task
                   for task in paper_tasks}
        for f in as_completed(futures):
            try:
                result = f.result()
                done += result["enhanced"]
                failed += result["failed"]
                pct = done / max(total_undescribed, 1) * 100
                _progress(f"[{done}/{total_undescribed} {pct:.0f}%] "
                          f"{result['paper_id'][:12]} "
                          f"+{result['enhanced']}/{result['enhanced'] + result['failed']}")
            except Exception as e:
                pid = futures[f].get("paper_id", "?")
                _progress(f"ERROR {pid}: {e}")

    elapsed = time.time() - t0
    print(f"\nDone. {done} enhanced, {failed} failed in {elapsed:.0f}s "
          f"({done / max(elapsed, 1):.1f} figs/s)")

    # Re-index caption_collection with new descriptions
    if reindex and done > 0:
        print("\nRe-indexing caption_collection with enhanced descriptions...")
        idx2 = VectorIndexer()
        for paper in papers:
            paper_figs = idx2.get_figures_by_paper(paper.paper_id)
            if paper_figs:
                idx2.caption_indexer.index_captions(paper_figs, paper.paper_id)
        print("Re-indexing complete.")


def enhance_paper_figures(paper_id: str, paper_info: dict = None, reindex: bool = True):
    """增强指定论文的所有图表（单进程，用于测试）"""
    indexer = VectorIndexer()
    figures = indexer.get_figures_by_paper(paper_id)
    if not figures:
        print(f"No figures for {paper_id}")
        return 0

    undescribed = [f for f in figures if not f.description]
    if not undescribed:
        print(f"All {len(figures)} figures already described")
        return 0

    print(f"Enhancing {len(undescribed)}/{len(figures)} figures for {paper_id}...")
    analyzer = MultimodalAnalyzer()
    enhancer = FigureEnhancer(analyzer)
    enhanced = enhancer.enhance_paper_figures(undescribed, paper_info)

    # 更新元数据
    meta_file = config.vector_db_path / f"{paper_id}_metadata.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        fig_map = {fig.figure_id: fig for fig in enhanced}
        for i, fig_data in enumerate(metadata.get("figures", [])):
            fid = fig_data["figure_id"]
            if fid in fig_map:
                e = fig_map[fid]
                metadata["figures"][i]["description"] = e.description
                metadata["figures"][i]["key_findings"] = e.key_findings
                metadata["figures"][i]["related_concepts"] = e.related_concepts
                metadata["figures"][i]["figure_type"] = e.figure_type
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    if reindex and enhanced:
        all_figs = indexer.get_figures_by_paper(paper_id)
        indexer.caption_indexer.index_captions(all_figs, paper_id)

    return len(enhanced)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhance figures with AI analysis")
    parser.add_argument("--paper-id", "-p", help="Specific paper ID to enhance")
    parser.add_argument("--domain", "-d", default="", help="Filter by domain")
    parser.add_argument("--subfield", "-s", default="", help="Filter by subfield")
    parser.add_argument("--all", "-a", action="store_true", help="Enhance all papers")
    parser.add_argument("--workers", "-w", type=int, default=4,
                        help="Number of concurrent workers (default: 4)")
    parser.add_argument("--no-reindex", action="store_true",
                        help="Skip re-indexing captions after enhancement")

    args = parser.parse_args()

    if args.all:
        enhance_all_figures(
            domain=args.domain, subfield=args.subfield,
            workers=args.workers, reindex=not args.no_reindex
        )
    elif args.paper_id:
        enhance_paper_figures(args.paper_id, reindex=not args.no_reindex)
    else:
        parser.print_help()
