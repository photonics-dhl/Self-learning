#!/usr/bin/env python
"""
Fix broken figure paths in researcher profiles — directory AND filename.
Strategy:
1. Map old dir → new dir (using year+journal from figure captions)
2. For each old figure ref, find matching new figure by Fig number in caption
3. Replace both directory and filename
"""
import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
VAULT = PROJECT_ROOT / "Obsidian-Vault"
PROFILE_DIR = VAULT / "2️⃣ 研究方向" / "Postdoc方向"
EXTRACTED_DIR = PROJECT_ROOT / ".claude"
VIZ_BASE = VAULT / "6️⃣ 工具" / "visualizations"

PROF_KEY_TO_FILE = {
    "baum": "Peter Baum.md", "chang": "Zenghu Chang.md",
    "gedik": "Nuh Gedik.md", "hommelhoff": "Peter Hommelhoff.md",
    "huber": "Rupert Huber.md", "kaertner": "Franz X Kärtner.md",
    "keller": "Ursula Keller.md", "kling": "Matthias Kling.md",
    "krausz": "Krausz.md", "leone": "Stephen Leone.md",
    "lhuillier": "Anne L'Huillier.md", "miao": "Jianwei Miao.md",
    "murnane": "Margaret Murnane.md", "nisoli": "Mauro Nisoli.md",
    "ropers": "Claus Ropers.md",
}

