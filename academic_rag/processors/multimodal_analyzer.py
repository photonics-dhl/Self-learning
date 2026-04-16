"""
学术论文 RAG 系统 - 多模态图表分析器
使用 GPT-4o 多模态模型分析论文图表
"""

import base64
import json
import re
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from academic_rag.config import config
from academic_rag.db.models import Figure


# 默认分析结果输出目录
DEFAULT_ANALYSIS_OUTPUT = Path(__file__).parent.parent / "figure_analysis"


@dataclass
class FigureAnalysis:
    """图表分析结果"""
    figure_id: str
    description: str
    key_findings: List[str]
    related_concepts: List[str]
    suggested_knowledge_points: List[str]
    figure_type: str

    def to_dict(self) -> dict:
        return {
            "figure_id": self.figure_id,
            "description": self.description,
            "key_findings": self.key_findings,
            "related_concepts": self.related_concepts,
            "suggested_knowledge_points": self.suggested_knowledge_points,
            "figure_type": self.figure_type,
        }

    def save_to_file(self, output_dir: Path) -> Path:
        """保存分析结果到 JSON 文件"""
        output_dir.mkdir(parents=True, exist_ok=True)
        # 使用 figure_id 作为文件名
        safe_id = re.sub(r'[^\w\-_.]', '_', self.figure_id)
        file_path = output_dir / f"{safe_id}_analysis.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return file_path


def save_analyses_batch(analyses: List[FigureAnalysis], output_dir: Path) -> List[Path]:
    """批量保存分析结果"""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for analysis in analyses:
        path = analysis.save_to_file(output_dir)
        paths.append(path)
    return paths


