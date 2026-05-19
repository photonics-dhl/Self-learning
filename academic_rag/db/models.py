"""
学术论文 RAG 系统 - 数据模型
支持多领域分类，与Obsidian知识树对应
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid


@dataclass
class Paper:
    """论文元数据"""
    paper_id: str = ""  # Set from file_hash after PDF processing
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    journal: str = ""
    doi: str = ""
    abstract: str = ""

    # 领域分类（与Obsidian知识树对应）
    domain: str = ""  # optics, physics, engineering, chemistry
    subfield: str = ""  # terahertz, metasurface, quantum_optics, etc.

    # 文件信息
    pdf_path: str = ""
    file_hash: str = ""  # 用于去重

    # 内容统计
    num_figures: int = 0
    num_tables: int = 0
    num_pages: int = 0
    num_text_chunks: int = 0

    # 关联的Obsidian笔记
    linked_notes: List[str] = field(default_factory=list)  # [[note_name]]

    # 时间戳
    added_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "doi": self.doi,
            "abstract": self.abstract,
            "domain": self.domain,
            "subfield": self.subfield,
            "pdf_path": self.pdf_path,
            "file_hash": self.file_hash,
            "num_figures": self.num_figures,
            "num_tables": self.num_tables,
            "num_pages": self.num_pages,
            "num_text_chunks": self.num_text_chunks,
            "linked_notes": self.linked_notes,
            "added_at": self.added_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        data = data.copy()
        if "added_at" in data and isinstance(data["added_at"], str):
            data["added_at"] = datetime.fromisoformat(data["added_at"])
        if "modified_at" in data and isinstance(data["modified_at"], str):
            data["modified_at"] = datetime.fromisoformat(data["modified_at"])
        return cls(**data)


@dataclass
class Figure:
    """论文图表"""
    figure_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    paper_id: str = ""
    figure_caption: str = ""
    figure_label: str = ""  # e.g., "Fig. 1", "Figure 2.3"

    # 位置信息
    page_num: int = 0
    bbox: tuple = field(default_factory=lambda: (0, 0, 0, 0))  # x0, y0, x1, y1

    # 图片信息
    image_path: str = ""
    image_hash: str = ""
    width: int = 0
    height: int = 0

    # 内容描述（可选，用于多模态分析）
    description: str = ""  # AI生成的图片描述
    key_findings: List[str] = field(default_factory=list)  # 关键发现

    # 关联的知识点
    related_concepts: List[str] = field(default_factory=list)
    linked_notes: List[str] = field(default_factory=list)

    # 元数据
    figure_type: str = ""  # photo, diagram, chart, graph, etc.
    added_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "figure_id": self.figure_id,
            "paper_id": self.paper_id,
            "figure_caption": self.figure_caption,
            "figure_label": self.figure_label,
            "page_num": self.page_num,
            "bbox": self.bbox,
            "image_path": self.image_path,
            "image_hash": self.image_hash,
            "width": self.width,
            "height": self.height,
            "description": self.description,
            "key_findings": self.key_findings,
            "related_concepts": self.related_concepts,
            "linked_notes": self.linked_notes,
            "figure_type": self.figure_type,
            "added_at": self.added_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Figure":
        data = data.copy()
        if "added_at" in data and isinstance(data["added_at"], str):
            data["added_at"] = datetime.fromisoformat(data["added_at"])
        return cls(**data)


@dataclass
class TextChunk:
    """文本块（用于向量化和检索）"""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    paper_id: str = ""
    figure_id: Optional[str] = None  # 关联的图表（如果有）

    # 内容
    text: str = ""
    text_type: str = "body"  # body, caption, heading, abstract, reference

    # 位置
    page_num: int = 0
    chunk_index: int = 0  # 在文档中的顺序

    # 向量化用
    heading: str = ""  # 所属章节标题
    section_path: str = ""  # e.g., "1. Introduction / 1.2 Background"

    # 领域分类
    domain: str = ""
    subfield: str = ""

    # 关联
    related_concepts: List[str] = field(default_factory=list)
    linked_notes: List[str] = field(default_factory=list)

    # 引用信息
    citations: List[str] = field(default_factory=list)  # [[cite:@Author2024]]格式

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "paper_id": self.paper_id,
            "figure_id": self.figure_id,
            "text": self.text,
            "text_type": self.text_type,
            "page_num": self.page_num,
            "chunk_index": self.chunk_index,
            "heading": self.heading,
            "section_path": self.section_path,
            "domain": self.domain,
            "subfield": self.subfield,
            "related_concepts": self.related_concepts,
            "linked_notes": self.linked_notes,
            "citations": self.citations,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TextChunk":
        return cls(**data)


@dataclass
class SearchResult:
    """搜索结果"""
    chunk: TextChunk
    paper: Paper
    figure: Optional[Figure] = None
    similarity: float = 0.0

    # 上下文（用于显示）
    highlight: str = ""  # 高亮匹配文本
    context_before: str = ""  # 匹配前的上下文
    context_after: str = ""  # 匹配后的上下文


@dataclass
class DomainTaxonomy:
    """领域分类器"""
    # 预定义的领域关键词
    DOMAIN_KEYWORDS = {
        "optics": [
            "terahertz", "thz", "laser", "optical", "photon", "photonics",
            "metasurface", "metamaterial", "plasmon", "diffraction",
            "spectroscopy", "nonlinear", "fiber", "waveguide", "antenna"
        ],
        "physics": [
            "semiconductor", "quantum", "electromagnetic", "condensed matter",
            "solid state", "band structure", "carrier", "phonon"
        ],
        "engineering": [
            "communication", "wireless", "radar", "imaging", "sensor",
            "circuit", "transistor", "cmos", "frequency multiplier"
        ],
        "chemistry": [
            "chemical", "molecular", "reaction", "catalyst", "polymer",
            "spectroscopy", "chromatography"
        ]
    }

    SUBFIELD_KEYWORDS = {
        "terahertz": ["thz", "terahertz", "sub-mm wave"],
        "metasurface": ["metasurface", "metamaterial", "metalens", "beamforming"],
        "quantum_optics": ["quantum", "entanglement", "single photon"],
        "fiber_optics": ["fiber", "optical fiber", "Fiber Bragg"],
        "nonlinear_optics": ["nonlinear", "second harmonic", "chi2", "chi3"],
        "spectroscopy": ["spectroscopy", "spectrum", "absorption"],
        "semiconductor": ["semiconductor", "gaas", "ingap", "silicon"],
        "electromagnetic": ["electromagnetic", "maxwell", "wave propagation"],
        "communication": ["communication", "wireless", "5g", "6g", "modulation"],
        "microwave": ["microwave", "rf", "waveguide", "coaxial"],
    }

    @classmethod
    def classify_domain(cls, text: str) -> tuple[str, str]:
        """
        根据文本内容分类领域和子领域
        返回: (domain, subfield)
        """
        text_lower = text.lower()

        # 优先检测子领域
        subfield_scores = {}
        for subfield, keywords in cls.SUBFIELD_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                subfield_scores[subfield] = score

        if subfield_scores:
            best_subfield = max(subfield_scores, key=subfield_scores.get)
        else:
            best_subfield = "general"

        # 检测领域
        domain_scores = {}
        for domain, keywords in cls.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
        else:
            best_domain = "other"

        return best_domain, best_subfield
