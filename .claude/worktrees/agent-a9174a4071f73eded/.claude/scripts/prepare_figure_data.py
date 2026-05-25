"""
Prepare figure data for each researcher profile enrichment.
Output: .claude/scripts/researcher_data/{researcher}/
  - summary.json: papers + figures overview
  - paper_{pid}.json: per-paper figure captions and paths

Usage:
  python .claude/scripts/prepare_figure_data.py              # all researchers
  python .claude/scripts/prepare_figure_data.py --researcher krausz  # single
"""
import json, sys, io, re
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CHROMA_DB = Path('z:/321/DHL/Self_Learning/academic_rag/chroma_db')
OUT_DIR = Path('z:/321/DHL/Self_Learning/.claude/scripts/researcher_data')

def load_all_papers():
    """Load all papers from chroma_db, grouped by researcher directory."""
    researchers = defaultdict(list)
    for mf in sorted(CHROMA_DB.glob('*_metadata.json')):
        with open(mf, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        paper = meta.get('paper', {})
        pdf = paper.get('pdf_path', '')
        researcher = 'unknown'
        if 'postdoc' in pdf:
            parts = Path(pdf).parts
            try:
                idx = parts.index('postdoc')
                researcher = parts[idx + 1] if idx + 1 < len(parts) else 'unknown'
            except ValueError:
                researcher = 'unknown'
        elif not pdf:
            researcher = 'no_pdf'

        # Deduplicate by paper_id (keep the one with most figures)
        pid = paper.get('paper_id', '')
        figs = meta.get('figures', [])
        tables = meta.get('tables', [])

        researchers[researcher].append({
            'paper_id': pid,
            'title': paper.get('title', ''),
            'authors': paper.get('authors', []),
            'year': paper.get('year', 0),
            'journal': paper.get('journal', ''),
            'doi': paper.get('doi', ''),
            'pdf_path': pdf,
            'filename': Path(pdf).name if pdf else '',
            'n_figs': len(figs),
            'n_tables': len(tables),
            'figures': [{
                'figure_id': f.get('figure_id', ''),
                'caption': f.get('figure_caption', ''),
                'label': f.get('figure_label', ''),
                'page': f.get('page_num', 0),
                'image_path': f.get('image_path', ''),
                'description': f.get('description', ''),
                'key_findings': f.get('key_findings', []),
                'related_concepts': f.get('related_concepts', []),
                'figure_type': f.get('figure_type', 'unknown'),
            } for f in figs],
            'tables': tables,
        })

    # Deduplicate: for same paper_id across multiple entries, keep the one with most figures
    for res in researchers:
        seen = {}
        deduped = []
        for p in researchers[res]:
            pid = p['paper_id']
            if pid not in seen or p['n_figs'] > seen[pid].n_figs:
                seen[pid] = p
                # Remove old, add new later
        for p in researchers[res]:
            pid = p['paper_id']
            if seen[pid] == p and p not in deduped:
                deduped.append(p)
        researchers[res] = sorted(deduped, key=lambda x: x['n_figs'], reverse=True)

    return dict(researchers)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--researcher', help='Single researcher name (directory name)')
    args = parser.parse_args()

    print("Loading chroma_db papers...")
    data = load_all_papers()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = [args.researcher] if args.researcher else sorted(data.keys())
    for res in targets:
        papers = data.get(res, [])
        if not papers:
            print(f"  {res}: no papers found")
            continue

        res_dir = OUT_DIR / res
        res_dir.mkdir(parents=True, exist_ok=True)

        total_figs = sum(p['n_figs'] for p in papers)
        print(f"\n{'='*60}")
        print(f"Researcher: {res}")
        print(f"  Papers: {len(papers)}")
        print(f"  Total figures: {total_figs}")

        # Write summary
        summary = {
            'researcher': res,
            'n_papers': len(papers),
            'n_figures': total_figs,
            'papers': [{k: v for k, v in p.items() if k != 'figures'}
                       for p in papers],
        }
        with open(res_dir / 'summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"  → {res_dir / 'summary.json'}")

        # Write per-paper data
        for p in papers:
            pid = p['paper_id'][:8]
            paper_file = res_dir / f'paper_{pid}.json'
            with open(paper_file, 'w', encoding='utf-8') as f:
                json.dump(p, f, ensure_ascii=False, indent=2)

            figs = p['figures']
            if figs:
                print(f"  [{pid}] {p['n_figs']:3d}f | {p['filename'][:70]}")
                for fig in figs[:3]:
                    caption = fig['caption'][:80].replace('\n', ' ')
                    print(f"         {fig['figure_id']} p{fig['page']}: {caption}")
                if len(figs) > 3:
                    print(f"         ... and {len(figs)-3} more figures")

    print(f"\nDone. Data in {OUT_DIR}")

if __name__ == '__main__':
    main()
