import urllib.request
import json
import time
import sys

dois = [
    # === Cavity QED landmark reviews ===
    '10.1103/RevModPhys.87.983',   # Raimond et al 2001?
    '10.1103/RevModPhys.85.823',   # maybe Kimble?
    '10.1103/RevModPhys.86.139',   # something in RMP 2014?
    '10.1103/RevModPhys.84.623',   # maybe Schoelkopf?
    '10.1103/RevModPhys.80.541',   # something?

    # Kimble Nature 2008 "quantum internet"
    '10.1038/nature07127',

    # Miller Nature Photonics single photon sources
    '10.1038/nphoton.2007.223',    # already known wrong

    # === Single photon sources ===
    '10.1038/s41566-023-01302-5',
    '10.1038/s41566-022-01107-z',
    '10.1038/nphoton.2016.177',
    '10.1038/nphoton.2015.241',

    # === Quantum optics reviews in Nature / Science ===
    '10.1038/41493',               # quantum cryptography?
    '10.1038/35596',               # Zeilinger?
    '10.1038/37561',               # Tonomura?
    '10.1038/44610',

    # === Reports on Progress in Physics - quantum optics ===
    '10.1088/0034-4885/68/8/R01',  # Monaghan - wrong
    '10.1088/0034-4885/74/7/074401',
    '10.1088/0034-4885/75/1/014401',
    '10.1088/0034-4885/77/7/076001',
    '10.1088/0034-4885/78/9/092001',
    '10.1088/0034-4885/79/8/084001',
    '10.1088/1361-6633/aab1c0',
    '10.1088/1361-6633/ab3a7f',
    '10.1088/1361-6633/ab14c2',
    '10.1088/1361-6633/ab3a3e',

    # === J Phys B special issues ===
    '10.1088/0953-4075/47/9/093001',
    '10.1088/0953-4075/48/11/113001',
    '10.1088/0953-4075/49/20/202001',
    '10.1088/2058-6272/aab1c0',
    '10.1088/1367-2630/17/1/012001',
    '10.1088/1367-2630/14/8/085005',
    '10.1088/1367-2630/18/7/073001',
    '10.1088/1367-2630/20/6/063036',

    # === AOP / Optica reviews ===
    '10.1364/OPTICA.4.000823',
    '10.1364/OPTICA.5.000356',
    '10.1364/OPTICA.3.000232',

    # === Entanglement / Bell tests ===
    '10.1103/RevModPhys.82.1917',   # Brunner et al Bell nonlocality?
    '10.1103/RevModPhys.86.419',    # maybe?

    # === Quantum optics textbooks ===
    '10.1007/978-3-319-99461-6',   # Vogel & Welsch
    '10.1007/978-3-662-04310-5',   # older Walls & Milburn?
    '10.1007/978-3-540-28874-7',   # Walls & Milburn 2nd ed?
    '10.1017/CBO9781139644105',    # Mandel & Wolf?
    '10.1017/CBO9780511791238',    # Gerry & Knight 2nd ed?
    '10.1093/acprof:oso/9780198566731.001.0001',  # Fox
    '10.1007/978-3-030-83027-0',   # Springer handbook
    '10.1007/978-3-030-47662-8',   # recent Springer

    # === RMP quantum optics classic ===
    '10.1103/RevModPhys.62.525',   # maybe something
    '10.1103/RevModPhys.63.91',    # maybe
    '10.1103/RevModPhys.64.881',   # maybe
    '10.1103/RevModPhys.65.113',   # maybe
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

print("\n=== Done ===")
