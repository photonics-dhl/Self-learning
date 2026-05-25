import urllib.request
import json
import time
import sys

dois = [
    # === Raimond et al cavity QED RMP 2001 ===
    '10.1103/RevModPhys.73.565',

    # === Walther cavity QED ===
    '10.1016/S0030-4018(03)00769-2',
    '10.1016/S0370-1573(01)00025-6',

    # === Hood & Kimble cavity QED ===
    '10.1016/S0030-4018(00)00741-0',

    # === Berman Malyshev review ===
    '10.1088/0953-4075/27/10/001',

    # === Vahala optical microcavities ===
    '10.1038/nature03604',

    # === Single photon sources ===
    '10.1038/nphoton.2007.223',  # wrong
    '10.1038/nature02081',       # Michler
    '10.1038/nature02870',       # Santori
    '10.1038/nature02948',       # Yuan
    '10.1038/nphoton.2013.287',  # maybe
    '10.1038/nphoton.2016.177',  # already wrong

    # === Aharonovich single photon ===
    '10.1038/nphoton.2011.24',
    '10.1038/nphoton.2012.218',

    # === Scheel quantum optics with structured light ===
    '10.1088/0953-4075/42/11/114005',  # already found

    # === Scully quantum optics review RMP ===
    '10.1103/RevModPhys.70.1009',

    # === Quantum measurement ===
    '10.1103/RevModPhys.86.307',
    '10.1103/RevModPhys.85.1083',  # Haroche Nobel - found

    # === Pan multi-photon review ===
    '10.1103/RevModPhys.84.777',   # found

    # === Kok & Braunstein review ===
    '10.1016/S0375-9601(00)00382-9',

    # === Walls & Milburn book DOI ===
    '10.1007/978-3-540-28874-7',

    # === Gerry Knight book DOI ===
    '10.1017/CBO9780511791238',

    # === Scully Zubairy book ===
    '10.1017/CBO9780511813993',  # found

    # === Mandel & Wolf ===
    '10.1017/CBO9781139644105',

    # === Quantum optics in phase space (Schleich) ===
    '10.1002/3527602976',

    # === Bachor & Ralph guide to experiments ===
    '10.1002/9783527622516',

    # === Kok textbook ===
    '10.1007/978-3-319-99461-6',

    # === Ashhab circuit QED ===
    '10.1016/j.physrep.2015.10.002',

    # === Blais circuit QED ===
    '10.1103/PhysRevA.75.032329',  # original circuit QED

    # === Gu et al circuit QED review ===
    '10.1016/j.physrep.2016.12.001',

    # === Quantum optics review in Nature Reviews Physics ===
    '10.1038/s42254-019-0084-3',
    '10.1038/s42254-020-0177-6',
    '10.1038/s42254-021-00355-z',
    '10.1038/s42254-022-00449-5',
    '10.1038/s42254-019-0090-2',
    '10.1038/s42254-019-0115-x',
    '10.1038/s42254-018-0009-4',

    # === Aspelmeyer & Kippenberg cavity optomechanics review ===
    '10.1103/RevModPhys.86.1391',  # found already

    # === Pfeifer et al quantum optics ===
    '10.1103/RevModPhys.85.751',
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
