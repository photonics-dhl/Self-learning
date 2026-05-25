#!/usr/bin/env python3
"""Import new papers to Zotero collections via Web API."""

import sys, requests, json, time, os
sys.stdout.reconfigure(encoding='utf-8')
for v in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(v, None)

API_KEY = 'gKXxzW93bZAWlbs0DCN0KVbj'
USER_ID = '20242032'
BASE = f'https://api.zotero.org/users/{USER_ID}'
HEADERS = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}

scholars = {
    'lhuillier': {'collection': 'CP83C6VV', 'name': "L'Huillier"},
    'miao': {'collection': '2D7JR5YV', 'name': 'Miao'},
    'baum': {'collection': 'ECGLT9Q6', 'name': 'Baum'},
    'gedik': {'collection': 'LA976NQY', 'name': 'Gedik'},
}

# First get a journalArticle template
tpl_r = requests.get(f'{BASE}/items/new?itemType=journalArticle', headers=HEADERS)
if tpl_r.status_code != 200:
    print(f'ERROR getting template: {tpl_r.status_code} {tpl_r.text}')
    sys.exit(1)
template = tpl_r.json()

summary = {}

for key, s in scholars.items():
    json_path = f'z:/321/DHL/Self_Learning/.claude/{key}_new_papers.json'
    with open(json_path, encoding='utf-8') as f:
        papers = json.load(f)

    print(f'\n=== {s["name"]} ({s["collection"]}): {len(papers)} papers ===')
    imported = 0
    skipped = 0

    for p in papers:
        doi = p['doi']
        title = p['title']

        # Check if DOI already exists in collection
        check_url = f'{BASE}/collections/{s["collection"]}/items?q={doi}'
        check_r = requests.get(check_url, headers=HEADERS)
        exists = False
        if check_r.status_code == 200:
            for item in check_r.json():
                item_doi = item.get('data', {}).get('DOI', '')
                if item_doi and item_doi.lower() == doi.lower():
                    exists = True
                    break

        if exists:
            print(f'  SKIP (exists): {doi} | {title[:80]}')
            skipped += 1
            continue

        # Build Zotero item
        item = {
            'itemType': 'journalArticle',
            'title': title,
            'DOI': doi,
            'date': p['year'],
            'creators': p.get('creators', []),
            'tags': [{'tag': '#needs-pdf'}],
            'collections': [s['collection']],
        }

        if p.get('journal'):
            item['publicationTitle'] = p['journal']

        # Create item
        create_r = requests.post(f'{BASE}/items', headers=HEADERS, json=[item])

        if create_r.status_code in (200, 201):
            result = create_r.json()
            if 'success' in result:
                item_key = result.get('success', {}).get('0', '?')
                print(f'  OK {item_key}: {doi} | {title[:80]}')
                imported += 1
            elif 'successful' in result:
                # Zotero v3 API format
                # Get the created item key from response
                try:
                    created = result.get('successful', {})
                    first_key = list(created.keys())[0] if created else '?'
                    print(f'  OK {first_key}: {doi} | {title[:80]}')
                    imported += 1
                except:
                    print(f'  OK?: {doi} | {title[:80]}')
                    imported += 1
            else:
                item_key = result.get('success', result.get('successful', {}))
                print(f'  OK: {doi} | {title[:80]}')
                imported += 1
        else:
            print(f'  FAIL [{create_r.status_code}]: {doi} | {title[:80]}')
            print(f'    {create_r.text[:200]}')
            skipped += 1

        time.sleep(0.3)  # Rate limit

    summary[key] = {'name': s['name'], 'total': len(papers), 'imported': imported, 'skipped': skipped}
    print(f'  -> Imported: {imported}, Skipped: {skipped}')

print('\n=== IMPORT SUMMARY ===')
total_imp = 0
for key, s in summary.items():
    print(f"  {s['name']}: {s['imported']} imported, {s['skipped']} skipped (of {s['total']})")
    total_imp += s['imported']
print(f'Total imported: {total_imp}')
