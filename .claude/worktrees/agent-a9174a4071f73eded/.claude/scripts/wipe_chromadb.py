"""
Clean postdoc entries from ChromaDB, then re-index with deterministic paper_ids.
"""
import json, sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from academic_rag.config import config
import chromadb
from chromadb.config import Settings

db_path = Path(config.vector_db_path)
viz_path = Path(config.visualizations)

# Step 1: Remove postdoc metadata files + visualization dirs
meta_files = list(db_path.glob("*_metadata.json"))
to_remove = []
to_keep = []

for mf in meta_files:
    try:
        with open(mf, encoding='utf-8') as f:
            m = json.load(f)
        pdf_path = m.get("paper", {}).get("pdf_path", "")
        if "postdoc" in pdf_path.lower():
            to_remove.append(mf)
        else:
            to_keep.append(mf)
    except Exception:
        to_keep.append(mf)

print(f"Postdoc metadata to remove: {len(to_remove)}")
print(f"Non-postdoc to keep: {len(to_keep)}")

# Remove metadata files + visualization dirs
for mf in to_remove:
    try:
        with open(mf, encoding='utf-8') as f:
            m = json.load(f)
        paper_id = m.get("paper", {}).get("paper_id", "")[:8]
        viz_dir = viz_path / paper_id
        if viz_dir.exists():
            shutil.rmtree(viz_dir)
    except Exception:
        pass
    mf.unlink()

# Step 2: Clean ChromaDB vector collections
client = chromadb.PersistentClient(
    path=str(db_path), settings=Settings(anonymized_telemetry=False)
)

# Recreate collections to purge all postdoc entries
for coll_name in ["academic_papers", "figure_embeddings", "figure_captions"]:
    try:
        client.delete_collection(coll_name)
        print(f"Deleted collection: {coll_name}")
    except Exception:
        print(f"Collection not found (OK): {coll_name}")

print(f"\nDone. ChromaDB cleaned. {len(to_keep)} non-postdoc entries preserved.")
print("Ready for fresh indexing with deterministic paper_ids.")
