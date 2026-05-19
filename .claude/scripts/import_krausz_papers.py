"""
Import Krausz missing papers into Zotero.
1. Create Zotero items with full metadata
2. Download OA PDFs and attach
3. Add to Krausz collection
"""
import json, os, sys, io, time, re, requests
from pathlib import Path
import dotenv
from pyzotero import zotero

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

ZOT_USER = os.environ['Zotero_user_ID']
ZOT_KEY = os.environ['Zotero_API_KEY']
KRAUSZ_COLLECTION = 'RYD9JI2U'
TMP_DIR = Path(os.environ.get('TEMP', '/tmp')) / 'zotero_import_krausz'
TMP_DIR.mkdir(parents=True, exist_ok=True)

zot = zotero.Zotero(ZOT_USER, 'user', ZOT_KEY)

def load_missing():
    with open(Path(__file__).parent / 'krausz_missing_25_enriched.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def find_arxiv_pdf(title):
    """Search arXiv for a paper by title and return PDF URL if found."""
    try:
        # Clean title for search
        q = re.sub(r'[^\w\s]', '', title)[:200]
        resp = requests.get(
            'http://export.arxiv.org/api/query',
            params={'search_query': f'ti:"{q}"', 'max_results': 2},
            timeout=15
        )
        if resp.status_code != 200:
            return None
        # Parse XML for first result
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        ns = {'a': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('a:entry', ns)
        if not entries:
            return None
        entry = entries[0]
        arxiv_title = entry.find('a:title', ns).text.strip()
        # Simple similarity check
        title_words = set(title.lower().split()[:10])
        arxiv_words = set(arxiv_title.lower().split()[:10])
        overlap = len(title_words & arxiv_words)
        if overlap >= 3:
            pdf_link = None
            for link in entry.findall('a:link', ns):
                if link.get('title') == 'pdf':
                    pdf_link = link.get('href')
                    break
            return pdf_link
    except Exception as e:
        print(f'  arXiv search error: {e}')
    return None

def download_pdf(url, filename):
    """Download PDF to temp dir. Return path or None."""
    if not url:
        return None
    filepath = TMP_DIR / filename
    try:
        print(f'  Downloading: {url[:100]}...')
        resp = requests.get(url, timeout=60, stream=True)
        if resp.status_code == 200 and 'pdf' in resp.headers.get('content-type', '').lower():
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            size_k = filepath.stat().st_size / 1024
            if size_k > 50:  # At least 50KB
                print(f'  OK: {size_k:.0f} KB')
                return str(filepath)
            else:
                print(f'  Too small ({size_k:.0f} KB), discarding')
                filepath.unlink(missing_ok=True)
        else:
            print(f'  Failed: HTTP {resp.status_code} type={resp.headers.get("content-type","?")[:50]}')
    except Exception as e:
        print(f'  Download error: {e}')
    return None

def create_zotero_items(papers):
    """Create Zotero items and return list of (item_key, title, pdf_path)."""
    results = []
    batch = []
    batch_info = []

    for i, paper in enumerate(papers):
        doi = paper.get('doi', '')
        title = paper.get('title', '')
        date = paper.get('date', '')
        journal = paper.get('journal', {})
        if isinstance(journal, dict):
            jname = journal.get('display_name', '')
        else:
            jname = str(journal)

        creators = paper.get('creators', [
            {'creatorType': 'author', 'firstName': 'Ferenc', 'lastName': 'Krausz'}
        ])

        template = zot.item_template('journalArticle')
        template['title'] = title
        template['DOI'] = doi
        template['date'] = date
        template['publicationTitle'] = jname
        template['creators'] = creators
        template['url'] = f'https://doi.org/{doi}' if doi else ''
        template['collections'] = [KRAUSZ_COLLECTION]

        batch.append(template)
        batch_info.append({
            'title': title,
            'doi': doi,
            'oa_url': paper.get('oa_url', ''),
            'is_oa': paper.get('is_oa', False),
            'creators': creators,
            'date': date,
            'journal': jname,
        })

    # Batch create
    print(f'Creating {len(batch)} items...')
    try:
        resp = zot.create_items(batch)
        # Parse response
        if 'success' in resp:
            for key, info in zip(resp['success'], batch_info):
                item_key = key if isinstance(key, str) else key.get('key', str(key))
                print(f'  Created: {info["title"][:80]} -> {item_key}')
                results.append({
                    'key': item_key,
                    'title': info['title'],
                    'doi': info['doi'],
                    'oa_url': info['oa_url'],
                    'is_oa': info['is_oa'],
                    'pdf_path': None
                })
        if 'failed' in resp:
            for fail_key, fail_info in zip(resp['failed'], batch_info):
                print(f'  FAILED: {fail_info["title"][:80]}')
        print(f'Done: {len(results)} created')
    except Exception as e:
        print(f'Batch create error: {e}')
        # Fall back to individual creation
        print('Retrying individually...')
        for info in batch_info:
            try:
                template = zot.item_template('journalArticle')
                template['title'] = info['title']
                template['DOI'] = info['doi']
                template['date'] = info.get('date', '')
                template['publicationTitle'] = info.get('journal', '')
                doi_val = info.get('doi', '')
                template['url'] = f'https://doi.org/{doi_val}' if doi_val else ''
                template['creators'] = info.get('creators', [{'creatorType': 'author', 'firstName': 'Ferenc', 'lastName': 'Krausz'}])
                template['collections'] = [KRAUSZ_COLLECTION]
                resp = zot.create_items([template])
                if 'success' in resp:
                    item_key = resp['success'][0] if isinstance(resp['success'][0], str) else resp['success'][0].get('key')
                    print(f'  Created: {info["title"][:80]} -> {item_key}')
                    results.append({
                        'key': item_key,
                        'title': info['title'],
                        'doi': info['doi'],
                        'oa_url': info['oa_url'],
                        'is_oa': info['is_oa'],
                        'pdf_path': None
                    })
                time.sleep(0.3)
            except Exception as e2:
                print(f'  Individual error: {e2}')

    return results

def attach_pdfs(results):
    """Download OA PDFs and attach to items."""
    for item in results:
        if not item['is_oa'] or not item['oa_url']:
            # Try arXiv
            print(f'\nSearching arXiv for: {item["title"][:80]}')
            arxiv_url = find_arxiv_pdf(item['title'])
            if arxiv_url:
                safe_name = re.sub(r'[^\w\s-]', '', item['title'][:60]).strip().replace(' ', '_') + '.pdf'
                pdf_path = download_pdf(arxiv_url, safe_name)
                if pdf_path:
                    item['pdf_path'] = pdf_path
            else:
                print(f'  No arXiv version found')
            continue

        safe_name = re.sub(r'[^\w\s-]', '', item['title'][:60]).strip().replace(' ', '_') + '.pdf'
        print(f'\nDownloading OA: {item["title"][:80]}')
        print(f'  URL: {item["oa_url"][:120]}')
        pdf_path = download_pdf(item['oa_url'], safe_name)
        if pdf_path:
            item['pdf_path'] = pdf_path

    # Now attach all downloaded PDFs
    for item in results:
        if item['pdf_path']:
            try:
                print(f'Attaching: {item["title"][:80]}')
                zot.attachment_simple([item['pdf_path']], parentid=item['key'])
                print(f'  Attached OK')
                time.sleep(0.3)
            except Exception as e:
                print(f'  Attach error: {e}')

def main():
    papers = load_missing()
    print(f'Loaded {len(papers)} papers')
    print(f'OA: {sum(1 for p in papers if p["is_oa"])}')
    print(f'Paywalled: {sum(1 for p in papers if not p["is_oa"])}')

    results = create_zotero_items(papers)
    print(f'\n--- Attaching PDFs ---')
    attach_pdfs(results)

    # Summary
    with_pdf = sum(1 for r in results if r['pdf_path'])
    print(f'\n=== SUMMARY ===')
    print(f'Total items created: {len(results)}')
    print(f'With PDF attached: {with_pdf}')
    print(f'Metadata only: {len(results) - with_pdf}')

    # Save results
    with open(Path(__file__).parent / 'krausz_import_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
