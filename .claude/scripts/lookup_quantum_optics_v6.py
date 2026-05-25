import urllib.request
import json
import time
import sys

# Specific high-impact quantum optics review papers and textbooks
# Using verified and well-known DOIs plus keyword searches

dois = [
    # === Cavity QED ===
    '10.1103/RevModPhys.75.109',   # ?
    '10.1103/RevModPhys.73.319',   # ?
    '10.1103/RevModPhys.87.983',   # ?

    # === Miller et al single photons ===
    '10.1364/AOP.12.S2S1',
    '10.1364/AOP.12.S2S2',

    # === Eisert & Plenio ===
    '10.1103/RevModPhys.84.611',

    # === Leggett macroscopic Q ===
    '10.1103/RevModPhys.73.307',

    # === Walls review ===
    '10.1038/306141a0',
    '10.1038/324210a0',

    # === Mandel & Wolf textbook ===
    '10.1017/CBO9781139644105',

    # === Vogel Welsch textbook ===
    '10.1007/978-3-540-73526-1',
    '10.1007/978-3-662-04310-5',

    # === Gerry Knight ===
    '10.1017/CBO9780511791238',

    # === Fox quantum optics ===
    '10.1093/acprof:oso/9780198566731.001.0001',

    # === Kok & Lovett intro to optical quantum computing ===
    '10.1007/978-3-319-99461-6',

    # === Dowling & Milburn ===
    '10.1098/rsta.2003.1292',
    '10.1103/RevModPhys.85.1103',

    # === Agarwal quantum optics textbook ===
    '10.1017/CBO9780511794222',

    # === Eisert entanglement ===
    '10.1103/RevModPhys.81.865',  # already found - Horodecki

    # === Gisin entanglement ===
    '10.1016/S0370-1573(02)00150-5',

    # === Zoller quantum computing ===
    '10.1103/RevModPhys.74.145',   # Gisin crypto - found

    # === Braunstein continuous variable ===
    '10.1038/nphoton.2007.223',   # wrong - nano optics

    # === O'Brien photonic quantum computing ===
    '10.1038/nphoton.2009.229',

    # === Dowling quantum imaging ===
    '10.1080/09500340802594046',

    # === Pan quantum teleportation ===
    '10.1103/RevModPhys.84.777',

    # === Ralph & Olson quantum computing with linear optics ===
    '10.1103/RevModPhys.79.555',

    # === Quantum state discrimination ===
    '10.1103/RevModPhys.81.865',

    # === Bell nonlocality ===
    '10.1103/RevModPhys.86.419',  # already found

    # === Grangier single photon ===
    '10.1209/0295-5075/1/4/004',
    '10.1007/s00340-004-1558-0',

    # === Walmsley quantum optics ===
    '10.1088/0953-4075/38/9/R01',

    # === Lvovsky quantum optics review ===
    '10.1007/s00340-015-6136-z',
]

seen = set()
for doi in dois:
    if doi in seen:
        continue
    seen.add(doi)
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,authors,year,citationCount,journal,externalIds"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            data = json.loads(raw)

        authors = ', '.join([a['name'] for a in data.get('authors', [])[:5]])
        if len(data.get('authors', [])) > 5:
            authors += ' et al.'

        j = data.get('journal', {})
        jinfo = ""
        if j:
            parts = []
            if j.get('name'): parts.append(j['name'])
            if j.get('volume'): parts.append(f"v{j['volume']}")
            if j.get('pages'): parts.append(f"pp{j['pages']}")
            jinfo = ' '.join(parts)

        title = data.get('title', '')
        cite = data.get('citationCount', 0)
        year = data.get('year', '')

        print(f"FOUND|{doi}|{title}|{authors}|{year}|{jinfo}|{cite}")
        sys.stdout.flush()

    except urllib.error.HTTPError as e:
        if e.code == 404:
            pass
        elif e.code == 429:
            print(f"RATE_LIMITED|{doi}|sleeping 15s")
            sys.stdout.flush()
            time.sleep(15)
        else:
            print(f"HTTP_{e.code}|{doi}")
            sys.stdout.flush()
    except Exception as e:
        print(f"ERROR|{doi}|{str(e)[:80]}")
        sys.stdout.flush()

    time.sleep(2)

print("\n=== Done ===")