class MultimodalAnalyzer:
    """
    多模态图表分析器

    支持多个多模态模型:
    - gpt-4o (DuckCoding, 需配置通道)
    - gpt-5 (ZChat, 推荐使用)
    """

    # 可用模型配置
    MODEL_CONFIGS = {
        "gpt-4o": {
            "api_key": "sk-p4O8ENsDylgdGfnSwwDAJAaQVNghknzz3uITiSiL4DaN1V2L",
            "base_url": "https://www.duckcoding.ai/v1",
        },
        "gpt-5": {
            "api_key": "sk-uK1cqmlDbsRaUyNS2lkcUGC6FRewPLUZ7GWbEvjrhDMzM6Rf",
            "base_url": "https://api.zchat.tech/v1",
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-5",  # 默认使用 gpt-5
        output_dir: Optional[Path] = None,
    ):
        if model in self.MODEL_CONFIGS:
            cfg = self.MODEL_CONFIGS[model]
            self.api_key = api_key or cfg["api_key"]
            self.base_url = base_url or cfg["base_url"]
        else:
            self.api_key = api_key or self.MODEL_CONFIGS["gpt-5"]["api_key"]
            self.base_url = base_url or self.MODEL_CONFIGS["gpt-5"]["base_url"]
        self.model = model
        self.vision_endpoint = f"{self.base_url}/chat/completions"
        # 分析结果输出目录
        self.output_dir = output_dir or DEFAULT_ANALYSIS_OUTPUT
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_figure(
        self,
        figure: Figure,
        context: str = "",
        save_result: bool = True,
    ) -> FigureAnalysis:
        """分析单个图表

        Args:
            figure: 图表对象
            context: 上下文信息（论文标题、作者等）
            save_result: 是否保存结果到文件

        Returns:
            FigureAnalysis: 分析结果
        """
        image_path = Path(figure.image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # 检测图片格式
        ext = image_path.suffix.lower()
        if ext == ".png":
            mime_type = "image/png"
        elif ext in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        else:
            mime_type = "image/png"

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        prompt = self._build_prompt(figure, context)
        response = self._call_vision_api(image_data, prompt, mime_type)
        analysis = self._parse_response(figure.figure_id, response)

        # 保存结果
        if save_result:
            saved_path = analysis.save_to_file(self.output_dir)
            print(f"  Saved: {saved_path.name}")

        return analysis

    def analyze_figures_batch(
        self,
        figures: List[Figure],
        context: str = "",
        save_results: bool = True,
    ) -> List[FigureAnalysis]:
        """批量分析图表

        Args:
            figures: 图表列表
            context: 上下文信息
            save_results: 是否保存结果

        Returns:
            List[FigureAnalysis]: 分析结果列表
        """
        results = []
        for figure in figures:
            try:
                analysis = self.analyze_figure(figure, context, save_result=save_results)
                results.append(analysis)
                print(f"Analyzed: {figure.figure_label}")
            except Exception as e:
                print(f"Error analyzing {figure.figure_id}: {e}")
                continue
        return results

    def _build_prompt(self, figure: Figure, context: str) -> str:
        caption = figure.figure_caption or "No caption"
        return f"""Analyze this scientific paper figure.

**Figure Label**: {figure.figure_label}
**Caption**: {caption}
**Context**: {context if context else "Academic paper figure"}

Respond ONLY with this exact JSON format, no other text:
{{"description": "what this figure shows", "key_findings": ["finding1", "finding2"], "related_concepts": ["concept1"], "suggested_knowledge_points": ["knowledge point this figure explains"], "figure_type": "diagram|photo|plot|graph|spectrum|setup"}}"""

    def _call_vision_api(self, image_data: str, prompt: str, mime_type: str = "image/png") -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
        }

        response = requests.post(self.vision_endpoint, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _parse_response(self, figure_id: str, response: str) -> FigureAnalysis:
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
            else:
                start, end = response.find("{"), response.rfind("}") + 1
                if start != -1 and end > start:
                    data = json.loads(response[start:end])
                else:
                    raise ValueError(f"Failed to parse: {response[:200]}")

        return FigureAnalysis(
            figure_id=figure_id,
            description=data.get("description", ""),
            key_findings=data.get("key_findings", []),
            related_concepts=data.get("related_concepts", []),
            suggested_knowledge_points=data.get("suggested_knowledge_points", []),
            figure_type=data.get("figure_type", "unknown"),
        )


class FigureEnhancer:
    """图表增强器"""

    def __init__(self, analyzer: MultimodalAnalyzer):
        self.analyzer = analyzer

    def enhance_figure(
        self,
        figure: Figure,
        paper_info: Dict[str, str] = None,
        save_result: bool = True,
    ) -> Figure:
        """增强单个图表"""
        context = ""
        if paper_info:
            context = f"Paper: {paper_info.get('title', '')}"
            if paper_info.get("section"):
                context += f"\nSection: {paper_info['section']}"

        try:
            analysis = self.analyzer.analyze_figure(figure, context, save_result=save_result)
            figure.description = analysis.description
            figure.key_findings = analysis.key_findings
            figure.related_concepts = analysis.related_concepts
            figure.figure_type = analysis.figure_type
            return figure
        except Exception as e:
            print(f"Error enhancing figure {figure.figure_id}: {e}")
            return figure

    def enhance_paper_figures(
        self,
        figures: List[Figure],
        paper_info: Dict[str, str] = None,
        save_results: bool = True,
    ) -> List[Figure]:
        """增强论文的所有图表"""
        context = ""
        if paper_info:
            context = f"Paper: {paper_info.get('title', '')}"
            authors = paper_info.get("authors", [])
            if authors:
                context += f" by {', '.join(authors[:2])}"
            if paper_info.get("year"):
                context += f" ({paper_info['year']})"

        enhanced = []
        for fig in figures:
            try:
                analysis = self.analyzer.analyze_figure(fig, context, save_result=save_results)
                fig.description = analysis.description
                fig.key_findings = analysis.key_findings
                fig.related_concepts = analysis.related_concepts
                fig.figure_type = analysis.figure_type
                enhanced.append(fig)
                print(f"Enhanced: {fig.figure_label}")
            except Exception as e:
                print(f"Failed: {fig.figure_label} - {e}")
                enhanced.append(fig)
        return enhanced
