"""
Clean ChromaDB duplicates caused by random-UUID paper_id bug.
Keeps the most recent entry per unique file_hash.
"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
from collections import defaultdict
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from academic_rag.config import config
from academic_rag.indexer.vector_indexer import VectorIndexer

db_path = Path(config.vector_db_path)
viz_path = Path(config.visualizations)
meta_files = sorted(db_path.glob("*_metadata.json"))

print(f"Found {len(meta_files)} metadata files")

# Group by file_hash
by_hash = defaultdict(list)
for mf in meta_files:
    try:
        with open(mf, encoding='utf-8') as f:
            m = json.load(f)
        fh = m.get("paper", {}).get("file_hash", "")
        paper_id = m.get("paper", {}).get("paper_id", "")
        title = m.get("paper", {}).get("title", "")[:60]
        if fh:
            by_hash[fh].append((mf, paper_id, title))
    except Exception as e:
        print(f"  Error reading {mf.name}: {e}")

# Count duplicates
dupes = {fh: entries for fh, entries in by_hash.items() if len(entries) > 1}
uniques = {fh: entries for fh, entries in by_hash.items() if len(entries) == 1}

print(f"Unique papers: {len(uniques)}")
print(f"Duplicate groups: {len(dupes)} (total dupes to remove: {sum(len(v) - 1 for v in dupes.values())})")

# Remove duplicates: keep the file with the most recent modification time
removed = 0
indexer = VectorIndexer()

for fh, entries in dupes.items():
    # Keep newest
    entries.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)
    keep = entries[0]
    for entry in entries[1:]:
        mf, paper_id, title = entry
        print(f"  REMOVE: {paper_id[:8]} | {title[:50]}")
        try:
            # Delete from ChromaDB
            try:
                result = indexer.collection.get(where={"paper_id": paper_id})
                if result and result.get("ids"):
                    indexer.collection.delete(ids=result["ids"])
            except Exception:
                pass

            # Delete metadata file
            mf.unlink(missing_ok=True)

            # Delete visualization directory
            viz_dir = viz_path / paper_id[:8]
            if viz_dir.exists():
                shutil.rmtree(viz_dir)

            removed += 1
        except Exception as e:
            print(f"    Error: {e}")

print(f"\nRemoved: {removed} duplicate entries")
print(f"Remaining: {len(meta_files) - removed} entries")
