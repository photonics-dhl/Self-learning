#!/usr/bin/env python3
"""Find top papers for sparse Zotero collections (L'Huillier, Miao, Baum, Gedik)."""

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
                    'ultrashort', 'few cycle', 'sub cycle',
                    'photoionization', 'tomography', 'phase transition', 'charge density wave',
                    'topological', 'berry curvature', 'weyl', 'dirac', 'fermi surface',
                    'photoemission', 'arpes', 'tr-arpes', 'spin', 'magnetism',
                    'electron diffraction', 'electron microscopy', 'coherent diffractive',
                    'ptychography', 'tomography', 'phase retrieval',
                    'electron microscope', 'ultrafast electron', '4d microscopy',
                    'quantum', 'wavefunction', 'molecular', 'atomic']


def is_physics_paper(title, journal, authors_str):
    text = (title + ' ' + journal + ' ' + ' '.join(authors_str)).lower()
    return any(kw in text for kw in physics_keywords)


scholars = {
    'lhuillier': {
        'author_id': 'A5087194862', 'name': "L'Huillier", 'collection': 'CP83C6VV',
        'existing_dois': {'10.1088/1361-6455/aa9735', '10.1038/nature09084',
                          '10.1103/PhysRevA.52.4747', '10.1103/PhysRevLett.74.3776',
                          '10.1103/PhysRevLett.106.143002', '10.1103/PhysRevA.49.2117'}
    },
    'miao': {
        'author_id': 'A5013484038', 'name': 'Miao', 'collection': '2D7JR5YV',
        'existing_dois': {'10.1126/science.aaa1394', '10.1038/s41586-025-09857-4',
                          '10.1126/science.abn3103', '10.1038/22498'}
    },
    'baum': {
        'author_id': 'A5000240801', 'name': 'Baum', 'collection': 'ECGLT9Q6',
        'existing_dois': {'10.1126/science.aaf8589', '10.1038/s41586-023-06074-9',
                          '10.1038/s41586-021-04306-4', '10.1126/science.aae0003',
                          '10.1126/science.1147724'}
    },
    'gedik': {
        'author_id': 'A5006803367', 'name': 'Gedik', 'collection': 'LA976NQY',
        'existing_dois': {'10.1038/s41586-021-04337-x', '10.1038/nphys4146',
                          '10.1038/s41586-018-0807-6', '10.1126/science.1239834'}
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
            'per_page': 50
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

            # Verify target author in author list (handle both curly and straight quotes)
            def normalize_last(name):
                n = name.lower()
                n = n.replace("'", "").replace("’", "").replace("‘", "")
                n = n.strip().rstrip('.')
                return n
            target_last = normalize_last(s['name'])
            author_last_names = [normalize_last(c['lastName']) for c in creators]
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

            if len(new_papers) >= 15:
                break

        all_new_papers[key] = new_papers
        print(f"{s['name']}: {len(new_papers)} new papers (existing: {len(s['existing_dois'])})")
        for p in new_papers:
            print(f"  {p['doi']} | {p['cites']}c | {p['year']} | {p['title'][:100]}")

        out_path = f'z:/321/DHL/Self_Learning/.claude/{key}_new_papers.json'
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(new_papers, f, ensure_ascii=False, indent=2)

        time.sleep(0.5)
    except Exception as e:
        print(f"{s['name']}: ERROR {e}")
        import traceback
        traceback.print_exc()

print()
print('=== SUMMARY ===')
total = sum(len(v) for v in all_new_papers.values())
for k, v in all_new_papers.items():
    print(f"  {k}: {len(v)} new -> collection {scholars[k]['collection']}")
print(f'Total new papers to import: {total}')