MANUAL_OVERRIDES = {
    ("baum", "2aa1e1ed"): "f6f1153a",
    ("huber", "a5c7b94e"): "95af5395",
    ("kling", "84a37544"): "5a2abe88",    # Uiberacker 2007 Nature, indexed year=1960
    ("krausz", "9d9019ec"): "a880300c",    # Krausz & Ivanov 2009 RMP
    ("hommelhoff", "d634f298"): "d85c68a9",  # England/Hommelhoff 2014 Rev Mod Phys
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
        r'(?:来源|source).*?((?:19|20)\d{2}).*?(Nat\.\s*Photon|Nat\.\s*Mater|Nat\.\s*Nano|Nat\.\s*Phys|Nat\.\s*Commun|Phys\.\s*Rev\.\s*Lett|Phys\.\s*Rev|Light[\s-]Sci|Optica|Opt\.\s*Lett|RMP|Science|Nature|PRL)',
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
    """Extract first author surname from the source citation near the figure ref."""
    pattern = re.compile(
        r'!\[\[6️⃣\s*工具[/\\]visualizations[/\\]' + re.escape(old_dir) + r'[/\\]'
    )
    m = pattern.search(content)
    if not m:
        return None
    before = content[max(0, m.start() - window):m.start()]
    # Source line: "（来源：Author Year Journal, Fig. N）" or "来源：Author et al. Year"
    # Take first word after 来源：
    src = re.findall(r'来源[：:]\s*([A-Z][a-z]+)', before)
    if not src:
        src = re.findall(r'source[：:]\s*([A-Z][a-z]+)', before, re.IGNORECASE)
    return src[-1].lower() if src else None

def extract_keywords_from_callout(content, old_dir, window=3000):
    """Extract English technical keywords from callout text near the figure ref."""
    pattern = re.compile(
        r'!\[\[6️⃣\s*工具[/\\]visualizations[/\\]' + re.escape(old_dir) + r'[/\\]'
    )
    m = pattern.search(content)
    if not m:
        return set()
    # Get text between source line and the figure ref
    before = content[max(0, m.start() - window):m.start()]
    # Find all English words (4+ chars) in the callout text
    # Exclude common stopwords
    stopwords = {'figure', 'image', 'table', 'source', 'with', 'from', 'this', 'that',
                 'which', 'their', 'have', 'been', 'also', 'such', 'each', 'more',
                 'between', 'about', 'these', 'would', 'could', 'other', 'after'}
    words = set(w.lower() for w in re.findall(r'[a-zA-Z]{4,}', before))
    return words - stopwords

def match_old_dir_to_paper(papers, old_dir, content, prof_key=""):
    """Map old_dir to new_dir by title keyword + year matching (journal often empty)."""
    override = MANUAL_OVERRIDES.get((prof_key, old_dir))
    if override:
        return override

    year, journal, heading = extract_year_and_heading(content, old_dir)
    author = extract_author_from_callout(content, old_dir)
    callout_keywords = extract_keywords_from_callout(content, old_dir)
    all_papers = list(papers.items())

    # Build candidate scoring
    scored = []
    heading_words = set()
    if heading:
        heading_words = set(re.findall(r'[a-zA-Z]{4,}', heading.lower()))
    journal_lower = journal.lower() if journal else ""

    for new_dir, paper in all_papers:
        score = 0
        title = paper.get("title", "").lower()
        pyear = paper.get("year", 0)

        # Year score: exact=5, ±1=3, ±2=1
        if year and pyear:
            ydiff = abs(year - pyear)
            if ydiff == 0:
                score += 5
            elif ydiff == 1:
                score += 3
            elif ydiff == 2:
                score += 1

        # Author match: very strong signal
        if author and author in title:
            score += 10

        # Journal match in extracted journal field (strong)
        pjournal = paper.get("journal", "").lower()
        if journal_lower and pjournal and journal_lower in pjournal:
            score += 8
        # Journal match in title (moderate — only for multi-word journal names)
        elif journal_lower and journal_lower in title:
            if len(journal_lower) > 7:
                score += 4
            elif len(journal_lower) > 5 and journal_lower not in ('nature', 'science'):
                score += 2

        # Callout keyword overlap with title
        t_words = set(re.findall(r'[a-zA-Z]{4,}', title))
        callout_overlap = len(callout_keywords & t_words)
        if callout_overlap > 0:
            score += callout_overlap * 2

        # Chinese heading keyword hints
        keyword_hints = {
            '电磁波形': 'electromagnetic waveform',
            '全光': 'all-optical',
            '退磁': 'demagnetization polarization phonon',
            '阿秒电子显微': 'attosecond electron microscopy sub-cycle',
            '电子衍射': 'electron diffraction 4d visualization transition',
            '波形电子显微': 'waveform electron microscopy',
            '光波电子': 'light-field charge carrier',
            'Bloch振荡': 'bloch oscillation', 'Bloch': 'bloch oscillation',
            '谷电子': 'valleytronics', '布洛赫': 'bloch',
            '逻辑门': 'logic gate',
            '纳米球': 'nanosphere nanoshell dielectric',
            '等离激元': 'plasmonic',
            '隧穿': 'tunneling tunneling',
            'attoclock': 'attoclock', 'streaking': 'streaking',
            '频率梳': 'frequency comb',
            '双光学选通': 'double optical gating dog',
            '水窗': 'water window',
            '阿秒动量显微': 'lightwave valleytronics momentum microscopy',
            '固体 HHG': 'solid high harmonic',
        }
        hw = set(heading_words)
        for cn, en in keyword_hints.items():
            if heading and cn in heading:
                hw.update(en.lower().split())

        kw_score = len(hw & t_words)
        if kw_score > 0:
            score += kw_score * 3

        scored.append((new_dir, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    if not scored:
        return None

    best_dir, best_score = scored[0]
    second_score = scored[1][1] if len(scored) > 1 else -99

    # Strong match: score >= 3
    if best_score >= 3:
        return best_dir

    # Moderate match: score >= 1 with clear gap to second
    if best_score >= 1 and (best_score - second_score) >= 2:
        return best_dir

    # Last resort: exact year match with exactly one paper
    if year:
        ym = [d for d, p in all_papers if p.get("year") == year]
        if len(ym) == 1:
            return ym[0]

    return None

def extract_fig_number_from_callout(content, old_dir, old_fname):
    """Extract paper figure number from the closest callout line above the ref.
    Takes the FIRST Fig. number from the source citation."""
    pattern = re.compile(
        r'!\[\[6️⃣\s*工具[/\\]visualizations[/\\]' + re.escape(old_dir) + r'[/\\]'
        + re.escape(old_fname) + r'\]\]'
    )
    m = pattern.search(content)
    if not m:
        return None

    # Get the text between this ref and the previous ref (or start of content)
    before = content[max(0, m.start() - 3000):m.start()]
    # Find all Fig. numbers in source citations in this window
    # Format: "（来源：Author Year Journal, Fig. N）" or "来源：..., Fig. N"
    # When multiple like "Fig. 2 + Fig. 3", take the first one (2)
    fig_nums = re.findall(r'Fig\.\s*(\d+)', before, re.IGNORECASE)
    if fig_nums:
        # Take the first Fig number from the closest source line
        # The closest source line is at the end of 'before'
        # Find the last source line and take its first Fig number
        source_lines = [l for l in before.split('\n') if re.search(r'fig\.', l, re.IGNORECASE) and ('来源' in l or 'source' in l.lower())]
        if source_lines:
            nums = re.findall(r'Fig\.\s*(\d+)', source_lines[-1], re.IGNORECASE)
            if nums:
                return int(nums[0])
        return int(fig_nums[-1])
    return None

def find_new_figure(paper_data, fig_number):
    """Find new figure filename by matching Fig. number in caption or label."""
    if fig_number is None:
        return None
    for fig in paper_data.get("figures", []):
        caption = fig.get("caption", "")
        label = fig.get("label", "")
        # Match "Fig. N", "Figure N", "FIG. N" at start
        m = re.match(r'Fig(?:ure)?\.?\s*(\d+)', caption.strip(), re.IGNORECASE)
        if not m:
            m = re.match(r'Fig(?:ure)?\.?\s*(\d+)', label.strip(), re.IGNORECASE)
        if m and int(m.group(1)) == fig_number:
            path = fig.get("image_path", "")
            return Path(path).name
    return None

def find_all_old_refs_with_filenames(content):
    """Find all old figure refs: [(old_dir, old_fname, full_match), ...]"""
    refs = re.findall(
        r'!\[\[(6️⃣\s*工具[/\\]visualizations[/\\]([a-f0-9]{8,16})[/\\]([^\]]+\.png))\]\]',
        content
    )
    return refs  # [(full_path, old_dir, old_fname), ...]

def main():
    DRY_RUN = False  # Verify FIRST, then set to False

    all_papers = {}
    for prof_key in PROF_KEY_TO_FILE:
        ef = EXTRACTED_DIR / f"{prof_key}_extracted.json"
        if ef.exists():
            with open(ef, encoding='utf-8') as f:
                data = json.load(f)
            papers = {}
            for p in data.get("papers", []):
                pid = p.get("paper_id", "")
                if pid:
                    papers[pid[:8]] = p
            all_papers[prof_key] = papers

    total_reps = 0
    profiles_fixed = 0

    for prof_key, filename in PROF_KEY_TO_FILE.items():
        profile_path = PROFILE_DIR / filename
        if not profile_path.exists():
            continue
        papers = all_papers.get(prof_key, {})
        if not papers:
            continue

        with open(profile_path, encoding='utf-8') as f:
            content = f.read()

        # Find all old refs
        old_refs = find_all_old_refs_with_filenames(content)
        if not old_refs:
            continue

        broken_refs = [(fp, od, ofn) for fp, od, ofn in old_refs
                       if not (VIZ_BASE / od).exists()]
        if not broken_refs:
            continue

        # Map old dirs to new dirs
        dir_map = {}
        for _, old_dir, _ in broken_refs:
            if old_dir in dir_map:
                continue
            override = MANUAL_OVERRIDES.get((prof_key, old_dir))
            if override:
                dir_map[old_dir] = override
            else:
                best = match_old_dir_to_paper(papers, old_dir, content, prof_key)
                if best:
                    dir_map[old_dir] = best

        print(f"\n  {prof_key}: {len(broken_refs)} broken refs in {len(set(d for _,d,_ in broken_refs))} dirs")

        # For each broken ref, find the matching new figure and replace
        # ONLY replace when BOTH directory AND filename can be matched
        new_content = content
        reps = 0
        for full_path, old_dir, old_fname in broken_refs:
            new_dir = dir_map.get(old_dir)
            if not new_dir:
                continue

            paper_data = papers.get(new_dir, {})
            fig_number = extract_fig_number_from_callout(content, old_dir, old_fname)
            new_fname = find_new_figure(paper_data, fig_number)

            if new_fname and new_fname != old_fname:
                old_ref = f"![[{full_path}]]"
                new_ref = f"![[6️⃣ 工具/visualizations/{new_dir}/{new_fname}]]"
                if old_ref in new_content:
                    new_content = new_content.replace(old_ref, new_ref)
                    reps += 1
                    if reps <= 15:
                        print(f"    {old_dir}/{old_fname} -> {new_dir}/{new_fname}")
            # If no fig match found, leave the reference unchanged
            # (changing only the directory would create an equally broken path)

        print(f"    => {reps} replacements")
        total_reps += reps

        if not DRY_RUN and reps > 0:
            backup = profile_path.with_suffix(".md.bak")
            with open(backup, 'w', encoding='utf-8') as f:
                f.write(content)
            with open(profile_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"    => WROTE {filename}")
            profiles_fixed += 1

    if DRY_RUN:
        print(f"\n=== DRY RUN: would fix {total_reps} references ===")
    else:
        print(f"\n=== DONE: {profiles_fixed} profiles, {total_reps} replacements ===")

if __name__ == "__main__":
    main()
