#!/usr/bin/env python3
"""
Integrated Deep Paper Analysis - 整合 OpenAlex + Zotero PDF 深度分析

功能：
1. 从 OpenAlex 检索论文元数据
2. 扫描 Zotero 本地 PDF 存储
3. 使用 PyMuPDF 深度分析 PDF
4. 整合结果进行 Thematic Synthesis

路径:
- Zotero storage: E:/PostGraduate/Science_softwares/Zotero/data/storage
- Output: DHL/review_deep_*.md
"""

import os
import re
import sys
import json
import codecs
import requests
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import fitz  # PyMuPDF

if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# =============================================================================
# 配置
# =============================================================================

OPENALEX_API_BASE = "https://api.openalex.org"
EMAIL = "research@example.com"
ZOTERO_STORAGE = "E:/PostGraduate/Science_softwares/Zotero/data/storage"
OUTPUT_DIR = "DHL"

# THz 主题定义
THZ_THEMES = {
    "PCA材料": ["low-temperature grown GaAs", "LT-GaAs", "InGaAs", "ion-implanted", "carrier lifetime", "mobility"],
    "PCA结构": ["bow-tie", "dipole", "strip-line", "interdigitated", "large-area", "plasmonic", "antenna"],
    "光整流晶体": ["lithium niobate", "LiNbO3", "ZnTe", "GaSe", "DAST", "tilted pulse front", "phase matching"],
    "空气等离子体": ["air plasma", "filamentation", "two-color", "four-wave mixing", "laser-induced plasma", "terawatt"],
    "QCL激光器": ["quantum cascade", "QCL", "intersubband", "heterostructure", "room temperature"],
    "检测技术": ["electro-optic sampling", "bolometer", "pyroelectric", "time-domain", "spectroscopy"],
}


# =============================================================================
# PDF 分析
# =============================================================================

def analyze_pdf(pdf_path: str) -> Optional[Dict]:
    """深度分析单个 PDF"""
    if not os.path.exists(pdf_path):
        return None

    try:
        doc = fitz.open(pdf_path)
        all_text = ""
        for page in doc:
            all_text += page.get_text() + "\n"
        doc.close()

        # 提取各部分
        sections = extract_sections(all_text)
        intro = sections.get('introduction', '') + sections.get('abstract', '')
        method = sections.get('methods', '') + sections.get('experimental', '')
        results = sections.get('results', '') + sections.get('discussion', '')

        # 深度提取
        analysis = {
            'title': extract_title_from_text(all_text),
            'abstract': sections.get('abstract', ''),
            'sections': sections,
            'research_question': extract_rq(intro),
            'approach': extract_approach(method + intro),
            'key_findings': extract_findings(results),
            'limitations': extract_limitations(results + sections.get('conclusion', '')),
            'gap_identified': extract_gap(intro + sections.get('conclusion', '')),
            'full_text': all_text[:30000],
            'success': True
        }
        return analysis

    except Exception as e:
        return {'error': str(e), 'success': False}


def extract_title_from_text(text: str) -> str:
    """从全文提取标题"""
    lines = text.split('\n')
    for line in lines[2:20]:
        stripped = line.strip()
        if len(stripped) > 30 and len(stripped.split()) > 4 and any(c.isupper() for c in stripped):
            if not any(x in stripped.lower() for x in ['http://', 'doi:', 'figure', 'tab.', 'article']):
                return re.sub(r'\s+', ' ', stripped)[:200]
    return "Unknown"


def extract_sections(text: str) -> Dict[str, str]:
    """提取论文章节"""
    sections = {'abstract': '', 'introduction': '', 'methods': '', 'results': '', 'discussion': '', 'conclusion': ''}

    markers = [
        ('abstract', ['abstract']),
        ('introduction', ['introduction', 'background', '1 introduction']),
        ('methods', ['method', 'experimental', 'setup', 'experiment']),
        ('results', ['result', 'measurement', 'observation']),
        ('discussion', ['discussion', 'analysis']),
        ('conclusion', ['conclusion', 'summary']),
    ]

    lines = text.split('\n')
    current = None
    content = []

    for line in lines:
        lower = line.lower().strip()
        new_section = None

        for sec_name, marker_list in markers:
            if any(lower.startswith(m) for m in marker_list) or re.match(r'^\s*\d+\.\s+(?:intro|method|result|concl)', lower):
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

    return {k: v[:10000] for k, v in sections.items()}


