#!/usr/bin/env python3
"""
PDF 解析模块 v1.0
从 Zotero 论文 PDF 中提取图片、文本、图注

依赖: PyMuPDF (已安装)
使用:
    python pdf_extract.py extract_images "Author2024" [--page N]
    python pdf_extract.py list_figures "Author2024"
    python pdf_extract.py text "Author2024" [--pages 1-5]
"""

import sys
import os
import requests
import json
import shutil
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Windows 编码兼容
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 清除代理
for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(v, None)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("WARNING: PyMuPDF not installed. Run: pip install PyMuPDF")

ZOTERO_API_KEY = os.getenv("ZOTERO_API_KEY", "gKXxzW93bZAWlbs0DCN0KVbj")
ZOTERO_USER_ID = os.getenv("ZOTERO_USER_ID", "20242032")
ZOTERO_API = f"https://api.zotero.org/users/{ZOTERO_USER_ID}"

# 全局缓存
_pdf_cache = {}
_attachment_cache = {}


def zotero_get_item(item_key: str) -> dict:
    """获取 Zotero item 元数据"""
    for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(v, None)
    headers = {"Zotero-API-Key": ZOTERO_API_KEY, "Zotero-API-Version": "3"}
    url = f"{ZOTERO_API}/items/{item_key}"
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def zotero_get_item_children(item_key: str) -> List[dict]:
    """获取 item 的子项（附件）"""
    for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(v, None)
    headers = {"Zotero-API-Key": ZOTERO_API_KEY, "Zotero-API-Version": "3"}
    url = f"{ZOTERO_API}/items/{item_key}/children"
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def zotero_get_attachment_info(attachment_key: str) -> dict:
    """获取附件（PDF）下载链接"""
    for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(v, None)
    headers = {"Zotero-API-Key": ZOTERO_API_KEY, "Zotero-API-Version": "3"}
    url = f"{ZOTERO_API}/items/{attachment_key}"
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    item = r.json()
    # 附件的 link mode 属性
    return {
        "key": item.get("key", ""),
        "filename": item.get("filename", ""),
        "contentType": item.get("contentType", ""),
        "itemType": item.get("itemType", ""),
        "download_url": item.get("links", {}).get("enclosure", {}).get("href", ""),
        "size": item.get("links", {}).get("enclosure", {}).get("length", 0),
    }


def find_pdf_in_zotero(doi: str = None, title: str = None) -> Optional[str]:
    """
    通过 DOI 或标题在 Zotero 中搜索 PDF 附件
    返回 PDF 本地路径（如果已同步）或下载 URL
    """
    for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(v, None)

    headers = {"Zotero-API-Key": ZOTERO_API_KEY, "Zotero-API-Version": "3"}

    # 搜索
    params = {"limit": 5}
    if doi:
        params["q"] = doi
        params["qmode"] = "everything"
    elif title:
        params["q"] = title
        params["qmode"] = "titleCreatorYear"
    else:
        return None

    r = requests.get(f"{ZOTERO_API}/items", headers=headers, params=params, timeout=15)
    r.raise_for_status()
    items = r.json()

    for item in items:
        # 找附件
        if item.get("itemType") == "attachment":
            continue
        key = item.get("key", "")
        children = zotero_get_item_children(key)
        for child in children:
            if child.get("itemType") == "attachment" and child.get("filename", "").endswith(".pdf"):
                return child.get("key", ""), child.get("filename", ""), child.get("download_url", "")

    return None


