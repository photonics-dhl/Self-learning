"""
Test script v3: Caption-driven + figure-label-aware extraction.

v3 improvements over v2:
1. Use caption width as horizontal reference (figure fills its column)
2. Include small text blocks in figure band as labels/annotations (fixes Fig. 8)
3. Extend bottom boundary to caption top (capture full figure-to-caption space)
4. Smarter top boundary: climb to highest figure element (image or label)
"""
import io
import re
import sys
from pathlib import Path

import fitz

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- Test paper ---
PDF_PATH = Path(r"Z:\321\DHL\Self_Learning\academic_rag\papers\postdoc\krausz\Hu 等 - 2026 - Ultrafast lasers for attosecond science.pdf")
PAPER_ID = "0044a2d6"
OUTPUT_DIR = Path(r"z:\tmp\test_figures_v3")

# Thresholds
MIN_CAPTION_LEN = 25     # real captions are descriptive paragraphs
MAX_FIGURE_NUM = 100     # filter OCR garbage "Fig. 7168"
LABEL_MAX_CHARS = 250    # text blocks shorter than this might be figure labels
LABEL_PROXIMITY_PT = 50  # how close a text block must be to image to be a label
ASPECT_RATIO_LIMIT = 15  # reject ribbon-like extractions


def find_real_captions(page):
    """Blocks that START with Fig./Figure and are descriptive."""
    captions = []
    for block in page.get_text("blocks"):
        text = block[4].strip()
        if not text or len(text) < MIN_CAPTION_LEN:
            continue
        prefix = text[:20].strip()
        m = re.match(r'(?:Figure|Fig\.?)\s*(\d+[A-Za-z]?)[\s.,:;]', prefix, re.IGNORECASE)
        if not m:
            continue
        fig_num_str = m.group(1)
        try:
            fig_num = int(re.sub(r'[A-Za-z]', '', fig_num_str))
            if fig_num > MAX_FIGURE_NUM:
                continue
        except ValueError:
            pass
        captions.append({
            'bbox': fitz.Rect(block[:4]),
            'text': text[:200],
            'label': m.group(0).rstrip('.,:; '),
            'fig_num': fig_num_str,
        })
    return captions


def get_image_rects(page):
    """Embedded image rectangles, noise filtered."""
    rects = []
    for img_info in page.get_images(full=True):
        try:
            rect = page.get_image_bbox(img_info)
            if rect and rect.is_valid and not rect.is_empty:
                if rect.width >= 30 and rect.height >= 30:
                    rects.append(rect)
        except Exception:
            pass
    return rects


def get_text_blocks_in_band(page, top_y, bottom_y):
    """All text blocks whose center falls in [top_y, bottom_y]."""
    result = []
    for block in page.get_text("blocks"):
        text = block[4].strip()
        if not text:
            continue
        bbox = fitz.Rect(block[:4])
        cy = (bbox.y0 + bbox.y1) / 2
        if top_y <= cy <= bottom_y:
            result.append({'bbox': bbox, 'text': text})
    return result


