"""
从 Zotero MCP 导入论文 PDF 到 RAG 处理工作区

直接复制 Zotero storage 中的 PDF 文件，不通过 MCP 下载。
用法:
    python academic_rag/import_from_zotero.py --professor krausz
    python academic_rag/import_from_zotero.py --all-postdoc
    python academic_rag/import_from_zotero.py --professor krausz --dry-run
"""

import argparse
import json
import shutil
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PAPERS_ROOT = PROJECT_ROOT / "academic_rag" / "papers"
MCP_URL = "http://127.0.0.1:23120/mcp"

POSTDOC_COLLECTIONS = {
    "krausz": "RYD9JI2U",
    "lhuillier": "CP83C6VV",
    "keller": "P8QNDVZI",
    "nisoli": "5TU3IPGM",
    "ropers": "64XUBNXA",
    "murnane": "9A6A63UM",
    "kaertner": "T9XRF88Q",
    "baum": "ECGLT9Q6",
    "kling": "V782UP9W",
    "hommelhoff": "BZWKSN9N",
    "huber": "DMMMLJ28",
    "chang": "4W3A4ZQE",
    "leone": "ZALV9WIK",
    "gedik": "LA976NQY",
    "miao": "2D7JR5YV",
}


class ZoteroMCPClient:
    """Lightweight Zotero MCP HTTP client."""

    def __init__(self, mcp_url: str = MCP_URL):
        self.mcp_url = mcp_url
        self.session_id = f"rag-import-{int(time.time())}"
        self._req_id = 0

    def _call(self, method: str, params: dict) -> dict:
        self._req_id += 1
        body = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._req_id,
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.mcp_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Mcp-Session-Id": self.session_id,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"MCP HTTP {e.code}: {body[:500]}")

    def init(self):
        result = self._call("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "rag-import", "version": "1.0"},
        })
        print(f"Connected: {result['result']['serverInfo']['name']}")
        return self

    def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        result = self._call("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        return result.get("result", {})

    @staticmethod
    def _unwrap_content(content: list | str | dict) -> list | dict:
        """
        MCP returns content as [{"type":"text","text":"<JSON>"}].
        Unwrap text blocks and parse JSON strings.
        """
        if isinstance(content, list):
            result = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    try:
                        parsed = json.loads(text)
                        if isinstance(parsed, list):
                            result.extend(parsed)
                        elif isinstance(parsed, dict):
                            result.append(parsed)
                    except json.JSONDecodeError:
                        result.append(block)
                elif isinstance(block, dict):
                    result.append(block)
            return result
        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return [content]
        return content if isinstance(content, (list, dict)) else []

    def get_collection_items(self, collection_key: str, limit: int = 100) -> list[dict]:
        result = self._call_tool("get_collection_items", {
            "collectionKey": collection_key,
            "limit": limit,
        })
        items = self._unwrap_content(result.get("content", []))
        return items if isinstance(items, list) else []

    def get_item_details(self, item_key: str) -> dict:
        result = self._call_tool("get_item_details", {
            "itemKey": item_key,
            "mode": "complete",
        })
        items = self._unwrap_content(result.get("content", []))
        if isinstance(items, list) and items:
            return items[0] if isinstance(items[0], dict) else {}
        return items if isinstance(items, dict) else {}


def _get_pdf_attachments(details: dict) -> list[dict]:
    """Extract PDF attachment info from item details. Returns local files (linkMode 0 or 1)."""
    attachments = details.get("attachments", []) or []
    pdfs = []
    for att in attachments:
        if not isinstance(att, dict):
            continue
        is_local = att.get("linkMode") in (0, 1)  # 0=linked, 1=imported into storage
        is_pdf = att.get("contentType") == "application/pdf"
        has_path = bool(att.get("path"))
        if is_local and is_pdf and has_path:
            pdfs.append(att)
    return pdfs


def _sanitize_filename(name: str) -> str:
    bad = '<>:"/\\|?*'
    for ch in bad:
        name = name.replace(ch, "_")
    return name[:200]


def import_collection(
    client: ZoteroMCPClient,
    collection_key: str,
    target_dir: Path,
    dry_run: bool = False,
) -> list[dict]:
    """
    Import all PDFs from a Zotero collection into target_dir.
    Copies directly from Zotero storage paths.
    """
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Importing collection {collection_key} → {target_dir}")
    items = client.get_collection_items(collection_key)
    print(f"  Items in collection: {len(items)}")

    results = []
    pdf_count = 0

    for item in items:
        item_key = item.get("key", "")
        title = item.get("title", f"untitled_{item_key}")[:100]

        if not item_key:
            continue

        # Get full details with attachments
        details = client.get_item_details(item_key)
        if not details:
            print(f"  SKIP: {title[:60]} — no details")
            results.append({"paper_title": title, "item_key": item_key, "success": False, "error": "no details"})
            continue

        pdf_attachments = _get_pdf_attachments(details)
        if not pdf_attachments:
            print(f"  SKIP: {title[:60]} — no PDF attachment")
            results.append({"paper_title": title, "item_key": item_key, "success": False, "error": "no PDF"})
            continue

        for att in pdf_attachments:
            src_path = att.get("path", "")
            filename = att.get("filename", "paper.pdf")
            safe_name = _sanitize_filename(filename)
            if not safe_name.lower().endswith(".pdf"):
                safe_name += ".pdf"

            dst_path = target_dir / safe_name
            src = Path(src_path)

            if dst_path.exists():
                print(f"  EXISTS: {safe_name}")
                results.append({"paper_title": title, "pdf_path": str(dst_path), "item_key": item_key, "success": True, "cached": True})
                pdf_count += 1
                break

            if not src.exists():
                print(f"  MISSING: {src_path}")
                results.append({"paper_title": title, "item_key": item_key, "success": False, "error": f"source not found: {src_path}"})
                continue

            if dry_run:
                size_mb = src.stat().st_size / (1024 * 1024)
                print(f"  [DRY RUN] Would copy: {safe_name} ({size_mb:.1f} MB)")
                results.append({"paper_title": title, "pdf_path": str(dst_path), "item_key": item_key, "success": True, "dry_run": True})
                pdf_count += 1
                break

            # Copy file
            print(f"  Copying: {safe_name}...", end=" ", flush=True)
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst_path)
                size_mb = src.stat().st_size / (1024 * 1024)
                print(f"OK ({size_mb:.1f} MB)")
                results.append({"paper_title": title, "pdf_path": str(dst_path), "item_key": item_key, "success": True})
                pdf_count += 1
                break
            except OSError as e:
                print(f"FAIL — {e}")
                results.append({"paper_title": title, "item_key": item_key, "success": False, "error": str(e)})

        time.sleep(0.3)  # Avoid hammering Zotero MCP

    print(f"  Result: {pdf_count}/{len(items)} PDFs imported")
    return results


