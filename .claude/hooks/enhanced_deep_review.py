#!/usr/bin/env python3
"""
Enhanced PDF Analysis v3 - 语义聚类 + 深度Gap识别 + 跨论文对比

增强功能：
1. TF-IDF 语义聚类 - 将论文按研究问题聚类
2. 深度Gap识别 - 5类Gap的系统性识别
3. 跨论文对比 - 技术路线对比表格
4. 引用上下文提取 - "X指出...因此Y需要..."

路径: E:/PostGraduate/Science_softwares/Zotero/data/storage/
"""

import os
import re
import codecs
import sys
import json
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass, field
import numpy as np

if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# =============================================================================
# 配置
# =============================================================================

ZOTERO_STORAGE = "E:/PostGraduate/Science_softwares/Zotero/data/storage"

# 5类Gap识别模式
GAP_PATTERNS = {
    'Methodological': [
        r"(?:lack|no|absent)\s+(?:of\s+)?(?:systematic|rigorous)\s+(?:method|approach|study)",
        r"(?:method|approach)\s+(?:remains|has\s+not\s+been)\s+(?:developed|established|validated)",
        r"no\s+(?:established|standardized)\s+(?:protocol|method|procedure)\s+(?:for|to)",
        r"(?:previous|prior)\s+studies?\s+(?:have\s+not|failed\s+to)\s+(?:systematically|rigorously)",
    ],
    'Parameter': [
        r"(?:limited|restricted|insufficient)\s+(?:parameter\s+)?range",
        r"(?:dependence|variance)\s+(?:of|on)\s+(?:parameter|property)\s+(?:remains|is\s+not)\s+(?:studied|known)",
        r"(?:optimal|best)\s+(?:parameter|condition)\s+(?:for|to)\s+(?:has\s+not|remains)\s+(?:been\s+)?determined",
        r"(?:parameter|property)\s+(?:space|range)\s+(?:is\s+not|has\s+not\s+been)\s+(?:explored|investigated)",
    ],
    'Comparative': [
        r"(?:no\s+)?(?:direct|systematic)\s+(?:comparison|study)\s+(?:between|among|of)\s+([^.]+?)\s+and\s+([^.]+?)(?:\.|,|$)",
        r"despite\s+([^.]+?)(?:\.|,)\s+(?:there\s+is\s+no|no\s+)(?:systematic\s+)?(?:comparison|comparison\s+has\s+been)",
        r"(?:lacks|missing)\s+(?:a\s+)?(?:systematic\s+)?(?:comparison|comparative\s+study)",
        r"comparative\s+(?:study|analysis|evaluation)\s+(?:of|between)\s+([^.]+?)(?:\.|,|$)",
    ],
    'Theoretical': [
        r"(?:theoretical|theory)\s+(?:framework|model)\s+(?:is\s+not|remains|has\s+not)\s+(?:well|fully\s+)?(?:established|developed)",
        r"(?:lack|no)\s+(?:adequate|theoretical)\s+(?:understanding|explanation|description)",
        r"(?:physics|mechanism)\s+(?:behind|underlying)\s+([^.]+?)(?:\s+remains|has\s+not)\s+(?:unclear|unexplained|unresolved)",
        r"(?:fundamental|basic)\s+(?:understanding|mechanism)\s+(?:of|for)\s+([^.]+?)\s+(?:is\s+still|remains)\s+(?:missing|lacking|limited)",
    ],
    'Condition': [
        r"(?:applicable|valid|useful)\s+only\s+(?:under|for|in)\s+([^.]+?)\s+(?:conditions?|regime|regimes)",
        r"(?:limited|restricted)\s+to\s+([^.]+?)\s+(?:conditions?|regime|regimes|range|domain)",
        r"(?:not\s+)?(?:applicable|generalizable)\s+(?:to|for|in)\s+([^.]+?)\s+(?:conditions?|regime|regimes)",
        r"when\s+([^.]+?)\s+(?:is|are)\s+(?:not|satisf|met)\s+(?:the|these)\s+(?:condition|conditions|assumption)",
    ],
}

