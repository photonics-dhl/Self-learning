import urllib.request
import json
import time
import sys

dois = [
    # === More targeted ===
    '10.1103/RevModPhys.87.983',    # Raimond cavity QED?
    '10.1103/RevModPhys.85.823',    # ?
    '10.1103/RevModPhys.86.139',    # ?
    '10.1103/RevModPhys.84.623',    # ?
    '10.1103/RevModPhys.80.541',    # ?

    # === RMP more ===
    '10.1103/RevModPhys.95.035001',
    '10.1103/RevModPhys.96.015001',
    '10.1103/RevModPhys.96.035002',

    # === Schoelkopf & Girvin circuit QED ===
    '10.1063/1.5114138',            # Physics Today
    '10.1103/Physics.1.10',         # Physics viewpoint

    # === Single photon detection ===
    '10.1364/AOP.12.S2S2',         # AOP single photon detection?

    # === Lvovsky quantum optics review ===
    '10.1088/2058-6272/aab1c0',     # wrong
    '10.1016/j.physrep.2018.07.001',

    # === textbook DOIs I haven't tried ===
    '10.1007/978-3-540-73526-1',    # Scully Zubairy?
    '10.1007/978-3-319-99461-6',    # Vogel Welsch
    '10.1007/978-3-662-04310-5',    # ?
    '10.1017/CBO9781139644105',     # ?
    '10.1017/CBO9780511791238',     # ?
    '10.1093/acprof:oso/9780198566731.001.0001',  # Fox
    '10.1017/CBO9780511813993',     # Scully Zubairy frontmatter

    # === Scully Zubairy actual book DOI ===
    '10.1017/CBO9780511813986',

    # === Let me try keyword search for specific topics ===
]

# First do the remaining DOIs
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
            print(f"RATE_LIMITED|{doi}")
            sys.stdout.flush()
            time.sleep(15)
        else:
            print(f"HTTP_{e.code}|{doi}")
            sys.stdout.flush()
    except Exception as e:
        print(f"ERROR|{doi}|{str(e)[:80]}")
        sys.stdout.flush()

    time.sleep(1.5)

# Now do keyword searches
print("\n=== KEYWORD SEARCHES ===")
queries = [
    "cavity QED review",
    "single photon source review",
    "quantum state tomography review",
    "quantum decoherence review",
    "squeezed light review",
    "photon statistics review quantum optics",
    "quantum entanglement review",
    "quantum optics experimental techniques review",
]

for q in queries:
    try:
        qenc = urllib.request.quote(q)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={qenc}&limit=5&fields=title,authors,year,citationCount,journal,externalIds&year=1995-2025&fieldsOfStudy=Physics"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
            data = json.loads(raw)

        print(f"\n--- Query: '{q}' ---")
        for p in data.get('data', []):
            authors = ', '.join([a['name'] for a in p.get('authors', [])[:4]])
            if len(p.get('authors', [])) > 4:
                authors += ' et al.'
            doi = p.get('externalIds', {}).get('DOI', 'N/A')
            cite = p.get('citationCount', 0)
            year = p.get('year', '')
            title = p.get('title', '')
            j = p.get('journal', {})
            jinfo = j.get('name', '') if j else ''
            print(f"  {doi}|{title}|{authors}|{year}|{jinfo}|{cite}")

        sys.stdout.flush()

    except Exception as e:
        print(f"ERROR search '{q}': {str(e)[:60]}")
        sys.stdout.flush()

    time.sleep(3)

print("\n=== Done ===")
