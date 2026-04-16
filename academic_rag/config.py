"""
学术论文 RAG 系统 - 配置
支持多领域分类（太赫兹、光学、物理等）
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import json

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
OBSIDIAN_VAULT = PROJECT_ROOT / "Obsidian-Vault"
PAPER_STORAGE = PROJECT_ROOT / "academic_rag" / "papers"
VECTOR_DB_PATH = PROJECT_ROOT / "academic_rag" / "chroma_db"
VISUALIZATIONS = OBSIDIAN_VAULT / "6️⃣ 工具" / "visualizations"

# 领域分类体系（与Obsidian知识树对应）
DOMAIN_TAXONOMY = {
    "optics": {
        "name": "光学",
        "subfields": {
            "terahertz": "太赫兹技术",
            "metasurface": "超表面/超构材料",
            "quantum_optics": "量子光学",
            "fiber_optics": "光纤光学",
            "nonlinear_optics": "非线性光学",
            "spectroscopy": "光谱学",
        }
    },
    "physics": {
        "name": "物理",
        "subfields": {
            "semiconductor": "半导体物理",
            "electromagnetic": "电磁场理论",
            "quantum_mechanics": "量子力学",
            "statistical_physics": "统计物理",
        }
    },
    "engineering": {
        "name": "工程",
        "subfields": {
            "communication": "通信工程",
            "microwave": "微波工程",
            "materials": "材料工程",
        }
    },
    "chemistry": {
        "name": "化学",
        "subfields": {
            "spectroscopy": "光谱化学",
            "materials_chem": "材料化学",
        }
    }
}

@dataclass
class RAGConfig:
    """RAG系统配置"""
    # 嵌入模型
    embedding_model: str = "BAAI/bge-m3"  # BGE-M3 多语言嵌入
    embedding_device: str = "cpu"  # cpu/cuda

    # 向量数据库
    vector_db_type: str = "chroma"
    collection_name: str = "academic_papers"

    # PDF处理
    extract_images: bool = True
    image_dpi: int = 300
    min_text_length: int = 50  # 最小文本块长度

    # 搜索参数
    top_k: int = 5
    similarity_threshold: float = 0.3

    # 路径
    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    obsidian_vault: Path = field(default_factory=lambda: OBSIDIAN_VAULT)
    paper_storage: Path = field(default_factory=lambda: PAPER_STORAGE)
    vector_db_path: Path = field(default_factory=lambda: VECTOR_DB_PATH)
    visualizations: Path = field(default_factory=lambda: VISUALIZATIONS)

    def __post_init__(self):
        """确保目录存在"""
        self.paper_storage.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)

    def get_subfield_path(self, domain: str, subfield: str) -> Path:
        """获取子领域对应的Obsidian路径"""
        domain_names = {
            "optics": "2️⃣ 研究方向",
            "physics": "1️⃣ 学科基础",
            "engineering": "3️⃣ 方法论",
            "chemistry": "1️⃣ 学科基础",
        }
        domain_path = self.obsidian_vault / domain_names.get(domain, "1️⃣ 学科基础")

        # 查找对应的子领域文件夹
        if domain == "optics" and subfield == "terahertz":
            return domain_path / "太赫兹技术"
        elif domain == "optics" and subfield == "metasurface":
            return domain_path / "超表面技术"
        elif domain == "optics" and subfield == "spectroscopy":
            return domain_path / "光谱学"
        else:
            return domain_path

    def to_dict(self) -> dict:
        return {
            "embedding_model": self.embedding_model,
            "embedding_device": self.embedding_device,
            "vector_db_type": self.vector_db_type,
            "collection_name": self.collection_name,
            "extract_images": self.extract_images,
            "image_dpi": self.image_dpi,
            "min_text_length": self.min_text_length,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
        }


# 全局配置实例
config = RAGConfig()
