#!/usr/bin/env python3
"""Import papers to Zotero via MCP (direct HTTP to local MCP server)."""

import sys, requests, json, time, os
sys.stdout.reconfigure(encoding='utf-8')
for v in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(v, None)

MCP_URL = 'http://127.0.0.1:23120/mcp'

scholars = {
    'lhuillier': {'collection': 'CP83C6VV', 'name': "L'Huillier"},
    'miao': {'collection': '2D7JR5YV', 'name': 'Miao'},
    'baum': {'collection': 'ECGLT9Q6', 'name': 'Baum'},
    'gedik': {'collection': 'LA976NQY', 'name': 'Gedik'},
}


def mcp_tool_call(tool_name, arguments, session_id=None):
    """Make an MCP tool call. Returns (parsed_result, session_id)."""
    rpc = {
        'jsonrpc': '2.0',
        'id': int(time.time() * 1000) % 1000000,
        'method': 'tools/call',
        'params': {
            'name': tool_name,
            'arguments': arguments
        }
    }
    headers = {'Content-Type': 'application/json'}
    if session_id:
        headers['Mcp-Session-Id'] = session_id

    try:
        r = requests.post(MCP_URL, json=rpc, headers=headers, timeout=30)
    except Exception as e:
        return None, session_id, f'Request error: {e}'

    new_sid = r.headers.get('Mcp-Session-Id', session_id)

    if r.status_code != 200:
        return None, new_sid, f'HTTP {r.status_code}'

    data = r.json()
    if 'error' in data:
        return None, new_sid, f'MCP error: {data["error"]}'

    result = data.get('result', {})
    content = result.get('content', [])
    if content and len(content) > 0:
        text = content[0].get('text', '{}')
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = text
        return parsed, new_sid, None
    return result, new_sid, None


def check_doi_exists(doi, collection_key, session_id):
    """Check if DOI already exists in a collection."""
    result, sid, err = mcp_tool_call('search_library', {
        'q': doi,
        'collectionKey': collection_key,
        'limit': 5
    }, session_id)

    if err or result is None:
        return False, sid

    items = result if isinstance(result, list) else result.get('items', result.get('results', []))
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                item_doi = item.get('doi', item.get('DOI', ''))
                if item_doi and item_doi.lower() == doi.lower():
                    return True, sid
    return False, sid


# First, skip pre-check for the test paper we already imported
already_imported_dois = {'10.1088/0953-4075/21/3/001'}  # test paper

summary = {}
session_id = None
total_imported = 0

for key, s in scholars.items():
    json_path = f'z:/321/DHL/Self_Learning/.claude/{key}_new_papers.json'
    with open(json_path, encoding='utf-8') as f:
        papers = json.load(f)

    print(f'\n=== {s["name"]} ({s["collection"]}): {len(papers)} papers ===')
    imported = 0
    skipped_dup = 0
    skipped_err = 0

    for i, p in enumerate(papers):
        doi = p['doi']
        title = p['title']

        if doi in already_imported_dois:
            print(f'  [{i+1}/{len(papers)}] SKIP (already imported): {doi}')
            skipped_dup += 1
            continue

        # Build creators
        creators = []
        for c in p.get('creators', [])[:10]:
            creators.append({
                'creatorType': 'author',
                'firstName': c.get('firstName', ''),
                'lastName': c.get('lastName', '')
            })

        # Build fields
        fields = {
            'title': title,
            'DOI': doi,
            'date': p.get('year', ''),
        }
        if p.get('journal'):
            fields['publicationTitle'] = p['journal']

        # Create item
        result, session_id, err = mcp_tool_call('write_item', {
            'action': 'create',
            'itemType': 'journalArticle',
            'fields': fields,
            'creators': creators,
            'tags': ['#needs-pdf']
        }, session_id)

        if err or result is None:
            print(f'  [{i+1}/{len(papers)}] FAIL: {doi} | {title[:80]}')
            print(f'    Error: {err}')
            skipped_err += 1
            continue

        # Parse the result to get item key
        item_key = None
        if isinstance(result, dict):
            data = result.get('data', {})
            item_key = data.get('itemKey')
            if not item_key and result.get('success'):
                item_key = result.get('data', {}).get('itemKey', list(result.get('data', {}).values())[0] if result.get('data') else None)

        if item_key:
            # Add to collection
            _, session_id, add_err = mcp_tool_call('add_items_to_collection', {
                'collectionKey': s['collection'],
                'itemKeys': [item_key]
            }, session_id)
            if add_err:
                print(f'  [{i+1}/{len(papers)}] WARN: item {item_key} created but collection add failed: {add_err}')
            print(f'  [{i+1}/{len(papers)}] OK {item_key}: {doi} ({p["cites"]}c) | {title[:70]}')
            imported += 1
            total_imported += 1
        else:
            print(f'  [{i+1}/{len(papers)}] OK (key unknown): {doi} | {title[:70]}')
            print(f'    Raw: {json.dumps(result)[:200]}')
            imported += 1
            total_imported += 1

        time.sleep(0.8)  # Rate limit - be conservative

    summary[key] = {'name': s['name'], 'total': len(papers), 'imported': imported,
                    'skipped_dup': skipped_dup, 'skipped_err': skipped_err}
    print(f'  -> Imported: {imported}, Dup: {skipped_dup}, Error: {skipped_err}')

print('\n' + '=' * 60)
print('IMPORT SUMMARY')
print('=' * 60)
for key, s in summary.items():
    print(f"  {s['name']}: {s['imported']} imported, {s['skipped_dup']} skip, {s['skipped_err']} err (of {s['total']})")
print(f'\nTotal imported: {total_imported}')