def extract_figures_v3(pdf_path, paper_id, output_dir):
    """Caption-driven v3: label-aware boundary detection."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for f in output_dir.iterdir():
        f.unlink()

    figures = []
    fig_counter = 0

    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc, 1):
            image_rects = get_image_rects(page)
            captions = find_real_captions(page)

            if not captions or not image_rects:
                continue

            captions.sort(key=lambda c: c['bbox'].y0)

            print(f"\n--- Page {page_num} ---")
            print(f"  Images: {len(image_rects)}, Captions: {len(captions)}")

            for i, cap in enumerate(captions):
                cap_bbox = cap['bbox']

                # Vertical band for this figure
                top_y = page.rect.y0 + 5 if i == 0 else captions[i - 1]['bbox'].y1 + 3
                bottom_y = cap_bbox.y0

                # --- Step 1: find embedded images in band ---
                fig_images = []
                for r in image_rects:
                    cy = (r.y0 + r.y1) / 2
                    if top_y <= cy <= bottom_y:
                        fig_images.append(r)

                if not fig_images:
                    continue

                # --- Step 2: compute initial bbox from images ---
                fig_bbox = fitz.Rect(fig_images[0])
                for r in fig_images[1:]:
                    fig_bbox.include_rect(r)

                # --- Step 3: find figure-label text blocks in band ---
                # Small text blocks (short, not paragraphs) near the figure
                # are likely labels/annotations (e.g., "OSCILLATOR", "PBS", arrows)
                text_blocks = get_text_blocks_in_band(page, top_y, bottom_y)

                for tb in text_blocks:
                    # Skip the caption itself
                    if tb['bbox'].y0 >= cap_bbox.y0 - 2:
                        continue
                    # Small blocks close to the figure → labels
                    dist = max(
                        fig_bbox.x0 - tb['bbox'].x1,
                        tb['bbox'].x0 - fig_bbox.x1,
                        fig_bbox.y0 - tb['bbox'].y1,
                        tb['bbox'].y0 - fig_bbox.y1,
                        0,
                    )
                    is_small = len(tb['text']) < LABEL_MAX_CHARS
                    is_close = dist < LABEL_PROXIMITY_PT

                    # Must horizontally overlap with figure (same column, not adjacent col)
                    horiz_overlaps = (
                        tb['bbox'].x0 < fig_bbox.x1 + 10
                        and tb['bbox'].x1 > fig_bbox.x0 - 10
                    )

                    if is_small and is_close and horiz_overlaps:
                        fig_bbox.include_rect(tb['bbox'])

                # --- Step 4: expand to caption width (figure fills column) ---
                fig_bbox.x0 = min(fig_bbox.x0, cap_bbox.x0)
                fig_bbox.x1 = max(fig_bbox.x1, cap_bbox.x1)

                # --- Step 5: expand vertically ---
                # Bottom: extend to caption top (small gap)
                fig_bbox.y1 = cap_bbox.y0 - 2

                # Top: small margin above highest content, but don't go wild
                fig_bbox.y0 -= 5
                if fig_bbox.y0 < page.rect.y0:
                    fig_bbox.y0 = page.rect.y0

                # Small horizontal margin for safety
                fig_bbox.x0 = max(page.rect.x0, fig_bbox.x0 - 5)
                fig_bbox.x1 = min(page.rect.x1, fig_bbox.x1 + 5)

                # --- Validate ---
                if fig_bbox.width < 50 or fig_bbox.height < 50:
                    continue
                aspect = max(fig_bbox.width, fig_bbox.height) / max(min(fig_bbox.width, fig_bbox.height), 1)
                if aspect > ASPECT_RATIO_LIMIT:
                    continue
                # y1 can't go below previous caption (overflow into next figure)
                if i < len(captions) - 1:
                    fig_bbox.y1 = min(fig_bbox.y1, captions[i + 1]['bbox'].y0 - 3)

                # --- Render ---
                try:
                    pix = page.get_pixmap(clip=fig_bbox, dpi=300)
                except Exception as e:
                    print(f"  RENDER ERROR: {cap['label']} — {e}")
                    continue

                fname = f"{paper_id}_p{page_num:02d}_f{fig_counter:02d}.png"
                fpath = output_dir / fname
                pix.save(str(fpath))

                figures.append({
                    'figure_id': f"{paper_id[:8]}_fig_{fig_counter:03d}",
                    'figure_label': cap['label'],
                    'figure_caption': cap['text'],
                    'page_num': page_num,
                    'image_path': str(fpath),
                    'width': pix.width,
                    'height': pix.height,
                    'n_images': len(fig_images),
                })

                print(f"  [{fig_counter}] {cap['label']}: {pix.width}x{pix.height} | {len(fig_images)} img(s)")
                fig_counter += 1

    return figures


if __name__ == "__main__":
    print(f"PDF: {PDF_PATH}")
    print(f"Output: {OUTPUT_DIR}")

    figures = extract_figures_v3(PDF_PATH, PAPER_ID, OUTPUT_DIR)

    print(f"\n{'='*60}")
    print(f"Total: {len(figures)} figures")
    for f in figures:
        print(f"  {f['figure_id']} | {f['figure_label']:10s} | p{f['page_num']:2d} | {f['width']}x{f['height']} | {f['n_images']} img(s)")
    print(f"\nOutput: {OUTPUT_DIR}")
