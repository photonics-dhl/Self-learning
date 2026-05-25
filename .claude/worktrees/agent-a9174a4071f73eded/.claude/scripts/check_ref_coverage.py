"""Compare indexed vs referenced paper dirs per professor."""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

BASE = Path(__file__).parent.parent
VAULT = BASE / "Obsidian-Vault"
EXTRACTED = BASE / ".claude"

# Find viz dir
VIZ = None
for d in VAULT.iterdir():
    if '工具' in d.name:
        for sd in d.iterdir():
            if 'visualizations' in sd.name:
                VIZ = sd
                break
        break

# Find profiles dir
PROFILE_DIR = None
for d in VAULT.iterdir():
    if '研究方向' in d.name:
        for sd in d.iterdir():
            if sd.is_dir() and 'Postdoc' in sd.name:
                PROFILE_DIR = sd
                break
        break

PROF_TO_FILE = {
    "baum": "Peter Baum.md", "chang": "Zenghu Chang.md",
    "gedik": "Nuh Gedik.md", "hommelhoff": "Peter Hommelhoff.md",
    "huber": "Rupert Huber.md", "kaertner": "Franz X Kärtner.md",
    "keller": "Ursula Keller.md", "kling": "Matthias Kling.md",
    "krausz": "Krausz.md", "leone": "Stephen Leone.md",
    "lhuillier": "Anne L'Huillier.md", "miao": "Jianwei Miao.md",
    "murnane": "Margaret Murnane.md", "nisoli": "Mauro Nisoli.md",
    "ropers": "Claus Ropers.md",
}

for prof, fname in sorted(PROF_TO_FILE.items()):
    pf = PROFILE_DIR / fname
    ef = EXTRACTED / f"{prof}_extracted.json"
    if not pf.exists():
        continue

    indexed_ids = set()
    if ef.exists():
        data = json.loads(ef.read_text(encoding='utf-8'))
        for p in data.get("papers", []):
            pid = p.get("paper_id", "")
            if pid:
                indexed_ids.add(pid[:8])

    content = pf.read_text(encoding='utf-8')
    refs = re.findall(r'!\[\[6.*?visualizations/([a-f0-9]{8,16})/', content)
    ref_dirs = set(refs)

    matched = ref_dirs & indexed_ids
    unmatched = ref_dirs - indexed_ids
    extra = indexed_ids - ref_dirs

    pct = f"{len(matched)}/{len(ref_dirs)}" if ref_dirs else "0/0"
    print(f"{prof:12s}: {pct} ref dirs matched, {len(unmatched)} unmatched, {len(extra)} indexed unused")
