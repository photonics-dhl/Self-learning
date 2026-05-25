import urllib.request
import json
import time
import sys

dois = [
    # === Aharonovich single photon sources review ===
    '10.1038/nphoton.2011.24',
    '10.1038/nphoton.2016.182',

    # === Eisert entanglement review ===
    '10.1002/1521-3889(200211)11:11<549::AID-ANDP549>3.0.CO;2-G',

    # === Single photon review Eisaman ===
    '10.1103/RevModPhys.83.33',
    '10.1088/0953-4075/44/9/093001',

    # === Zwiller single photon ===
    '10.1016/j.repl.2012.07.001',

    # === Bucklew & Kan review quantum detection ===
    '10.1016/S0370-1573(00)00020-5',

    # === Lvovsky & Raymer continuous variable tomography ===
    '10.1103/RevModPhys.81.299',  # found but only 53 citations? check again

    # === Quantum tomography review ===
    '10.1007/s00340-015-6136-z',

    # === Paris et al quantum tomography ===
    '10.1007/3-540-44939-8_1',

    # === Leonhardt quantum state measurement ===
    '10.1007/978-3-662-03747-0',

    # === Hadamard tomography ===
    '10.1103/RevModPhys.82.1889',

    # === Mandel wolf review article ===
    '10.1364/JOSA.51.00897',

    # === Mandel review 1999 ===
    '10.1103/RevModPhys.71.S240',

    # === Agarwal quantum optics reviews ===
    '10.1016/S0370-1573(02)00166-9',
    '10.1103/RevModPhys.68.591',

    # === Carmichael statistical methods ===
    '10.1007/978-3-662-05377-7',

    # === Gardiner & Zoller quantum noise ===
    '10.1007/978-3-662-04115-3',

    # === Plenio & Knight review decoherence ===
    '10.1103/RevModPhys.70.101',

    # === Leggett review macroscopic quantum ===
    '10.1103/RevModPhys.73.307',  # found

    # === Joos & Zeh decoherence ===
    '10.1007/BF00753907',

    # === Schlosshauer decoherence review ===
    '10.1103/RevModPhys.76.1267',  # found

    # === Zurek decoherence review ===
    '10.1103/RevModPhys.75.715',  # found

    # === Huang quantum optics in semiconductor nanostructures ===
    '10.1088/0034-4885/66/6/203',

    # === Roy & Olive review ===
    '10.1016/j.physrep.2017.05.002',

    # === Dowling & Milburn review ===
    '10.1098/rsta.2003.1292',  # wrong
    '10.1103/RevModPhys.85.1103',  # encoding error

    # === Quantum electrodynamics in circuits - Blais ===
    '10.1103/PhysRevA.69.062320',

    # === Waltraff circuit QED ===
    '10.1038/nature02842',

    # === Schoelkopf & Girvin Physics Today ===
    '10.1063/1.2794087',

    # === Gu et al microwave quantum optics review ===
    '10.1016/j.physrep.2016.10.001',
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
