#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
学术论文 RAG 系统 - 批量增强图表
使用多模态AI分析图表内容
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from academic_rag.config import config
from academic_rag.db.models import Figure
from academic_rag.processors.multimodal_analyzer import MultimodalAnalyzer, FigureEnhancer
from academic_rag.indexer.vector_indexer import VectorIndexer


def enhance_paper_figures(paper_id: str, paper_info: dict = None):
    """增强指定论文的所有图表"""
    indexer = VectorIndexer()
    analyzer = MultimodalAnalyzer()
    enhancer = FigureEnhancer(analyzer)

    # 获取论文的图表
    figures = indexer.get_figures_by_paper(paper_id)

    if not figures:
        print(f"No figures found for paper: {paper_id}")
        return

    print(f"Found {len(figures)} figures for paper {paper_id}")

    # 增强所有图表
    enhanced_figures = enhancer.enhance_paper_figures(figures, paper_info)

    # 更新元数据
    meta_file = config.vector_db_path / f"{paper_id}_metadata.json"
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # 更新figures
        fig_map = {fig.figure_id: fig for fig in enhanced_figures}
        for i, fig_data in enumerate(metadata.get("figures", [])):
            fig_id = fig_data["figure_id"]
            if fig_id in fig_map:
                enhanced = fig_map[fig_id]
                metadata["figures"][i]["description"] = enhanced.description
                metadata["figures"][i]["key_findings"] = enhanced.key_findings
                metadata["figures"][i]["related_concepts"] = enhanced.related_concepts
                metadata["figures"][i]["figure_type"] = enhanced.figure_type

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"Updated metadata for {paper_id}")

    print(f"\nEnhanced {len(enhanced_figures)} figures")


def enhance_all_figures(domain: str = "", subfield: str = ""):
    """增强所有已索引论文的图表"""
    indexer = VectorIndexer()
    analyzer = MultimodalAnalyzer()
    enhancer = FigureEnhancer(analyzer)

    # 获取所有论文
    papers = indexer.list_papers(domain=domain, subfield=subfield)

    print(f"Found {len(papers)} papers to process")

    for paper in papers:
        figures = indexer.get_figures_by_paper(paper.paper_id)
        if not figures:
            continue

        # 检查是否已有描述
        described = sum(1 for f in figures if f.description)
        if described == len(figures):
            print(f"Skipping {paper.paper_id} - all figures already described")
            continue

        print(f"\nProcessing {paper.title[:50]}...")

        paper_info = {
            "title": paper.title,
            "authors": paper.authors,
            "year": paper.year,
        }

        enhanced = enhancer.enhance_paper_figures(figures, paper_info)

        # 更新元数据
        meta_file = config.vector_db_path / f"{paper.paper_id}_metadata.json"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            fig_map = {fig.figure_id: fig for fig in enhanced}
            for i, fig_data in enumerate(metadata.get("figures", [])):
                fig_id = fig_data["figure_id"]
                if fig_id in fig_map:
                    e = fig_map[fig_id]
                    metadata["figures"][i]["description"] = e.description
                    metadata["figures"][i]["key_findings"] = e.key_findings
                    metadata["figures"][i]["related_concepts"] = e.related_concepts
                    metadata["figures"][i]["figure_type"] = e.figure_type

            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhance figures with AI analysis")
    parser.add_argument("--paper-id", "-p", help="Specific paper ID to enhance")
    parser.add_argument("--domain", "-d", default="", help="Filter by domain")
    parser.add_argument("--subfield", "-s", default="", help="Filter by subfield")
    parser.add_argument("--all", "-a", action="store_true", help="Enhance all papers")

    args = parser.parse_args()

    if args.all:
        enhance_all_figures(domain=args.domain, subfield=args.subfield)
    elif args.paper_id:
        enhance_paper_figures(args.paper_id)
    else:
        parser.print_help()
