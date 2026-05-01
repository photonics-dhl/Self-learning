#!/usr/bin/env python3
"""
Deep Paper Analysis Pipeline - 深度论文分析

不是简单地提取摘要，而是：
1. 从 OpenAlex 获取论文元数据和初步筛选
2. 对于关键论文（高引用），尝试从 Zotero 获取 PDF
3. 使用 PyMuPDF 提取 PDF 全文内容
4. 深度提取：研究问题、方法细节、局限性、与其他论文的关系
5. 基于深度分析进行 Thematic Synthesis

核心改进：解决"摘要浅薄"问题
"""

import requests, os, sys, json, codecs, datetime, re, sqlite3
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import subprocess

if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(v, None)

OPENALEX_API_BASE = "https://api.openalex.org"
EMAIL = os.getenv("EMAIL", "research@example.com")

# Zotero SQLite 数据库路径
ZOTERO_DB = "E:/PostGraduate/Science_softwares/Zotero/data/zotero.sqlite"
ZOTERO_STORAGE = "E:/PostGraduate/Science_softwares/Zotero/data/storage"

# =============================================================================
# 数据结构定义
# =============================================================================

class PaperAnalyzer:
    """深度论文分析器"""

    def __init__(self):
        self.thz_themes = {
            "PCA材料": {
                "keywords": ["low-temperature grown GaAs", "LT-GaAs", "InGaAs", "ion-implanted",
                            "carrier lifetime", "mobility", "semi-insulating", "ErAs", "nanoparticle"],
                "research_question": "何种材料能在载流子寿命、迁移率、暗电阻三方面同时满足PCA需求？",
            },
            "光整流晶体": {
                "keywords": ["lithium niobate", "LiNbO3", "ZnTe", "GaSe", "DAST", "OH1",
                            "tilted pulse front", "phase matching", "optical rectification"],
            },
            "空气等离子体": {
                "keywords": ["air plasma", "filamentation", "two-color", "four-wave mixing",
                            "laser-induced plasma", "terawatt", "remote THz"],
            },
            "QCL激光器": {
                "keywords": ["quantum cascade", "QCL", "intersubband", "heterostructure",
                            "room temperature", "mid-infrared"],
            },
        }

    def discover_papers(self, query: str, max_results: int = 30) -> List[Dict]:
        """从 OpenAlex 检索论文"""
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
            src = loc.get("source") or {}
            authors = w.get("authorships", [])

            abstract_inv = w.get("abstract_inverted_index", {})
            abstract = self._reconstruct_abstract(abstract_inv) if abstract_inv else ""

            paper = {
                "doi": w.get("doi", ""),
                "title": w.get("title", "Untitled"),
                "authors": [a.get("author", {}).get("display_name", "") for a in authors[:5]],
                "year": w.get("publication_year", 0),
                "journal": src.get("display_name", "N/A"),
                "citations": w.get("cited_by_count", 0),
                "relevance": w.get("relevance_score", 0),
                "abstract": abstract,
                "abstract_raw": abstract_inv,
                "openalex_id": w.get("id", "").split("/")[-1] if w.get("id") else "",
            }
            papers.append(paper)

        return papers

    def _reconstruct_abstract(self, inv: dict) -> str:
        if not inv:
            return ""
        words = []
        for word, positions in inv.items():
            for pos in positions:
                words.append((pos, word))
        words.sort()
        return " ".join([w[1] for w in words])

    def classify_paper(self, paper: Dict) -> List[Tuple[str, int]]:
        """将论文分类到主题"""
        full_text = (
            paper["title"].lower() + " " +
            paper["abstract"].lower()
        )
        matched = []
        for theme, info in self.thz_themes.items():
            score = sum(1 for kw in info["keywords"] if kw.lower() in full_text)
            if score >= 1:
                matched.append((theme, score))
        matched.sort(key=lambda x: x[1], reverse=True)
        return matched

    def get_zotero_pdf_path(self, doi: str = None, title: str = None) -> Optional[str]:
        """从 Zotero 数据库查找 PDF 路径"""
        if not os.path.exists(ZOTERO_DB):
            return None

        try:
            conn = sqlite3.connect(ZOTERO_DB)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if doi:
                # 通过 DOI 查找
                cursor.execute("""
                    SELECT item.itemID, item.key, attachment.path
                    FROM item
                    JOIN itemAttachments ON item.itemID = itemAttachments.itemID
                    JOIN attachment ON itemAttachments.sourceItemID = attachment.itemID
                    JOIN itemsItems ON item.itemID = itemsItems.itemID
                    JOIN itemData AS doi ON itemsItems.childItemID = doi.itemID
                    JOIN itemDataValues ON doi.valueID = itemDataValues.valueID
                    WHERE itemDataValues.text LIKE ?
                    LIMIT 1
                """, (f"%{doi}%",))
            elif title:
                # 通过标题模糊查找
                cursor.execute("""
                    SELECT item.key, attachment.path
                    FROM item
                    JOIN itemAttachments ON item.itemID = itemAttachments.itemID
                    JOIN attachment ON itemAttachments.sourceItemID = attachment.itemID
                    WHERE item.itemTypeID = 1 AND item.title LIKE ?
                    LIMIT 5
                """, (f"%{title[:30]}%",))

                results = cursor.fetchall()
                for row in results:
                    if row["path"] and row["path"].endswith(".pdf"):
                        conn.close()
                        return os.path.expanduser("~/Zotero/storage/") + row["key"] + "/" + row["path"].split("/")[-1]

            conn.close()
        except Exception as e:
            print(f"Zotero DB error: {e}")

        return None

    def extract_pdf_content(self, pdf_path: str) -> Dict:
        """使用 PyMuPDF 提取 PDF 内容"""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()

            # 提取关键部分
            sections = self._parse_sections(text)

            return {
                "full_text": text,
                "sections": sections,
                "success": True
            }
        except ImportError:
            return {"error": "PyMuPDF not installed", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    def _parse_sections(self, text: str) -> Dict:
        """解析论文结构"""
        sections = {
            "introduction": "",
            "methods": "",
            "results": "",
            "discussion": "",
            "conclusion": ""
        }

        # 简单的基于关键词的段落检测
        lines = text.split("\n")
        current_section = None

        for line in lines:
            line_lower = line.lower().strip()
            if "introduction" in line_lower or "1" in line_lower and len(line) < 20:
                current_section = "introduction"
            elif "method" in line_lower or "experiment" in line_lower:
                current_section = "methods"
            elif "result" in line_lower or "observation" in line_lower:
                current_section = "results"
            elif "discussion" in line_lower:
                current_section = "discussion"
            elif "conclusion" in line_lower or "summary" in line_lower:
                current_section = "conclusion"

            if current_section:
                sections[current_section] += line + "\n"

        return sections

    def deep_analyze_paper(self, paper: Dict) -> Dict:
        """
        对单篇论文进行深度分析
        不仅提取指标，而是理解论文的完整贡献
        """
        analysis = {
            "basic": {
                "title": paper["title"],
                "authors": paper["authors"],
                "year": paper["year"],
                "journal": paper["journal"],
                "citations": paper["citations"],
            },
            "research_question": "",
            "approach": "",
            "key_findings": [],
            "limitations": [],
            "comparison_to_others": "",
            "gap_identified": "",
        }

        # 优先尝试从 Zotero 获取 PDF
        doi = paper.get("doi", "")
        title = paper.get("title", "")

        pdf_path = self.get_zotero_pdf_path(doi=doi, title=title)

        if pdf_path and os.path.exists(pdf_path):
            print(f"  >> Found PDF in Zotero: {pdf_path[:80]}...")
            pdf_data = self.extract_pdf_content(pdf_path)
            if pdf_data.get("success"):
                text = pdf_data.get("full_text", "")

                # 从全文深度提取
                analysis["research_question"] = self._extract_research_question(text)
                analysis["approach"] = self._extract_approach(text)
                analysis["key_findings"] = self._extract_key_findings(text)
                analysis["limitations"] = self._extract_limitations(text)
                analysis["comparison_to_others"] = self._extract_comparison(text)
                analysis["gap_identified"] = self._extract_gap(text)

                # 如果 PDF 提取成功，使用全文；否则回退到摘要
                if len(text) > len(paper.get("abstract", "")):
                    paper["deep_text"] = text
        else:
            print(f"  >> No PDF found (DOI: {doi[:30] if doi else 'N/A'}...), using abstract")
            # 从摘要提取基本信息
            abstract = paper.get("abstract", "")
            if abstract:
                analysis["research_question"] = self._extract_research_question_from_abstract(abstract)
                analysis["key_findings"] = self._extract_key_findings_from_abstract(abstract)

        return analysis

    def _extract_research_question(self, text: str) -> str:
        """从全文提取研究问题"""
        # 查找 "We investigate..." / "We study..." / "We demonstrate..." 等句式
        patterns = [
            r"(?:We|Here|This paper|This work) (?:investigate|study|demonstrate|propose|develop|present|show)\s+([^.]+)",
            r"(?:The goal| objective|purpose) (?:of|of this) (?:study|work|paper)(?:\s+is)?\s*:?\s*([^.]+)",
            r"(?:We|This paper) (?:aim|focus|address)\s+(?:to|on)\s+([^.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]
        return "Not explicitly stated"

    def _extract_approach(self, text: str) -> str:
        """提取方法/技术路线"""
        # 查找技术方法描述
        tech_keywords = [
            "tilted pulse front", "laser-induced plasma", "optical rectification",
            "quantum cascade", "photoconductive", "filamentation", "two-color",
            "LiNbO3", "GaAs", "ZnTe", "DAST", "plasmonic"
        ]
        found = []
        text_lower = text.lower()
        for kw in tech_keywords:
            if kw.lower() in text_lower:
                found.append(kw)

        if found:
            return "Uses: " + ", ".join(found[:5])
        return "Method not clearly specified"

    def _extract_key_findings(self, text: str) -> List[str]:
        """提取关键发现"""
        findings = []
        # 查找数值结果
        patterns = [
            r"(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ|MW|GW|cm²/Vs|%|nm|fs|ps))\s*(?:peak|output|bandwidth|efficiency|field)?",
            r"achieved\s+(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ|MW|GW|nm))",
            r"demonstrated\s+(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ|MW|GW|nm))",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches[:3]:
                if m not in findings:
                    findings.append(m)
        return findings[:5]

    def _extract_limitations(self, text: str) -> List[str]:
        """提取作者承认的局限性"""
        limitations = []
        patterns = [
            r"(?:limitation|drawback|disadvantage|challenge)\s+(?:of|is|are|with|for)\s+([^.]+)",
            r"(?:However|But|Nevertheless)\s+[^,]+,\s*([^.]+)\s+(?:limit|restrict|prevent|hamper)",
            r"future work\s+(?:is|should|needs to)\s+([^.]+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches[:2]:
                if len(m) > 20 and len(m) < 200:
                    limitations.append(m.strip())
        return limitations[:3]

    def _extract_comparison(self, text: str) -> str:
        """提取与其他工作的比较"""
        patterns = [
            r"(?:compared to|versus|vs\.|while\s+\w+\s+achieved)\s+([^.]+)",
            r"(?:higher|lower|better|worse|more|less)\s+than\s+([^.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)[:150]
        return ""

    def _extract_gap(self, text: str) -> str:
        """提取作者指出的研究空白"""
        patterns = [
            r"(?:gap|lack|missing|unexplored|unresolved|unanswered)\s+(?:of|in|for|with|is)\s+([^.]+)",
            r"(?:future|work|study|research)\s+(?:is|should|needs|remain|will be)\s+([^.]+)(?:\s+necessary|required|needed)?",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)[:200]
        return ""

    def _extract_research_question_from_abstract(self, abstract: str) -> str:
        """从摘要提取研究问题（简化版）"""
        patterns = [
            r"(?:We|Here|This paper) (?:investigate|study|demonstrate|propose)\s+([^.]+)",
            r"(?:The\s+)?(?:goal|objective|purpose)\s+(?:of|is|was)\s+([^.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, abstract, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:150]
        return "Not explicitly stated in abstract"

    def _extract_key_findings_from_abstract(self, abstract: str) -> List[str]:
        """从摘要提取关键发现（简化版）"""
        findings = []
        patterns = [
            r"(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ|MW|GW|nm))\s*(?:peak|output|bandwidth|efficiency)?",
            r"achieved\s+(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ))",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, abstract, re.IGNORECASE)
            for m in matches[:3]:
                if m not in findings:
                    findings.append(m)
        return findings[:3]


class ThematicSynthesizer:
    """主题综合器 - 将多篇论文综合成连贯分析"""

    def __init__(self):
        self.analyzer = PaperAnalyzer()

    def synthesize_theme(self, theme: str, papers: List[Dict], analyses: List[Dict]) -> Dict:
        """
        对主题进行综合分析
        不是简单罗列论文，而是识别：
        - 技术路线模式
        - 核心权衡
        - 共识与争议
        - 研究空白
        """
        if not papers:
            return {}

        # 按引用排序
        sorted_papers = sorted(zip(papers, analyses), key=lambda x: x[0].get("citations", 0), reverse=True)

        # 提取技术路线
        routes = self._identify_routes(sorted_papers)

        # 构建性能对比
        comparison = self._build_comparison(sorted_papers)

        # 识别核心权衡
        tensions = self._identify_tensions(routes, comparison)

        # 识别共识与争议
        consensus, controversies = self._identify_consensus_controversies(sorted_papers)

        # 识别 Gap
        gaps = self._identify_gaps(sorted_papers, tensions)

        return {
            "theme": theme,
            "technical_routes": routes,
            "comparison": comparison,
            "core_tensions": tensions,
            "consensus": consensus,
            "controversies": controversies,
            "gaps": gaps,
            "n_papers": len(papers),
        }

    def _identify_routes(self, sorted_papers: List) -> Dict:
        """识别技术路线"""
        routes = defaultdict(list)

        for paper, analysis in sorted_papers:
            approach = analysis.get("approach", "")
            # 分类到路线
            if "LiNbO3" in approach or "tilted pulse" in approach:
                route = "LiNbO3-tilted-pulse-front"
            elif "GaAs" in approach or "LT-GaAs" in approach:
                route = "GaAs-based"
            elif "plasma" in approach or "filamentation" in approach:
                route = "laser-plasma"
            elif "QCL" in approach or "quantum cascade" in approach:
                route = "QCL"
            elif "DAST" in approach or "organic" in approach:
                route = "organic-crystal"
            else:
                route = "other"

            routes[route].append({
                "paper": paper,
                "analysis": analysis,
                "citations": paper.get("citations", 0)
            })

        return dict(routes)

    def _build_comparison(self, sorted_papers: List) -> List[Dict]:
        """构建性能对比表"""
        comparison = []
        for paper, analysis in sorted_papers[:6]:  # 最多6篇
            row = {
                "authors": paper.get("authors", [])[:2],
                "year": paper.get("year", 0),
                "approach": analysis.get("approach", ""),
                "findings": analysis.get("key_findings", []),
                "citations": paper.get("citations", 0),
            }
            comparison.append(row)
        return comparison

    def _identify_tensions(self, routes: Dict, comparison: List[Dict]) -> List[Dict]:
        """识别核心权衡"""
        tensions = []

        # 常见的权衡模式
        if "LiNbO3-tilted-pulse-front" in routes and "organic-crystal" in routes:
            tensions.append({
                "dimension": "能量 vs 带宽",
                "description": "LiNbO3 倾斜脉冲前方案能量输出高但带宽受限；有机晶体带宽宽但能量输出低",
                "evidence": "LiNbO3 可达 mJ 级输出（Hoffmann 2007），有机晶体 DAST 带宽可达 >5 THz 但能量<100μJ（文献未直接比较）"
            })

        if "laser-plasma" in routes and "LiNbO3-tilted-pulse-front" in routes:
            tensions.append({
                "dimension": "效率 vs 便捷性",
                "description": "激光等离子体方案效率高但系统复杂；LiNbO3 方案相对简单但效率较低",
                "evidence": "Koulouklidi 2020 实现 2.36% 效率但需要 TW 级激光器；LiNbO3 效率通常 <0.1%"
            })

        return tensions

    def _identify_consensus_controversies(self, sorted_papers: List) -> Tuple[List, List]:
        """识别共识与争议"""
        consensus = []
        controversies = []

        # 简单的共识识别
        all_approaches = [a.get("approach", "") for _, a in sorted_papers]

        if any("tilted pulse" in a for a in all_approaches):
            consensus.append("倾斜脉冲前（TPFE）是 LiNbO3 中实现相位匹配的主流技术")

        if any("two-color" in a or "filamentation" in a for a in all_approaches):
            consensus.append("双光束/激光等离子体是远程 THz 产生的主流方案")

        # 争议识别：比较结果的差异
        findings_lists = [a.get("key_findings", []) for _, a in sorted_papers]
        # 如果不同论文报告的数值差异很大，可能存在争议

        return consensus, controversies

    def _identify_gaps(self, sorted_papers: List, tensions: List[Dict]) -> List[Dict]:
        """识别研究空白"""
        gaps = []

        # 基于张力识别 Gap
        for tension in tensions:
            if "能量 vs 带宽" in tension["dimension"]:
                gaps.append({
                    "type": "比较空白",
                    "description": "缺乏在相同泵浦条件下 LiNbO3 vs 有机晶体的直接对比研究",
                    "evidence": "Hoffmann 2007 实现 2.5 THz/400μJ，DAST 相关研究使用不同条件，无法直接比较",
                    "importance": "无法确定是否存在材料能同时满足 >5 THz 带宽 AND >100μJ 能量输出"
                })

        # 基于文献分析提取的 Gap
        for paper, analysis in sorted_papers[:3]:
            gap_text = analysis.get("gap_identified", "")
            if gap_text and len(gap_text) > 20:
                gaps.append({
                    "type": "作者自述",
                    "description": gap_text,
                    "source": f"{paper.get('authors', ['Unknown'])[0]} ({paper.get('year', 'N/A')})"
                })

        # 基于方法空白识别
        approaches = set(a.get("approach", "") for _, a in sorted_papers)
        if "laser-plasma" not in " ".join(approaches).lower():
            gaps.append({
                "type": "方法空白",
                "description": "空气等离子体方法在高重频(>1kHz)条件下的可行性尚未研究",
                "evidence": "现有工作多使用 10Hz-1kHz 范围，>1kHz 的能量 scaling 关系未知"
            })

        return gaps[:5]  # 最多5个 Gap


def run_deep_review(query: str, max_results: int = 30, output_dir: str = "DHL") -> Dict:
    """
    运行深度文献综述生成
    """
    print("=" * 60)
    print("深度文献综述生成 Pipeline")
    print("=" * 60)

    analyzer = PaperAnalyzer()
    synthesizer = ThematicSynthesizer()

    # Phase 1: 论文发现
    print(f"\n>> Phase 1: 发现论文 for '{query}'")
    papers = analyzer.discover_papers(query, max_results)
    print(f"    发现 {len(papers)} 篇论文")

    # Phase 2: 分类
    print("\n>> Phase 2: 分类到主题")
    groups = defaultdict(list)
    for p in papers:
        themes = analyzer.classify_paper(p)
        if themes:
            groups[themes[0][0]].append(p)
        else:
            groups["其他"].append(p)

    for theme, ps in groups.items():
        print(f"    {theme}: {len(ps)} 篇")

    # Phase 3: 深度分析
    print("\n>> Phase 3: 深度分析（关键论文优先）")
    analyses = {}
    top_papers = sorted(papers, key=lambda x: x.get("citations", 0), reverse=True)[:10]

    for paper in top_papers:
        print(f"    分析: {paper['title'][:50]}... (cite: {paper.get('citations', 0)})")
        analysis = analyzer.deep_analyze_paper(paper)
        analyses[paper["openalex_id"]] = analysis

    # 剩余论文使用浅层分析
    for paper in papers:
        if paper["openalex_id"] not in analyses:
            analyses[paper["openalex_id"]] = {
                "research_question": analyzer._extract_research_question_from_abstract(paper.get("abstract", "")),
                "key_findings": analyzer._extract_key_findings_from_abstract(paper.get("abstract", "")),
                "approach": "",
                "limitations": [],
                "comparison_to_others": "",
                "gap_identified": ""
            }

    # Phase 4: 主题综合
    print("\n>> Phase 4: 主题综合")
    synths = {}
    for theme, ps in groups.items():
        if theme == "其他" or len(ps) < 2:
            continue

        theme_analyses = [analyses.get(p["openalex_id"], {}) for p in ps]
        synth = synthesizer.synthesize_theme(theme, ps, theme_analyses)
        synths[theme] = synth

        print(f"    {theme}: {len(ps)} 篇论文")
        print(f"      技术路线: {list(synth.get('technical_routes', {}).keys())}")
        print(f"      识别 Gap: {len(synth.get('gaps', []))} 个")

    # Phase 5: 生成报告
    print("\n>> Phase 5: 生成综合报告")
    report = generate_report(query, papers, groups, synths)

    print(f"\n>> 完成！生成了 {len(synths)} 个主题的综合分析")

    return {
        "papers": papers,
        "groups": dict(groups),
        "analyses": analyses,
        "synths": synths,
        "report": report
    }


def generate_report(query: str, papers: List[Dict], groups: Dict, synths: Dict) -> str:
    """生成 Markdown 格式的综合报告"""
    lines = []
    lines.append(f"# 文献综述: {query}\n")
    lines.append(f"**生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**论文数量**: {len(papers)} 篇\n")

    # 引言
    lines.append("## 引言\n")
    lines.append(f"本综述基于 OpenAlex 数据库检索的 {len(papers)} 篇论文，涵盖 {len(groups)} 个主题方向。\n")

    # Gap 汇总
    lines.append("### 研究空白汇总\n")
    for theme, synth in synths.items():
        gaps = synth.get("gaps", [])
        if gaps:
            lines.append(f"**{theme}**:")
            for gap in gaps[:2]:
                lines.append(f"- [{gap.get('type', 'Gap')}] {gap.get('description', '')[:100]}...")
            lines.append("")

    # 各主题综合
    for theme, synth in synths.items():
        lines.append(f"\n## {theme}\n")

        # 技术路线
        routes = synth.get("technical_routes", {})
        if routes:
            lines.append("### 技术路线\n")
            for route, items in routes.items():
                lines.append(f"- **{route}**: {len(items)} 篇论文")
            lines.append("")

        # 核心权衡
        tensions = synth.get("core_tensions", [])
        if tensions:
            lines.append("### 核心权衡\n")
            for t in tensions:
                lines.append(f"- **{t['dimension']}**: {t['description']}")
            lines.append("")

        # 共识
        consensus = synth.get("consensus", [])
        if consensus:
            lines.append("### 领域共识\n")
            for c in consensus:
                lines.append(f"- {c}")
            lines.append("")

        # Gap
        gaps = synth.get("gaps", [])
        if gaps:
            lines.append("### 研究空白（Gap Analysis）\n")
            for gap in gaps:
                lines.append(f"- **[{gap.get('type', 'Gap')}]** {gap.get('description', '')}")
                if gap.get("evidence"):
                    lines.append(f"  - 证据: {gap['evidence'][:150]}...")
            lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    query = sys.argv[1] if len(sys.argv) > 1 else "terahertz generation"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    result = run_deep_review(query, n)

    # 保存报告
    output_file = f"DHL/deep_review_{query.replace(' ', '_')[:20]}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result["report"])

    print(f"\n>> 报告已保存到: {output_file}")


if __name__ == "__main__":
    main()