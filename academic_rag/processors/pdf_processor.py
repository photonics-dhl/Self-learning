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

from academic_rag.config import config
from academic_rag.db.models import Paper, Figure, TextChunk, DomainTaxonomy


class PDFProcessor:
    """PDF论文处理器 - 提取文本、图表和元数据"""

    def __init__(self, extract_images: bool = True, image_dpi: int = 300):
        self.extract_images = extract_images
        self.image_dpi = image_dpi
        self.taxonomy = DomainTaxonomy()

        # 图表类型模式
        self.figure_patterns = [
            r"(?:Figure|Fig\.?|Fig\.?)\s*(\d+[A-Za-z]?)",
            r"(?:Plot|Plot\.?)\s*(\d+[A-Za-z]?)",
            r"(?:Chart|Ch\.?)\s*(\d+[A-Za-z]?)",
            r"(?:Panel|Panel\.?)\s*([A-Za-z])",
            r"图\s*(\d+[A-Za-z]?)",
            r"第\s*(\d+)\s*图",
        ]

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

    def process(self, pdf_path: str | Path, domain: str = "", subfield: str = "") -> Tuple[Paper, List[Figure], List[TextChunk]]:
        """
        处理单个PDF论文

        Args:
            pdf_path: PDF文件路径
            domain: 领域分类（如 "optics"）
            subfield: 子领域分类（如 "terahertz"）

        Returns:
            (Paper, List[Figure], List[TextChunk])
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

        # 提取文本块
        text_chunks = self._extract_text_chunks(pdf_path, paper.paper_id, domain, subfield)

        # 更新统计
        paper.num_figures = len(figures)
        paper.num_text_chunks = len(text_chunks)

        return paper, figures, text_chunks

    def _compute_file_hash(self, pdf_path: Path) -> str:
        """计算文件MD5哈希"""
        hasher = hashlib.md5()
        with open(pdf_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """从PDF提取元数据"""
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

                # 尝试从PDF元数据获取
                doc_metadata = doc.metadata
                if doc_metadata:
                    metadata["title"] = doc_metadata.get("title", "")
                    metadata["doi"] = doc_metadata.get("doi", "")

                # 尝试从第一页提取标题和作者
                if len(doc) > 0:
                    first_page = doc[0]
                    text = first_page.get_text()

                    # 提取标题（通常在第一页顶部）
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if lines:
                        metadata["title"] = lines[0][:200]  # 取第一行作为标题

                    # 尝试提取作者（通常在标题下方）
                    if len(lines) > 1:
                        # 简单启发式：找包含多个逗号或"and"的行
                        for line in lines[1:5]:
                            if "," in line and len(line) < 200:
                                authors = re.split(r",\s*|\s+and\s+", line)
                                if 1 < len(authors) <= 10:
                                    metadata["authors"] = [a.strip() for a in authors if a.strip()]
                                    break

                    # 尝试提取年份
                    year_match = re.search(r"\b(19|20)\d{2}\b", text)
                    if year_match:
                        metadata["year"] = int(year_match.group())

                # 尝试提取摘要
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

                # 尝试从PDF信息获取期刊
                if doc_metadata:
                    metadata["journal"] = doc_metadata.get("journal", "")

        except Exception as e:
            print(f"Warning: Error extracting metadata from {pdf_path}: {e}")

        return metadata

    def _auto_classify(self, title: str, abstract: str) -> Tuple[str, str]:
        """根据标题和摘要自动分类"""
        combined = f"{title} {abstract}"
        return self.taxonomy.classify_domain(combined)

    def _extract_figures(self, pdf_path: Path, paper_id: str) -> List[Figure]:
        """从PDF提取图表"""
        figures = []
        figure_counter = 0

        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc, 1):
                    # 获取页面文本用于图表标题匹配
                    page_text = page.get_text()

                    # 查找图表
                    image_list = page.get_images(full=True)

                    for img_index, img_info in enumerate(image_list):
                        try:
                            xref = img_info[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            image_ext = base_image["ext"]

                            # 计算图片hash
                            img_hash = hashlib.md5(image_bytes).hexdigest()

                            # 构建文件名
                            img_filename = f"{paper_id}_p{page_num}_i{img_index}.{image_ext}"
                            img_path = config.visualizations / paper_id[:8] / img_filename

                            # 保存图片
                            img_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(img_path, "wb") as f:
                                f.write(image_bytes)

                            # 尝试匹配图表标题
                            caption = self._find_figure_caption(page_text, img_index, page_num)

                            figure = Figure(
                                figure_id=f"{paper_id[:8]}_fig_{figure_counter:03d}",
                                paper_id=paper_id,
                                figure_label=caption.get("label", f"Fig. {figure_counter + 1}"),
                                figure_caption=caption.get("caption", ""),
                                page_num=page_num,
                                image_path=str(img_path),
                                image_hash=img_hash,
                                width=base_image.get("width", 0),
                                height=base_image.get("height", 0),
                                figure_type=caption.get("type", "unknown"),
                            )
                            figures.append(figure)
                            figure_counter += 1

                        except Exception as e:
                            print(f"Warning: Error extracting image {img_index} from page {page_num}: {e}")
                            continue

        except Exception as e:
            print(f"Warning: Error extracting figures from {pdf_path}: {e}")

        return figures

    def _find_figure_caption(self, page_text: str, img_index: int, page_num: int) -> Dict[str, str]:
        """在页面文本中查找图表标题"""
        result = {"label": "", "caption": "", "type": "unknown"}

        # 分割文本为行
        lines = page_text.split("\n")

        # 查找包含Figure的行
        for i, line in enumerate(lines):
            line_clean = line.strip()

            # 匹配各种图标模式
            for pattern in self.figure_patterns:
                match = re.search(pattern, line_clean, re.IGNORECASE)
                if match:
                    result["label"] = match.group(0)
                    result["type"] = self._classify_figure_type(line_clean)
                    result["caption"] = line_clean
                    return result

        # 如果没找到，返回默认标签
        result["label"] = f"Fig. {img_index + 1}"
        return result

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
    ) -> List[Tuple[Paper, List[Figure], List[TextChunk]]]:
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
