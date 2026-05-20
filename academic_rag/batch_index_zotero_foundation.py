"""
批量索引 Zotero "学科基础" 集合 PDF 到 RAG 系统
使用 BGE-M3 (文本) + CLIP (图像) 双模型索引

Usage:
    python academic_rag/batch_index_zotero_foundation.py
    python academic_rag/batch_index_zotero_foundation.py --collection "06 超材料与纳米光学"
    python academic_rag/batch_index_zotero_foundation.py --figures-only
    python academic_rag/batch_index_zotero_foundation.py --regenerate
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from academic_rag.processors.pdf_processor import PDFProcessor
from academic_rag.indexer.vector_indexer import VectorIndexer
from academic_rag.indexer.figure_indexer import FigureIndexer
from academic_rag.db.models import Paper, Figure
from academic_rag.config import config

# Zotero API 配置
ZOTERO_API_KEY = "gKXxzW93bZAWlbs0DCN0KVbj"
ZOTERO_USER_ID = "20242032"

# 子集合 key → (domain, subfield, 中文名)
SUBCOLLECTION_MAP = {
    "8B94ZY5F": ("physics", "electromagnetic", "01 电磁地基"),
    "98YX4QVB": ("optics", "wave_optics", "02 波动光学"),
    "773C6X5I": ("optics", "quantum_optics", "03 量子光学"),
    "BHGS5HE7": ("optics", "laser_physics", "04 激光物理"),
    "RXZT7XPF": ("physics", "semiconductor", "05 半导体物理"),
    "4WRFHU2Y": ("optics", "nanophotonics", "06 超材料与纳米光学"),
    "BAZQDAUH": ("engineering", "photonics", "07 工程基础"),
}


def fetch_collection_items(collection_key: str) -> List[Dict]:
    """通过 Zotero API 获取集合内所有条目"""
    import urllib.request
    import urllib.error

    url = f"https://api.zotero.org/users/{ZOTERO_USER_ID}/collections/{collection_key}/items?limit=100&format=json"
    req = urllib.request.Request(url, headers={"Zotero-API-Key": ZOTERO_API_KEY})

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            items = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"  API error for {collection_key}: {e}")
        return []

    # 过滤掉附件和笔记（只要父条目）
    return [it for it in items if it.get("data", {}).get("itemType") not in ("attachment", "note")]


# Zotero 本地存储根目录
ZOTERO_STORAGE = Path(r"E:\PostGraduate\Science_softwares\Zotero\data\storage")


def get_best_pdf(item: Dict) -> Optional[str]:
    """从条目的 attachments 中选择最佳 PDF 路径

    Zotero Web API 不暴露本地路径（path 字段为空），
    但附件 key 对应 storage 子文件夹，glob 查找 PDF。

    优先级: linkMode=0 (本地导入) > linkMode=1 (imported_url)
    """
    import urllib.request

    data = item.get("data", {})
    key = data.get("key", "")
    url = f"https://api.zotero.org/users/{ZOTERO_USER_ID}/items/{key}/children?format=json"
    req = urllib.request.Request(url, headers={"Zotero-API-Key": ZOTERO_API_KEY})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            children = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    pdfs = []
    for child in children:
        cd = child.get("data", {})
        if cd.get("itemType") == "attachment" and cd.get("contentType") == "application/pdf":
            att_key = cd.get("key", "")
            link_mode = cd.get("linkMode", 1)

            # 先检查 API 返回的 path（linkMode=0 时可能有值）
            api_path = cd.get("path", "")
            if api_path and Path(api_path).exists():
                pdfs.append((link_mode, api_path))
                continue

            # 用 attachment key 查找 storage 文件夹中的 PDF
            storage_dir = ZOTERO_STORAGE / att_key
            if storage_dir.exists():
                found = list(storage_dir.glob("*.pdf"))
                if found:
                    pdfs.append((link_mode, str(found[0])))

    if not pdfs:
        return None

    # linkMode=0 (imported_file) 优先，再按文件大小（大的通常是全文）
    pdfs.sort(key=lambda x: (x[0], -Path(x[1]).stat().st_size if Path(x[1]).exists() else 0))
    return pdfs[0][1]


def index_figures_only_for_collection(indexer, collection_key=None):
    """Re-index CLIP embeddings for papers already indexed."""
    db_path = config.vector_db_path
    meta_files = sorted(db_path.glob("*_metadata.json"))
    if not meta_files:
        print("No metadata files found.")
        return []

    summary = []
    for meta_file in meta_files:
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

        paper = Paper.from_dict(meta["paper"])
        figures = [Figure.from_dict(fd) for fd in meta.get("figures", [])]

        if not figures:
            continue

        n = indexer.index_paper_figures(paper, figures)
        summary.append({"paper_id": paper.paper_id, "title": paper.title[:60], "figures_indexed": n})
        print(f"  CLIP: {paper.title[:60]} → {n} embeddings")

    return summary


def index_collection(
    collection_key: str,
    domain: str,
    subfield: str,
    name_cn: str,
    processor: PDFProcessor,
    indexer: VectorIndexer,
    regenerate: bool = False,
):
    """索引单个子集合的所有 PDF"""
    print(f"\n{'='*60}")
    print(f"Collection: {name_cn} ({domain}/{subfield})")
    print(f"{'='*60}")

    items = fetch_collection_items(collection_key)
    if not items:
        print(f"  No items found.")
        return {"collection": name_cn, "total": 0, "indexed": 0, "skipped": 0, "failed": 0}

    print(f"  Found {len(items)} items. Resolving PDF paths...")

    indexed = 0
    skipped = 0
    failed = 0

    for i, item in enumerate(items):
        data = item.get("data", {})
        title = data.get("title", "Unknown")
        item_key = data.get("key", "")

        pdf_path = get_best_pdf(item)
        if not pdf_path:
            print(f"  [{i+1}/{len(items)}] NO PDF: {title[:60]}")
            skipped += 1
            continue

        if not Path(pdf_path).exists():
            print(f"  [{i+1}/{len(items)}] MISSING: {pdf_path[:80]}")
            skipped += 1
            continue

        # 检查是否已索引
        paper_id = Path(pdf_path).stem
        if not regenerate and indexer._is_paper_indexed(paper_id):
            print(f"  [{i+1}/{len(items)}] SKIP: {title[:60]}")
            skipped += 1
            continue

        try:
            # PDF 处理
            paper, figures, chunks, tables = processor.process(
                pdf_path, domain=domain, subfield=subfield
            )

            if not chunks:
                print(f"  [{i+1}/{len(items)}] EMPTY: {title[:60]} (no text chunks)")
                skipped += 1
                continue

            # 文本索引 (BGE-M3)
            if indexer.index_paper(paper, figures, chunks):
                # 图像索引 (CLIP)
                n_fig = 0
                if indexer.figure_indexer and figures:
                    n_fig = indexer.index_paper_figures(paper, figures)

                indexed += 1
                print(
                    f"  [{i+1}/{len(items)}] OK: {title[:60]} "
                    f"[{len(chunks)} chunks, {len(figures)} figs, {n_fig} CLIP]"
                )
            else:
                failed += 1
                print(f"  [{i+1}/{len(items)}] FAIL: {title[:60]}")

        except Exception as e:
            failed += 1
            print(f"  [{i+1}/{len(items)}] ERROR: {title[:60]} — {e}")

    print(f"  Result: {indexed} indexed, {skipped} skipped, {failed} failed")
    return {
        "collection": name_cn,
        "domain": domain,
        "subfield": subfield,
        "total": len(items),
        "indexed": indexed,
        "skipped": skipped,
        "failed": failed,
    }


def main():
    parser = argparse.ArgumentParser(description="Batch index Zotero '学科基础' collection into RAG")
    parser.add_argument(
        "--collection", "-c",
        help="Index specific subcollection only (e.g. '06 超材料与纳米光学')",
    )
    parser.add_argument("--figures-only", action="store_true", help="Only re-index CLIP figure embeddings")
    parser.add_argument("--regenerate", "-r", action="store_true", help="Re-index even if already indexed")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # 选择子集合
    collections = SUBCOLLECTION_MAP
    if args.collection:
        collections = {
            k: v for k, v in collections.items() if args.collection in v[2]
        }
        if not collections:
            print(f"Collection '{args.collection}' not found. Available:")
            for k, v in SUBCOLLECTION_MAP.items():
                print(f"  {v[2]} (key={k})")
            return

    print("Loading BGE-M3 + CLIP models...")
    figure_indexer = FigureIndexer()
    processor = PDFProcessor(extract_images=True, image_dpi=300)
    indexer = VectorIndexer(figure_indexer=figure_indexer)
    print("Models loaded.\n")

    if args.figures_only:
        print("FIGURES-ONLY mode: re-indexing CLIP embeddings")
        start = time.time()
        summary = index_figures_only_for_collection(indexer)
        elapsed = time.time() - start
        total_figs = sum(r["figures_indexed"] for r in summary)
        print(f"\nCLIP COMPLETE: {len(summary)} papers, {total_figs} embeddings, {elapsed:.1f}s")
        return

    print(f"Processing {len(collections)} subcollection(s).")

    start = time.time()
    results = []

    for col_key, (domain, subfield, name_cn) in collections.items():
        result = index_collection(
            col_key, domain, subfield, name_cn,
            processor, indexer, regenerate=args.regenerate,
        )
        results.append(result)

    elapsed = time.time() - start
    total_indexed = sum(r["indexed"] for r in results)
    total_items = sum(r["total"] for r in results)
    total_skipped = sum(r["skipped"] for r in results)
    total_failed = sum(r["failed"] for r in results)

    print(f"\n{'='*60}")
    print(f"BATCH INDEX COMPLETE")
    print(f"  Collections: {len(results)}")
    print(f"  Items: {total_items} total")
    print(f"  Indexed: {total_indexed}")
    print(f"  Skipped: {total_skipped}")
    print(f"  Failed: {total_failed}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"{'='*60}")

    for r in results:
        print(f"  {r['collection']}: {r['indexed']}/{r['total']} indexed, {r['skipped']} skip, {r['failed']} fail")


if __name__ == "__main__":
    main()