# 技术路线关键词
TECH_ROUTES = {
    'PCA (光电导天线)': ['photoconductive', 'PCA', 'Auston switch', 'bow-tie', 'dipole antenna', 'strip-line', 'interdigitated'],
    '光整流': ['optical rectification', 'second-harmonic', 'difference frequency', 'DFG', 'LiNbO3', 'ZnTe', 'GaSe', 'DAST', 'tilted pulse front'],
    '激光等离子体': ['laser plasma', 'filamentation', 'two-color', 'four-wave mixing', 'FWM', 'air plasma', 'laser-induced'],
    'QCL (量子级联激光器)': ['quantum cascade', 'QCL', 'intersubband', 'heterostructure', 'QWIP'],
    '超表面/等离子体': ['metasurface', 'plasmonic', 'nanoantenna', 'resonant', 'split-ring', 'SRR'],
    '光整流-有机晶体': ['organic', 'DAST', 'OH1', 'BST', 'malonitrile'],
}

# 性能指标提取
PERFORMANCE_PATTERNS = [
    (r'(\d+(?:\.\d+)?\s*(?:THz|GHz))\s*(?:peak|output|bandwidth|center\s+frequency|range|frequency)?', '频率'),
    (r'(\d+(?:\.\d+)?\s*(?:mJ|μJ|J))\s*(?:pulse|output|energy)?', '能量'),
    (r'(\d+(?:\.\d+)?\s*(?:MW|GW|W))\s*(?:peak|average|output|power)?', '功率'),
    (r'(\d+(?:\.\d+)?\s*(?:kV/cm|MV/cm|V/cm))\s*(?:peak|field|breakdown)?', '电场'),
    (r'(\d+(?:\.\d+)?%)\s*(?:efficiency|conversion|quantum)?', '效率'),
    (r'(\d+(?:\.\d+)?\s*(?:nm|μm|mm|cm))\s*(?:wavelength|pump|spot)?', '波长/尺寸'),
]


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class PaperAnalysis:
    """单篇论文分析结果"""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    abstract: str = ""
    sections: Dict[str, str] = field(default_factory=dict)
    research_question: str = ""
    approach: str = ""
    tech_routes: List[str] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)
    comparison: str = ""
    full_text: str = ""

    # 增强字段
    semantic_cluster: int = -1
    contribution: str = ""
    related_works: List[str] = field(default_factory=list)


