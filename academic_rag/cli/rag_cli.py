"""
学术论文 RAG 系统 - CLI工具
Phase 5: 命令行接口
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from academic_rag.config import config
from academic_rag.processors.pdf_processor import PDFProcessor, BatchProcessor
from academic_rag.indexer.vector_indexer import VectorIndexer
from academic_rag.api.search_api import SearchAPI


def cmd_index(args):
    """索引PDF论文"""
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        return 1

    # 处理PDF
    processor = PDFProcessor(extract_images=True, image_dpi=300)
    paper, figures, chunks = processor.process(
        pdf_path,
        domain=args.domain or "",
        subfield=args.subfield or "",
    )

    # 创建索引器
    indexer = VectorIndexer()
    indexer.index_paper(paper, figures, chunks, regenerate=args.regenerate)

    print(f"\nIndexed: {paper.title}")
    print(f"  Paper ID: {paper.paper_id}")
    print(f"  Domain: {paper.domain}/{paper.subfield}")
    print(f"  Figures: {len(figures)}")
    print(f"  Text chunks: {len(chunks)}")

    return 0


def cmd_index_dir(args):
    """批量索引目录中的PDF"""
    dir_path = Path(args.directory)

    if not dir_path.exists():
        print(f"Error: Directory not found: {dir_path}")
        return 1

    processor = PDFProcessor(extract_images=True, image_dpi=300)
    batch = BatchProcessor(processor)

    results = batch.process_directory(
        dir_path,
        domain=args.domain or "",
        subfield=args.subfield or "",
        recursive=args.recursive,
    )

    # 索引所有论文
    indexer = VectorIndexer()
    success_count = 0

    for paper, figures, chunks in results:
        if indexer.index_paper(paper, figures, chunks, regenerate=args.regenerate):
            success_count += 1

    print(f"\nIndexed {success_count}/{len(results)} papers")
    return 0


def cmd_search(args):
    """搜索论文内容"""
    indexer = VectorIndexer()
    api = SearchAPI(indexer)

    results = api.search(
        query=args.query,
        domain=args.domain or "",
        subfield=args.subfield or "",
        top_k=args.top_k,
    )

    print(f"\nFound {results['total']} results for: {args.query}")
    print(f"Filters: domain={args.domain or 'all'}, subfield={args.subfield or 'all'}")
    print()

    for i, r in enumerate(results["results"], 1):
        paper = r["paper"]
        print(f"{i}. [{paper['title'][:60]}...]")
        print(f"   Authors: {paper['authors']} ({paper['year']})")
        print(f"   Similarity: {r['similarity']:.3f}")
        print(f"   Highlight: {r['highlight'][:100]}...")

        if r.get("figure"):
            fig = r["figure"]
            print(f"   Figure: {fig['figure_label']} (p.{fig['page_num']})")
            print(f"   Caption: {fig['figure_caption'][:80]}...")

        print()

    return 0


def cmd_find_figure(args):
    """为知识点查找合适配图"""
    indexer = VectorIndexer()
    api = SearchAPI(indexer)

    result = api.find_figure_for_knowledge_point(
        knowledge_point=args.concept,
        domain=args.domain or "optics",
        subfield=args.subfield or "terahertz",
    )

    if not result:
        print(f"No figure found for: {args.concept}")
        return 1

    print(f"\nBest match for: {args.concept}")
    print(f"Image: {result['image_path']}")
    print(f"\nSource:")
    print(f"  Paper: {result['source']['paper_title']}")
    print(f"  Authors: {result['source']['authors']}")
    print(f"  Year: {result['source']['year']}")
    print(f"  Figure: {result['source']['figure_label']}")
    print(f"  Caption: {result['source']['figure_caption']}")
    print(f"\nUsage Guide:")
    print(f"  {result['usage_guide']['description']}")
    print(f"  Key findings: {result['usage_guide']['key_findings']}")
    print(f"\nContext (from paper):")
    print(f"  Section: {result['context']['section']}")
    print(f"  Page: {result['context']['page']}")
    print(f"  Quote: {result['context']['text_quote'][:200]}...")

    # 输出Obsidian引用格式
    print(f"\nObsidian引用:")
    print(f"  {result['obsidian_ref']}")

    return 0


def cmd_list(args):
    """列出已索引的论文"""
    indexer = VectorIndexer()

    papers = indexer.list_papers(domain=args.domain or "", subfield=args.subfield or "")

    if not papers:
        print("No papers indexed yet.")
        return 0

    print(f"\nIndexed papers ({len(papers)}):")
    for p in papers:
        print(f"  [{p.paper_id}] {p.title[:50]}...")
        print(f"       {p.authors[:2] if p.authors else 'Unknown'} ({p.year}) - {p.domain}/{p.subfield}")

    return 0


def cmd_stats(args):
    """显示统计信息"""
    indexer = VectorIndexer()
    stats = indexer.get_stats()

    print("\n=== Academic RAG Statistics ===")
    print(f"Total papers: {stats['total_papers']}")
    print(f"Total text chunks: {stats['total_chunks']}")
    print(f"Total figures: {stats['total_figures']}")
    print(f"Embedding model: {stats['embedding_model']}")
    print(f"Database path: {stats['db_path']}")

    return 0


def cmd_figures(args):
    """列出论文的图表"""
    indexer = VectorIndexer()
    api = SearchAPI(indexer)

    figures = api.get_paper_figures(
        paper_id=args.paper_id,
        concept_filter=args.filter or "",
    )

    if not figures:
        print(f"No figures found for paper: {args.paper_id}")
        return 1

    print(f"\nFigures in paper {args.paper_id} ({len(figures)}):")
    for i, fig in enumerate(figures, 1):
        print(f"  {i}. {fig['figure_label']} (p.{fig['page_num']})")
        print(f"     Type: {fig['figure_type']}")
        print(f"     Caption: {fig['figure_caption'][:80]}...")
        print(f"     Path: {fig['image_path']}")
        print()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Academic Paper RAG CLI - 学术论文检索增强生成系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # index - 索引单个PDF
    index_parser = subparsers.add_parser("index", help="Index a single PDF paper")
    index_parser.add_argument("pdf", help="Path to PDF file")
    index_parser.add_argument("--domain", "-d", default="", help="Domain (optics/physics/etc)")
    index_parser.add_argument("--subfield", "-s", default="", help="Subfield (terahertz/metasurface/etc)")
    index_parser.add_argument("--regenerate", "-r", action="store_true", help="Regenerate if exists")
    index_parser.set_defaults(func=cmd_index)

    # index-dir - 批量索引
    index_dir_parser = subparsers.add_parser("index-dir", help="Index all PDFs in a directory")
    index_dir_parser.add_argument("directory", help="Directory containing PDFs")
    index_dir_parser.add_argument("--domain", "-d", default="", help="Default domain")
    index_dir_parser.add_argument("--subfield", "-s", default="", help="Default subfield")
    index_dir_parser.add_argument("--recursive", action="store_true", default=True, help="Recursive search")
    index_dir_parser.add_argument("--regenerate", "-r", action="store_true", help="Regenerate if exists")
    index_dir_parser.set_defaults(func=cmd_index_dir)

    # search - 搜索
    search_parser = subparsers.add_parser("search", help="Search paper content")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--domain", "-d", default="", help="Filter by domain")
    search_parser.add_argument("--subfield", "-s", default="", help="Filter by subfield")
    search_parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    search_parser.set_defaults(func=cmd_search)

    # find-figure - 查找配图
    find_fig_parser = subparsers.add_parser("find-figure", help="Find figure for knowledge point")
    find_fig_parser.add_argument("concept", help="Knowledge point concept")
    find_fig_parser.add_argument("--domain", "-d", default="optics", help="Domain")
    find_fig_parser.add_argument("--subfield", "-s", default="terahertz", help="Subfield")
    find_fig_parser.set_defaults(func=cmd_find_figure)

    # list - 列出论文
    list_parser = subparsers.add_parser("list", help="List indexed papers")
    list_parser.add_argument("--domain", "-d", default="", help="Filter by domain")
    list_parser.add_argument("--subfield", "-s", default="", help="Filter by subfield")
    list_parser.set_defaults(func=cmd_list)

    # stats - 统计
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.set_defaults(func=cmd_stats)

    # figures - 列出图表
    fig_parser = subparsers.add_parser("figures", help="List figures in a paper")
    fig_parser.add_argument("paper_id", help="Paper ID")
    fig_parser.add_argument("--filter", "-f", default="", help="Filter by concept")
    fig_parser.set_defaults(func=cmd_figures)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