def extract_images_from_pdf(pdf_path: str, output_dir: str = "DHL/figures/extracted", dpi: int = 150) -> List[Dict]:
    """
    从 PDF 提取所有图片
    返回: [{"page": 1, "index": 0, "path": "fig1.png", "caption": "..."}, ...]
    """
    if not PYMUPDF_AVAILABLE:
        print("ERROR: PyMuPDF not installed")
        return []

    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    results = []

    for page_num, page in enumerate(doc):
        images = page.get_images(full=True)
        for img_idx, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # 生成文件名
            img_hash = hashlib.md5(image_bytes[:8192]).hexdigest()[:8]
            filename = f"p{page_num+1:03d}_img{img_idx+1}_{img_hash}.{image_ext}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            # 尝试提取图注（相邻文字块）
            caption = ""
            text_blocks = page.get_text("dict")["blocks"]
            for block in text_blocks:
                if block.get("type") == 0:  # text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            txt = span["text"].strip()
                            if len(txt) > 5 and len(txt) < 300:
                                caption += txt + " "

            caption = caption.strip()[:200]

            results.append({
                "page": page_num + 1,
                "index": img_idx + 1,
                "path": filepath,
                "relative_path": f"figures/extracted/{filename}",
                "caption": caption,
                "width": base_image["width"],
                "height": base_image["height"],
                "ext": image_ext,
                "size_kb": len(image_bytes) // 1024,
            })

    doc.close()
    return results


def extract_text_from_pdf(pdf_path: str, pages: Optional[Tuple[int, int]] = None) -> str:
    """
    从 PDF 提取文本
    pages: (start, end) 1-indexed, None 表示全部
    """
    if not PYMUPDF_AVAILABLE:
        print("ERROR: PyMuPDF not installed")
        return ""

    doc = fitz.open(pdf_path)
    texts = []

    start = (pages[0] - 1) if pages else 0
    end = pages[1] if pages else len(doc)

    for page_num in range(start, min(end, len(doc))):
        page = doc[page_num]
        text = page.get_text("text")
        texts.append(f"=== Page {page_num + 1} ===\n{text}")

    doc.close()
    return "\n".join(texts)


def extract_figure_with_context(pdf_path: str, page_num: int, figure_index: int, output_dir: str) -> Dict:
    """
    提取特定页面的特定图片及其上下文（图片上方/下方的文字）
    page_num: 1-indexed
    figure_index: 1-indexed
    """
    if not PYMUPDF_AVAILABLE:
        return {}

    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]  # 0-indexed

    images = page.get_images(full=True)
    if figure_index > len(images):
        return {}

    img = images[figure_index - 1]
    xref = img[0]
    base_image = doc.extract_image(xref)
    image_bytes = base_image["image"]
    image_ext = base_image["ext"]

    img_hash = hashlib.md5(image_bytes[:8192]).hexdigest()[:8]
    filename = f"p{page_num:03d}_fig{figure_index}_{img_hash}.{image_ext}"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "wb") as f:
        f.write(image_bytes)

    # 提取图片周围的文本作为 caption
    img_rect = None
    for img_info in page.get_images(full=True):
        if img_info[0] == xref:
            # 获取图片在页面上的位置
            img_list = page.get_image_info()
            for info in img_list:
                if info.get("xref") == xref:
                    img_rect = fitz.Rect(info["bbox"])
                    break
            break

    caption = ""
    if img_rect:
        # 收集图片下方最近的文字块
        text_blocks = page.get_text("dict")["blocks"]
        for block in text_blocks:
            if block.get("type") == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        bbox = fitz.Rect(span["bbox"])
                        # 检查文字是否在图片下方 0-100pt
                        if bbox.y0 > img_rect.y1 and bbox.y0 < img_rect.y1 + 100:
                            caption += span["text"].strip() + " "

    doc.close()
    return {
        "page": page_num,
        "figure": figure_index,
        "path": filepath,
        "relative_path": f"figures/extracted/{filename}",
        "caption": caption.strip()[:300],
        "width": base_image["width"],
        "height": base_image["height"],
    }