def main():
    parser = argparse.ArgumentParser(description="Import PDFs from Zotero to RAG workspace")
    parser.add_argument("--collection", "-c", help="Zotero collection key")
    parser.add_argument("--target", "-t", help="Target subdirectory under academic_rag/papers/")
    parser.add_argument("--all-postdoc", action="store_true", help="Import all 15 postdoc professor collections")
    parser.add_argument("--dry-run", action="store_true", help="List what would be imported without copying")
    parser.add_argument("--professor", "-p", help="Professor name from postdoc collection keys")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    client = ZoteroMCPClient().init()
    all_results = []

    if args.all_postdoc:
        for name, key in POSTDOC_COLLECTIONS.items():
            target_dir = PAPERS_ROOT / "postdoc" / name
            results = import_collection(client, key, target_dir, dry_run=args.dry_run)
            all_results.extend(results)
            time.sleep(0.5)
    elif args.professor:
        name = args.professor.lower()
        if name not in POSTDOC_COLLECTIONS:
            print(f"Unknown professor: {name}")
            print(f"Known: {', '.join(POSTDOC_COLLECTIONS)}")
            sys.exit(1)
        key = POSTDOC_COLLECTIONS[name]
        target_dir = PAPERS_ROOT / "postdoc" / name
        results = import_collection(client, key, target_dir, dry_run=args.dry_run)
        all_results.extend(results)
    elif args.collection:
        target_dir = PAPERS_ROOT / (args.target or args.collection)
        results = import_collection(client, args.collection, target_dir, dry_run=args.dry_run)
        all_results.extend(results)
    else:
        parser.print_help()
        sys.exit(1)

    success = sum(1 for r in all_results if r["success"])
    fail = len(all_results) - success
    print(f"\n{'='*50}")
    print(f"Total: {len(all_results)} papers, {success} success, {fail} failed")

    if fail:
        print("\nFailures:")
        for r in all_results:
            if not r["success"]:
                print(f"  - {r['paper_title'][:60]}: {r.get('error', 'unknown')}")


if __name__ == "__main__":
    main()
