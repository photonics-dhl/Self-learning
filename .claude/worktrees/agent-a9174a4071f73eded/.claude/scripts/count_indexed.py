"""Count indexed papers per professor."""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))
from academic_rag.config import config
from collections import Counter

db = Path(config.vector_db_path)
meta_files = list(db.glob('*_metadata.json'))
print(f'Total metadata files: {len(meta_files)}')

prof_counts = Counter()
for mf in meta_files:
    try:
        with open(mf, encoding='utf-8') as f:
            m = json.load(f)
        pdf_path = m.get('paper', {}).get('pdf_path', '')
        parts = pdf_path.replace('\\', '/').split('/')
        prof = 'unknown'
        for i, p in enumerate(parts):
            if p == 'postdoc' and i + 1 < len(parts):
                prof = parts[i + 1]
                break
        prof_counts[prof] += 1
    except Exception as e:
        prof_counts['error'] += 1

for p, c in prof_counts.most_common():
    print(f'  {p}: {c}')
