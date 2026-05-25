"""Quick stats on all researcher profiles."""
import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

BASE = Path(__file__).parent.parent
VAULT = BASE / "Obsidian-Vault"

# Find Postdoc dir
PROFILE_DIR = None
for d in VAULT.iterdir():
    name = d.name
    if '研究方向' in name:
        for sd in d.iterdir():
            if sd.is_dir() and 'Postdoc' in sd.name:
                PROFILE_DIR = sd
                break
        break

# Find viz dir
VIZ_DIR = None
for d in VAULT.iterdir():
    if '工具' in d.name:
        for sd in d.iterdir():
            if 'visualizations' in sd.name:
                VIZ_DIR = sd
                break
        break

for md in sorted(PROFILE_DIR.glob("*.md")):
    if md.name == "README.md":
        continue
    content = md.read_text(encoding='utf-8')
    lines = len(content.splitlines())
    figs = content.count('![[6')
    broken = 0
    for m in re.finditer(r'!\[\[6.*?visualizations/(.+?\.png)\]\]', content):
        ref = m.group(1).replace('\\', '/')
        img = VIZ_DIR / ref
        if not img.exists():
            broken += 1
    print(f"{md.stem:25s}: {lines:5d} lines, {figs:2d} figs, {broken:2d} broken")
