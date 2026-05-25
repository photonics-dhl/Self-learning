"""Test actual fix_figure_paths functions with debug output."""
import sys, io, json, re, importlib.util
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

BASE = Path(__file__).parent.parent
VAULT = BASE / "Obsidian-Vault"

# Import fix_figure_paths directly
spec = importlib.util.spec_from_file_location("fix", BASE / ".claude" / "fix_figure_paths.py")
fix = importlib.util.module_from_spec(spec)
# Override stdout before executing
spec.loader.exec_module(fix)

# Restore stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROFILE_DIR = None
for d in VAULT.iterdir():
    if '研究方向' in d.name:
        for sd in d.iterdir():
            if sd.is_dir() and 'Postdoc' in sd.name:
                PROFILE_DIR = sd
                break
        break

VIZ = None
for d in VAULT.iterdir():
    if '工具' in d.name:
        for sd in d.iterdir():
            if 'visualizations' in sd.name:
                VIZ = sd
                break
        break

# Test Kling
ef = BASE / ".claude" / "kling_extracted.json"
data = json.loads(ef.read_text(encoding='utf-8'))
papers = {}
for p in data.get("papers", []):
    pid = p.get("paper_id", "")
    if pid:
        papers[pid[:8]] = p

content = (PROFILE_DIR / "Matthias Kling.md").read_text(encoding='utf-8')
old_refs = fix.find_all_old_refs_with_filenames(content)
broken_refs = [(fp, od, ofn) for fp, od, ofn in old_refs if not (VIZ / od).exists()]
print(f"Kling broken refs: {len(broken_refs)}")

for full_path, old_dir, old_fname in broken_refs[:2]:
    print(f"\n[{old_dir}] {old_fname}")

    year, journal, heading = fix.extract_year_and_heading(content, old_dir)
    author = fix.extract_author_from_callout(content, old_dir)
    ck = fix.extract_keywords_from_callout(content, old_dir)
    print(f"  year={year} journal={journal!r} author={author!r}")
    print(f"  heading={heading[:80]}")
    print(f"  callout keywords ({len(ck)}): {list(ck)[:15]}")

    new_dir = fix.match_old_dir_to_paper(papers, old_dir, content, "kling")
    print(f"  => new_dir={new_dir}")

    if new_dir:
        paper_data = papers.get(new_dir, {})
        fn = fix.extract_fig_number_from_callout(content, old_dir, old_fname)
        print(f"  fig_number={fn}")
        if fn:
            nfn = fix.find_new_figure(paper_data, fn)
            print(f"  new_fname={nfn}")
            if nfn:
                print(f"  old_fname={old_fname}")
                print(f"  {'WOULD REPLACE' if nfn != old_fname else 'SAME FILE'}")
