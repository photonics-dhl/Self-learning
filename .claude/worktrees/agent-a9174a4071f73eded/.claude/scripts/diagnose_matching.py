"""Diagnose why matching fails for specific professors."""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

BASE = Path(__file__).parent.parent
VAULT = BASE / "Obsidian-Vault"
EXTRACTED = BASE / ".claude"

PROFILE_DIR = None
for d in VAULT.iterdir():
    if '研究方向' in d.name:
        for sd in d.iterdir():
            if sd.is_dir() and 'Postdoc' in sd.name:
                PROFILE_DIR = sd
                break
        break

PROF_TO_FILE = {
    "hommelhoff": "Peter Hommelhoff.md",
    "huber": "Rupert Huber.md",
    "kling": "Matthias Kling.md",
    "krausz": "Krausz.md",
    "leone": "Stephen Leone.md",
    "murnane": "Margaret Murnane.md",
    "ropers": "Claus Ropers.md",
}

for prof, fname in sorted(PROF_TO_FILE.items()):
    pf = PROFILE_DIR / fname
    ef = EXTRACTED / f"{prof}_extracted.json"
    if not pf.exists() or not ef.exists():
        continue

    data = json.loads(ef.read_text(encoding='utf-8'))
    content = pf.read_text(encoding='utf-8')

    # Find broken refs
    refs = re.findall(r'!\[\[6.*?visualizations/([a-f0-9]{8,16})/([^\]]+\.png)\]\]', content)

    # Check which are broken
    VIZ = None
    for d in VAULT.iterdir():
        if '工具' in d.name:
            for sd in d.iterdir():
                if 'visualizations' in sd.name:
                    VIZ = sd
                    break
            break

    broken_refs = [(d, f) for d, f in refs if not (VIZ / d).exists()]
    if not broken_refs:
        continue

    print(f"\n{'='*60}")
    print(f"{prof}: {len(broken_refs)} broken refs")
    print(f"Indexed papers:")
    for p in data.get("papers", []):
        pid = p.get("paper_id", "")[:8]
        title = p.get("title", "")[:80]
        year = p.get("year", "")
        journal = p.get("journal", "")
        print(f"  [{pid}] y={year} j={journal!r} {title}")

    print(f"\nBroken ref details:")
    for old_dir, old_fname in broken_refs[:4]:
        # Find callout caption
        pattern = re.compile(r'!\[\[6.*?visualizations/' + re.escape(old_dir) + r'/' + re.escape(old_fname) + r'\]\]')
        m = pattern.search(content)
        if m:
            before = content[max(0, m.start() - 800):m.start()]
            # Get source line
            src_lines = [l for l in before.split('\n') if '来源' in l or 'source' in l.lower()]
            src = src_lines[-1].strip() if src_lines else 'N/A'
            # Get heading
            headings = re.findall(r'^#{2,4}\s+(.+)$', before, re.MULTILINE)
            heading = headings[-1].strip() if headings else 'N/A'
            print(f"  [{old_dir}] {old_fname}")
            print(f"    Heading: {heading[:100]}")
            print(f"    Source: {src[:200]}")
