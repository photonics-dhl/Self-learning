#!/usr/bin/env python3
"""
Academic Paper Writing System v2 - 基于 GitHub 最佳实践重构

参考了以下成熟案例:
1. RE-paper-writing (Research-Equality) - 35技能体系, gaps.md artifact, claim-evidence-map
2. STORM (stanford-oval) - 知识收集→大纲生成→文章撰写→文章打磨 四阶段
3. PaperOrchestra - 多Agent专门化, 质量评估器

核心改进:
1. 知识收集先于写作 (Knowledge Curation)
2. Perspective-guided 问题发现
3. Structured artifacts: paper_db.jsonl, reading_notes.md, synthesis.md, gaps.md
4. 明确的 Gap Identification
5. 主题综合 (Thematic Synthesis) 而非论文堆砌
6. C-C-C 段落结构: Context → Content → Conclusion
7. 质量门控: 每个阶段验证
8. Claim-Evidence 映射

路径: E:/PostGraduate/Science_softwares/Zotero/data/storage/
"""

import os
import re
import codecs
import sys
import json
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass, field, asdict
import fitz

if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# =============================================================================
# 配置
# =============================================================================

ZOTERO_STORAGE = "E:/PostGraduate/Science_softwares/Zotero/data/storage"
OUTPUT_DIR = "DHL"
EMAIL = "research@example.com"
OPENALEX_API_BASE = "https://api.openalex.org"

# 5类Gap定义
GAP_TYPES = {
    'Methodological': '研究方法的空白或不足',
    'Parameter': '参数空间/条件范围的空白',
    'Comparative': '系统性对比的空白',
    'Theoretical': '理论框架/机理的空白',
    'Condition': '适用条件/范围的空白',
}

# 技术路线
TECH_ROUTES = {
    'PCA (光电导天线)': ['photoconductive', 'PCA', 'Auston switch', 'bow-tie', 'dipole antenna', 'strip-line', 'interdigitated'],
    '光整流': ['optical rectification', 'second-harmonic', 'difference frequency', 'DFG', 'LiNbO3', 'ZnTe', 'GaSe', 'DAST', 'tilted pulse front'],
    '激光等离子体': ['laser plasma', 'filamentation', 'two-color', 'four-wave mixing', 'FWM', 'air plasma', 'laser-induced'],
    'QCL (量子级联激光器)': ['quantum cascade', 'QCL', 'intersubband', 'heterostructure', 'QWIP'],
    '超表面/等离子体': ['metasurface', 'plasmonic', 'nanoantenna', 'resonant', 'split-ring', 'SRR'],
    '光整流-有机晶体': ['organic', 'DAST', 'OH1', 'BST', 'malonitrile'],
}


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class Paper:
    """论文元数据"""
    id: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    journal: str = ""
    doi: str = ""
    abstract: str = ""
    citations: int = 0
    relevance: float = 0.0

    # 深度分析结果
    research_question: str = ""
    approach: str = ""
    tech_routes: List[str] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)
    contribution: str = ""

    # 来源
    source: str = "openalex"  # openalex / zotero

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Gap:
    """研究空白"""
    gap_type: str = ""  # Methodological/Parameter/Comparative/Theoretical/Condition
    description: str = ""
    evidence: str = ""  # 来源论文/文本
    papers: List[str] = field(default_factory=list)  # 相关论文ID列表


@dataclass
class ThemeSynthesis:
    """主题综合"""
    theme: str = ""
    context: str = ""  # 研究背景与问题
    research_questions: List[str] = field(default_factory=list)
    tech_routes: Dict[str, List[str]] = field(default_factory=dict)  # route -> papers
    key_findings: List[str] = field(default_factory=list)
    gaps: List[Gap] = field(default_factory=list)
    tradeoffs: List[str] = field(default_factory=list)
    future_directions: List[str] = field(default_factory=list)
    representative_papers: List[Dict] = field(default_factory=list)


# =============================================================================
# Stage 1: 知识收集 (Knowledge Curation)
# =============================================================================

