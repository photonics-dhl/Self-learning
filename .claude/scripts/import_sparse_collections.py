#!/usr/bin/env python3
"""Import top papers for sparse Postdoc collections via OpenAlex."""

import requests, sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')
for v in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(v, None)

headers = {
    'User-Agent': 'Mozilla/5.0 (Python AcademicResearchBot/1.0; mailto:dhl@research.org)',
    'Accept': 'application/json'
}

physics_keywords = ['attosecond', 'femtosecond', 'ultrafast', 'laser', 'harmonic', 'x-ray', 'xuv',
                    'terahertz', 'thz', 'optical', 'photon', 'electron', 'pulse', 'spectroscopy',
                    'nonlinear', 'photoemission', 'ionization', 'tunneling', 'waveform', 'soliton',
                    'semiconductor', 'graphene', 'valley', 'bloch', 'exciton', 'phonon', 'plasmon',
                    'nanotip', 'nanoparticle', 'nanoscale', 'diffraction', 'imaging', 'coherent',
                    'carrier', 'band', 'quantum cascade', 'frequency comb', 'waveguide', 'photonic',
                    'mode-lock', 'sesam', 'saturable', 'supercontinuum', 'oscillator',
                    'streaking', 'soft x', 'euv', 'extreme ultraviolet', 'mid-infrared',
                    'few-cycle', 'sub-cycle', 'lightwave', 'field-driven',
                    'time-resolved', 'pump-probe', 'transient', 'dielectric laser',
                    'free-electron', 'high-harmonic', 'high order', 'near-field',
                    'nanophoton', 'surface plasmon', 'rogue wave', 'soliton molecule',
                    'ultrashort', 'few cycle', 'sub cycle']


def is_physics_paper(title, journal, authors_str):
    text = (title + ' ' + journal + ' ' + ' '.join(authors_str)).lower()
    return any(kw in text for kw in physics_keywords)


scholars = {
    'murnane': {
        'author_id': 'A5082853262', 'name': 'Murnane', 'collection': '9A6A63UM',
        'existing_dois': {'10.1126/science.280.5368.1412', '10.1126/science.1218497',
                          '10.1126/science.aaa1394', '10.1038/nphoton.2014.293'}
    },
    'kling': {
        'author_id': 'A5087798025', 'name': 'Kling', 'collection': 'V782UP9W',
        'existing_dois': {'10.1038/nphoton.2011.258', '10.1038/nature09212',
                          '10.1038/nature05648', '10.1126/science.1126259',
                          '10.1038/nphys1983', '10.48550/arXiv.2604.15085'}
    },
    'leone': {
        'author_id': 'A5065870462', 'name': 'Leone', 'collection': 'ZALV9WIK',
        'existing_dois': {'10.1038/nature09212', '10.1126/science.1260311',
                          '10.1038/s41570-018-0008-8', '10.48550/arXiv.2602.09565',
                          '10.1103/kfjh-zc96'}
    },
    'keller': {
        'author_id': 'A5044432958', 'name': 'Keller', 'collection': 'P8QNDVZI',
        'existing_dois': {'10.1038/nature01938', '10.1126/science.1163439',
                          '10.1038/nphys982', '10.1126/science.286.5444.1507',
                          '10.1038/nphys2125', '10.1126/science.aag1268',
                          '10.1016/j.physrep.2014.09.002'}
    },
    'chang': {
        'author_id': 'A5033727414', 'name': 'Chang', 'collection': '4W3A4ZQE',
        'existing_dois': {'10.1126/science.280.5368.1412', '10.1038/nphoton.2013.362',
                          '10.1038/s41467-020-16480-6', '10.1038/nphoton.2014.48',
                          '10.1364/OL.42.001816'}
    },
    'ropers': {
        'author_id': 'A5024251066', 'name': 'Ropers', 'collection': '64XUBNXA',
        'existing_dois': {'10.1038/nature06402', '10.1126/science.aal5326',
                          '10.1038/nature14463', '10.1103/PhysRevLett.102.086809',
                          '10.1038/nature10878'}
    },
    'huber': {
        'author_id': 'A5013199236', 'name': 'Huber', 'collection': 'DMMMLJ28',
        'existing_dois': {'10.1088/1361-6463/50/4/043001', '10.1038/nphoton.2013.349',
                          '10.1038/35104522', '10.1038/nature14652',
                          '10.1038/s41586-018-0013-6', '10.1088/2053-1583/ae2b82',
                          '10.48550/arXiv.2602.12844'}
    },
}

all_new_papers = {}

for key, s in scholars.items():
    try:
        url = 'https://api.openalex.org/works'
        params = {
            'mailto': 'dhl@research.org',
            'filter': f'author.id:{s["author_id"]}',
            'sort': 'cited_by_count:desc',
            'per_page': 25
        }
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()

        new_papers = []
        for w in data.get('results', []):
            doi = (w.get('doi') or '').replace('https://doi.org/', '')
            if not doi or doi in s['existing_dois']:
                continue
            title = w.get('title', '')
            year = w.get('publication_year', '')
            cites = w.get('cited_by_count', 0)
            journal = ''
            if w.get('primary_location') and w['primary_location'].get('source'):
                journal = w['primary_location']['source'].get('display_name', '')

            creators = []
            author_names = []
            for auth in w.get('authorships', []):
                a = auth.get('author', {})
                if a.get('display_name'):
                    name = a['display_name']
                    author_names.append(name)
                    parts = name.split(' ', 1)
                    last = parts[-1] if len(parts) > 1 else name
                    first = parts[0] if len(parts) > 1 else ''
                    creators.append({'creatorType': 'author', 'firstName': first, 'lastName': last})

            # Verify target author in author list
            target_last = s['name'].lower()
            author_last_names = [c['lastName'].lower() for c in creators]
            if not any(target_last == ln for ln in author_last_names):
                continue

            # Physics filter
            if not is_physics_paper(title, journal, author_names):
                continue

            if len(creators) > 10:
                creators = creators[:10]

            new_papers.append({
                'doi': doi, 'title': title, 'year': str(year),
                'cites': cites, 'journal': journal, 'creators': creators
            })

            if len(new_papers) >= 8:
                break

        all_new_papers[key] = new_papers
        print(f"{s['name']}: {len(new_papers)} filtered new (existing: {len(s['existing_dois'])})")
        for p in new_papers:
            print(f"  {p['doi']} | {p['cites']}c | {p['title'][:90]}")

        with open(f'z:/321/DHL/Self_Learning/.claude/{key}_new_papers.json', 'w', encoding='utf-8') as f:
            json.dump(new_papers, f, ensure_ascii=False, indent=2)

        time.sleep(0.5)
    except Exception as e:
        print(f"{s['name']}: ERROR {e}")

print()
print('=== SUMMARY ===')
total = sum(len(v) for v in all_new_papers.values())
for k, v in all_new_papers.items():
    print(f"  {k}: {len(v)} new -> collection {scholars[k]['collection']}")
print(f'Total new papers to import: {total}')