def extract_rq(text: str) -> str:
    """提取研究问题"""
    patterns = [
        r"(?:We|Here|This paper)\s+(?:investigate|study|demonstrate|propose)\s+(?:the\s+)?([^.]+)",
        r"(?:goal|objective)\s+(?:of|is)\s*:?\s*([^.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return re.sub(r'\s+', ' ', match.group(1).strip())[:200]
    return ""


def extract_approach(text: str) -> str:
    """提取技术方法"""
    keywords = [
        'tilted pulse front', 'optical rectification', 'photoconductive', 'filamentation',
        'two-color', 'QCL', 'quantum cascade', 'LiNbO3', 'GaAs', 'ZnTe', 'GaSe', 'DAST',
        'LT-GaAs', 'electro-optic sampling', 'bolometer', 'plasmonic', 'metasurface',
    ]
    found = [kw for kw in keywords if kw.lower() in text.lower()]
    return "Methods: " + ", ".join(found[:8]) if found else ""


def extract_findings(text: str) -> List[str]:
    """提取关键发现（数值）"""
    findings = []
    patterns = [
        r'(\d+(?:\.\d+)?\s*(?:THz|GHz))\s*(?:peak|output|bandwidth|range|frequency)?',
        r'(\d+(?:\.\d+)?\s*(?:mJ|μJ))\s*(?:pulse|output|energy)?',
        r'(\d+(?:\.\d+)?%)\s*(?:efficiency|conversion)?',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            if m not in findings:
                findings.append(m)
    return findings[:8]


def extract_limitations(text: str) -> List[str]:
    """提取局限性"""
    limitations = []
    patterns = [
        r"(?:limitation|drawback)\s+(?:of|is|are)\s+([^.]+)",
        r"future\s+(?:work|research)\s+(?:should|needs)\s+([^.]+)",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            if len(m) > 30 and len(m) < 200 and m not in limitations:
                limitations.append(m.strip())
    return limitations[:3]


def extract_gap(text: str) -> str:
    """提取研究空白"""
    patterns = [
        r"(?:gap|lack|missing|unexplored)\s+(?:of|in|for)\s+([^.]+?)(?:\.|,|$)",
        r"no\s+(?:systematic\s+)?(?:study|research)\s+(?:has\s+been\s+)?(?:done|on)\s+([^.]+?)(?:\.|,|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return re.sub(r'\s+', ' ', match.group(0)[:250])
    return ""


# =============================================================================
# Zotero 扫描
# =============================================================================

def scan_zotero_pdfs() -> Dict[str, Dict]:
    """扫描 Zotero 本地 PDF 存储"""
    pdf_analyses = {}

    if not os.path.exists(ZOTERO_STORAGE):
        print(f"Zotero storage not found: {ZOTERO_STORAGE}")
        return pdf_analyses

    items = os.listdir(ZOTERO_STORAGE)
    print(f"Scanning {len(items)} items in Zotero storage...")

    for item_key in items:
        item_dir = os.path.join(ZOTERO_STORAGE, item_key)
        if not os.path.isdir(item_dir):
            continue

        pdfs = [f for f in os.listdir(item_dir) if f.endswith('.pdf')]
        if not pdfs:
            continue

        pdf_path = os.path.join(item_dir, pdfs[0])

        # 快速检查是否是 THz 相关
        try:
            doc = fitz.open(pdf_path)
            first_text = doc[0].get_text() if len(doc) > 0 else ""
            doc.close()

            if 'terahertz' in first_text.lower() or ' thz ' in first_text.lower():
                print(f"  Analyzing: {pdfs[0][:50]}...")
                analysis = analyze_pdf(pdf_path)
                if analysis and analysis.get('success'):
                    pdf_analyses[item_key] = analysis
        except:
            continue

    print(f"Found and analyzed {len(pdf_analyses)} THz-related PDFs")
    return pdf_analyses


# =============================================================================
# OpenAlex 检索
# =============================================================================

def search_openalex(query: str, max_results: int = 30) -> List[Dict]:
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
        src = loc.get("source", {})

        inv = w.get("abstract_inverted_index", {})
        abstract = ""
        if inv:
            words = []
            for word, positions in inv.items():
                for pos in positions:
                    words.append((pos, word))
            words.sort()
            abstract = " ".join([x[1] for x in words])

        paper = {
            "openalex_id": w.get("id", "").split("/")[-1] if w.get("id") else "",
            "doi": w.get("doi", ""),
            "title": w.get("title", "Untitled"),
            "authors": [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:5]],
            "year": w.get("publication_year", 0),
            "journal": src.get("display_name", "N/A"),
            "citations": w.get("cited_by_count", 0),
            "relevance": w.get("relevance_score", 0),
            "abstract": abstract,
        }
        papers.append(paper)

    return papers


def classify_paper(paper: Dict) -> List[Tuple[str, int]]:
    """分类论文到主题"""
    full_text = paper["title"].lower() + " " + paper["abstract"].lower()
    matched = []
    for theme, keywords in THZ_THEMES.items():
        score = sum(1 for kw in keywords if kw.lower() in full_text)
        if score >= 1:
            matched.append((theme, score))
    matched.sort(key=lambda x: x[1], reverse=True)
    return matched


# =============================================================================
# 主题综合
# =============================================================================

def synthesize_theme(theme: str, papers: List[Dict], pdf_analyses: Dict) -> Dict:
    """综合分析主题"""
    if not papers:
        return {}

    sorted_papers = sorted(papers, key=lambda x: x.get("citations", 0), reverse=True)

    # 提取方法和技术路线
    routes = defaultdict(list)
    all_findings = []
    all_gaps = []

    for paper in sorted_papers[:6]:
        # 尝试匹配 PDF 分析结果
        pdf_match = None
        for key, analysis in pdf_analyses.items():
            if any(author.lower() in analysis.get('title', '').lower()
                   for author in paper.get('authors', [])):
                pdf_match = analysis
                break

        if pdf_match:
            approach = pdf_match.get('approach', '')
            findings = pdf_match.get('key_findings', [])
            gap = pdf_match.get('gap_identified', '')
        else:
            approach = extract_approach(paper.get('abstract', ''))
            findings = extract_findings(paper.get('abstract', ''))
            gap = extract_gap(paper.get('abstract', ''))

        # 分类路线
        if 'LiNbO3' in approach or 'optical rectification' in approach:
            route = 'optical_rectification'
        elif 'photoconductive' in approach or 'PCA' in approach:
            route = 'PCA'
        elif 'filamentation' in approach or 'plasma' in approach:
            route = 'laser_plasma'
        elif 'QCL' in approach or 'quantum cascade' in approach:
            route = 'QCL'
        elif 'metasurface' in approach or 'plasmonic' in approach:
            route = 'metasurface'
        else:
            route = 'other'

        routes[route].append({
            'paper': paper,
            'approach': approach,
            'findings': findings
        })

        all_findings.extend(findings)
        if gap:
            all_gaps.append(gap)

    return {
        'theme': theme,
        'papers': sorted_papers[:6],
        'routes': dict(routes),
        'findings': list(set(all_findings))[:10],
        'gaps': all_gaps[:5],
        'n_papers': len(papers),
    }


def write_deep_review(query: str, papers: List[Dict], groups: Dict, synths: Dict) -> str:
    """生成深度文献综述"""
    lines = []

    lines.append(f"# 深度文献综述: {query}\n")
    lines.append(f"**生成时间**: 2026-04-29")
    lines.append(f"**论文数量**: OpenAlex {len(papers)} 篇 + Zotero PDF {sum(len(v) for v in groups.values())} 篇\n")

    # 引言 - Gap 汇总
    lines.append("## 研究空白汇总\n")
    for theme, synth in synths.items():
        gaps = synth.get('gaps', [])
        if gaps:
            lines.append(f"### {theme}")
            for gap in gaps[:2]:
                lines.append(f"- **{gap.get('type', 'Gap')}**: {gap.get('description', gap)[:150]}...")
            lines.append("")

    # 各主题深度分析
    for theme, synth in synths.items():
        lines.append(f"\n## {theme}\n")

        routes = synth.get('routes', {})
        if routes:
            lines.append("### 技术路线\n")
            for route, items in routes.items():
                lines.append(f"- **{route}** ({len(items)} 篇): {', '.join([i['approach'][:60] for i in items[:2]])}")
            lines.append("")

        # 关键发现
        findings = synth.get('findings', [])
        if findings:
            lines.append("### 关键性能指标\n")
            lines.append(f"数值范围: {', '.join(findings[:8])}")
            lines.append("")

        # Gap 分析
        gaps = synth.get('gaps', [])
        if gaps:
            lines.append("### 研究空白 (Gap Analysis)\n")
            for gap in gaps:
                lines.append(f"- **[{gap.get('type', 'Gap')}]** {gap.get('description', str(gap))[:200]}")
            lines.append("")

        # 论文列表
        lines.append("### 代表性论文\n")
        for i, p in enumerate(synth.get('papers', [])[:4], 1):
            authors = ', '.join(p.get('authors', [])[:2])
            lines.append(f"{i}. {authors} ({p.get('year', 'N/A')}) - {p.get('title', 'N/A')[:60]}... (cite: {p.get('citations', 0)})")
        lines.append("")

    # 讨论
    lines.append("\n## 讨论\n")
    lines.append("### 跨主题综合\n")

    all_routes = set()
    for synth in synths.values():
        all_routes.update(synth.get('routes', {}).keys())

    lines.append(f"识别到的技术路线: {', '.join(all_routes)}\n")

    # 核心权衡
    lines.append("\n### 核心权衡\n")
    lines.append("- **效率 vs 带宽**: 光整流方案能量高但带宽受限；等离子体方案带宽宽但能量较低")
    lines.append("- **功率 vs 便捷性**: 高功率方案通常需要复杂系统")
    lines.append("- **成熟度 vs 潜力**: 已有方案成熟但性能趋于饱和；新方案潜力大但未成熟")
    lines.append("")

    return "\n".join(lines)


# =============================================================================
# 主流程
# =============================================================================

def run_deep_review(query: str, max_results: int = 30) -> Dict:
    """运行完整深度综述流程"""
    print("=" * 60)
    print("深度文献综述生成 - OpenAlex + Zotero PDF 整合")
    print("=" * 60)

    # Phase 1: OpenAlex 检索
    print(f"\n>> Phase 1: OpenAlex 检索 '{query}'")
    papers = search_openalex(query, max_results)
    print(f"    找到 {len(papers)} 篇论文")

    # Phase 2: Zotero PDF 扫描
    print("\n>> Phase 2: Zotero PDF 深度扫描")
    pdf_analyses = scan_zotero_pdfs()
    print(f"    分析了 {len(pdf_analyses)} 个 PDF")

    # Phase 3: 分类
    print("\n>> Phase 3: 论文分类")
    groups = defaultdict(list)
    for p in papers:
        themes = classify_paper(p)
        if themes:
            groups[themes[0][0]].append(p)
        else:
            groups["其他"].append(p)

    for theme, ps in sorted(groups.items(), key=lambda x: -len(x[1])):
        print(f"    {theme}: {len(ps)} 篇")

    # Phase 4: 主题综合
    print("\n>> Phase 4: 主题深度综合")
    synths = {}
    for theme in THZ_THEMES:
        ps = groups.get(theme, [])
        if len(ps) >= 1:
            synth = synthesize_theme(theme, ps, pdf_analyses)
            synths[theme] = synth
            print(f"    {theme}: {len(ps)} 篇, {len(synth.get('routes', {}))} 条技术路线")

    # Phase 5: 生成报告
    print("\n>> Phase 5: 生成综述")
    report = write_deep_review(query, papers, groups, synths)

    # 保存
    output_file = f"{OUTPUT_DIR}/review_deep_{query.replace(' ', '_')[:20]}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n>> 完成！报告保存到: {output_file}")

    return {
        'papers': papers,
        'groups': dict(groups),
        'pdf_analyses': pdf_analyses,
        'synths': synths,
        'report': report
    }


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "terahertz generation"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    result = run_deep_review(query, n)
    print(f"\n生成了 {len(result['synths'])} 个主题的综合分析")


if __name__ == "__main__":
    main()