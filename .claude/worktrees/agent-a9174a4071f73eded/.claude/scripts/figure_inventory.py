"""
Build researcher → paper → figure inventory for profile enrichment.
Matches Zotero collection items to chroma_db papers by PDF filename.
"""
import json, sys, io, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CHROMA_DB = Path('z:/321/DHL/Self_Learning/academic_rag/chroma_db')
PROFILES_DIR = Path('z:/321/DHL/Self_Learning/Obsidian-Vault/2️⃣ 研究方向/Postdoc方向')

# ----- Step 1: Load all chroma_db papers with their filenames -----
chroma_papers = {}  # filename_stem → paper info
for mf in sorted(CHROMA_DB.glob('*_metadata.json')):
    with open(mf, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    paper = meta.get('paper', {})
    pdf_path = paper.get('pdf_path', '')
    if pdf_path:
        filename = Path(pdf_path).name
        stem = Path(pdf_path).stem  # without .pdf
        chroma_papers[filename] = {
            'paper_id': paper.get('paper_id', ''),
            'title': paper.get('title', ''),
            'n_figs': len(meta.get('figures', [])),
            'n_tabs': len(meta.get('tables', [])),
            'figures': meta.get('figures', []),
            'tables': meta.get('tables', []),
            'pdf_path': pdf_path,
            'domain': paper.get('domain', ''),
            'subfield': paper.get('subfield', ''),
        }
        # Also index by stem
        chroma_papers[stem] = chroma_papers[filename]

print(f"Loaded {len(set(p.get('paper_id','') for p in chroma_papers.values()))} unique papers from chroma_db")
print()

# ----- Step 2: Load all researcher profiles -----
profiles = {}
for pf in sorted(PROFILES_DIR.glob('*.md')):
    if pf.name in ['README.md', 'Krausz.md.tmp']:
        continue
    content = pf.read_text(encoding='utf-8')
    zkey = re.search(r'zotero_collection_key:\s*"(\w*)"', content)
    title = re.search(r'title:\s*"(.+?)"', content)
    pc = re.search(r'paper_count:\s*(\d+)', content)
    fig_count = len(re.findall(r'!\[\[6️⃣ 工具/visualizations/', content))

    profiles[pf.stem] = {
        'file': pf.name,
        'zkey': zkey.group(1) if zkey else '',
        'title': title.group(1) if title else pf.stem,
        'paper_count': int(pc.group(1)) if pc else 0,
        'figs_in_profile': fig_count,
        'papers': [],  # will fill from Zotero
    }

# Print current state
print("=== Current Profile State ===")
print(f"{'Researcher':25s} | {'zkey':10s} | Papers | Figs")
print("-" * 60)
for name, p in profiles.items():
    print(f"{p['title']:25s} | {p['zkey']:10s} | {p['paper_count']:6d} | {p['figs_in_profile']:4d}")

print()
print("=== ChromaDB Papers by Domain/Subfield ===")
from collections import Counter
domains = Counter((p.get('domain','?'), p.get('subfield','?')) for p in chroma_papers.values()
                  if len(p.get('paper_id','')) == 8)  # only unique by paper_id length
for (d, s), c in domains.most_common():
    print(f"  {d}/{s}: {c} papers")

# Print all chroma papers with figure counts, organized by filename
print()
print("=== ChromaDB Paper Filenames (for matching) ===")
seen = set()
for filename, info in sorted(chroma_papers.items()):
    pid = info['paper_id']
    if pid in seen or not filename.endswith('.pdf'):
        continue
    seen.add(pid)
    print(f"  [{pid[:8]}] {info['n_figs']:3d}f | {filename[:100]}")

print()
print("Run with --match to see which chroma papers match known researcher Zotero papers.")