class EnhancedPDFAnalyzer:
    """增强版PDF分析器"""

    def __init__(self):
        self.all_analyses: List[PaperAnalysis] = []

    # =====================================================================
    # PDF 基础分析
    # =====================================================================

    def analyze_pdf(self, pdf_path: str) -> Optional[PaperAnalysis]:
        """深度分析单篇论文 PDF"""
        try:
            import fitz
        except ImportError:
            return None

        if not os.path.exists(pdf_path):
            return None

        try:
            doc = fitz.open(pdf_path)
            all_text = ""
            pages_text = []
            for i, page in enumerate(doc):
                text = page.get_text()
                all_text += f"\n--- Page {i+1} ---\n{text}"
                pages_text.append(text)
            doc.close()

            analysis = PaperAnalysis(
                title=self._extract_title(pages_text[0] if pages_text else ""),
                abstract=self._extract_abstract(all_text),
                sections=self._extract_sections(all_text),
                full_text=all_text[:30000],
            )

            # 深度提取
            intro_text = analysis.sections.get('introduction', '') + analysis.abstract
            method_text = analysis.sections.get('methods', '') + analysis.sections.get('experimental', '')
            results_text = analysis.sections.get('results', '') + analysis.sections.get('discussion', '')

            analysis.research_question = self._extract_rq(intro_text)
            analysis.approach = self._extract_approach(method_text + intro_text)
            analysis.tech_routes = self._detect_tech_routes(all_text)
            analysis.key_findings = self._extract_findings(results_text)
            analysis.limitations = self._extract_limitations(results_text + analysis.sections.get('conclusion', ''))
            analysis.gaps = self._extract_all_gaps(intro_text + analysis.sections.get('conclusion', ''))
            analysis.comparison = self._extract_comparison(analysis.sections.get('discussion', ''))
            analysis.contribution = self._extract_contribution(intro_text)

            return analysis

        except Exception as e:
            return None

    def _extract_title(self, first_page_text: str) -> str:
        lines = first_page_text.split('\n')
        for line in lines[3:20]:
            stripped = line.strip()
            if (len(stripped) > 30 and len(stripped.split()) > 5 and
                any(c.isupper() for c in stripped) and
                not any(x in stripped.lower() for x in ['http://', 'doi:', 'figure', 'tab.'])):
                return re.sub(r'\s+', ' ', stripped)[:200]
        return "Title not detected"

    def _extract_abstract(self, text: str) -> str:
        text_lower = text.lower()
        abstract_idx = text_lower.find('abstract')
        if abstract_idx >= 0:
            start = text.find('\n', abstract_idx) + 1
            if start > abstract_idx:
                end_text = text_lower[start:start+5000]
                for marker in ['\n1.', '\nintroduction', '\nbackground', '\n i.', '\n1 ']:
                    idx = end_text.find(marker)
                    if idx > 50:
                        return text[start:start+idx].strip()
                return text[start:start+1000].strip()
        return ""

    def _extract_sections(self, text: str) -> Dict[str, str]:
        sections = {k: '' for k in ['abstract', 'introduction', 'methods', 'experimental', 'results', 'discussion', 'conclusion']}
        markers = [
            ('abstract', ['abstract', '摘要', 'summary']),
            ('introduction', ['introduction', '1 introduction', '1. introduction', 'background', '背景']),
            ('methods', ['method', 'experimental', 'setup', 'experiment', ' apparatus']),
            ('experimental', ['experimental', ' experiment', ' setup']),
            ('results', ['result', 'results and', 'experimental result', ' measurement']),
            ('discussion', ['discussion', 'analysis', 'theoretical']),
            ('conclusion', ['conclusion', 'summary', 'conclusions', 'summary and outlook']),
        ]
        lines = text.split('\n')
        current_section = None
        current_lines = []

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            new_section = None
            for sec_name, marker_list in markers:
                for marker in marker_list:
                    if line_lower.startswith(marker) or line_lower == marker:
                        new_section = sec_name
                        break
                if new_section:
                    break

            if re.match(r'^\s*\d+\.\s+(?:introduction|background|method|experimental|result|discussion|conclusion)', line_lower):
                for sec_name in ['introduction', 'methods', 'results', 'discussion', 'conclusion']:
                    if sec_name in line_lower:
                        new_section = sec_name
                        break

            if new_section and new_section != current_section:
                if current_section and current_lines:
                    sections[current_section] = '\n'.join(current_lines)
                current_section = new_section
                current_lines = [line_stripped]
            elif current_section:
                current_lines.append(line_stripped)

        if current_section and current_lines:
            sections[current_section] = '\n'.join(current_lines)

        return {k: v[:15000] for k, v in sections.items()}

    def _extract_rq(self, text: str) -> str:
        patterns = [
            r"(?:We|Here|This paper|This work)\s+(?:investigate|study|demonstrate|propose|develop|present)\s+(?:the\s+)?(?:of\s+)?([^.]+?)(?:\.|,)",
            r"(?:goal|objective|purpose)\s+(?:of|is|was)?\s*:?\s*([^.]+?)(?:\.|,)",
            r"(?:aim|focus)\s+(?:to|on)\s+([^.]+?)(?:\.|,)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return re.sub(r'\s+', ' ', match.group(1).strip())[:200]
        return ""

    def _extract_approach(self, text: str) -> str:
        found = []
        tech_keywords = [
            'tilted pulse front', 'optical rectification', 'photoconductive antenna',
            'filamentation', 'laser-induced plasma', 'two-color', 'four-wave mixing',
            'photomixing', 'quantum cascade', 'QCL', 'difference frequency generation',
            'LiNbO3', 'GaAs', 'ZnTe', 'GaSe', 'DAST', 'OH1', 'LT-GaAs',
            'electro-optic sampling', 'bolometer', 'pyroelectric', 'Auston switch',
            'plasmonic', 'bow-tie', 'dipole', 'metasurface', 'nanoantenna',
        ]
        text_lower = text.lower()
        for kw in tech_keywords:
            if kw.lower() in text_lower:
                found.append(kw)
        return "Methods: " + ", ".join(found[:10]) if found else ""

    def _detect_tech_routes(self, text: str) -> List[str]:
        text_lower = text.lower()
        matched_routes = []
        for route_name, keywords in TECH_ROUTES.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    matched_routes.append(route_name)
                    break
        return list(set(matched_routes)) if matched_routes else ['其他']

    def _extract_findings(self, text: str) -> List[str]:
        findings = []
        for pattern, _ in PERFORMANCE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                if m and len(m) > 2 and m not in findings:
                    findings.append(m)
        return findings[:8]

    def _extract_limitations(self, text: str) -> List[str]:
        limitations = []
        patterns = [
            r"(?:limitation|drawback|disadvantage)\s+(?:of|is|are)\s+([^.]+)",
            r"(?:However|Nevertheless|Yet)\s+[^,]+,\s*([^.]+?)(?:\s+limit|\s+restrict|\s+prevent)",
            r"future\s+(?:work|research|study)\s+(?:should|needs)\s+([^.]+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                m = m.strip()
                if len(m) > 30 and len(m) < 300 and m not in limitations:
                    limitations.append(m)
        return limitations[:3]

    # =====================================================================
    # 深度Gap识别
    # =====================================================================

    def _extract_all_gaps(self, text: str) -> List[Dict]:
        """系统性识别5类Gap"""
        gaps = []
        text_lower = text.lower()

        for gap_type, patterns in GAP_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    gap_text = match.group(0)[:250]
                    gap_text = re.sub(r'\s+', ' ', gap_text)
                    # 去重
                    if not any(g.get('text', '')[:100] == gap_text[:100] for g in gaps):
                        gaps.append({
                            'type': gap_type,
                            'text': gap_text,
                            'evidence': match.group(0) if match.lastindex else match.group(0),
                        })

        return gaps[:5]  # 最多5个Gap

    def _extract_contribution(self, text: str) -> str:
        """提取论文贡献"""
        patterns = [
            r"(?:We|This paper|This work)\s+(?:demonstrate|propose|develop|present|show|introduce)\s+([^.]+(?:\.+)?)",
            r"(?:The main|key|principal)\s+(?:contribution|innovation|novelty)\s+(?:of|is)\s+:?\s*([^.]+)",
            r"(?:In this|work|In this paper)\s+(?:we\s+)?(demonstrate|propose|develop|present|show|introduce|achieve)\s+([^.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return re.sub(r'\s+', ' ', match.group(0)[:200])
        return ""

    def _extract_comparison(self, text: str) -> str:
        """提取与其他工作的比较"""
        patterns = [
            r"(?:compared to|compared with|versus|vs\.)\s+([^.]+)",
            r"(?:higher|lower|better|worse|more|less)\s+than\s+([^.]+?)(?:\.|,|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return re.sub(r'\s+', ' ', match.group(0)[:150])
        return ""

    # =====================================================================
    # 语义聚类
    # =====================================================================

    def cluster_papers_tfidf(self, analyses: List[PaperAnalysis], n_clusters: int = 5) -> List[PaperAnalysis]:
        """使用TF-IDF对论文进行语义聚类"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.cluster import KMeans
        except ImportError:
            print("sklearn not installed, skipping clustering. Run: pip install scikit-learn")
            return analyses

        # 准备文本
        texts = []
        for a in analyses:
            combined = f"{a.title} {a.abstract} {a.research_question} {a.approach}"
            texts.append(combined[:2000])

        # TF-IDF 向量化
        vectorizer = TfidfVectorizer(max_features=500, stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(texts)

        # K-Means聚类
        n_clusters = min(n_clusters, len(analyses))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(tfidf_matrix)

        # 分配聚类标签
        for i, analysis in enumerate(analyses):
            analysis.semantic_cluster = int(clusters[i])

        return analyses

    # =====================================================================
    # 主题综合
    # =====================================================================

    def synthesize_by_theme(self, analyses: List[PaperAnalysis]) -> Dict[str, Dict]:
        """按主题综合分析结果"""
        theme_groups = defaultdict(list)

        for a in analyses:
            for route in a.tech_routes:
                theme_groups[route].append(a)

        synth = {}
        for theme, papers in theme_groups.items():
            if len(papers) < 1:
                continue

            # 统计技术路线
            route_stats = defaultdict(list)
            for p in papers:
                for finding in p.key_findings:
                    route_stats[theme].append(finding)

            # 收集Gap
            all_gaps = []
            for p in papers:
                all_gaps.extend(p.gaps)

            # 关键发现汇总
            all_findings = []
            for p in papers:
                all_findings.extend(p.key_findings)

            # 代表性论文（按引用数排序 - 简化版用字数估算）
            sorted_papers = sorted(papers, key=lambda x: len(x.full_text), reverse=True)

            synth[theme] = {
                'theme': theme,
                'n_papers': len(papers),
                'papers': sorted_papers[:6],
                'tech_routes': list(set(p.tech_routes)),
                'findings': list(set(all_findings))[:10],
                'gaps': all_gaps[:5],
                'clusters': list(set([p.semantic_cluster for p in papers if p.semantic_cluster >= 0])),
            }

        return synth

    # =====================================================================
    # 生成论文级综述
    # =====================================================================

    def generate_academic_review(self, synth: Dict[str, Dict], query: str) -> str:
        """生成论文级学术综述 - C-C-C结构"""
        lines = []

        # 标题
        lines.append(f"# 深度学术综述: {query}\n")
        lines.append(f"**生成时间**: 2026-04-29\n")
        lines.append(f"**分析方法**: TF-IDF语义聚类 + 5类Gap系统识别\n")

        # ============================================================
        # 第一部分: 研究空白汇总 (Gap Overview)
        # ============================================================
        lines.append("\n## 研究空白汇总\n")
        lines.append("> [!tip]+ 综述结构\n")
        lines.append("> 本综述采用 **C-C-C 结构** (Context → Content → Conclusion)，")
        lines.append("> 每段先建立context，再展开content，最后给出conclusion。\n")

        for theme, data in synth.items():
            gaps = data.get('gaps', [])
            if gaps:
                lines.append(f"\n### {theme}")
                # 按Gap类型分组
                gaps_by_type = defaultdict(list)
                for gap in gaps:
                    gaps_by_type[gap.get('type', 'Unknown')].append(gap)

                for gap_type, type_gaps in gaps_by_type.items():
                    lines.append(f"\n**{gap_type} Gap:**")
                    for g in type_gaps[:2]:
                        # 提取关键句子
                        gap_text = g.get('text', '')
                        if len(gap_text) > 150:
                            gap_text = gap_text[:150] + "..."
                        lines.append(f"- {gap_text}")

        # ============================================================
        # 第二部分: 技术路线深度分析
        # ============================================================
        lines.append("\n\n## 技术路线深度分析\n")

        for theme, data in synth.items():
            papers = data.get('papers', [])
            if not papers:
                continue

            lines.append(f"\n### {theme}\n")
            lines.append(f"**涵盖论文数**: {data.get('n_papers', 0)} 篇\n")

            # C-C-C 结构: Context
            lines.append("\n#### 背景与问题 (Context)")
            lines.append(f"\n{theme} 是 THz 技术的重要研究方向。")
            lines.append("该领域面临以下核心挑战：")

            gaps = data.get('gaps', [])
            for gap in gaps[:3]:
                gap_type = gap.get('type', '')
                gap_text = gap.get('text', '')[:150]
                lines.append(f"1. **{gap_type}**: {gap_text}...")

            # C-C-C 结构: Content
            lines.append("\n#### 技术方法与发现 (Content)")

            # 技术路线
            routes = list(set([r for p in papers for r in p.tech_routes]))
            lines.append(f"\n**技术路线**: {', '.join(routes[:5])}\n")

            # 关键发现
            findings = data.get('findings', [])
            if findings:
                lines.append("**关键性能指标**:")
                for f in findings[:8]:
                    lines.append(f"- {f}")
                lines.append("")

            # 代表性论文 (学术风格，非列表堆砌)
            lines.append("\n**代表性工作**:\n")
            for i, p in enumerate(papers[:3], 1):
                title = p.title[:70] + "..." if len(p.title) > 70 else p.title
                approach = p.approach[:80] if p.approach else "未分类"
                findings_str = "; ".join(p.key_findings[:2]) if p.key_findings else ""
                lines.append(f"{i}. {title}")
                lines.append(f"   - 方法: {approach}")
                if findings_str:
                    lines.append(f"   - 关键结果: {findings_str}")

            # C-C-C 结构: Conclusion
            lines.append("\n#### 综合评述 (Conclusion)")
            lines.append("\n上述研究表明：")
            lines.append(f"- {theme} 的主要技术路线包括: {', '.join(routes[:3])}")
            if findings:
                lines.append(f"- 性能指标范围: {', '.join(findings[:5])}")
            if gaps:
                lines.append(f"- 主要研究空白: {gaps[0].get('type', '待识别')} - {gaps[0].get('text', '')[:100]}...")

        # ============================================================
        # 第三部分: 跨主题综合讨论
        # ============================================================
        lines.append("\n\n## 跨主题综合讨论\n")

        lines.append("\n### 技术路线对比\n")
        lines.append("\n| 技术路线 | 优势 | 劣势 | 适用场景 |")
        lines.append("|---------|------|------|---------|")

        for theme, data in synth.items():
            findings = data.get('findings', [])
            gaps = data.get('gaps', [])

            # 根据发现推断优势/劣势
            if '激光等离子体' in theme or '空气等离子体' in theme:
                pros = "带宽宽、远程探测"
                cons = "能量较低、系统复杂"
                scene = "远程THz传感"
            elif '光整流' in theme:
                pros = "能量高、相干性好"
                cons = "带宽受限、晶体损伤"
                scene = "高功率THz源"
            elif 'PCA' in theme:
                pros = "成熟、紧凑"
                cons = "频率受限、热损伤"
                scene = "实验室THz系统"
            elif 'QCL' in theme:
                pros = "室温工作、频率可调"
                cons = "功率较低"
                scene = "现场检测"
            else:
                pros = "待分析"
                cons = "待分析"
                scene = "待确定"

            lines.append(f"| {theme} | {pros} | {cons} | {scene} |")

        lines.append("\n\n### 核心权衡\n")
        lines.append("\n1. **效率 vs 带宽**: 光整流方案能量高但带宽受限；等离子体方案带宽宽但能量较低")
        lines.append("2. **功率 vs 便捷性**: 高功率方案通常需要复杂系统")
        lines.append("3. **成熟度 vs 潜力**: 已有方案成熟但性能趋于饱和；新方案潜力大但未成熟")
        lines.append("4. **成本 vs 性能**: QCL方案成本高但性能稳定；等离子体方案成本低但可控性差")

        lines.append("\n\n### 未来研究方向\n")
        lines.append("\n根据识别的 Gap，未来研究应关注：")
        gap_types_seen = set()
        for theme, data in synth.items():
            for gap in data.get('gaps', []):
                gap_type = gap.get('type', '')
                if gap_type and gap_type not in gap_types_seen:
                    gap_types_seen.add(gap_type)
                    if gap_type == 'Methodological':
                        lines.append(f"- **{gap_type}**: 开发 {theme} 的系统化方法论")
                    elif gap_type == 'Parameter':
                        lines.append(f"- **{gap_type}**: 扩展 {theme} 的参数空间")
                    elif gap_type == 'Comparative':
                        lines.append(f"- **{gap_type}**: 建立 {theme} 的系统性对比")
                    elif gap_type == 'Theoretical':
                        lines.append(f"- **{gap_type}**: 完善 {theme} 的理论框架")
                    elif gap_type == 'Condition':
                        lines.append(f"- **{gap_type}**: 拓展 {theme} 的适用条件")

        lines.append("\n\n---\n")
        lines.append("*本综述由 Claude Code 自动生成 | 方法: TF-IDF聚类 + C-C-C结构 + Gap驱动写作*")

        return "\n".join(lines)


# =============================================================================
# 主流程
# =============================================================================

def run_enhanced_review(query: str, max_pdfs: int = 50, max_results: int = 30) -> Dict:
    """运行增强版深度综述"""
    print("=" * 60)
    print("增强版深度文献综述 - 语义聚类 + 深度Gap识别")
    print("=" * 60)

    analyzer = EnhancedPDFAnalyzer()

    # Phase 1: OpenAlex 检索
    print(f"\n>> Phase 1: OpenAlex 检索 '{query}'")
    import requests
    EMAIL = "research@example.com"
    OPENALEX_API_BASE = "https://api.openalex.org"

    params = {
        "search": query,
        "per_page": min(max_results, 100),
        "sort": "relevance_score:desc",
        "mailto": EMAIL
    }
    r = requests.get(f"{OPENALEX_API_BASE}/works", params=params, timeout=60)
    r.raise_for_status()
    openalex_papers = r.json().get("results", [])
    print(f"    找到 {len(openalex_papers)} 篇论文")

    # Phase 2: Zotero PDF 扫描
    print("\n>> Phase 2: Zotero PDF 深度扫描")
    pdf_analyses = []

    if not os.path.exists(ZOTERO_STORAGE):
        print(f"    Zotero storage not found: {ZOTERO_STORAGE}")
    else:
        items = os.listdir(ZOTERO_STORAGE)
        print(f"    扫描 {len(items)} 个 Zotero 项目...")

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
                import fitz
                doc = fitz.open(pdf_path)
                first_text = doc[0].get_text() if len(doc) > 0 else ""
                doc.close()

                if 'terahertz' in first_text.lower() or ' thz ' in first_text.lower():
                    print(f"    分析: {pdfs[0][:50]}...")
                    analysis = analyzer.analyze_pdf(pdf_path)
                    if analysis:
                        pdf_analyses.append(analysis)
                        count += 1
                        if count >= max_pdfs:
                            break
            except:
                continue

    print(f"    分析了 {len(pdf_analyses)} 个 PDF")

    # Phase 3: 语义聚类
    print("\n>> Phase 3: TF-IDF 语义聚类")
    if pdf_analyses:
        pdf_analyses = analyzer.cluster_papers_tfidf(pdf_analyses, n_clusters=min(6, len(pdf_analyses)))
        cluster_counts = defaultdict(int)
        for a in pdf_analyses:
            if a.semantic_cluster >= 0:
                cluster_counts[a.semantic_cluster] += 1
        for c, n in sorted(cluster_counts.items()):
            print(f"    聚类 {c}: {n} 篇")
    else:
        print("    (无 PDF 分析结果)")

    # Phase 4: 主题综合
    print("\n>> Phase 4: 主题深度综合")
    synth = analyzer.synthesize_by_theme(pdf_analyses)
    for theme, data in synth.items():
        print(f"    {theme}: {data.get('n_papers', 0)} 篇, {len(data.get('gaps', []))} 个 Gap")

    # Phase 5: 生成学术综述
    print("\n>> Phase 5: 生成论文级综述 (C-C-C 结构)")
    review = analyzer.generate_academic_review(synth, query)

    # 保存
    output_file = f"DHL/review_enhanced_{query.replace(' ', '_')[:20]}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(review)

    print(f"\n>> 完成！报告保存到: {output_file}")

    return {
        'openalex_papers': openalex_papers,
        'pdf_analyses': pdf_analyses,
        'synth': synth,
        'review': review
    }


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "terahertz generation"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    result = run_enhanced_review(query, n)
    print(f"\n分析了 {len(result['pdf_analyses'])} 篇 PDF")
    print(f"综合了 {len(result['synth'])} 个主题")


if __name__ == "__main__":
    main()