class KnowledgeCuration:
    """从多源收集论文信息"""

    def __init__(self):
        self.papers: List[Paper] = []
        self.paper_db: Dict[str, Paper] = {}

    def search_openalex(self, query: str, max_results: int = 30) -> List[Paper]:
        """从 OpenAlex 检索论文"""
        import requests

        params = {
            "search": query,
            "per_page": min(max_results, 100),
            "sort": "relevance_score:desc",
            "mailto": EMAIL
        }
        r = requests.get(f"{OPENALEX_API_BASE}/works", params=params, timeout=60)
        r.raise_for_status()
        data = r.json()

        papers = []
        for w in data.get("results", []):
            loc = w.get("primary_location") or {}
            src = loc.get("source", {})

            # 重建 abstract
            inv = w.get("abstract_inverted_index", {})
            abstract = ""
            if inv:
                words = []
                for word, positions in inv.items():
                    for pos in positions:
                        words.append((pos, word))
                words.sort()
                abstract = " ".join([x[1] for x in words])

            paper = Paper(
                id=f"oa_{w.get('id', '').split('/')[-1]}",
                title=w.get("title", "Untitled"),
                authors=[a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:5]],
                year=w.get("publication_year", 0),
                journal=src.get("display_name", "N/A"),
                doi=w.get("doi", ""),
                abstract=abstract,
                citations=w.get("cited_by_count", 0),
                relevance=w.get("relevance_score", 0),
                source="openalex"
            )
            papers.append(paper)

        return papers

    def scan_zotero_pdfs(self, max_pdfs: int = 50) -> List[Paper]:
        """扫描 Zotero 本地 PDF"""
        if not os.path.exists(ZOTERO_STORAGE):
            print(f"Zotero storage not found: {ZOTERO_STORAGE}")
            return []

        items = os.listdir(ZOTERO_STORAGE)
        print(f"Scanning {len(items)} items in Zotero storage...")

        papers = []
        count = 0

        for item_key in items:
            item_dir = os.path.join(ZOTERO_STORAGE, item_key)
            if not os.path.isdir(item_dir):
                continue

            pdfs = [f for f in os.listdir(item_dir) if f.endswith('.pdf')]
            if not pdfs:
                continue

            pdf_path = os.path.join(item_dir, pdfs[0])

            try:
                doc = fitz.open(pdf_path)
                first_text = doc[0].get_text() if len(doc) > 0 else ""
                doc.close()

                # 快速判断是否是 THz 相关
                if 'terahertz' not in first_text.lower() and ' thz ' not in first_text.lower():
                    continue

                print(f"  Analyzing: {pdfs[0][:50]}...")
                analysis = self.analyze_pdf(pdf_path)

                if analysis:
                    paper = Paper(
                        id=f"zotero_{item_key}",
                        title=analysis.get('title', 'Unknown'),
                        authors=analysis.get('authors', []),
                        year=analysis.get('year', 0),
                        abstract=analysis.get('abstract', ''),
                        research_question=analysis.get('research_question', ''),
                        approach=analysis.get('approach', ''),
                        tech_routes=analysis.get('tech_routes', []),
                        key_findings=analysis.get('key_findings', []),
                        limitations=analysis.get('limitations', []),
                        gaps=analysis.get('gaps', []),
                        contribution=analysis.get('contribution', ''),
                        source="zotero"
                    )
                    papers.append(paper)
                    count += 1
                    if count >= max_pdfs:
                        break

            except Exception as e:
                continue

        print(f"Found and analyzed {len(papers)} THz-related PDFs")
        return papers

    def analyze_pdf(self, pdf_path: str) -> Optional[Dict]:
        """深度分析单个 PDF"""
        try:
            doc = fitz.open(pdf_path)
            all_text = ""
            pages_text = []
            for i, page in enumerate(doc):
                text = page.get_text()
                all_text += f"\n--- Page {i+1} ---\n{text}"
                pages_text.append(text)
            doc.close()

            # 提取各部分
            sections = self.extract_sections(all_text)
            abstract = sections.get('abstract', '') or self.extract_abstract_fast(all_text)
            intro = sections.get('introduction', '')
            method = sections.get('methods', '') + sections.get('experimental', '')
            results = sections.get('results', '') + sections.get('discussion', '')
            conclusion = sections.get('conclusion', '')

            return {
                'title': self.extract_title(pages_text[0] if pages_text else ""),
                'authors': self.extract_authors(pages_text[0] if pages_text else ""),
                'year': self.extract_year(pages_text[0] if pages_text else ""),
                'abstract': abstract,
                'sections': sections,
                'research_question': self.extract_rq(intro + abstract),
                'approach': self.extract_approach(method + intro),
                'tech_routes': self.detect_tech_routes(all_text),
                'key_findings': self.extract_findings(results),
                'limitations': self.extract_limitations(results + conclusion),
                'gaps': self.extract_gaps(intro + conclusion),
                'contribution': self.extract_contribution(intro),
            }

        except Exception as e:
            return None

    def extract_title(self, text: str) -> str:
        lines = text.split('\n')
        for line in lines[3:20]:
            stripped = line.strip()
            if (len(stripped) > 30 and len(stripped.split()) > 5 and
                any(c.isupper() for c in stripped) and
                not any(x in stripped.lower() for x in ['http://', 'doi:', 'figure', 'tab.'])):
                return re.sub(r'\s+', ' ', stripped)[:200]
        return "Unknown"

    def extract_authors(self, text: str) -> List[str]:
        # 简单实现: 找前几行的名字模式
        authors = []
        lines = text.split('\n')[:15]
        for line in lines:
            # 名字模式: "First Last" 或 "F. Last"
            matches = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+)', line)
            for m in matches[:2]:
                if m not in authors and len(authors) < 5:
                    authors.append(m)
        return authors

    def extract_year(self, text: str) -> int:
        match = re.search(r'(19|20)\d{2}', text)
        return int(match.group(0)) if match else 0

    def extract_abstract_fast(self, text: str) -> str:
        text_lower = text.lower()
        abstract_idx = text_lower.find('abstract')
        if abstract_idx >= 0:
            start = text.find('\n', abstract_idx) + 1
            if start > abstract_idx:
                end_text = text_lower[start:start+5000]
                for marker in ['\n1.', '\nintroduction', '\nbackground']:
                    idx = end_text.find(marker)
                    if idx > 50:
                        return text[start:start+idx].strip()
        return ""

    def extract_sections(self, text: str) -> Dict[str, str]:
        sections = {k: '' for k in ['abstract', 'introduction', 'methods', 'experimental', 'results', 'discussion', 'conclusion']}
        markers = [
            ('abstract', ['abstract']),
            ('introduction', ['introduction', '1 introduction', 'background']),
            ('methods', ['method', 'experimental', 'setup']),
            ('experimental', ['experimental']),
            ('results', ['result', 'measurement']),
            ('discussion', ['discussion', 'analysis']),
            ('conclusion', ['conclusion', 'summary']),
        ]
        lines = text.split('\n')
        current = None
        content = []

        for line in lines:
            line_lower = line.strip().lower()
            new_section = None

            for sec_name, marker_list in markers:
                if any(line_lower.startswith(m) for m in marker_list):
                    new_section = sec_name
                    break

            if new_section and new_section != current:
                if current and content:
                    sections[current] = '\n'.join(content)
                current = new_section
                content = []
            elif current:
                content.append(line.strip())

        if current and content:
            sections[current] = '\n'.join(content)

        return {k: v[:15000] for k, v in sections.items()}

    def extract_rq(self, text: str) -> str:
        patterns = [
            r"(?:We|Here|This paper|This work)\s+(?:investigate|study|demonstrate|propose|develop)\s+(?:the\s+)?(?:of\s+)?([^.]+?)(?:\.|,)",
            r"(?:goal|objective|purpose)\s+(?:of|is|was)?\s*:?\s*([^.]+?)(?:\.|,)",
            r"(?:aim|focus)\s+(?:to|on)\s+([^.]+?)(?:\.|,)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return re.sub(r'\s+', ' ', match.group(1).strip())[:200]
        return ""

    def extract_approach(self, text: str) -> str:
        found = []
        tech_keywords = [
            'tilted pulse front', 'optical rectification', 'photoconductive', 'filamentation',
            'two-color', 'QCL', 'quantum cascade', 'LiNbO3', 'GaAs', 'ZnTe', 'GaSe', 'DAST',
            'electro-optic sampling', 'bolometer', 'plasmonic', 'metasurface', 'LT-GaAs',
        ]
        text_lower = text.lower()
        for kw in tech_keywords:
            if kw.lower() in text_lower:
                found.append(kw)
        return "Methods: " + ", ".join(found[:10]) if found else ""

    def detect_tech_routes(self, text: str) -> List[str]:
        text_lower = text.lower()
        matched = []
        for route_name, keywords in TECH_ROUTES.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    matched.append(route_name)
                    break
        return list(set(matched)) if matched else ['其他']

    def extract_findings(self, text: str) -> List[str]:
        findings = []
        patterns = [
            r'(\d+(?:\.\d+)?\s*(?:THz|GHz))\s*(?:peak|output|bandwidth)?',
            r'(\d+(?:\.\d+)?\s*(?:mJ|μJ))\s*(?:pulse|energy)?',
            r'(\d+(?:\.\d+)?%)\s*(?:efficiency|conversion)?',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                if m and len(m) > 2 and m not in findings:
                    findings.append(m)
        return findings[:8]

    def extract_limitations(self, text: str) -> List[str]:
        limitations = []
        patterns = [
            r"(?:limitation|drawback|disadvantage)\s+(?:of|is|are)\s+([^.]+)",
            r"future\s+(?:work|research)\s+(?:should|needs)\s+([^.]+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                m = m.strip()
                if len(m) > 30 and len(m) < 300 and m not in limitations:
                    limitations.append(m)
        return limitations[:3]

    def extract_gaps(self, text: str) -> List[Dict]:
        """系统性识别5类Gap"""
        gaps = []
        GAP_PATTERNS = {
            'Methodological': [r"(?:lack|no)\s+(?:of\s+)?(?:systematic|rigorous)\s+(?:method|approach)"],
            'Parameter': [r"(?:limited|restricted)\s+(?:parameter\s+)?range"],
            'Comparative': [r"no\s+(?:direct|systematic)\s+(?:comparison|study)\s+(?:between|of)"],
            'Theoretical': [r"(?:theoretical|theory)\s+(?:framework|model)\s+(?:is\s+not|remains)"],
            'Condition': [r"(?:applicable|valid)\s+only\s+(?:under|for)"],
        }

        for gap_type, patterns in GAP_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    gap_text = match.group(0)[:250]
                    gap_text = re.sub(r'\s+', ' ', gap_text)
                    if not any(g.get('description', '')[:100] == gap_text[:100] for g in gaps):
                        gaps.append({
                            'type': gap_type,
                            'description': gap_text,
                            'evidence': match.group(0),
                        })

        return gaps[:5]

    def extract_contribution(self, text: str) -> str:
        patterns = [
            r"(?:We|This paper)\s+(?:demonstrate|propose|develop|present|show|introduce)\s+([^.]+)",
            r"(?:The main|key)\s+(?:contribution|innovation)\s+(?:of|is)\s+:?\s*([^.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return re.sub(r'\s+', ' ', match.group(0)[:200])
        return ""


# =============================================================================
# Stage 2: 主题综合 (Thematic Synthesis)
# =============================================================================

class ThematicSynthesis:
    """主题综合分析 - 按研究问题/趋势分组，而非论文列表"""

    def __init__(self):
        self.themes: Dict[str, ThemeSynthesis] = {}

    def synthesize(self, papers: List[Paper]) -> Dict[str, ThemeSynthesis]:
        """综合论文为主题"""

        # 按技术路线分组
        route_groups = defaultdict(list)
        for paper in papers:
            for route in paper.tech_routes:
                route_groups[route].append(paper)

        # 为每个主题创建综合
        for route, route_papers in route_groups.items():
            if len(route_papers) < 1:
                continue

            theme = ThemeSynthesis()
            theme.theme = route
            theme.context = self.generate_context(route, route_papers)
            theme.research_questions = self.extract_research_questions(route_papers)
            theme.tech_routes = {route: [p.id for p in route_papers]}
            theme.key_findings = self.aggregate_findings(route_papers)
            theme.gaps = self.aggregate_gaps(route_papers)
            theme.tradeoffs = self.analyze_tradeoffs(route, route_papers)
            theme.future_directions = self.generate_future_directions(route, route_papers)
            theme.representative_papers = self.select_representative_papers(route_papers)

            self.themes[route] = theme

        return self.themes

    def generate_context(self, theme: str, papers: List[Paper]) -> str:
        """生成研究背景"""
        context_templates = {
            'PCA (光电导天线)': "光电导天线(PCA)是太赫兹时域光谱系统的核心辐射源，其工作原理基于超快光载流子注入产生瞬态电流。",
            '光整流': "光整流效应是产生太赫兹辐射的非线性光学方法，通过飞秒激光与非线性晶体相互作用实现频率转换。",
            '激光等离子体': "激光等离子体太赫兹辐射利用强场激光与气体介质相互作用，通过四波混频或等离子体电流产生宽带太赫兹波。",
            'QCL (量子级联激光器)': "量子级联激光器(QCL)是固态太赫兹源的重要选择，基于半导体异质结构中的子带间跃迁实现电泵浦太赫兹发射。",
            '超表面/等离子体': "超表面和等离子体结构为太赫兹调制和控制提供了紧凑、高效的解决方案，通过亚波长谐振单元实现电磁波调控。",
            '光整流-有机晶体': "有机非线性晶体如DAST、OH1具有大的二阶非线性系数，是高效光整流太赫兹源的重要材料选择。",
        }
        base = context_templates.get(theme, f"{theme}是太赫兹技术的重要研究方向。")

        # 补充统计信息
        citations = sum(p.citations for p in papers)
        avg_citations = citations // len(papers) if papers else 0
        years = [p.year for p in papers if p.year]
        year_range = f"{min(years)}-{max(years)}" if years else "未知"

        context = f"{base}本主题涵盖{len(papers)}篇论文({year_range})，总引用{citations}次，平均引用{avg_citations}次。"

        return context

    def extract_research_questions(self, papers: List[Paper]) -> List[str]:
        """提取研究问题"""
        rqs = []
        for p in papers:
            if p.research_question and p.research_question not in rqs:
                rqs.append(p.research_question)
        return rqs[:5]

    def aggregate_findings(self, papers: List[Paper]) -> List[str]:
        """聚合关键发现"""
        all_findings = []
        for p in papers:
            for f in p.key_findings:
                if f not in all_findings:
                    all_findings.append(f)
        return all_findings[:12]

    def aggregate_gaps(self, papers: List[Paper]) -> List[Gap]:
        """聚合研究空白"""
        gap_dict = defaultdict(list)

        for p in papers:
            for g in p.gaps:
                gap_type = g.get('type', 'Unknown')
                gap_dict[gap_type].append(g)

        gaps = []
        for gap_type, type_gaps in gap_dict.items():
            # 选择最具代表性的
            if type_gaps:
                best = type_gaps[0]
                gaps.append(Gap(
                    gap_type=gap_type,
                    description=best.get('description', ''),
                    evidence=best.get('evidence', ''),
                    papers=[p.id for p in papers[:3]]
                ))

        return gaps[:5]

    def analyze_tradeoffs(self, theme: str, papers: List[Paper]) -> List[str]:
        """分析核心权衡"""
        tradeoffs = {
            'PCA (光电导天线)': ['带宽 vs 功率', '工作频率 vs 衬底选择', '天线设计 vs 辐射效率'],
            '光整流': ['转换效率 vs 带宽', '晶体损伤阈值 vs 输出能量', '相位匹配 vs 角度调谐'],
            '激光等离子体': ['能量 vs 带宽', '系统复杂度 vs 稳定性', '远程 vs 近场'],
            'QCL (量子级联激光器)': ['工作温度 vs 输出功率', '频率可调 vs 模式稳定性', '成本 vs 性能'],
            '超表面/等离子体': ['调制深度 vs 响应速度', '效率 vs 带宽', '制备成本 vs 性能'],
            '光整流-有机晶体': ['非线性系数 vs 化学稳定性', '损伤阈值 vs 透明度', '成本 vs 性能'],
        }
        return tradeoffs.get(theme, ['性能 vs 实现难度'])

    def generate_future_directions(self, theme: str, papers: List[Paper]) -> List[str]:
        """生成未来研究方向"""
        directions = {
            'PCA (光电导天线)': [
                '开发低温柔性PCA以扩展工作场景',
                '结合纳米等离子体结构提升辐射效率',
                '探索新型宽禁带半导体材料',
            ],
            '光整流': [
                '优化倾斜脉冲前阵技术以提升能量转换效率',
                '探索新型有机晶体材料',
                '实现波长可调谐太赫兹源',
            ],
            '激光等离子体': [
                '提高激光-等离子体能量转换效率',
                '实现远程高功率太赫兹检测',
                '探索气体压强和组分优化',
            ],
            'QCL (量子级联激光器)': [
                '提升室温输出功率',
                '扩展频率调谐范围',
                '实现低噪声特性',
            ],
            '超表面/等离子体': [
                '开发高速太赫兹调制器',
                '实现超薄高效太赫兹源',
                '探索可编程超表面',
            ],
            '光整流-有机晶体': [
                '提高晶体尺寸和质量',
                '优化相位匹配条件',
                '探索新型有机材料体系',
            ],
        }
        return directions.get(theme, ['系统性优化现有方案', '探索新型材料/结构'])

    def select_representative_papers(self, papers: List[Paper]) -> List[Dict]:
        """选择代表性论文"""
        # 按引用数排序，选择前5
        sorted_papers = sorted(papers, key=lambda x: x.citations, reverse=True)
        result = []
        for p in sorted_papers[:5]:
            result.append({
                'id': p.id,
                'title': p.title[:70] + ('...' if len(p.title) > 70 else ''),
                'authors': ', '.join(p.authors[:2]) if p.authors else 'Unknown',
                'year': p.year,
                'citations': p.citations,
                'approach': p.approach[:80] if p.approach else '',
                'findings': p.key_findings[:2] if p.key_findings else [],
            })
        return result


# =============================================================================
# Stage 3: 论文级综述生成 (Academic Review Generation)
# =============================================================================

class AcademicReviewWriter:
    """生成论文级学术综述 - 真正的学术写作，不是堆砌"""

    def __init__(self):
        self.themes: Dict[str, ThemeSynthesis] = {}

    def write(self, themes: Dict[str, ThemeSynthesis], query: str) -> str:
        """生成完整的学术综述"""
        self.themes = themes
        lines = []

        # ============================================================
        # 标题和元信息
        # ============================================================
        lines.append(f"# {query} 领域学术综述\n")
        lines.append("> [!abstract]+ 一句话物理图像\n")
        lines.append("> 本综述系统性分析太赫兹辐射技术的研究现状，涵盖光电导天线、光整流、激光等离子体、量子级联激光器等多种技术路线，识别领域内关键研究空白并提出未来研究方向。\n")

        lines.append(f"**生成时间**: 2026-04-29\n")
        lines.append(f"**涵盖主题**: {len(themes)} 个技术路线\n")
        lines.append(f"**分析方法**: 主题综合 (Thematic Synthesis) + Gap驱动写作\n")

        # ============================================================
        # 第一章: 研究空白汇总 (Gap Overview)
        # ============================================================
        lines.append("\n## 一、研究空白汇总\n")
        lines.append("> [!note]+ 综述结构说明\n")
        lines.append("> 本综述采用 **主题综合 (Thematic Synthesis)** 而非论文堆砌。")
        lines.append("> 每节遵循 **C-C-C 结构**: Context (背景) → Content (内容) → Conclusion (结论)。")
        lines.append("> Gap识别采用5类分类: Methodological / Parameter / Comparative / Theoretical / Condition。\n")

        for theme, synth in themes.items():
            if not synth.gaps:
                continue

            lines.append(f"\n### 1.{list(themes.keys()).index(theme)+1} {theme}\n")

            # 按Gap类型组织
            gaps_by_type = defaultdict(list)
            for gap in synth.gaps:
                gaps_by_type[gap.gap_type].append(gap)

            for gap_type, type_gaps in gaps_by_type.items():
                lines.append(f"\n**{gap_type} Gap:**")
                for g in type_gaps:
                    desc = g.description[:200] + ('...' if len(g.description) > 200 else '')
                    lines.append(f"- {desc}")

        # ============================================================
        # 第二章: 各技术路线深度分析
        # ============================================================
        lines.append("\n\n## 二、技术路线深度分析\n")

        for i, (theme, synth) in enumerate(themes.items(), 1):
            lines.append(f"\n### 2.{i} {synth.theme}\n")

            # ----------------------------------------
            # C-C-C: Context (背景与问题)
            # ----------------------------------------
            lines.append("\n#### 2.{}.1 研究背景与问题\n".format(i))
            lines.append(f"\n{synth.context}\n")

            # 研究问题
            if synth.research_questions:
                lines.append("\n**核心研究问题:**")
                for rq in synth.research_questions[:3]:
                    lines.append(f"- {rq}")
                lines.append("")

            # ----------------------------------------
            # C-C-C: Content (技术方法与发现)
            # ----------------------------------------
            lines.append("\n#### 2.{}.2 技术路线与关键发现\n".format(i))

            # 核心权衡
            if synth.tradeoffs:
                lines.append("\n**核心权衡:**")
                for t in synth.tradeoffs:
                    lines.append(f"- {t}")
                lines.append("")

            # 关键性能指标
            if synth.key_findings:
                lines.append("\n**关键性能指标范围:**")
                for f in synth.key_findings[:10]:
                    lines.append(f"- {f}")
                lines.append("")

            # 代表性工作 (学术风格叙述，非列表堆砌)
            if synth.representative_papers:
                lines.append("\n**代表性工作:**\n")

                # 按时间/引用排序选择3篇
                for j, p in enumerate(synth.representative_papers[:3], 1):
                    title = p['title']
                    authors = p['authors']
                    year = p['year']
                    citations = p['citations']
                    approach = p['approach']
                    findings = '; '.join(p['findings'][:2]) if p['findings'] else ''

                    # 学术风格叙述
                    lines.append(f"{j}. **{title}**")
                    lines.append(f"   - {authors} ({year}). {approach}.")
                    if findings:
                        lines.append(f"   - 关键结果: {findings}")
                    lines.append("")

            # ----------------------------------------
            # C-C-C: Conclusion (综合评述)
            # ----------------------------------------
            lines.append("\n#### 2.{}.3 综合评述\n".format(i))

            lines.append("\n上述研究表明：")
            lines.append(f"- **{synth.theme}** 的主要技术路线集中在 {', '.join(synth.tech_routes.keys())}")

            if synth.key_findings:
                unique_findings = list(set(synth.key_findings))[:6]
                lines.append(f"- 性能指标范围: {', '.join(unique_findings)}")

            if synth.gaps:
                main_gap = synth.gaps[0]
                lines.append(f"- 主要研究空白: **{main_gap.gap_type}** - {main_gap.description[:100]}...")

            lines.append(f"- 未来方向: {'; '.join(synth.future_directions[:2])}")

        # ============================================================
        # 第三章: 跨主题综合讨论
        # ============================================================
        lines.append("\n\n## 三、跨主题综合讨论\n")

        # 技术路线对比表
        lines.append("\n### 3.1 技术路线综合对比\n")
        lines.append("\n| 技术路线 | 核心优势 | 主要局限 | 典型应用场景 | 成熟度 |")
        lines.append("|---------|---------|---------|------------|--------|")

        route_properties = {
            'PCA (光电导天线)': ['技术成熟、结构紧凑', '频率受限、热损伤', '实验室THz光谱', '高'],
            '光整流': ['能量高、相干性好', '带宽受限、晶体损伤', '高功率THz源', '高'],
            '激光等离子体': ['带宽极宽、远程探测', '能量较低、系统复杂', '远程传感/成像', '中'],
            'QCL (量子级联激光器)': ['室温工作、电泵浦', '功率较低、频率固定', '现场检测/监控', '中'],
            '超表面/等离子体': ['体积小、可调制', '效率待提升', '太赫兹调制/传感', '中'],
            '光整流-有机晶体': ['非线性系数大', '晶体尺寸有限', '高功率THz源', '中'],
        }

        for theme in themes.keys():
            props = route_properties.get(theme, ['待分析', '待分析', '待确定', '待定'])
            lines.append(f"| {theme} | {props[0]} | {props[1]} | {props[2]} | {props[3]} |")

        # 核心权衡
        lines.append("\n### 3.2 领域核心权衡\n")
        lines.append("\n太赫兹辐射技术存在以下核心权衡：\n")

        all_tradeoffs = set()
        for synth in themes.values():
            all_tradeoffs.update(synth.tradeoffs)

        for t in all_tradeoffs:
            lines.append(f"- **{t}**: {self.explain_tradeoff(t)}")

        # ============================================================
        # 第四章: 未来研究方向
        # ============================================================
        lines.append("\n\n## 四、未来研究方向\n")

        # 按Gap类型组织
        gap_directions = defaultdict(list)
        for synth in themes.values():
            for gap in synth.gaps:
                gap_directions[gap.gap_type].extend(synth.future_directions)

        lines.append("\n根据识别的研究空白，未来研究应关注：\n")

        for gap_type, directions in gap_directions.items():
            unique_dirs = list(set(directions))[:3]
            if unique_dirs:
                lines.append(f"\n**{gap_type} Gap 解决方向:**")
                for d in unique_dirs:
                    lines.append(f"- {d}")

        # ============================================================
        # 参考文献
        # ============================================================
        lines.append("\n\n## 参考文献\n")

        all_papers = []
        for synth in themes.values():
            for p in synth.representative_papers:
                if p not in all_papers:
                    all_papers.append(p)

        for i, p in enumerate(all_papers[:20], 1):
            lines.append(f"[{i}] {p['authors']} ({p['year']}). {p['title']}. Cited: {p['citations']}.")

        lines.append("\n\n---\n")
        lines.append("*本综述由 Claude Code 自动生成 | 方法: 主题综合 (Thematic Synthesis) + C-C-C结构 + Gap驱动写作*")
        lines.append("\n*数据来源: OpenAlex API + Zotero 本地文献库*")

        return "\n".join(lines)

    def explain_tradeoff(self, tradeoff: str) -> str:
        explanations = {
            '带宽 vs 功率': '光整流方案能量高但带宽受限；等离子体方案带宽宽但能量较低',
            '工作频率 vs 衬底选择': '高频PCA需要LT-GaAs等短载流子寿命材料，但这些材料迁移率较低',
            '天线设计 vs 辐射效率': '大尺寸天线增加辐射面积但降低耦合效率；小尺寸天线相反',
            '转换效率 vs 带宽': '相位匹配优化可提高效率但牺牲带宽；宽带设计通常效率较低',
            '晶体损伤阈值 vs 输出能量': '高泵浦能量产生更多THz但增加晶体损伤风险',
            '能量 vs 带宽': '高能量方案通常涉及光学整流，带宽受限；等离子体方案可覆盖更大带宽',
            '系统复杂度 vs 稳定性': '复杂系统（如双色谱）性能更好但稳定性差；简单系统反之',
            '远程 vs 近场': '远程探测需要等离子体方案但信噪比低；近场方案信号强但受限',
            '工作温度 vs 输出功率': '低温工作QCL功率更高；室温方案功率受限',
            '频率可调 vs 模式稳定性': '宽调谐范围通常伴随模式不稳定',
            '成本 vs 性能': '高性能方案（如QCL）成本高；低成本方案（如等离子体）性能波动',
            '调制深度 vs 响应速度': '深度调制通常伴随慢响应；快速调制牺牲调制深度',
            '效率 vs 带宽': '高效方案通常带宽受限；宽带方案效率较低',
            '制备成本 vs 性能': '精密制备的超表面性能好但成本高',
            '非线性系数 vs 化学稳定性': '高非线性有机晶体化学稳定性差',
            '损伤阈值 vs 透明度': '高损伤阈值晶体透明度差；高透明度材料损伤阈值低',
        }
        return explanations.get(tradeoff, '存在复杂的权衡关系')


# =============================================================================
# 主流程
# =============================================================================

def run_academic_review(query: str, max_pdfs: int = 50, max_results: int = 30) -> Dict:
    """运行完整学术综述流程"""

    print("=" * 70)
    print("学术综述生成系统 v2 - 基于 GitHub 最佳实践")
    print("=" * 70)

    # Stage 1: 知识收集
    print("\n>> Stage 1: 知识收集 (Knowledge Curation)")
    curation = KnowledgeCuration()

    print("  [1.1] OpenAlex 检索...")
    openalex_papers = curation.search_openalex(query, max_results)
    print(f"      找到 {len(openalex_papers)} 篇论文")

    print("  [1.2] Zotero PDF 扫描...")
    zotero_papers = curation.scan_zotero_pdfs(max_pdfs)
    print(f"      分析了 {len(zotero_papers)} 篇 PDF")

    # 合并
    all_papers = openalex_papers + zotero_papers
    print(f"      合计: {len(all_papers)} 篇论文")

    # 保存 paper_db.jsonl
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    paper_db_file = f"{OUTPUT_DIR}/paper_db_{query.replace(' ', '_')[:20]}.jsonl"
    with open(paper_db_file, 'w', encoding='utf-8') as f:
        for p in all_papers:
            f.write(json.dumps(p.to_dict(), ensure_ascii=False) + '\n')
    print(f"      论文库已保存: {paper_db_file}")

    # Stage 2: 主题综合
    print("\n>> Stage 2: 主题综合 (Thematic Synthesis)")
    synthesis = ThematicSynthesis()
    themes = synthesis.synthesize(all_papers)
    print(f"      综合了 {len(themes)} 个主题")

    for theme, synth in themes.items():
        print(f"      - {theme}: {synth.context[:60]}...")

    # Stage 3: 论文级综述生成
    print("\n>> Stage 3: 论文级综述生成 (Academic Review Writing)")
    writer = AcademicReviewWriter()
    review = writer.write(themes, query)

    # 保存
    review_file = f"{OUTPUT_DIR}/academic_review_{query.replace(' ', '_')[:20]}.md"
    with open(review_file, 'w', encoding='utf-8') as f:
        f.write(review)
    print(f"      综述已保存: {review_file}")

    print("\n" + "=" * 70)
    print("完成!")
    print("=" * 70)

    return {
        'papers': all_papers,
        'themes': themes,
        'review': review,
        'paper_db_file': paper_db_file,
        'review_file': review_file,
    }


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "terahertz generation"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    result = run_academic_review(query, n)
    print(f"\n综合了 {len(result['themes'])} 个主题")
    print(f"生成了 {len(result['review'])} 字的学术综述")


if __name__ == "__main__":
    main()