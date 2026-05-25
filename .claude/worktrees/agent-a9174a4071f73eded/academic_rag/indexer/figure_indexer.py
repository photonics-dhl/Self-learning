"""
学术论文 RAG 系统 - 图像索引器
Phase 1: CLIP 跨模态嵌入，实现 text↔image 语义检索
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import numpy as np
import chromadb
import torch
from chromadb.config import Settings
from PIL import Image

from academic_rag.config import config
from academic_rag.db.models import Paper, Figure


class FigureIndexer:
    """图像向量索引器 — CLIP 跨模态嵌入 + ChromaDB 存储"""

    def __init__(
        self,
        clip_model_name: str = "ViT-B-32",
        clip_pretrained: str = "laion2b_s34b_b79k",
        device: str = "cpu",
    ):
        self.clip_model_name = clip_model_name
        self.clip_pretrained = clip_pretrained
        self.device = device
        self._figures: Dict[str, Figure] = {}
        self._model = None
        self._preprocess = None
        self._tokenizer = None

        self._init_chromadb()

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def _lazy_load(self):
        """延迟加载 CLIP 模型（仅在首次使用时加载）"""
        if self._model is not None:
            return
        import open_clip
        print(f"Loading CLIP model: {self.clip_model_name} ({self.clip_pretrained})")
        cache = str(config.models_cache_dir)
        self._model, _, self._preprocess = open_clip.create_model_and_transforms(
            self.clip_model_name, pretrained=self.clip_pretrained, cache_dir=cache
        )
        self._tokenizer = open_clip.get_tokenizer(self.clip_model_name)
        self._model = self._model.to(self.device).eval()
        print(f"CLIP loaded. Embedding dim: {config.clip_embedding_dim}")

    def _init_chromadb(self):
        db_path = str(config.vector_db_path)
        self.chroma_client = chromadb.PersistentClient(
            path=db_path, settings=Settings(anonymized_telemetry=False)
        )
        self.figure_collection = self.chroma_client.get_or_create_collection(
            name=config.figure_collection_name,
            metadata={
                "description": "Figure CLIP embeddings for cross-modal retrieval",
                "embedding_model": f"CLIP-{self.clip_model_name}-{self.clip_pretrained}",
                "embedding_dim": str(config.clip_embedding_dim),
            },
        )
        print(f"Figure ChromaDB ready. Collection: {config.figure_collection_name}")

    # ─── Indexing ──────────────────────────────────────────────

    def index_figures(self, figures: List[Figure], paper: Paper) -> int:
        """
        批量索引导入图像

        Returns:
            成功索引的图像数量
        """
        if not figures:
            return 0
        self._lazy_load()

        valid_figures = []
        image_tensors = []
        captions = []

        for fig in figures:
            img_tensor = self._load_image(fig.image_path)
            if img_tensor is None:
                continue
            image_tensors.append(img_tensor)
            captions.append(self._build_caption_text(fig))
            valid_figures.append(fig)

        if not valid_figures:
            return 0

        # 批量生成 CLIP 嵌入
        with torch.no_grad():
            img_batch = torch.stack(image_tensors).to(self.device)
            img_features = self._model.encode_image(img_batch)
            img_features = img_features / img_features.norm(dim=-1, keepdim=True)

            text_tokens = self._tokenizer(captions)
            text_features = self._model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        # 存储到 ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for i, fig in enumerate(valid_figures):
            combined_emb = self._combine_embeddings(img_features[i], text_features[i], alpha=0.7)

            ids.append(fig.figure_id)
            documents.append(captions[i])
            metadatas.append({
                "paper_id": fig.paper_id,
                "figure_label": fig.figure_label,
                "figure_caption": fig.figure_caption[:500],
                "figure_type": fig.figure_type,
                "page_num": fig.page_num,
                "image_path": fig.image_path,
                "width": fig.width,
                "height": fig.height,
                "paper_title": paper.title[:200],
                "paper_year": paper.year,
                "domain": paper.domain,
                "subfield": paper.subfield,
            })
            embeddings.append(combined_emb.cpu().numpy().tolist())

        # 删除旧数据（重新索引）
        existing = self.figure_collection.get(where={"paper_id": paper.paper_id})
        if existing["ids"]:
            self.figure_collection.delete(ids=existing["ids"])

        self.figure_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        for fig in valid_figures:
            self._figures[fig.figure_id] = fig

        print(f"FigureIndexer: indexed {len(valid_figures)} figures for paper {paper.paper_id[:8]}")
        return len(valid_figures)

    # ─── Search ────────────────────────────────────────────────

    def search_by_text(
        self,
        query: str,
        top_k: int = 5,
        domain: str = "",
        subfield: str = "",
        figure_type: str = "",
        min_similarity: float = 0.25,
    ) -> List[Dict[str, Any]]:
        """
        文本查询 → 匹配图像

        Args:
            query: 自然语言描述，e.g. "optical rectification setup diagram"
            top_k: 返回数量
            domain: 领域筛选
            subfield: 子领域筛选
            figure_type: 图像类型筛选 (diagram/setup/plot/photo/spectrum)
            min_similarity: 最小相似度阈值

        Returns:
            [{figure_id, similarity, caption, image_path, paper_title, ...}, ...]
        """
        if not query.strip():
            return []
        self._lazy_load()

        # CLIP 文本嵌入
        text_tokens = self._tokenizer([query])
        with torch.no_grad():
            text_feat = self._model.encode_text(text_tokens)
            text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)

        # 构建过滤条件
        where_filter = {}
        if domain:
            where_filter["domain"] = domain
        if subfield:
            where_filter["subfield"] = subfield

        # ChromaDB 查询
        try:
            if where_filter:
                results = self.figure_collection.query(
                    query_embeddings=text_feat.cpu().numpy().tolist(),
                    n_results=top_k * 3,
                    where=where_filter,
                )
            else:
                results = self.figure_collection.query(
                    query_embeddings=text_feat.cpu().numpy().tolist(),
                    n_results=top_k * 3,
                )
        except Exception as e:
            print(f"Figure search error: {e}")
            return []

        output = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            similarity = 1 - distance / 2

            if similarity < min_similarity:
                continue

            metadata = results["metadatas"][0][i]

            if figure_type and metadata.get("figure_type") != figure_type:
                continue

            output.append({
                "figure_id": results["ids"][0][i],
                "similarity": round(similarity, 4),
                "caption": metadata.get("figure_caption", ""),
                "label": metadata.get("figure_label", ""),
                "figure_type": metadata.get("figure_type", ""),
                "image_path": metadata.get("image_path", ""),
                "page_num": metadata.get("page_num", 0),
                "paper_id": metadata.get("paper_id", ""),
                "paper_title": metadata.get("paper_title", ""),
                "paper_year": metadata.get("paper_year", 0),
                "domain": metadata.get("domain", ""),
                "subfield": metadata.get("subfield", ""),
            })

            if len(output) >= top_k:
                break

        return output

    def search_by_image(
        self,
        image_path: str,
        top_k: int = 5,
        min_similarity: float = 0.25,
    ) -> List[Dict[str, Any]]:
        """图像 → 相似图像检索"""
        img_tensor = self._load_image(image_path)
        if img_tensor is None:
            return []

        self._lazy_load()
        with torch.no_grad():
            img_batch = torch.stack([img_tensor]).to(self.device)
            img_feat = self._model.encode_image(img_batch)
            img_feat = img_feat / img_feat.norm(dim=-1, keepdim=True)

        results = self.figure_collection.query(
            query_embeddings=img_feat.cpu().numpy().tolist(),
            n_results=top_k,
        )

        output = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            similarity = 1 - distance / 2
            if similarity < min_similarity:
                continue
            metadata = results["metadatas"][0][i]
            output.append({
                "figure_id": results["ids"][0][i],
                "similarity": round(similarity, 4),
                "caption": metadata.get("figure_caption", ""),
                "image_path": metadata.get("image_path", ""),
                "paper_title": metadata.get("paper_title", ""),
            })

        return output

    def get_figures_by_paper(self, paper_id: str) -> List[Dict[str, Any]]:
        """获取论文的所有已索引图像"""
        try:
            results = self.figure_collection.get(where={"paper_id": paper_id})
            return [
                {
                    "figure_id": rid,
                    "caption": meta.get("figure_caption", ""),
                    "image_path": meta.get("image_path", ""),
                    "figure_type": meta.get("figure_type", ""),
                    "page_num": meta.get("page_num", 0),
                }
                for rid, meta in zip(results["ids"], results["metadatas"])
            ]
        except Exception:
            return []

    def delete_paper(self, paper_id: str):
        try:
            results = self.figure_collection.get(where={"paper_id": paper_id})
            if results["ids"]:
                self.figure_collection.delete(ids=results["ids"])
        except Exception:
            pass

    def get_stats(self) -> Dict[str, Any]:
        try:
            count = self.figure_collection.count()
        except Exception:
            count = 0
        return {
            "total_indexed_figures": count,
            "model": f"CLIP-{self.clip_model_name}",
            "embedding_dim": config.clip_embedding_dim,
            "collection": config.figure_collection_name,
        }

    # ─── Internal ──────────────────────────────────────────────

    def _load_image(self, image_path: str) -> Optional[torch.Tensor]:
        """加载并预处理图像，返回 [C, H, W] tensor"""
        img_path = Path(image_path)
        if not img_path.exists():
            return None
        try:
            img = Image.open(img_path).convert("RGB")
            return self._preprocess(img)
        except Exception:
            return None

    def _build_caption_text(self, fig: Figure) -> str:
        """构建用于 CLIP text encoder 的 caption 文本"""
        parts = [fig.figure_label, fig.figure_caption]
        if fig.description:
            parts.append(fig.description)
        return " ".join(p for p in parts if p)

    def _combine_embeddings(
        self,
        img_emb: torch.Tensor,
        text_emb: torch.Tensor,
        alpha: float = 0.7,
    ) -> torch.Tensor:
        """
        α-混合图像和文本嵌入
        alpha=0.7: 偏重图像嵌入，caption 提供语义锚定
        """
        combined = alpha * img_emb + (1 - alpha) * text_emb
        return combined / combined.norm(dim=-1, keepdim=True)


class CaptionIndexer:
    """
    图像标题索引器 — 将 figure captions 作为独立 ChromaDB 文本块存储

    目的: 替代 _find_related_figure() 的 page-number heuristic,
         改用 caption 与 chunk 的 BGE-M3 语义相似度匹配
    """

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self._init_chromadb()

    def _init_chromadb(self):
        db_path = str(config.vector_db_path)
        self.chroma_client = chromadb.PersistentClient(
            path=db_path, settings=Settings(anonymized_telemetry=False)
        )
        self.caption_collection = self.chroma_client.get_or_create_collection(
            name="figure_captions",
            metadata={
                "description": "Figure captions for semantic chunk-to-figure matching",
                "embedding_model": "BAAI/bge-m3",
            },
        )

    def index_captions(self, figures: List[Figure], paper_id: str) -> int:
        if not figures:
            return 0
        texts = [f"{fig.figure_label}: {fig.figure_caption}" for fig in figures]
        embeddings = self.embedding_model.encode(texts)
        ids = [fig.figure_id for fig in figures]
        metadatas = [
            {
                "paper_id": fig.paper_id,
                "page_num": fig.page_num,
                "figure_label": fig.figure_label,
                "figure_type": fig.figure_type,
            }
            for fig in figures
        ]

        existing = self.caption_collection.get(where={"paper_id": paper_id})
        if existing["ids"]:
            self.caption_collection.delete(ids=existing["ids"])

        self.caption_collection.add(
            ids=ids, embeddings=embeddings.tolist(), documents=texts, metadatas=metadatas
        )
        return len(ids)

    def find_best_figure(
        self,
        chunk_text: str,
        paper_id: str,
        min_similarity: float = 0.3,
    ) -> Optional[Tuple[str, float]]:
        """
        为文本块找到最匹配的图像

        Returns:
            (figure_id, similarity) or None
        """
        chunk_emb = self.embedding_model.encode([chunk_text])
        try:
            results = self.caption_collection.query(
                query_embeddings=chunk_emb.tolist(),
                n_results=3,
                where={"paper_id": paper_id},
            )
        except Exception:
            return None

        if not results["ids"] or not results["ids"][0]:
            return None

        distance = results["distances"][0][0]
        similarity = 1 - distance / 2
        if similarity < min_similarity:
            return None

        return results["ids"][0][0], similarity
