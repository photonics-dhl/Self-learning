"""
学术论文 RAG 系统 - PDF处理器
Phase 1: 提取论文的文本、图表和元数据
"""

import hashlib
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import asdict

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image, ImageEnhance

from academic_rag.config import config
from academic_rag.db.models import Paper, Figure, TextChunk, DomainTaxonomy


class PDFProcessor:
    """PDF论文处理器 - 提取文本、图表和元数据"""

    def __init__(self, extract_images: bool = True, image_dpi: int = 300, enhance: bool = True):
        self.extract_images = extract_images
        self.image_dpi = image_dpi
        self.enhance = enhance
        self.taxonomy = DomainTaxonomy()
        # 噪声过滤参数
        self.min_figure_size = config.min_figure_size  # 100px
        self.max_aspect_ratio = 20.0   # 超 20:1 = 线条/分隔符/logo
        self.min_aspect_ratio = 0.05   # 同理
        self._MAX_IMAGES_PER_PAGE = 500  # cap for formula-heavy pages

        # 标题模式
        self.heading_patterns = [
            r"^\d+\.\s+.+$",  # 1. Introduction
            r"^\d+\.\d+\s+.+$",  # 1.2 Background
            r"^#{1,6}\s+.+$",  # Markdown headings
        ]

        # 参考引用模式
        self.citation_patterns = [
            r"\[(\d+)\]",  # [1], [2-5]
            r"\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s*\d{4})\)",  # (Smith et al., 2020)
        ]

    def process(self, pdf_path: str | Path, domain: str = "", subfield: str = "",
                extract_tables: bool = True) -> Tuple[Paper, List[Figure], List[TextChunk], List[Dict[str, Any]]]:
        """
        处理单个PDF论文

        Args:
            pdf_path: PDF文件路径
            domain: 领域分类（如 "optics"）
            subfield: 子领域分类（如 "terahertz"）
            extract_tables: 是否提取表格

        Returns:
            (Paper, List[Figure], List[TextChunk], List[Dict] tables)
        """
        pdf_path = Path(pdf_path)

        # 计算文件hash
        file_hash = self._compute_file_hash(pdf_path)

        # 提取元数据
        metadata = self._extract_metadata(pdf_path)

        # 自动分类（如果未指定）
        if not domain or not subfield:
            domain, subfield = self._auto_classify(metadata.get("title", ""), metadata.get("abstract", ""))

        # 创建Paper对象
        paper = Paper(
            title=metadata.get("title", pdf_path.stem),
            authors=metadata.get("authors", []),
            year=metadata.get("year", 0),
            journal=metadata.get("journal", ""),
            doi=metadata.get("doi", ""),
            domain=domain,
            subfield=subfield,
            pdf_path=str(pdf_path),
            file_hash=file_hash,
            num_pages=metadata.get("num_pages", 0),
        )

        # 提取图片（如果启用）
        figures = []
        if self.extract_images:
            figures = self._extract_figures(pdf_path, paper.paper_id)

        # 提取表格
        tables = []
        if extract_tables:
            tables = self._extract_tables(pdf_path, paper.paper_id)

        # 提取文本块
        text_chunks = self._extract_text_chunks(pdf_path, paper.paper_id, domain, subfield)

        # 更新统计
        paper.num_figures = len(figures)
        paper.num_text_chunks = len(text_chunks)

        return paper, figures, text_chunks, tables

    def _compute_file_hash(self, pdf_path: Path) -> str:
        """计算文件MD5哈希"""
        hasher = hashlib.md5()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """从PDF提取元数据 — font-size-aware title detection."""
        metadata = {
            "title": "",
            "authors": [],
            "year": 0,
            "journal": "",
            "doi": "",
            "abstract": "",
            "num_pages": 0,
        }

        try:
            with fitz.open(pdf_path) as doc:
                metadata["num_pages"] = len(doc)

                doc_metadata = doc.metadata
                if doc_metadata:
                    metadata["title"] = doc_metadata.get("title", "")
                    metadata["doi"] = doc_metadata.get("doi", "")

                if len(doc) > 0:
                    first_page = doc[0]

                    # Font-size-aware title extraction
                    extracted_title = self._extract_title_from_page(first_page)
                    if extracted_title:
                        metadata["title"] = extracted_title

                    # Author extraction
                    text = first_page.get_text()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if len(lines) > 1:
                        for line in lines[1:8]:
                            if "," in line and len(line) < 300:
                                authors = re.split(r",\s*|\s+and\s+", line)
                                if 1 < len(authors) <= 15:
                                    metadata["authors"] = [a.strip() for a in authors if a.strip()]
                                    break

                    year_match = re.search(r"\b(19|20)\d{2}\b", text)
                    if year_match:
                        metadata["year"] = int(year_match.group())

                # Abstract extraction
                for page in doc:
                    text = page.get_text()
                    abstract_match = re.search(
                        r"(?:Abstract|SUMMARY|摘要)[:\s]*([^\n]+(?:\n[^\n]+){1,10})",
                        text,
                        re.IGNORECASE | re.DOTALL
                    )
                    if abstract_match:
                        metadata["abstract"] = abstract_match.group(1)[:1000]
                        break

                if doc_metadata:
                    metadata["journal"] = doc_metadata.get("journal", "")

        except Exception as e:
            print(f"Warning: Error extracting metadata from {pdf_path}: {e}")

        return metadata

    def _extract_title_from_page(self, page: fitz.Page) -> str:
        """Extract paper title from first page using font-size + position heuristics.

        Title is in the top 50% of the page, has the largest font size among
        non-header text, and is not a drop cap (one huge char + rest normal).
        After finding the title start, extends to adjacent same-font-size lines.
        """
        page_h = page.rect.height

        # Collect individual lines with font info, only top 50% of page
        lines: list[dict] = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                sizes = [s.get("size", 0) for s in line["spans"]]
                text = "".join(s["text"] for s in line["spans"]).strip()
                if not text or len(text) < 3:
                    continue
                y0 = line["bbox"][1]
                if y0 > page_h * 0.5:
                    continue

                max_size = max(sizes)
                median_size = sorted(sizes)[len(sizes) // 2]

                # Drop-cap detection: one giant char + normal text
                if max_size > 0 and median_size > 0 and max_size > median_size * 3 and len(sizes) > 1:
                    continue

                lines.append({
                    "text": text,
                    "size": max_size,
                    "y0": y0,
                    "x0": line["bbox"][0],
                    "x1": line["bbox"][2],
                })

        if not lines:
            return ""

        _SKIP_WORDS = {"ARTICLES", "ARTICLE", "RESEARCH ARTICLE", "REVIEW",
                        "LETTER", "REPORT", "COMMENTARY", "REPORTS"}

        # Find best title starting line: largest font that passes filters
        lines.sort(key=lambda L: -L["size"])
        best = None
        for L in lines:
            t = L["text"]
            if t.strip().upper() in _SKIP_WORDS:
                continue
            if t == t.upper() and len(t) < 60:
                continue
            if re.match(r'^\d+\.\s+[A-Z]\.\s+\w+,', t):
                continue
            if t.startswith("doi:") or t.startswith("http"):
                continue
            if len(t) < 10:
                continue
            best = L
            break

        if not best:
            return ""

        # Extend downward to adjacent lines of similar font size (multi-line titles).
        # Only lines within 50pt vertical gap and 5 lines max. No upward extension —
        # journal headers above the title would get chained in.
        title_parts = [best["text"]]
        size_tol = 2.0
        _MAX_TITLE_LINES = 5
        _MAX_GAP = 50  # pt

        y_below = best["y0"]
        x_below = (best["x0"], best["x1"])
        while len(title_parts) < _MAX_TITLE_LINES:
            cands = [
                L for L in lines
                if 0 < L["y0"] - y_below <= _MAX_GAP
                and abs(L["size"] - best["size"]) <= size_tol
                and not (L["x1"] < x_below[0] - 20 or L["x0"] > x_below[1] + 20)
            ]
            if not cands:
                break
            cands.sort(key=lambda L: L["y0"])
            title_parts.append(cands[0]["text"])
            y_below = cands[0]["y0"]
            x_below = (cands[0]["x0"], cands[0]["x1"])

        return " ".join(title_parts)[:200]

    def _auto_classify(self, title: str, abstract: str) -> Tuple[str, str]:
        """根据标题和摘要自动分类"""
        combined = f"{title} {abstract}"
        return self.taxonomy.classify_domain(combined)

    # --- Caption-driven figure extraction thresholds ---
    _MIN_CAPTION_LEN = 25       # real captions are descriptive paragraphs
    _MAX_FIGURE_NUM = 100       # filter OCR garbage "Fig. 7168"
    _LABEL_MAX_CHARS = 250      # text blocks shorter than this might be figure labels
    _LABEL_PROXIMITY_PT = 50    # max distance from image to be a label
    _ASPECT_RATIO_LIMIT = 15    # reject ribbon-like extractions

    def _find_real_captions(self, page: fitz.Page, prefix: str = "Figure") -> list[dict]:
        """Blocks that START with Fig./Figure or Table/Tab. and are descriptive."""
        captions = []
        for block in page.get_text("blocks"):
            text = block[4].strip()
            if not text or len(text) < self._MIN_CAPTION_LEN:
                continue
            prefix_text = text[:30].strip()
            if prefix == "Figure":
                m = re.match(r'(?:Figure|Fig\.?)\s*(\d+[A-Za-z]?)[\s.,:;]', prefix_text, re.IGNORECASE)
            else:
                m = re.match(r'(?:Table|Tab\.?)\s*(\d+[A-Za-z]?)[\s.,:;]', prefix_text, re.IGNORECASE)
            if not m:
                continue
            fig_num_str = m.group(1)
            try:
                fig_num = int(re.sub(r'[A-Za-z]', '', fig_num_str))
                if fig_num > self._MAX_FIGURE_NUM:
                    continue
            except ValueError:
                pass
            captions.append({
                'bbox': fitz.Rect(block[:4]),
                'text': text[:300],
                'label': m.group(0).rstrip('.,:; '),
                'fig_num': fig_num_str,
            })
        return captions

    def _get_image_rects(self, page: fitz.Page) -> list[fitz.Rect]:
        """Embedded image rectangles, noise filtered (min 30pt each side).
        Capped at _MAX_IMAGES_PER_PAGE — formula-heavy pages have thousands
        of tiny inline rasters that contribute nothing to real figures."""
        rects = []
        for i, img_info in enumerate(page.get_images(full=True)):
            if i >= self._MAX_IMAGES_PER_PAGE:
                break
            try:
                rect = page.get_image_bbox(img_info)
                if rect and rect.is_valid and not rect.is_empty:
                    if rect.width >= 30 and rect.height >= 30:
                        rects.append(rect)
            except Exception:
                pass
        return rects

    _CLUSTER_GAP_PT = 25  # max vertical gap within a multi-panel figure

    def _cluster_image_rects(self, rects: list[fitz.Rect]) -> list[list[fitz.Rect]]:
        """Group nearby image rects into multi-panel clusters by vertical proximity."""
        if not rects:
            return []
        sorted_rects = sorted(rects, key=lambda r: (r.y0, r.x0))
        clusters = [[sorted_rects[0]]]
        for r in sorted_rects[1:]:
            last = clusters[-1][-1]
            if r.y0 - last.y1 <= self._CLUSTER_GAP_PT:
                clusters[-1].append(r)
            else:
                clusters.append([r])
        return clusters

    def _get_text_blocks_in_band(self, page: fitz.Page, top_y: float, bottom_y: float) -> list[dict]:
        """All text blocks whose vertical center falls in [top_y, bottom_y]."""
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

    def _extract_figures(self, pdf_path: Path, paper_id: str) -> List[Figure]:
        """Caption-driven v4: image clustering + nearest-caption matching + full-width fallback."""
        figures = []
        fig_counter = 0

        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc, 1):
                    image_rects = self._get_image_rects(page)
                    captions = self._find_real_captions(page, "Figure")

                    if not captions:
                        continue

                    captions.sort(key=lambda c: c['bbox'].y0)

                    for i, cap in enumerate(captions):
                        cap_bbox = cap['bbox']

                        # Band ABOVE caption
                        prev_y1 = captions[i - 1]['bbox'].y1 if i > 0 else page.rect.y0
                        above_top = prev_y1 + 3
                        above_bot = cap_bbox.y0

                        # Band BELOW caption — start just below caption text, not the block's
                        # potentially massive y1 (some blocks span entire columns).
                        next_y0 = captions[i + 1]['bbox'].y0 if i + 1 < len(captions) else page.rect.y1
                        below_top = cap_bbox.y0 + 30
                        below_bot = next_y0 - 3

                        # Multi-column guard
                        if above_top >= above_bot:
                            above_top = page.rect.y0 + 5

                        # Cluster image rects, pick cluster nearest to caption
                        image_clusters = self._cluster_image_rects(image_rects)
                        cap_cy = (cap_bbox.y0 + cap_bbox.y1) / 2
                        candidates = []  # (cluster, centroid_y, from_above)
                        for cl in image_clusters:
                            cy = sum((r.y0 + r.y1) / 2 for r in cl) / len(cl)
                            if above_top <= cy <= above_bot:
                                candidates.append((cl, cy, True))
                            elif below_top <= cy <= below_bot:
                                candidates.append((cl, cy, False))

                        if len(candidates) > 1:
                            candidates.sort(key=lambda x: abs(x[1] - cap_cy))

                        if candidates:
                            fig_images = candidates[0][0]
                            from_above = candidates[0][2]
                        else:
                            fig_images = []
                            from_above = False

                        if fig_images:
                            fig_bbox = fitz.Rect(fig_images[0])
                            for r in fig_images[1:]:
                                fig_bbox.include_rect(r)

                            # Include small text blocks as labels (above band only)
                            if from_above:
                                text_blocks = self._get_text_blocks_in_band(page, above_top, above_bot)
                                for tb in text_blocks:
                                    if tb['bbox'].y0 >= cap_bbox.y0 - 2:
                                        continue
                                    dist = max(
                                        fig_bbox.x0 - tb['bbox'].x1,
                                        tb['bbox'].x0 - fig_bbox.x1,
                                        fig_bbox.y0 - tb['bbox'].y1,
                                        tb['bbox'].y0 - fig_bbox.y1,
                                        0,
                                    )
                                    is_small = len(tb['text']) < self._LABEL_MAX_CHARS
                                    is_close = dist < self._LABEL_PROXIMITY_PT
                                    horiz_overlaps = (
                                        tb['bbox'].x0 < fig_bbox.x1 + 10
                                        and tb['bbox'].x1 > fig_bbox.x0 - 10
                                    )
                                    if is_small and is_close and horiz_overlaps:
                                        fig_bbox.include_rect(tb['bbox'])

                            fig_bbox.x0 = min(fig_bbox.x0, cap_bbox.x0)
                            fig_bbox.x1 = max(fig_bbox.x1, cap_bbox.x1)
                        else:
                            # Fallback: render from above_top to caption.
                            # Expand to full text-area width — figures often span
                            # wider than their caption column in multi-column layouts.
                            text_x0 = cap_bbox.x0
                            text_x1 = cap_bbox.x1
                            for blk in page.get_text("blocks"):
                                t = blk[4].strip()
                                if len(t) > 20:
                                    text_x0 = min(text_x0, blk[0])
                                    text_x1 = max(text_x1, blk[2])
                            # Keep within page with small margin
                            text_x0 = max(page.rect.x0 + 20, text_x0)
                            text_x1 = min(page.rect.x1 - 20, text_x1)
                            fig_bbox = fitz.Rect(
                                text_x0,
                                above_top,
                                text_x1,
                                cap_bbox.y0 - 2,
                            )

                        # Vertical expansion — if images below caption, extend to them
                        if not from_above and fig_images:
                            fig_bbox.y1 = cap_bbox.y0 - 2
                            for r in fig_images:
                                fig_bbox.y1 = max(fig_bbox.y1, r.y1 + 5)
                        else:
                            fig_bbox.y1 = cap_bbox.y0 - 2
                        fig_bbox.y0 -= 5
                        if fig_bbox.y0 < page.rect.y0:
                            fig_bbox.y0 = page.rect.y0

                        # Horizontal margin
                        fig_bbox.x0 = max(page.rect.x0, fig_bbox.x0 - 5)
                        fig_bbox.x1 = min(page.rect.x1, fig_bbox.x1 + 5)

                        # Validate
                        if fig_bbox.width < 50 or fig_bbox.height < 50:
                            continue
                        aspect = max(fig_bbox.width, fig_bbox.height) / max(min(fig_bbox.width, fig_bbox.height), 1)
                        if aspect > self._ASPECT_RATIO_LIMIT:
                            continue
                        if i < len(captions) - 1:
                            fig_bbox.y1 = min(fig_bbox.y1, captions[i + 1]['bbox'].y0 - 3)

                        # Render
                        try:
                            pix = page.get_pixmap(clip=fig_bbox, dpi=self.image_dpi)
                        except Exception as e:
                            print(f"Warning: Render error for {cap['label']} on page {page_num}: {e}")
                            continue

                        image_bytes = pix.tobytes("png")
                        img_hash = hashlib.md5(image_bytes).hexdigest()

                        img_filename = f"{paper_id}_p{page_num:02d}_f{fig_counter:02d}.png"
                        img_path = config.visualizations / paper_id[:8] / img_filename
                        img_path.parent.mkdir(parents=True, exist_ok=True)
                        pix.save(str(img_path))

                        if self.enhance:
                            self._post_process_image(img_path)

                        if self._is_noise_image(pix.width, pix.height):
                            continue

                        figure = Figure(
                            figure_id=f"{paper_id[:8]}_fig_{fig_counter:03d}",
                            paper_id=paper_id,
                            figure_label=cap['label'],
                            figure_caption=cap['text'],
                            page_num=page_num,
                            image_path=str(img_path),
                            image_hash=img_hash,
                            width=pix.width,
                            height=pix.height,
                            figure_type=self._classify_figure_type(cap['text']),
                            bbox=(fig_bbox.x0, fig_bbox.y0, fig_bbox.x1, fig_bbox.y1),
                        )
                        figures.append(figure)
                        fig_counter += 1

        except Exception as e:
            print(f"Warning: Error extracting figures from {pdf_path}: {e}")

        return figures

    def _extract_tables(self, pdf_path: Path, paper_id: str) -> List[Dict[str, Any]]:
        """从PDF提取表格 — caption-driven + fitz渲染。

        返回表格字典列表，每个包含 table_id, paper_id, table_label,
        table_caption, page_num, image_path, width, height。
        """
        tables = []
        table_counter = 0

        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc, 1):
                    captions = self._find_real_captions(page, "Table")

                    if not captions:
                        continue

                    captions.sort(key=lambda c: c['bbox'].y0)

                    for i, cap in enumerate(captions):
                        cap_bbox = cap['bbox']

                        # Vertical band: previous caption to this caption
                        top_y = page.rect.y0 + 5 if i == 0 else captions[i - 1]['bbox'].y1 + 3
                        bottom_y = cap_bbox.y0

                        # Table region: caption width, band height
                        table_bbox = fitz.Rect(
                            cap_bbox.x0,
                            top_y,
                            cap_bbox.x1,
                            cap_bbox.y0 - 2,
                        )

                        if table_bbox.width < 50 or table_bbox.height < 50:
                            continue

                        # Don't overflow into next caption
                        if i < len(captions) - 1:
                            table_bbox.y1 = min(table_bbox.y1, captions[i + 1]['bbox'].y0 - 3)

                        # Clamp to page
                        table_bbox.x0 = max(page.rect.x0, table_bbox.x0 - 5)
                        table_bbox.x1 = min(page.rect.x1, table_bbox.x1 + 5)

                        try:
                            pix = page.get_pixmap(clip=table_bbox, dpi=self.image_dpi)
                        except Exception as e:
                            print(f"Warning: Render error for {cap['label']} on page {page_num}: {e}")
                            continue

                        img_filename = f"{paper_id}_p{page_num:02d}_t{table_counter:02d}.png"
                        img_path = config.visualizations / paper_id[:8] / img_filename
                        img_path.parent.mkdir(parents=True, exist_ok=True)
                        pix.save(str(img_path))

                        if self.enhance:
                            self._post_process_image(img_path)

                        tables.append({
                            'table_id': f"{paper_id[:8]}_tab_{table_counter:03d}",
                            'paper_id': paper_id,
                            'table_label': cap['label'],
                            'table_caption': cap['text'],
                            'page_num': page_num,
                            'image_path': str(img_path),
                            'width': pix.width,
                            'height': pix.height,
                        })
                        table_counter += 1

        except Exception as e:
            print(f"Warning: Error extracting tables from {pdf_path}: {e}")

        return tables

    def _classify_figure_type(self, caption: str) -> str:
        """根据标题内容分类图表类型"""
        caption_lower = caption.lower()

        if any(kw in caption_lower for kw in ["photo", "image", "micrograph", "sem", "tem", "aftm"]):
            return "photo"
        elif any(kw in caption_lower for kw in ["diagram", "schematic", "illustration"]):
            return "diagram"
        elif any(kw in caption_lower for kw in ["plot", "curve", "trace"]):
            return "plot"
        elif any(kw in caption_lower for kw in ["graph", "chart"]):
            return "graph"
        elif any(kw in caption_lower for kw in ["spectrum", "spectra"]):
            return "spectrum"
        elif any(kw in caption_lower for kw in ["setup", "apparatus", "system"]):
            return "setup"
        else:
            return "unknown"

    def _post_process_image(self, img_path: Path) -> None:
        """Pillow后期增强: 适度锐化和对比度提升。

        Re-rendering at 300 DPI 已大幅提升品质，此步骤作为廉价的最后润色。
        参数选择保守以避免过度处理(halo artifacts, 色调偏移)。
        """
        try:
            img = Image.open(img_path)
            # 仅处理RGB/RGBA图像
            if img.mode not in ("RGB", "RGBA"):
                return

            # 保守锐化 (factor 1.15 — 仅增强边缘，不引入光晕)
            sharpener = ImageEnhance.Sharpness(img)
            img = sharpener.enhance(1.15)

            # 微调对比度 (factor 1.08 — 拉伸直方图但不裁剪)
            contrast = ImageEnhance.Contrast(img)
            img = contrast.enhance(1.08)

            img.save(img_path, quality=95)
        except Exception:
            pass  # 增强失败静默跳过，不影响提取流程

    def _is_noise_image(self, width: int, height: int) -> bool:
        """过滤 PDF 中嵌入的非图像噪声 (logo, 图标, 分隔线, 单像素)"""
        if width < self.min_figure_size or height < self.min_figure_size:
            return True
        if height == 0 or width == 0:
            return True
        ratio = width / height
        if ratio > self.max_aspect_ratio or ratio < self.min_aspect_ratio:
            return True
        if width <= 2 or height <= 2:
            return True
        return False

    def _extract_text_chunks(self, pdf_path: Path, paper_id: str, domain: str, subfield: str) -> List[TextChunk]:
        """从PDF提取文本块"""
        chunks = []
        chunk_index = 0

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # 提取文本
                    text = page.extract_text()

                    if not text:
                        continue

                    # 清理文本
                    text = self._clean_text(text)

                    # 按段落分割
                    paragraphs = self._split_paragraphs(text)

                    for para in paragraphs:
                        if len(para) < config.min_text_length:
                            continue

                        # 判断文本类型
                        text_type = self._classify_text_type(para)

                        # 提取章节标题
                        heading = self._extract_heading(para)

                        # 提取引用
                        citations = self._extract_citations(para)

                        # 分类
                        para_domain, para_subfield = self.taxonomy.classify_domain(para)

                        chunk = TextChunk(
                            chunk_id=f"{paper_id[:8]}_chunk_{chunk_index:04d}",
                            paper_id=paper_id,
                            text=para,
                            text_type=text_type,
                            page_num=page_num,
                            chunk_index=chunk_index,
                            heading=heading,
                            domain=para_domain if not domain else domain,
                            subfield=para_subfield if not subfield else subfield,
                            citations=citations,
                        )
                        chunks.append(chunk)
                        chunk_index += 1

        except Exception as e:
            print(f"Warning: Error extracting text from {pdf_path}: {e}")

        return chunks

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空白
        text = re.sub(r"\s+", " ", text)
        # 移除特殊字符（保留基本标点）
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
        return text.strip()

    def _split_paragraphs(self, text: str) -> List[str]:
        """将文本分割成段落"""
        # 按双换行或单换行分割
        paragraphs = re.split(r"\n\n+|\n(?=[A-Z])|\r\n\r\n+", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _classify_text_type(self, text: str) -> str:
        """分类文本类型"""
        text_lower = text.lower()

        if text_lower.startswith("abstract"):
            return "abstract"
        elif text_lower.startswith("introduction"):
            return "introduction"
        elif text_lower.startswith("conclusion") or text_lower.startswith("summary"):
            return "conclusion"
        elif text_lower.startswith("reference") or text_lower.startswith("bibliography"):
            return "reference"
        elif len(text) < 100 and not text.endswith((".", "!", "?")):
            return "heading"
        else:
            return "body"

    def _extract_heading(self, text: str) -> str:
        """提取章节标题"""
        # 匹配常见的标题模式
        for pattern in self.heading_patterns:
            match = re.match(pattern, text.strip())
            if match:
                return text.strip()[:100]  # 限制长度
        return ""

    def _extract_citations(self, text: str) -> List[str]:
        """提取参考文献引用"""
        citations = []

        # 数字引用 [1], [2-5]
        num_refs = re.findall(r"\[(\d+(?:-\d+)?)\]", text)
        citations.extend([f"[[cite:#{ref}]]" for ref in num_refs])

        # 作者-年份引用 (Smith et al., 2020)
        author_refs = re.findall(r"\(([A-Z][a-z]+(?:\s+et\s+al\.?)?,\s*\d{4})\)", text)
        citations.extend([f"[[cite:@{ref}]]" for ref in author_refs])

        return list(set(citations))  # 去重


class BatchProcessor:
    """批量处理多个PDF"""

    def __init__(self, processor: PDFProcessor):
        self.processor = processor

    def process_directory(
        self,
        dir_path: str | Path,
        domain: str = "",
        subfield: str = "",
        recursive: bool = True,
    ) -> List[Tuple[Paper, List[Figure], List[TextChunk], List[Dict[str, Any]]]]:
        """
        批量处理目录中的所有PDF

        Args:
            dir_path: 目录路径
            domain: 默认领域分类
            subfield: 默认子领域分类
            recursive: 是否递归子目录

        Returns:
            List of (Paper, List[Figure], List[TextChunk])
        """
        dir_path = Path(dir_path)
        results = []

        # 查找所有PDF
        if recursive:
            pdf_files = list(dir_path.rglob("*.pdf"))
        else:
            pdf_files = list(dir_path.glob("*.pdf"))

        print(f"Found {len(pdf_files)} PDF files in {dir_path}")

        for pdf_path in pdf_files:
            try:
                print(f"Processing: {pdf_path.name}")
                result = self.processor.process(pdf_path, domain, subfield)
                results.append(result)
            except Exception as e:
                print(f"Error processing {pdf_path}: {e}")
                continue

        return results
