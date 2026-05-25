import urllib.request
import json
import time
import sys

# More targeted DOIs for specific quantum optics review topics
dois = [
    # === Cavity QED ===
    '10.1103/RevModPhys.87.983',    # Raimond et al 2001? or 2015?
    '10.1103/RevModPhys.85.823',    # Walther cavity QED?
    '10.1103/RevModPhys.86.139',    # maybe quantum optomechanics
    '10.1103/RevModPhys.84.623',    # maybe single-photon sources RMP
    '10.1103/RevModPhys.80.541',    # maybe cavity QED

    # === Aspelmeyer quantum optomechanics ===
    '10.1103/RevModPhys.86.1391',   # might not exist
    '10.1364/AOP.6.000337',         # maybe not right DOI

    # === Kimble cavity QED ===
    '10.1038/35146651',

    # === Single photon sources ===
    '10.1038/nphoton.2007.223',     # Lal nano-optics (wrong)

    # === More targeted searches ===
    '10.1103/RevModPhys.58.1001',   # older RMP
    '10.1103/RevModPhys.62.867',    # Carmichael?
    '10.1103/RevModPhys.62.347',    # Loudon?

    # === Quantum state tomography ===
    '10.1103/RevModPhys.81.299',    # Lvovsky continuous-variable tomography
    '10.1088/0953-4075/42/11/114005',
    '10.1002/1521-3889(200211)11:11<549::AID-ANDP549>3.0.CO;2-G',

    # === Quantum decoherence ===
    '10.1002/(SICI)1521-3889(199812)7:12<873::AID-ANDP873>3.0.CO;2-5',
    '10.1103/RevModPhys.76.1267',   # maybe Joos Zeh?
    '10.1103/RevModPhys.75.715',    # maybe decoherence
    '10.1103/RevModPhys.75.108',    # maybe decoherence

    # === Photon statistics / quantum optics review ===
    '10.1016/S0079-6727(99)00011-2',
    '10.1103/RevModPhys.71.1',      # Mandel?
    '10.1103/RevModPhys.70.1009',   # already tried

    # === Gerry & Knight textbook ===
    '10.1017/CBO9780511791238',

    # === Fox textbook ===
    '10.1093/acprof:oso/9780198566731.001.0001',

    # === Walls & Milburn textbook ===
    '10.1007/978-3-662-04310-5',
    '10.1007/978-3-540-28874-7',
    '10.1007/978-3-319-99461-6',

    # === Mandel & Wolf textbook ===
    '10.1017/CBO9781139644105',

    # === Agarwal textbook ===
    '10.1017/CBO9780511794222',

    # === Quantum optics key experiments ===
    '10.1103/PhysRevLett.57.2547',  # squeezing
    '10.1038/41948',                 # teleportation
    '10.1038/37519',

    # === Advances in Optics and Photonics ===
    '10.1364/AOP.12.000416',
    '10.1364/AOP.11.000356',
    '10.1364/AOP.10.000247',
    '10.1364/AOP.8.000337',
    '10.1364/AOP.7.000456',
    '10.1364/AOP.6.000337',
    '10.1364/AOP.5.000271',
    '10.1364/AOP.4.000306',
    '10.1364/AOP.3.000306',
    '10.1364/AOP.3.000242',
    '10.1364/AOP.2.000395',
    '10.1364/AOP.1.1.000001',

    # === Nature Photonics reviews ===
    '10.1038/s41566-022-01094-1',
    '10.1038/s41566-021-00913-2',
    '10.1038/s41566-020-00757-6',
    '10.1038/s41566-019-0539-3',
    '10.1038/s41566-019-0485-0',
    '10.1038/s41566-018-0303-3',
    '10.1038/s41566-018-0288-y',
    '10.1038/nphoton.2017.85',
    '10.1038/nphoton.2016.238',
    '10.1038/nphoton.2015.11',
    '10.1038/nphoton.2014.298',
    '10.1038/nphoton.2014.192',
    '10.1038/nphoton.2013.342',
    '10.1038/nphoton.2012.342',
    '10.1038/nphoton.2011.334',

    # === Science / Nature landmark ===
    '10.1126/science.282.5389.706',
    '10.1126/science.1076452',
    '10.1126/science.285.5425.251',
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
        print(f"ERROR|{doi}|{str(e)[:60]}")
        sys.stdout.flush()

    time.sleep(1.5)

print("\n=== Done ===")