def extract_figures_from_doi(doi: str, output_dir: str = "DHL/figures/extracted", max_pages: int = 10) -> List[Dict]:
    """
    完整流程：通过 DOI 找到 PDF → 提取所有图片
    """
    print(f">> Searching Zotero for DOI: {doi}")

    # 1. Zotero 搜索
    result = find_pdf_in_zotero(doi=doi)
    if not result:
        print(f"    No PDF found in Zotero for DOI: {doi}")
        return []

    attachment_key, filename, download_url = result
    print(f"    Found: {filename} (key={attachment_key})")

    # 2. 获取 PDF 实际文件路径
    # Zotero 本地同步后路径通常是 ~/Zotero/storage/{attachment_key}/
    zotero_storage = find_zotero_storage_path()
    pdf_path = os.path.join(zotero_storage, attachment_key, filename)

    if not os.path.exists(pdf_path):
        # 尝试其他常见路径模式
        possible_paths = [
            os.path.join(zotero_storage, attachment_key, filename),
            os.path.join(zotero_storage, attachment_key, f"{attachment_key}.pdf"),
            os.path.join(zotero_storage, filename),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                pdf_path = p
                break
        else:
            print(f"    PDF file not found locally: {pdf_path}")
            print(f"    Download URL: {download_url}")
            return []

    print(f">> Extracting images from: {pdf_path}")
    figures = extract_images_from_pdf(pdf_path, output_dir)

    for fig in figures:
        print(f"    [Page {fig['page']}] Fig {fig['index']}: {fig['relative_path']} ({fig['width']}x{fig['height']}, {fig['size_kb']}KB)")
        if fig['caption']:
            print(f"        Caption: {fig['caption'][:100]}...")

    return figures


def find_zotero_storage_path() -> str:
    """查找 Zotero 存储路径"""
    # 常见路径
    candidates = [
        os.path.expanduser("~/Zotero/storage"),
        "C:/Users/Mac/Zotero/storage",
        "D:/Zotero/storage",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


def list_all_figures(doi: str = None, title: str = None, output_dir: str = "DHL/figures/extracted") -> List[Dict]:
    """列出某论文的所有图片（不提取，只获取信息）"""
    pass  # 类似上面的流程，但只 scan 不保存


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "extract_images":
        # python pdf_extract.py extract_images "10.1088/1361-6463/50/4/043001"
        arg = sys.argv[2] if len(sys.argv) > 2 else ""
        if not arg:
            print("Usage: pdf_extract.py extract_images <doi_or_title>")
            sys.exit(1)
        doi = arg if "10." in arg else None
        figures = extract_figures_from_doi(doi or arg, output_dir="DHL/figures/extracted")
        print(f"\n>> Total figures extracted: {len(figures)}")

    elif cmd == "text":
        # python pdf_extract.py text "10.xxxx" --pages 1-5
        arg = sys.argv[2] if len(sys.argv) > 2 else ""
        pages = None
        for a in sys.argv:
            if a.startswith("--pages"):
                idx = sys.argv.index(a)
                if idx + 1 < len(sys.argv):
                    p = sys.argv[idx + 1]
                    if "-" in p:
                        s, e = p.split("-")
                        pages = (int(s), int(e))
        if not arg:
            print("Usage: pdf_extract.py text <doi> [--pages 1-5]")
            sys.exit(1)
        doi = arg if "10." in arg else None

        result = find_pdf_in_zotero(doi=doi)
        if not result:
            print(f"No PDF found for: {arg}")
            sys.exit(1)
        attachment_key, filename, _ = result

        zotero_storage = find_zotero_storage_path()
        pdf_path = os.path.join(zotero_storage, attachment_key, filename)
        if not os.path.exists(pdf_path):
            print(f"PDF not found: {pdf_path}")
            sys.exit(1)

        text = extract_text_from_pdf(pdf_path, pages=pages)
        print(text[:5000])

    elif cmd == "find":
        # python pdf_extract.py find "10.xxxx"
        arg = sys.argv[2] if len(sys.argv) > 2 else ""
        result = find_pdf_in_zotero(doi=arg if "10." in arg else None, title=arg if "10." not in arg else None)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
