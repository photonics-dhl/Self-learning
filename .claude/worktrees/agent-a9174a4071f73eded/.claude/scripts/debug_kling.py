"""Debug Kling fix matching."""
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

BASE = Path(__file__).parent.parent
VAULT = BASE / "Obsidian-Vault"

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

# Copy needed functions inline
MANUAL_OVERRIDES = {
    ("baum", "2aa1e1ed"): "f6f1153a",
    ("huber", "a5c7b94e"): "95af5395",
}

def extract_year_and_heading(content, old_dir, window=4000):
    pattern = re.compile(r'!\[\[6️⃣\s*工具[/\\]visualizations[/\\]' + re.escape(old_dir) + r'[/\\]')
    m = pattern.search(content)
    if not m:
        return None, None, ""
    before = content[max(0, m.start() - window):m.start()]
    year = None
    journal = None
    yj = re.findall(
        r'(?:来源|source).*?((?:19|20)\d{2}).*?(Science|Nature|PRL|Nat\.\s*Photon|Nat\.\s*Mater|Nat\.\s*Nano|Nat\.\s*Phys|Nat\.\s*Commun|Phys\.\s*Rev\.\s*Lett|Optica|Opt\.\s*Lett|Light[\s-]Sci)',
        before, re.IGNORECASE
    )
    if yj:
        year = int(yj[-1][0])
        journal = yj[-1][1].lower()
    else:
        years = re.findall(r'((?:19|20)\d{2})', before)
        if years:
            year = int(years[-1])
    headings = re.findall(r'^#{2,4}\s+(.+)$', before, re.MULTILINE)
    heading = ""
    for h in reversed(headings):
        h = h.strip()
        if len(h) > 10:
            heading = h
            break
    return year, journal, heading

def extract_author_from_callout(content, old_dir, window=3000):
    pattern = re.compile(r'!\[\[6️⃣\s*工具[/\\]visualizations[/\\]' + re.escape(old_dir) + r'[/\\]')
    m = pattern.search(content)
    if not m:
        return None
    before = content[max(0, m.start() - window):m.start()]
    src = re.findall(r'来源[：:]\s*([A-Z][a-z]+)', before)
    if not src:
        src = re.findall(r'source[：:]\s*([A-Z][a-z]+)', before, re.IGNORECASE)
    return src[-1].lower() if src else None

def match_old_dir_to_paper(papers, old_dir, content, prof_key=""):
    override = MANUAL_OVERRIDES.get((prof_key, old_dir))
    if override:
        return override
    year, journal, heading = extract_year_and_heading(content, old_dir)
    author = extract_author_from_callout(content, old_dir)
    all_papers = list(papers.items())
    scored = []
    heading_words = set()
    if heading:
        heading_words = set(re.findall(r'[a-zA-Z]{4,}', heading.lower()))
    journal_lower = journal.lower() if journal else ""
    for new_dir, paper in all_papers:
        score = 0
        title = paper.get("title", "").lower()
        pyear = paper.get("year", 0)
        if year and pyear:
            ydiff = abs(year - pyear)
            if ydiff == 0: score += 3
            elif ydiff == 1: score += 2
            elif ydiff == 2: score += 1
        if author and author in title:
            score += 5
        if journal_lower:
            if journal_lower in title:
                score += 3
            pjournal = paper.get("journal", "").lower()
            if journal_lower in pjournal:
                score += 3
        hw = set(heading_words)
        t_words = set(re.findall(r'[a-zA-Z]{4,}', title))
        kw_score = len(hw & t_words)
        if kw_score > 0:
            score += kw_score * 2
        scored.append((new_dir, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    if not scored:
        return None
    best_dir, best_score = scored[0]
    if best_score >= 2:
        return best_dir
    if year:
        ym = [d for d, p in all_papers if p.get("year") == year]
        if len(ym) == 1:
            return ym[0]
    return None

def extract_fig_number_from_callout(content, old_dir, old_fname):
    pattern = re.compile(
        r'!\[\[6️⃣\s*工具[/\\]visualizations[/\\]' + re.escape(old_dir) + r'[/\\]'
        + re.escape(old_fname) + r'\]\]'
    )
    m = pattern.search(content)
    if not m:
        return None
    before = content[max(0, m.start() - 3000):m.start()]
    fig_nums = re.findall(r'Fig\.\s*(\d+)', before, re.IGNORECASE)
    if fig_nums:
        source_lines = [l for l in before.split('\n') if re.search(r'fig\.', l, re.IGNORECASE) and ('来源' in l or 'source' in l.lower())]
        if source_lines:
            nums = re.findall(r'Fig\.\s*(\d+)', source_lines[-1], re.IGNORECASE)
            if nums:
                return int(nums[0])
        return int(fig_nums[-1])
    return None

def find_new_figure(paper_data, fig_number):
    if fig_number is None:
        return None
    for fig in paper_data.get("figures", []):
        caption = fig.get("caption", "")
        label = fig.get("label", "")
        m = re.match(r'Fig\.\s*(\d+)', caption.strip(), re.IGNORECASE)
        if not m:
            m = re.match(r'Fig\.\s*(\d+)', label.strip(), re.IGNORECASE)
        if m and int(m.group(1)) == fig_number:
            path = fig.get("image_path", "")
            return Path(path).name
    return None

# Load Kling data
ef = BASE / ".claude" / "kling_extracted.json"
data = json.loads(ef.read_text(encoding='utf-8'))
papers = {}
for p in data.get("papers", []):
    pid = p.get("paper_id", "")
    if pid:
        papers[pid[:8]] = p

content = (PROFILE_DIR / "Matthias Kling.md").read_text(encoding='utf-8')

# Find all refs
all_refs = re.findall(
    r'!\[\[(6️⃣\s*工具[/\\]visualizations[/\\]([a-f0-9]{8,16})[/\\]([^\]]+\.png))\]\]',
    content
)
broken_refs = [(fp, od, ofn) for fp, od, ofn in all_refs if not (VIZ / od).exists()]
print(f"Broken: {len(broken_refs)}")

for full_path, old_dir, old_fname in broken_refs:
    new_dir = match_old_dir_to_paper(papers, old_dir, content, "kling")
    print(f"[{old_dir}] -> new_dir={new_dir}")
    if new_dir:
        paper_data = papers.get(new_dir, {})
        fn = extract_fig_number_from_callout(content, old_dir, old_fname)
        print(f"  fig_number={fn}")
        if fn:
            nfn = find_new_figure(paper_data, fn)
            print(f"  new_fname={nfn}")
            print(f"  old_fname={old_fname}")
            if nfn and nfn != old_fname:
                print(f"  => WOULD REPLACE")
            else:
                print(f"  => SKIP")
