import json
from pathlib import Path
from collections import Counter

db = Path(r'z:\321\DHL\Self_Learning\academic_rag\chroma_db')
prof_counts = Counter()
papers = []

for mf in sorted(db.glob('*_metadata.json')):
    with open(mf, encoding='utf-8') as f:
        m = json.load(f)
    pdf = m.get('paper', {}).get('pdf_path', '')
    title = m.get('paper', {}).get('title', '')[:70]
    paper_id = m.get('paper', {}).get('paper_id', '')[:16]
    n_figs = len(m.get('figures', []))
    n_chunks = len(m.get('chunks', []))

    # Extract professor
    prof = 'unknown'
    norm = pdf.replace('\\', '/')
    if 'postdoc/' in norm:
        prof = norm.split('postdoc/')[1].split('/')[0]

    prof_counts[prof] += 1
    papers.append((prof, paper_id, n_figs, n_chunks, title))

print("=== Professor Indexing Status ===")
for prof, count in sorted(prof_counts.items()):
    print(f"  {prof:15s}: {count} papers")

print(f"\nTotal: {len(papers)} papers indexed")

# Expected counts from previous session
expected = {
    'baum': 5, 'chang': 5, 'gedik': 4, 'hommelhoff': 4,
    'huber': 7, 'kaertner': 5, 'keller': 5, 'kling': 5,
    'krausz': 8, 'leone': 5, 'lhuillier': 5, 'miao': 5,
    'murnane': 5, 'nisoli': 5, 'ropers': 4,
}
print("\n=== Missing/Incomplete ===")
for prof, exp in sorted(expected.items()):
    actual = prof_counts.get(prof, 0)
    status = "OK" if actual >= exp else f"MISSING {exp - actual}"
    if status != "OK":
        print(f"  {prof:15s}: have {actual}, need {exp} -> {status}")

print(f"\n=== Detail ===")
for prof, pid, figs, chunks, title in sorted(papers):
    print(f"  {prof:15s} | {pid:16s} | {figs:2d}f {chunks:2d}c | {title}")
