"""
从Zotero收藏夹复制PDF到academic_rag/papers/对应分类目录。
用法: python academic_rag/copy_zotero_to_rag.py
"""
import json
import shutil
import sys
from pathlib import Path

# Zotero storage path
ZOTERO_STORAGE = Path(r"E:\PostGraduate\Science_softwares\Zotero\data\storage")
# Target base directory
RAG_PAPERS = Path(r"Z:\321\DHL\Self_Learning\academic_rag\papers")

# Collection mapping: Zotero collection key -> directory name
COLLECTIONS = {
    "8B94ZY5F": "01_电磁地基",
    "98YX4QVB": "02_波动光学",
    "773C6X5I": "03_量子光学",
    "BHGS5HE7": "04_激光物理",
    "RXZT7XPF": "05_半导体物理",
    "4WRFHU2Y": "06_超材料与纳米光学",
    "BAZQDAUH": "07_工程基础",
    "EQ5DFXR5": "08_DFT_TDDFT",
}

def main():
    import urllib.request
    import urllib.error

    zotero_local = Path(r"E:\PostGraduate\Science_softwares\Zotero\data")
    # Read Zotero API key and user ID from .env
    env_path = Path(r"Z:\321\DHL\Self_Learning\.env")
    api_key = None
    user_id = None
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("Zotero_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("Zotero_user_ID="):
                user_id = line.split("=", 1)[1].strip().strip('"').strip("'")

    if not api_key or not user_id:
        print("ERROR: Zotero_API_KEY or Zotero_user_ID not found in .env")
        sys.exit(1)

    headers = {"Zotero-API-Key": api_key, "Zotero-API-Version": "3"}

    total_copied = 0
    total_skipped = 0

    for coll_key, dir_name in COLLECTIONS.items():
        target_dir = RAG_PAPERS / dir_name
        target_dir.mkdir(parents=True, exist_ok=True)

        # Get items in collection
        url = f"https://api.zotero.org/users/{user_id}/collections/{coll_key}/items?limit=100&format=json"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                items = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"ERROR fetching collection {dir_name}: {e}")
            continue

        for item in items:
            data = item.get("data", {})
            if data.get("itemType") in ("attachment", "note"):
                continue

            title = data.get("title", "Unknown")
            date = data.get("date", "n.d")[:4] if data.get("date") else "n.d"
            item_key = data.get("key", "")

            # Get attachments for this item
            children_url = f"https://api.zotero.org/users/{user_id}/items/{item_key}/children?format=json"
            children_req = urllib.request.Request(children_url, headers=headers)
            try:
                with urllib.request.urlopen(children_req, timeout=15) as resp:
                    children = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                print(f"  WARNING: Could not fetch children for {title}: {e}")
                continue

            # Find PDF attachment
            # Zotero API returns path=None for imported attachments;
            # actual file is at storage/<child_key>/<filename>
            pdf_path = None
            for child in children:
                cdata = child.get("data", {})
                if cdata.get("itemType") == "attachment" and cdata.get("contentType") == "application/pdf":
                    child_key = child.get("key", "")
                    filename = cdata.get("filename", "")
                    path_str = cdata.get("path")
                    if path_str:
                        # Absolute path
                        pdf_path = Path(path_str)
                    elif filename and child_key:
                        # Imported file: storage/<key>/<filename>
                        pdf_path = ZOTERO_STORAGE / child_key / filename
                    if pdf_path and pdf_path.exists():
                        break
                    else:
                        pdf_path = None

            if not pdf_path or not pdf_path.exists():
                print(f"  SKIP (no PDF): {title}")
                total_skipped += 1
                continue

            # Build target filename: AuthorYear_short_title.pdf
            creators = data.get("creators", [])
            first_author = creators[0].get("lastName", "Unknown") if creators else "Unknown"
            safe_title = "".join(c for c in title[:50] if c.isalnum() or c in " _-").strip()
            safe_title = safe_title.replace(" ", "_")
            target_file = target_dir / f"{first_author}{date}_{safe_title}.pdf"

            if target_file.exists():
                print(f"  EXISTS: {target_file.name}".encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
                total_skipped += 1
                continue

            try:
                shutil.copy2(str(pdf_path), str(target_file))
            except Exception as e:
                name_safe = target_file.name.encode("ascii", errors="replace").decode("ascii")
                print(f"  ERROR copying {name_safe}: {e}")
                total_skipped += 1
                continue
            size_kb = pdf_path.stat().st_size // 1024
            name_safe = target_file.name.encode("ascii", errors="replace").decode("ascii")
            print(f"  COPIED: {name_safe} ({size_kb}KB)")
            total_copied += 1

    print(f"\n=== Done: {total_copied} copied, {total_skipped} skipped ===")

if __name__ == "__main__":
    main()
