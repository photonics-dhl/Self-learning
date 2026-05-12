"""
学术论文 RAG 系统 - 向量索引器
Phase 2: 使用ChromaDB存储和检索向量
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import asdict

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from academic_rag.config import config
from academic_rag.db.models import Paper, Figure, TextChunk, SearchResult
from academic_rag.indexer.figure_indexer import FigureIndexer, CaptionIndexer


class VectorIndexer:
    """向量索引器 - 使用ChromaDB存储论文块和向量"""

    def __init__(
        self,
        collection_name: str = "academic_papers",
        embedding_model: str = "BAAI/bge-m3",
        device: str = "cpu",
        figure_indexer: Optional[FigureIndexer] = None,
    ):
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.device = device

        # 初始化嵌入模型
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model, device=device)

        # 初始化ChromaDB
        self._init_chromadb()

        # 图像索引器（可选，需要 CLIP）
        self.figure_indexer = figure_indexer

        # 标题索引器（语义匹配 chunk → figure）
        self.caption_indexer = CaptionIndexer(self.embedding_model)

        # 内存存储（用于快速查询）
        self._papers: Dict[str, Paper] = {}
        self._figures: Dict[str, Figure] = {}
        self._chunks: Dict[str, TextChunk] = {}

    def _init_chromadb(self):
        """初始化ChromaDB"""
        db_path = str(config.vector_db_path)

        self.chroma_client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False),
        )

        # 创建或获取集合
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Academic paper chunks with embeddings"},
        )

        print(f"ChromaDB initialized at {db_path}, collection: {self.collection_name}")

    def index_paper(
        self,
        paper: Paper,
        figures: List[Figure],
        chunks: List[TextChunk],
        tables: List[Dict[str, Any]] = None,
        regenerate: bool = False,
    ) -> bool:
        """
        索引一篇论文的所有内容

        Args:
            paper: 论文元数据
            figures: 图表列表
            chunks: 文本块列表
            tables: 表格列表 (list of dict)
            regenerate: 是否重新生成（删除旧数据）

        Returns:
            是否成功
        """
        try:
            paper_id = paper.paper_id

            # 检查是否已索引
            if not regenerate and self._is_paper_indexed(paper_id):
                print(f"Paper {paper_id} already indexed. Use regenerate=True to re-index.")
                return False

            # 删除旧数据（如果重新生成）
            if regenerate:
                self._delete_paper(paper_id)

            # 存储论文元数据
            self._papers[paper_id] = paper

            # 存储图表
            for fig in figures:
                self._figures[fig.figure_id] = fig

            # 向量化并存储文本块
            self._index_chunks(paper_id, chunks)

            # 保存元数据到文件
            self._save_metadata(paper_id, paper, figures, chunks, tables or [])

            n_tables = len(tables) if tables else 0
            print(f"Indexed paper {paper_id}: {paper.title[:50]}...")
            print(f"  - {len(chunks)} text chunks")
            print(f"  - {len(figures)} figures")
            print(f"  - {n_tables} tables")

            return True

        except Exception as e:
            print(f"Error indexing paper: {e}")
            return False

    def _index_chunks(self, paper_id: str, chunks: List[TextChunk]):
        """向量化并存储文本块"""
        if not chunks:
            return

        # 批量获取嵌入
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)

        # 准备批量数据
        ids = [chunk.chunk_id for chunk in chunks]
        documents = texts
        metadatas = [
            {
                "paper_id": chunk.paper_id,
                "page_num": chunk.page_num,
                "text_type": chunk.text_type,
                "heading": chunk.heading,
                "domain": chunk.domain,
                "subfield": chunk.subfield,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ]

        # 批量添加到集合
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas,
        )

        # 存储到内存
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk

        # 索引图像标题用于语义匹配
        paper_figs = [f for f in self._figures.values() if f.paper_id == paper_id]
        if paper_figs:
            self.caption_indexer.index_captions(paper_figs, paper_id)

    def _is_paper_indexed(self, paper_id: str) -> bool:
        """检查论文是否已索引"""
        try:
            result = self.collection.get(
                where={"paper_id": paper_id},
                limit=1,
            )
            return len(result["ids"]) > 0
        except:
            return False

    def _delete_paper(self, paper_id: str):
        """删除论文的所有数据"""
        try:
            result = self.collection.get(where={"paper_id": paper_id})
            if result["ids"]:
                self.collection.delete(ids=result["ids"])
        except:
            pass

        self._papers.pop(paper_id, None)
        self._figures = {k: v for k, v in self._figures.items() if v.paper_id != paper_id}
        self._chunks = {k: v for k, v in self._chunks.items() if v.paper_id != paper_id}

        meta_file = config.vector_db_path / f"{paper_id}_metadata.json"
        if meta_file.exists():
            meta_file.unlink()

    def _save_metadata(
        self,
        paper_id: str,
        paper: Paper,
        figures: List[Figure],
        chunks: List[TextChunk],
        tables: List[Dict[str, Any]] = None,
    ):
        """保存元数据到JSON文件"""
        meta_file = config.vector_db_path / f"{paper_id}_metadata.json"

        metadata = {
            "paper": paper.to_dict(),
            "figures": [fig.to_dict() for fig in figures],
            "tables": tables or [],
            "chunks": [chunk.to_dict() for chunk in chunks],
        }

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def search(
        self,
        query: str,
        domain: str = "",
        subfield: str = "",
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[SearchResult]:
        """
        语义搜索

        Args:
            query: 查询文本
            domain: 筛选领域
            subfield: 筛选子领域
            top_k: 返回数量
            similarity_threshold: 相似度阈值

        Returns:
            SearchResult列表
        """
        where_filter = None
        conditions = []
        if domain:
            conditions.append({"domain": domain})
        if subfield:
            conditions.append({"subfield": subfield})
        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}

        query_embedding = self.embedding_model.encode([query])

        try:
            if where_filter:
                results = self.collection.query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=top_k * 2,
                    where=where_filter,
                )
            else:
                results = self.collection.query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=top_k * 2,
                )
        except Exception as e:
            print(f"Search error: {e}")
            return []

        search_results = []
        for i in range(len(results["ids"][0])):
            doc_id = results["ids"][0][i]
            document = results["documents"][0][i]
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            similarity = 1 - distance / 2

            if similarity < similarity_threshold:
                continue

            paper_id = metadata["paper_id"]
            paper = self._papers.get(paper_id)
            if not paper:
                paper = self._load_paper_metadata(paper_id)

            figure = self._find_related_figure(doc_id, paper_id)
            chunk = self._chunks.get(doc_id)

            if paper:
                result = SearchResult(
                    chunk=chunk,
                    paper=paper,
                    figure=figure,
                    similarity=similarity,
                    highlight=self._create_highlight(document, query),
                    context_before=self._get_context_before(document, query, 100),
                    context_after=self._get_context_after(document, query, 100),
                )
                search_results.append(result)

            if len(search_results) >= top_k:
                break

        return search_results

    def search_by_figure_concept(
        self,
        concept: str,
        domain: str = "",
        subfield: str = "",
        top_k: int = 5,
    ) -> List[Tuple[Figure, Paper, float]]:
        """按概念搜索图表"""
        results = self.search(
            query=f"figure showing {concept}",
            domain=domain,
            subfield=subfield,
            top_k=top_k * 2,
        )

        figure_results = []
        seen_figures = set()

        for result in results:
            if result.figure and result.figure.figure_id not in seen_figures:
                figure_results.append((result.figure, result.paper, result.similarity))
                seen_figures.add(result.figure.figure_id)

            if len(figure_results) >= top_k:
                break

        return figure_results

    def _load_paper_metadata(self, paper_id: str) -> Optional[Paper]:
        """从文件加载论文元数据"""
        meta_file = config.vector_db_path / f"{paper_id}_metadata.json"

        if not meta_file.exists():
            return None

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            paper = Paper.from_dict(metadata["paper"])
            self._papers[paper_id] = paper

            for fig_dict in metadata.get("figures", []):
                figure = Figure.from_dict(fig_dict)
                self._figures[figure.figure_id] = figure

            for chunk_dict in metadata.get("chunks", []):
                chunk = TextChunk.from_dict(chunk_dict)
                self._chunks[chunk.chunk_id] = chunk

            return paper

        except Exception as e:
            print(f"Error loading paper metadata: {e}")
            return None

    def _find_related_figure(self, chunk_id: str, paper_id: str) -> Optional[Figure]:
        """语义匹配查找关联图表 — 使用 caption embedding 而非页码启发式"""
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            return None

        result = self.caption_indexer.find_best_figure(chunk.text, paper_id)
        if result:
            figure_id, similarity = result
            return self._figures.get(figure_id)

        # Fallback: 页码匹配（caption 未索引时）
        page_figures = [
            fig for fig in self._figures.values()
            if fig.paper_id == paper_id and fig.page_num == chunk.page_num
        ]
        return page_figures[0] if page_figures else None

    def _create_highlight(self, document: str, query: str) -> str:
        """创建高亮文本"""
        words = query.lower().split()
        highlight = document

        first_match_pos = -1
        for word in words:
            pos = highlight.lower().find(word)
            if pos != -1 and (first_match_pos == -1 or pos < first_match_pos):
                first_match_pos = pos

        if first_match_pos == -1:
            return document[:200] + "..."

        start = max(0, first_match_pos - 50)
        end = min(len(highlight), first_match_pos + 150)
        return "..." + highlight[start:end] + "..."

    def _get_context_before(self, document: str, query: str, char_limit: int) -> str:
        """获取匹配前的上下文"""
        words = query.lower().split()
        first_match_pos = -1

        for word in words:
            pos = document.lower().find(word)
            if pos != -1 and (first_match_pos == -1 or pos < first_match_pos):
                first_match_pos = pos

        if first_match_pos == -1:
            return ""

        start = max(0, first_match_pos - char_limit)
        return document[start:first_match_pos]

    def _get_context_after(self, document: str, query: str, char_limit: int) -> str:
        """获取匹配后的上下文"""
        words = query.lower().split()
        last_match_pos = -1

        for word in words:
            pos = document.lower().find(word)
            if pos != -1:
                last_match_pos = max(last_match_pos, pos + len(word))

        if last_match_pos == -1:
            return ""

        end = min(len(document), last_match_pos + char_limit)
        return document[last_match_pos:end]

    def index_paper_figures(self, paper: Paper, figures: List[Figure]) -> int:
        """使用 CLIP 索引论文图像 (创建跨模态嵌入)"""
        if not self.figure_indexer:
            print("FigureIndexer not available. Install open-clip-torch.")
            return 0
        return self.figure_indexer.index_figures(figures, paper)

    def search_figures_by_text(
        self, query: str, top_k: int = 5, domain: str = "", figure_type: str = ""
    ) -> List[dict]:
        """CLIP 文本→图像检索"""
        if not self.figure_indexer:
            return []
        return self.figure_indexer.search_by_text(
            query, top_k=top_k, domain=domain, figure_type=figure_type
        )

    def get_paper_by_id(self, paper_id: str) -> Optional[Paper]:
        """获取论文元数据"""
        if paper_id in self._papers:
            return self._papers[paper_id]
        return self._load_paper_metadata(paper_id)

    def get_figures_by_paper(self, paper_id: str) -> List[Figure]:
        """获取论文的所有图表"""
        if paper_id not in self._papers:
            self._load_paper_metadata(paper_id)

        return [fig for fig in self._figures.values() if fig.paper_id == paper_id]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        # Ensure all papers loaded from disk
        db_path = config.vector_db_path
        for meta_file in sorted(db_path.glob("*_metadata.json")):
            paper_id = meta_file.stem.replace("_metadata", "")
            if paper_id not in self._papers:
                self._load_paper_metadata(paper_id)

        return {
            "total_papers": len(self._papers),
            "total_chunks": self.collection.count(),
            "total_figures": len(self._figures),
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model_name,
            "db_path": str(config.vector_db_path),
        }

    def list_papers(self, domain: str = "", subfield: str = "") -> List[Paper]:
        """列出所有已索引的论文（从磁盘元数据扫描）"""
        # Load all metadata files from disk
        db_path = config.vector_db_path
        for meta_file in sorted(db_path.glob("*_metadata.json")):
            paper_id = meta_file.stem.replace("_metadata", "")
            if paper_id not in self._papers:
                self._load_paper_metadata(paper_id)

        papers = list(self._papers.values())

        if domain:
            papers = [p for p in papers if p.domain == domain]
        if subfield:
            papers = [p for p in papers if p.subfield == subfield]

        return sorted(papers, key=lambda p: p.added_at, reverse=True)
