"""Verify fixed figure paths actually exist on disk."""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

VAULT = Path(r"z:\321\DHL\Self_Learning\Obsidian-Vault")
PROFILE_DIR = next(VAULT.glob("2* 研究方向/Postdoc方向"))
VIZ_DIR = None

# Find visualizations directory
for d in VAULT.iterdir():
    name = d.name
    if '工具' in name:
        for sd in d.iterdir():
            if 'visualizations' in sd.name:
                VIZ_DIR = sd
                break
        break

if not VIZ_DIR:
    print("ERROR: visualizations dir not found")
    sys.exit(1)

print(f"Viz dir: {VIZ_DIR}")

for prof_file in sorted(PROFILE_DIR.glob("*.md")):
    if prof_file.name == "README.md":
        continue
    content = prof_file.read_text(encoding='utf-8')
    # Find all figure refs
    refs = re.findall(r'!\[\[.*?visualizations/(.+?\.png)\]\]', content, re.IGNORECASE)
    if not refs:
        continue

    ok = 0
    missing = 0
    for ref in refs:
        ref_clean = ref.replace('\\', '/')
        img_path = VIZ_DIR / ref_clean
        if img_path.exists():
            ok += 1
        else:
            missing += 1
            if missing <= 3:
                print(f"  MISSING: {prof_file.stem}: {ref_clean}")

    status = "OK" if missing == 0 else f"{ok}/{ok+missing} OK ({missing} missing)"
    print(f"  {prof_file.stem:25s}: {status}")
