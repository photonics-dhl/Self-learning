"""
学术论文 RAG 系统 - 搜索API
Phase 3: 提供语义搜索和图表搜索接口
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict

from academic_rag.indexer.vector_indexer import VectorIndexer
from academic_rag.db.models import SearchResult, Paper, Figure


class SearchAPI:
    """
    学术论文搜索API

    提供语义搜索、以图搜文、以文搜图等功能
    支持领域/子领域筛选
    """

    def __init__(self, indexer: VectorIndexer):
        self.indexer = indexer

    def search(
        self,
        query: str,
        domain: str = "",
        subfield: str = "",
        top_k: int = 5,
        include_figures: bool = True,
    ) -> Dict[str, Any]:
        """
        语义搜索论文内容

        Args:
            query: 查询文本
            domain: 筛选领域 (optics/physics/engineering/chemistry)
            subfield: 筛选子领域 (terahertz/metasurface/quantum_optics等)
            top_k: 返回数量
            include_figures: 是否包含关联图表

        Returns:
            {
                "results": [...],
                "total": N,
                "query": query,
                "filters": {"domain": ..., "subfield": ...}
            }
        """
        results = self.indexer.search(
            query=query,
            domain=domain,
            subfield=subfield,
            top_k=top_k,
        )

        return {
            "results": [self._format_result(r, include_figures) for r in results],
            "total": len(results),
            "query": query,
            "filters": {"domain": domain, "subfield": subfield},
        }

    def search_figures(
        self,
        concept: str,
        domain: str = "",
        subfield: str = "",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        按概念搜索图表

        用于查找与特定概念相关的图表，
        帮助用户找到合适的配图

        Args:
            concept: 概念描述 (e.g., "photoconductive antenna THz generation")
            domain: 筛选领域
            subfield: 筛选子领域
            top_k: 返回数量

        Returns:
            {
                "figures": [...],
                "total": N,
                "concept": concept
            }
        """
        figure_results = self.indexer.search_by_figure_concept(
            concept=concept,
            domain=domain,
            subfield=subfield,
            top_k=top_k,
        )

        return {
            "figures": [
                {
                    "figure": self._format_figure(fig),
                    "paper": self._format_paper(paper),
                    "similarity": sim,
                }
                for fig, paper, sim in figure_results
            ],
            "total": len(figure_results),
            "concept": concept,
        }

    def get_paper_figures(
        self,
        paper_id: str,
        concept_filter: str = "",
    ) -> List[Dict[str, Any]]:
        """
        获取指定论文的所有图表，支持概念过滤

        Args:
            paper_id: 论文ID
            concept_filter: 过滤概念 (e.g., "system diagram", "experimental setup")

        Returns:
            匹配的图表列表
        """
        figures = self.indexer.get_figures_by_paper(paper_id)

        if not concept_filter:
            return [self._format_figure(fig) for fig in figures]

        # 概念过滤
        filtered = []
        for fig in figures:
            caption_lower = fig.figure_caption.lower()
            desc_lower = fig.description.lower()
            concept_lower = concept_filter.lower()

            # 检查标题或描述是否包含概念关键词
            concept_words = concept_lower.split()
            match_count = sum(1 for w in concept_words if w in caption_lower or w in desc_lower)

            if match_count >= len(concept_words) * 0.5:  # 50%匹配即可
                filtered.append(self._format_figure(fig))

        return filtered

    def get_figure_details(self, figure_id: str) -> Optional[Dict[str, Any]]:
        """
        获取图表详细信息

        包括：
        - 基本信息（标题、标签、页码）
        - 图片路径
        - AI生成的内容描述（如果有）
        - 关键发现（如果有）
        - 关联的概念
        """
        # 从所有论文的图表中查找
        stats = self.indexer.get_stats()
        # 遍历查找（简单粗暴，可以优化）
        for paper in self.indexer.list_papers():
            figures = self.indexer.get_figures_by_paper(paper.paper_id)
            for fig in figures:
                if fig.figure_id == figure_id:
                    return {
                        "figure": self._format_figure(fig),
                        "paper": self._format_paper(paper),
                        "description": fig.description,
                        "key_findings": fig.key_findings,
                        "related_concepts": fig.related_concepts,
                    }
        return None

    def suggest_figure_for_concept(
        self,
        concept: str,
        domain: str = "",
        figure_type: str = "",
    ) -> List[Dict[str, Any]]:
        """
        为指定概念推荐合适的图表

        这是一个辅助功能，帮助用户找到适合解释特定概念的图表

        Args:
            concept: 概念描述 (e.g., "THz PCA emission principle")
            domain: 领域
            figure_type: 图表类型偏好 (diagram/photo/plot/graph/spectrum/setup)

        Returns:
            推荐的图表列表
        """
        # 搜索相关图表
        results = self.search_figures(
            concept=concept,
            domain=domain,
            top_k=10,
        )

        # 按类型过滤
        if figure_type:
            results["figures"] = [
                r for r in results["figures"]
                if r["figure"].get("figure_type") == figure_type
            ]

        return results["figures"][:5]  # 返回前5个

    def search_figures_crossmodal(
        self,
        query: str,
        domain: str = "",
        subfield: str = "",
        figure_type: str = "",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        CLIP 跨模态图像检索 — text→image

        直接使用 CLIP 在图像嵌入空间中查找，而非通过文本中间层
        """
        results = self.indexer.search_figures_by_text(
            query=query,
            top_k=top_k,
            domain=domain,
            figure_type=figure_type,
        )
        return {
            "figures": results,
            "total": len(results),
            "query": query,
            "method": "CLIP-crossmodal",
        }

    def find_figure_for_knowledge_point(
        self,
        knowledge_point: str,
        domain: str = "optics",
        subfield: str = "terahertz",
    ) -> Optional[Dict[str, Any]]:
        """
        为知识点查找合适的配图

        CLIP 跨模态优先，回退到文本匹配
        """
        # 1. CLIP 跨模态检索
        clip_results = self.indexer.search_figures_by_text(
            query=f"{knowledge_point} diagram schematic",
            top_k=3,
            domain=domain,
        )
        if clip_results:
            best = clip_results[0]
            return self._format_clip_match(best, knowledge_point)

        # 2. 回退: BGE-M3 文本检索
        query = f"{knowledge_point} diagram schematic illustration"
        results = self.search(
            query=query,
            domain=domain,
            subfield=subfield,
            top_k=10,
            include_figures=True,
        )

        best_match = None
        best_score = 0.0
        for r in results["results"]:
            if r.get("figure"):
                score = r["similarity"]
                fig_caption = r["figure"].get("figure_caption", "").lower()
                kp_lower = knowledge_point.lower()
                if any(kw in fig_caption for kw in kp_lower.split()):
                    score += 0.2
                if score > best_score:
                    best_score = score
                    best_match = r

        if best_match:
            return self._format_best_figure_match(best_match, knowledge_point)

        return None

    def _format_result(self, result: SearchResult, include_figures: bool) -> Dict[str, Any]:
        """格式化搜索结果"""
        formatted = {
            "paper": self._format_paper(result.paper),
            "chunk": {
                "text": result.chunk.text if result.chunk else "",
                "text_type": result.chunk.text_type if result.chunk else "",
                "page_num": result.chunk.page_num if result.chunk else 0,
                "heading": result.chunk.heading if result.chunk else "",
            },
            "similarity": result.similarity,
            "highlight": result.highlight,
            "context_before": result.context_before,
            "context_after": result.context_after,
        }

        if include_figures and result.figure:
            formatted["figure"] = self._format_figure(result.figure)

        return formatted

    def _format_paper(self, paper: Paper) -> Dict[str, Any]:
        """格式化论文信息"""
        return {
            "paper_id": paper.paper_id,
            "title": paper.title,
            "authors": ", ".join(paper.authors[:3]) + (", et al." if len(paper.authors) > 3 else ""),
            "year": paper.year,
            "journal": paper.journal,
            "domain": paper.domain,
            "subfield": paper.subfield,
        }

    def _format_figure(self, figure: Figure) -> Dict[str, Any]:
        """格式化图表信息"""
        return {
            "figure_id": figure.figure_id,
            "paper_id": figure.paper_id,
            "figure_label": figure.figure_label,
            "figure_caption": figure.figure_caption,
            "page_num": figure.page_num,
            "image_path": figure.image_path,
            "width": figure.width,
            "height": figure.height,
            "description": figure.description,
            "figure_type": figure.figure_type,
            "key_findings": figure.key_findings,
        }

    def _format_best_figure_match(
        self,
        result: Dict[str, Any],
        knowledge_point: str,
    ) -> Dict[str, Any]:
        """
        格式化最佳图表匹配

        返回适合直接在Obsidian笔记中使用的格式
        """
        paper = result["paper"]
        figure = result["figure"]
        chunk = result["chunk"]

        return {
            "image_path": figure["image_path"],
            "obsidian_ref": f"![[{figure['image_path'].split('/')[-1]}]]",
            "source": {
                "paper_title": paper["title"],
                "authors": paper["authors"],
                "year": paper["year"],
                "figure_label": figure["figure_label"],
                "figure_caption": figure["figure_caption"],
            },
            "usage_guide": {
                "description": figure.get("description", ""),
                "key_findings": figure.get("key_findings", []),
                "how_to_use": self._generate_usage_guide(figure, knowledge_point),
            },
            "context": {
                "text_quote": chunk["text"][:500] + "..." if len(chunk["text"]) > 500 else chunk["text"],
                "section": chunk["heading"],
                "page": chunk["page_num"],
            },
        }

    def _format_clip_match(
        self,
        match: Dict[str, Any],
        knowledge_point: str,
    ) -> Dict[str, Any]:
        """格式化 CLIP 跨模态匹配结果"""
        image_path = match.get("image_path", "")
        img_filename = Path(image_path).name if image_path else ""
        return {
            "image_path": image_path,
            "obsidian_ref": f"![[{img_filename}]]",
            "source": {
                "paper_title": match.get("paper_title", ""),
                "paper_year": match.get("paper_year", 0),
                "figure_label": match.get("label", ""),
                "figure_caption": match.get("caption", ""),
            },
            "usage_guide": {
                "description": match.get("caption", ""),
                "key_findings": [],
                "how_to_use": f"CLIP 跨模态检索匹配 {knowledge_point}\n图表标题：{match.get('caption', '')}",
            },
            "similarity": match.get("similarity", 0),
            "method": "CLIP-crossmodal",
        }

    def _generate_usage_guide(self, figure: Dict[str, Any], knowledge_point: str) -> str:
        """生成图表使用指南"""
        fig_type = figure.get("figure_type", "unknown")
        caption = figure.get("figure_caption", "")

        guides = {
            "diagram": f"此图为原理示意图，适合解释 {knowledge_point} 的工作原理。\n图表标题：{caption}",
            "photo": f"此图为实验照片/显微照片，展示了实际的 {knowledge_point}。\n图表标题：{caption}",
            "plot": f"此图为数据曲线图，展示了 {knowledge_point} 的性能特性。\n图表标题：{caption}",
            "setup": f"此图为实验装置图，展示了测量 {knowledge_point} 的系统结构。\n图表标题：{caption}",
            "spectrum": f"此图为光谱图，展示了 {knowledge_point} 的频谱特性。\n图表标题：{caption}",
            "graph": f"此图为图表，适合展示 {knowledge_point} 的对比数据。\n图表标题：{caption}",
        }

        return guides.get(fig_type, f"此图可用于说明 {knowledge_point}。\n图表标题：{caption}")
