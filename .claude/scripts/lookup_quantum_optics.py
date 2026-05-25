import urllib.request
import json
import time
import sys

dois = [
    # === Quantum optics fundamentals (squeezed light, entanglement, photon statistics) ===
    '10.1103/RevModPhys.77.513',  # Braunstein & van Loock - Quantum info with continuous variables
    '10.1103/RevModPhys.82.1155', # Weedbrook et al - Gaussian quantum info
    '10.1103/RevModPhys.85.553',  # Adesso et al - Continuous variable quantum info
    '10.1103/RevModPhys.74.145',  # Mandel & Wolf review
    '10.1103/RevModPhys.70.1009', # Scully review
    '10.1103/RevModPhys.75.107',  # Zoller quantum optics
    '10.1103/RevModPhys.83.33',   # Quantum decoherence
    '10.1103/RevModPhys.84.77',   # Quantum optomechanics
    '10.1103/RevModPhys.84.623',  # Single photon sources
    '10.1103/RevModPhys.73.319',  # Blatt & Zoller quantum computing with ions
    '10.1103/RevModPhys.80.541',  # Ekert quantum cryptography
    '10.1103/RevModPhys.78.1137', # Zoller quantum comms
    '10.1103/RevModPhys.85.1083', # O'Brien photonic quantum computing
    '10.1103/RevModPhys.86.187',  # Aspelmeyer quantum optomechanics
    '10.1103/RevModPhys.81.299',  # Schleich quantum optics in phase space
    '10.1103/RevModPhys.75.457',  # Bouwmeester quantum teleportation
    '10.1103/RevModPhys.82.2313', # Polkovnikov quantum quench
    '10.1103/RevModPhys.92.025002', # Recent RMP
    '10.1103/RevModPhys.93.025001',
    '10.1103/RevModPhys.90.035005',
    '10.1103/RevModPhys.89.035002',
    '10.1103/RevModPhys.88.021002',

    # === Advances in Optics and Photonics ===
    '10.1364/AOP.3.000306',
    '10.1364/AOP.5.000271',
    '10.1364/AOP.6.000337',
    '10.1364/AOP.7.000456',
    '10.1364/AOP.2.000395',
    '10.1364/AOP.9.000356',
    '10.1364/AOP.1.1.000001',

    # === Nature Photonics ===
    '10.1038/nphoton.2009.251',
    '10.1038/nphoton.2012.326',
    '10.1038/nphoton.2007.223',
    '10.1038/nphoton.2013.271',
    '10.1038/s41566-018-0320-2',
    '10.1038/s41566-019-0552-6',
    '10.1038/s41566-020-00721-4',
    '10.1038/nphoton.2016.182',
    '10.1038/nphoton.2014.192',
    '10.1038/nphoton.2015.12',

    # === Nature Physics / Nature Reviews ===
    '10.1038/nphys1286',
    '10.1038/nphys2355',
    '10.1038/s42254-019-0084-3',
    '10.1038/s42254-020-0177-6',
    '10.1038/s42254-021-00355-z',
    '10.1038/s42254-022-00449-5',

    # === Reports on Progress in Physics ===
    '10.1088/0034-4885/66/9/201',
    '10.1088/0034-4885/80/1/016001',
    '10.1088/0034-4885/82/1/012001',
    '10.1088/1361-6633/aa9119',
    '10.1088/1361-6633/ab0123',
    '10.1088/0034-4885/74/7/074401',
    '10.1088/0034-4885/68/8/R01',
    '10.1088/0034-4885/68/5/R01',

    # === PRL/Laser & Photonics Reviews / other ===
    '10.1002/lpor.201100026',
    '10.1002/lpor.201500030',
    '10.1002/lpor.202000039',

    # === Textbooks ===
    '10.1017/CBO9780511813993',
    '10.1007/978-3-540-73526-1',
    '10.1093/acprof:oso/9780198506730.001.0001',
    '10.1007/978-3-319-99461-6',
    '10.1017/CBO9781139168297',
]

found = 0
for doi in dois:
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,authors,year,citationCount,journal,externalIds"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        authors = ', '.join([a['name'] for a in data.get('authors', [])[:5]])
        if len(data.get('authors', [])) > 5:
            authors += ' et al.'

        j = data.get('journal', {})
        jinfo = f"{j.get('name','')} v{j.get('volume','')} pp{j.get('pages','')}" if j else ''

        print(f"FOUND|{doi}|{data.get('title','')}|{authors}|{data.get('year','')}|{jinfo}|{data.get('citationCount',0)}")
        found += 1
        sys.stdout.flush()

    except Exception as e:
        err = str(e)
        if '404' in err:
            print(f"NOT_FOUND|{doi}|")
        elif '429' in err:
            print(f"RATE_LIMITED|{doi}| sleeping 10s")
            time.sleep(10)
        else:
            print(f"ERROR|{doi}|{err}")
        sys.stdout.flush()

    time.sleep(2)

print(f"\n=== Summary: {found}/{len(dois)} found ===")
