import urllib.request
import json
import time
import sys

dois = [
    # === Squeezed light / quantum optics fundamentals ===
    '10.1103/RevModPhys.77.513',    # Braunstein & van Loock - CV quantum info
    '10.1103/RevModPhys.82.1155',   # Clerk et al - Quantum noise, measurement
    '10.1103/RevModPhys.86.187',    # Aspelmeyer - Quantum optomechanics
    '10.1103/RevModPhys.89.035002', # Degen - Quantum sensing
    '10.1103/RevModPhys.90.035005', # Pezze - Quantum metrology
    '10.1103/RevModPhys.92.025002', # Xu - QKD with realistic devices
    '10.1103/RevModPhys.85.1083',   # Haroche Nobel lecture

    # === More RMP reviews to try ===
    '10.1103/RevModPhys.96.045001',
    '10.1103/RevModPhys.95.035001',
    '10.1103/RevModPhys.94.015001',
    '10.1103/RevModPhys.93.041003',
    '10.1103/RevModPhys.87.137',
    '10.1103/RevModPhys.87.983',
    '10.1103/RevModPhys.86.139',
    '10.1103/RevModPhys.85.823',
    '10.1103/RevModPhys.84.623',
    '10.1103/RevModPhys.83.771',
    '10.1103/RevModPhys.82.2313',
    '10.1103/RevModPhys.81.865',
    '10.1103/RevModPhys.80.541',
    '10.1103/RevModPhys.79.55',
    '10.1103/RevModPhys.78.1137',

    # === Laser & Photonics Reviews ===
    '10.1002/lpor.202000215',
    '10.1002/lpor.202000029',
    '10.1002/lpor.201900103',
    '10.1002/lpor.201800272',
    '10.1002/lpor.201700243',
    '10.1002/lpor.201600253',

    # === Photonics Reviews / JOSA B ===
    '10.1364/JOSAB.37.000C10',

    # === Reviews on squeezed light specifically ===
    '10.1364/JOSAB.4.001550',       # Slusher review on squeezed light
    '10.1364/JOSAB.4.001453',       # Walls review on squeezing

    # === J Phys B / J Phys A ===
    '10.1088/0953-4075/39/18/R01',
    '10.1088/0953-4075/38/9/R01',
    '10.1088/1751-8121/49/46/463001',
    '10.1088/0953-4075/42/11/114005',

    # === Optica / OSA ===
    '10.1364/OPTICA.6.000467',
    '10.1364/OPTICA.3.000232',

    # === PRA/PRL famous ===
    '10.1103/PhysRevLett.55.2409',  # Slusher squeezed light
    '10.1103/PhysRevA.33.4033',     # Walls squeezed states
    '10.1103/PhysRevA.46.679',      # quantum state tomography

    # === Science/Nature famous ===
    '10.1126/science.1081018',
    '10.1038/38647',

    # === Actual review papers in Nature Rev Phys ===
    '10.1038/s42254-020-0186-5',
    '10.1038/s42254-019-0115-x',
    '10.1038/s42254-019-0090-2',

    # === Proc. Royal Society ===
    '10.1098/rspa.2004.1352',

    # === Springer Handbook ===
    '10.1007/978-3-030-83027-0',

    # === Cambridge / Oxford textbooks ===
    '10.1017/CBO9780511813993',      # Scully & Zubairy
    '10.1017/CBO9781139644605',      # Gerry & Knight
    '10.1017/CBO9780511813993',      # Scully & Zubairy (duplicate, skip)
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
            data = json.loads(resp.read().decode('utf-8', errors='replace'))

        authors = ', '.join([a['name'] for a in data.get('authors', [])[:6]])
        if len(data.get('authors', [])) > 6:
            authors += ' et al.'

        j = data.get('journal', {})
        jinfo = f"{j.get('name','')} v{j.get('volume','')} pp{j.get('pages','')}" if j else ''

        title = data.get('title', '')
        # Filter: only show if quantum-related keywords in title
        title_lower = title.lower()
        quantum_keywords = ['quantum', 'squeez', 'entangl', 'photon', 'cavity', 'qed', 'coheren',
                          'decoheren', 'tomograph', 'single-photon', 'nonclassical', 'non-classical',
                          'optomech', 'optical', 'laser', 'atom', 'light', 'beam split',
                          'teleport', 'cryptography', 'qubit', 'qkd', 'review']

        # Show all for now, mark relevance
        relevant = any(kw in title_lower for kw in quantum_keywords)
        mark = ">>>" if relevant else "   "

        print(f"{mark}FOUND|{doi}|{title}|{authors}|{data.get('year','')}|{jinfo}|{data.get('citationCount',0)}")
        sys.stdout.flush()

    except urllib.error.HTTPError as e:
        if e.code == 404:
            pass  # silent skip
        elif e.code == 429:
            print(f"RATE_LIMITED|{doi}| sleeping 15s")
            sys.stdout.flush()
            time.sleep(15)
        else:
            print(f"HTTP_ERROR|{doi}|{e.code}")
            sys.stdout.flush()
    except Exception as e:
        print(f"ERROR|{doi}|{str(e)[:80]}")
        sys.stdout.flush()

    time.sleep(2)

print("\n=== Done ===")
