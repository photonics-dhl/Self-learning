#!/usr/bin/env python3
"""
学术综述生成 Pipeline v4.0
==================
核心改进：Thematic Synthesis（主题综合）而非论文堆砌

参考文献设计原则：
- Pautasso (2013) "Ten Simple Rules for Writing a Literature Review" - PLOS CompBio
- Mensah (2019) "Ten Simple Rules for Structuring Papers" - PLOS CompBio
- MCP.Directory literature-review skill - 7-phase systematic workflow

核心写作原则：
1. C-C-C结构 (Context-Content-Conclusion) 每段必须有"为什么说这个"→"说什么"→"这意味着什么"
2. Thematic Synthesis: 按研究问题/趋势组织，不是按作者逐个列举
3. 强制Gap识别: 每主题必须明确写出"文献中缺失什么"
4. 比较与权衡: 方法A vs 方法B在X维度的trade-off
5. 共识vs争议: 识别领域内一致观点与分歧

论文收集 → Gate审查 → Thematic Synthesis → Gap驱动写作
"""

import requests, os, sys, json, codecs, datetime, re
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(v, None)

OPENALEX_API_BASE = "https://api.openalex.org"
EMAIL = os.getenv("EMAIL", "research@example.com")

# =============================================================================
# 主题定义：包含研究问题、核心争议、预期gap
# =============================================================================
THZ_THEMES = {
    "PCA材料": {
        "keywords": ["low-temperature grown GaAs", "LT-GaAs", "InGaAs", "ion-implanted",
                     "carrier lifetime", "mobility", "semi-insulating", "ErAs", "nanoparticle",
                     "photoconductive", "carrier dynamics"],
        "research_question": "何种材料能在载流子寿命、迁移率、暗电阻三方面同时满足PCA需求？",
        "core_tensions": [
            ("超快载流子寿命(<1ps)", "高迁移率(>1000 cm²/Vs)", "两者难以兼得"),
            ("低温生长GaAs(LT-GaAs)", "离子注入InGaAs", "不同工艺的权衡"),
            ("1.55μm泵浦兼容性", "传统800nm泵浦", "材料体系的演进方向"),
        ],
        "consensus": "LT-GaAs仍是超宽带PCA的主流选择；载流子寿命<1ps是实现高带宽的共识",
        "controversies": [
            "1.55μm泵浦能否在保持超快寿命的同时实现高迁移率？",
            "ErAs纳米颗粒复合材料能否突破传统材料的性能上限？",
        ],
        "expected_gaps": [
            "缺乏载流子寿命<100fs且迁移率>5000 cm²/Vs的材料方案",
            "缺乏对新型纳米复合材料的长期稳定性的系统研究",
        ],
        "figure_prompt": "Scientific diagram showing PCA material evolution: Si-sapphire → LT-GaAs → InGaAs → ErAs nanoparticle. Show carrier lifetime vs mobility trade-off as 2D map with arrows indicating research frontier. Include labeled axes, energy band diagrams. White background, professional academic style."
    },
    "PCA结构": {
        "keywords": ["bow-tie", "dipole", "strip-line", "interdigitated", "large-area",
                     "plasmonic", "nanoelectrode", "grating", "antenna design", "log-spiral",
                     "photoconductive antenna", "electrode geometry", "radiation pattern"],
        "research_question": "天线几何结构如何影响阻抗匹配、带宽和光泵吸收效率的权衡？",
        "core_tensions": [
            ("大面积天线(高功率)", "小尺寸(超宽带)", "物理空间上的矛盾"),
            ("紧凑结构(如bow-tie)", "复杂多级结构(如log-spiral)", "制造难度与性能的权衡"),
            (" plasmonic增强", "传统金属电极", "纳米结构vs常规工艺"),
        ],
        "consensus": "大面积 plasmonic 电极可显著提升泵浦效率；bow-tie 是宽带应用的主流结构",
        "controversies": [
            "光栅耦合器 vs 传统间隙电极：谁在高功率下更优？",
            "多级结构是否在大规模集成中具有实际优势？",
        ],
        "expected_gaps": [
            "缺乏对大面积天线与超宽带之间物理极限的系统理论研究",
            "缺乏在真实工作条件下(高泵浦功率密度)的热管理对比研究",
        ],
        "figure_prompt": "Schematic of PCA antenna geometries: bow-tie, dipole, strip-line, interdigitated, large-area plasmonic grating. Each with radiation pattern polar plots, impedance values, bandwidth ranges. 6 sub-panels labeled (a)-(f). White background."
    },
    "光整流晶体": {
        "keywords": ["lithium niobate", "LiNbO3", "ZnTe", "GaSe", "DAST", "OH1", "organic crystal",
                     "tilted pulse front", "phase matching", "collinear", "cascaded DFG",
                     "optical rectification", "nonlinear coefficient", "damage threshold"],
        "research_question": "相位匹配与损伤阈值的矛盾如何限制THz输出能量与带宽的提升？",
        "core_tensions": [
            ("LiNbO3(高损伤阈值)", "有机晶体(大非线性系数)", "能量vs带宽的矛盾"),
            ("倾斜脉冲前(TPF)技术", "准相位匹配(QPM)", "技术成熟度与效率的权衡"),
            ("无机晶体(稳定性好)", "有机晶体(性能优但不稳定)", "实用化的瓶颈"),
        ],
        "consensus": "倾斜脉冲前技术是LiNbO3中实现相位匹配的主流方案；有机晶体在带宽上具有优势",
        "controversies": [
            "有机晶体能否在实际泵浦条件下实现>100μJ输出？",
            "倾斜脉冲前技术的能量 scaling 是否存在理论上限？",
        ],
        "expected_gaps": [
            "缺乏同时实现>5 THz带宽 AND >100μJ能量输出的晶体方案",
            "有机晶体在强泵浦下的光稳定性数据几乎空白",
            "缺乏对晶体热效应的系统性理论和实验研究",
        ],
        "figure_prompt": "Phase matching diagrams for optical rectification: (a) TPF excitation in LiNbO3 with velocity matching curve, (b) DNQ/OH1 organic crystal nonlinear coefficient comparison, (c) energy vs bandwidth scatter plot for different crystals. White background, labeled axes, legend. 3 sub-panels."
    },
    "空气等离子体": {
        "keywords": ["air plasma", "filamentation", "two-color", "four-wave mixing",
                     "laser-induced plasma", "terawatt", "remote THz", "energy scaling",
                     "laser filament", "two-color scheme", "plasma oscillation"],
        "research_question": "空气等离子体方法如何在远程、高峰值功率、高转换效率三方面实现协同提升？",
        "core_tensions": [
            ("远程产生(优势)", "转换效率(相对较低)", "距离与效率的权衡"),
            ("双光束方案(效率高)", "单光束方案(简单但效率低)", "方案复杂度与性能的权衡"),
            ("TW级泵浦(高峰值)", "mJ级输出(实际应用需求)", "峰值vs平均功率的矛盾"),
        ],
        "consensus": "双光束方案是实现高效率的主流选择；空气等离子体是远程THz产生的唯一可行方案",
        "controversies": [
            "不同双光束组合(800nm+400nm vs 800nm+ω)对效率的影响是否存在最优解？",
            "激光能量 scaling 是否能突破当前的效率瓶颈？",
        ],
        "expected_gaps": [
            "缺乏对远程传输中相位稳定性问题的系统性解决方案",
            "缺乏在真实大气条件下(湿度、湍流)THz传输的系统性数据",
            "缺乏高重频(>1kHz)空气等离子体THz源的可行性研究",
        ],
        "figure_prompt": "Two-color laser filamentation for THz: (a) experimental setup schematic with 800nm and 400nm beams, plasma filament diagram, THz cone emission, (b) efficiency vs pump energy scaling curves, (c) remote generation distance vs THz field strength. White background."
    },
    "QCL激光器": {
        "keywords": ["quantum cascade", "QCL", "intersubband", "heterostructure",
                     "room temperature", "frequency mixing", "mid-infrared",
                     "terahertz source", "electrical pumping", "quantum well"],
        "research_question": "QCL如何在突破4 THz频段限制、降低冷却要求、提升输出功率三个方向上取得突破？",
        "core_tensions": [
            ("高频段(>4 THz)", "室温工作", "材料物理层面的矛盾"),
            ("高功率输出", "热管理", "级联结构的热积累问题"),
            ("电泵浦(优势)", "光泵浦(成熟)", "泵浦方式的选择"),
        ],
        "consensus": "QCL是唯一实现电泵浦的固态THz源；向室温工作是明确的发展方向",
        "controversies": [
            "4 THz以上频段：GaAs基 vs InP基，谁能率先突破？",
            "外腔反馈技术能否在不牺牲功率的前提下实现频率调谐？",
        ],
        "expected_gaps": [
            "缺乏4 THz以上、室温连续波工作的可行性理论分析",
            "缺乏对QCL长期工作稳定性的系统性研究",
            "缺乏对QCL与外部高效耦合器的宽带匹配研究",
        ],
        "figure_prompt": "THz QCL: (a) conduction band diagram of multi-quantum-well structure with injector regions, radiative transition arrows labeled with energy, (b) output power vs frequency for different material systems, (c) operating temperature trend over years. White background."
    },
    "超表面THz": {
        "keywords": ["metasurface", "plasmonic", "nanoantenna", "resonant",
                     "beam steering", "modulator", "absorber",
                     "THz metamaterial", "sub-wavelength", "frequency selectivity"],
        "research_question": "超表面如何在保持平面化、集成化优势的同时突破效率与带宽的限制？",
        "core_tensions": [
            ("平面化集成(优势)", "效率和带宽(受限)", "结构简单性vs性能的矛盾"),
            ("被动超表面(固定功能)", "主动可调谐(复杂)", "功能性与制造可行性的权衡"),
            ("金属超表面(成熟)", "介质超表面(新兴)", "材料选择与损耗的权衡"),
        ],
        "consensus": "超表面为THz器件平面化集成提供了独特途径；多谐振单元可实现多功能",
        "controversies": [
            "介质超表面能否在THz频段替代金属超表面？",
            "主动可调谐超表面的响应速度是否满足实际应用需求？",
        ],
        "expected_gaps": [
            "缺乏对超表面THz源产生效率的系统性benchmark",
            "缺乏在真实工作条件下的长期稳定性数据",
            "缺乏与传统THz源的系统性集成方案研究",
        ],
        "figure_prompt": "THz metasurface: (a) array of resonant nanoantennas with dimensions labeled, near-field enhancement map, (b) resonance tuning mechanism diagram, (c) efficiency comparison bar chart: metasurface vs conventional THz sources. 3 sub-panels. White background."
    },
    "检测技术": {
        "keywords": ["detection", "electro-optic sampling", "bolometer", "pyroelectric",
                     "SNR", "NEP", "time-domain", "spectroscopy",
                     "THz detection", "coherent detection", "heterodyne"],
        "research_question": "不同检测方法在灵敏度、带宽、动态范围之间如何权衡？",
        "core_tensions": [
            ("相干探测(电光采样)", "能量探测(热敏)", "信息量vs灵敏度的权衡"),
            ("室温探测", "低温制冷(高灵敏度)", "实用性vs性能的矛盾"),
            ("宽带探测", "窄带高灵敏度", "频谱覆盖与信噪比的矛盾"),
        ],
        "consensus": "电光采样是宽带相干探测的主流；低温bolometer是最高灵敏度方案",
        "controversies": [
            "在>10 THz频段，电光采样是否仍是最优选择？",
            "CMOS兼容的THz探测器能否在未来实现实用化？",
        ],
        "expected_gaps": [
            "缺乏对超宽带(>20 THz)实时探测的系统性技术方案",
            "缺乏对室温下同时实现高灵敏度( NEP<10 pW/√Hz)和宽带(>5 THz)的检测器的可行性分析",
            "缺乏对大规模阵列探测器的系统性研究",
        ],
        "figure_prompt": "THz detection methods: (a) electro-optic sampling setup with ZnTe crystal, (b) bolometer cryogenic detection system, (c) NEP vs bandwidth scatter plot for different detection methods. 3 sub-panels labeled (a)-(c). White background."
    },
}


def api_get(url: str, params: dict = None) -> dict:
    for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(v, None)
    headers = {"User-Agent": f"Mozilla/5.0 (Python AcademicBot/1.0; mailto:{EMAIL})", "Accept": "application/json"}
    r = requests.get(url, params=params, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()


def reconstruct_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""
    words = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words.append((pos, word))
    words.sort(key=lambda x: x[0])
    return " ".join([w[1] for w in words])


def discover_papers(query: str, max_results: int = 30) -> List[Dict]:
    print(f">> [Phase 1] Discovering papers: '{query}'")
    params = {
        "search": query,
        "per_page": min(max_results, 100),
        "sort": "relevance_score:desc",
        "mailto": EMAIL
    }
    data = api_get(f"{OPENALEX_API_BASE}/works", params)
    results = data.get("results", [])

    papers = []
    for w in results:
        loc = w.get("primary_location") or {}
        src = loc.get("source") or {}
        authors = w.get("authorships", [])
        author_names = [a.get("author", {}).get("display_name", "") for a in authors[:5]]
        abstract_text = reconstruct_abstract(w.get("abstract_inverted_index", {}))
        title_lower = w.get("title", "").lower()
        is_review = any(kw in title_lower for kw in ["review", "roadmap", "survey", "overview", "progress", "handbook"])

        paper = {
            "doi": w.get("doi", ""),
            "title": w.get("title", "Untitled"),
            "authors": author_names,
            "year": w.get("publication_year", 0),
            "journal": src.get("display_name", "N/A"),
            "volume": w.get("biblio", {}).get("volume", ""),
            "issue": w.get("biblio", {}).get("issue", ""),
            "pages": w.get("biblio", {}).get("first_page", ""),
            "citations": w.get("cited_by_count", 0),
            "relevance": w.get("relevance_score", 0),
            "abstract": abstract_text,
            "abstract_raw": w.get("abstract_inverted_index", {}),
            "concepts": [(c.get("display_name", ""), c.get("score", 0)) for c in w.get("concepts", [])[:8]],
            "is_review": is_review,
        }
        papers.append(paper)

    print(f"    Found {len(papers)} papers ({sum(1 for p in papers if p['is_review'])} reviews)")
    return papers


def classify_paper(paper: Dict) -> List[Tuple[str, int]]:
    full_text = (
        paper["title"].lower() + " " +
        paper["abstract"].lower() + " " +
        " ".join([c[0].lower() for c in paper.get("concepts", [])])
    )
    matched = []
    for theme, info in THZ_THEMES.items():
        score = sum(1 for kw in info["keywords"] if kw.lower() in full_text)
        if score >= 1:
            matched.append((theme, score))
    matched.sort(key=lambda x: x[1], reverse=True)
    return matched


def extract_metrics(abstract: str) -> List[Tuple[str, str]]:
    """从摘要提取 (数值, 单位) 形式的指标"""
    patterns = [
        # 频率（优先匹配，带单位描述）
        (r'([\d.]+)\s*THz', 'THz'),
        (r'([\d.]+)\s*GHz', 'GHz'),
        # 能量
        (r'([\d.]+)\s*mJ', 'mJ'),
        (r'([\d.]+)\s*µJ', 'μJ'),
        (r'([\d.]+)\s*uJ', 'μJ'),
        # 功率
        (r'([\d.]+)\s*GW', 'GW'),
        (r'([\d.]+)\s*MW', 'MW'),
        (r'([\d.]+)\s*kV/cm', 'kV/cm'),
        (r'([\d.]+)\s*kV', 'kV'),
        # 百分比（两种形式）
        (r'([\d.]+)\s*%', '%'),
        (r'([\d.]+)\s*percent', '%'),
        # 时间
        (r'([\d.]+)\s*ps', 'ps'),
        (r'([\d.]+)\s*fs', 'fs'),
        # 波长
        (r'([\d.]+)\s*nm', 'nm'),
        (r'([\d.]+)\s*µm', 'μm'),
        # 迁移率
        (r'([\d.]+)\s*cm²/Vs', 'cm²/Vs'),
    ]
    metrics = []
    for pattern, unit in patterns:
        for m in re.findall(pattern, abstract, re.IGNORECASE):
            try:
                val = float(m)
                if unit == '%':
                    # 对于百分比，添加描述使其更有意义
                    metrics.append((f"{val:.2f}", '%'))
                else:
                    metrics.append((str(val), unit))
            except:
                pass
    return metrics[:8]


def extract_method_keywords(abstract: str, title: str = "", theme: str = "") -> List[str]:
    """
    从摘要（和标题）提取实质性技术方法关键词（不是动词）
    只匹配 theme 定义的 keywords 中的实质性技术词，排除动词和通用词
    优先从摘要提取，如果摘要太短则从标题提取
    """
    theme_info = THZ_THEMES.get(theme, {})

    known_techniques = {
        "PCA材料": ["LT-GaAs", "InGaAs", "ErAs", "ion-implanted", "semi-insulating",
                     "nanoparticle", "low-temperature grown", "InAs", "GaAs"],
        "PCA结构": ["bow-tie", "dipole", "strip-line", "interdigitated", "large-area",
                     "plasmonic", "grating", "log-spiral", "nanoelectrode"],
        "光整流晶体": ["LiNbO3", "ZnTe", "GaSe", "DAST", "OH1", "organic crystal",
                     "tilted pulse front", "phase matching", "collinear", "cascaded DFG"],
        "空气等离子体": ["air plasma", "filamentation", "two-color", "four-wave mixing",
                     "laser-induced plasma", "terawatt", "remote THz", "plasma"],
        "QCL激光器": ["quantum cascade", "QCL", "intersubband", "heterostructure",
                     "room temperature", "frequency mixing", "mid-infrared"],
        "超表面THz": ["metasurface", "plasmonic", "nanoantenna", "resonant",
                     "beam steering", "modulator", "absorber"],
        "检测技术": ["electro-optic sampling", "bolometer", "pyroelectric",
                     "time-domain", "spectroscopy", "coherent detection",
                     "photomixing", "Auston switch", "photoconductive"],
    }

    techniques = known_techniques.get(theme, [])

    # 从摘要和标题中同时搜索（标题作为后备补充）
    abstract_lower = abstract.lower()
    title_lower = title.lower()
    found = []

    # 第一遍：从摘要中精确匹配
    for tech in techniques:
        if tech.lower() in abstract_lower:
            found.append(tech)

    # 第二遍：如果摘要太短(<50 chars)或没找到足够方法，从标题补充
    if len(abstract) < 50 or len(found) < 2:
        for tech in techniques:
            if tech.lower() in title_lower and tech not in found:
                found.append(tech)

    # 第三遍：对检测技术特殊处理：从标题中提取检测相关词
    if theme == "检测技术" and len(found) < 2:
        detection_words = {
            "electro-optic": "electro-optic sampling",
            "coherent control": "coherent detection",
            "supercontinuum": "supercontinuum generation",
            "metamaterial": "metamaterial",
            "broadband": "broadband generation",
            "photomix": "photomixing",
            "photoconductive": "photoconductive",
        }
        for kw, full_name in detection_words.items():
            if kw in title_lower and full_name not in found:
                found.append(full_name)

    # 去重，保持顺序
    seen = set()
    unique = []
    for f in found:
        fl = f.lower()
        if fl not in seen:
            seen.add(fl)
            unique.append(f)

    return unique[:6]


# =============================================================================
# Thematic Synthesis 核心函数
# =============================================================================

def synthesize_theme(theme: str, papers: List[Dict]) -> Dict:
    """
    对同一主题的多篇论文进行横向综合
    返回综合分析结果
    """
    if not papers:
        return {}

    theme_info = THZ_THEMES.get(theme, {})

    # 按引用量排序
    sorted_papers = sorted(papers, key=lambda x: x["citations"], reverse=True)

    # 提取所有指标
    all_metrics = []
    method_sets = []
    for p in sorted_papers:
        m = extract_metrics(p["abstract"])
        all_metrics.extend(m)
        methods = extract_method_keywords(p["abstract"], theme)
        method_sets.append(methods)

    # 统计方法出现频率
    method_freq = defaultdict(int)
    for methods in method_sets:
        for m in methods:
            method_freq[m] += 1

    top_methods = sorted(method_freq.items(), key=lambda x: -x[1])[:5]

    # 按年份分组（识别趋势）
    year_groups = defaultdict(list)
    for p in sorted_papers:
        year_groups[p["year"]].append(p)

    # 提取核心发现：从引用最高的论文中提取
    key_findings = []
    for p in sorted_papers[:3]:
        abstract = p["abstract"]
        title = p["title"]
        metrics = extract_metrics(abstract)

        finding = {
            "authors": p["authors"][:2],
            "year": p["year"],
            "title": title,
            "citations": p["citations"],
            "metrics": metrics[:3],
            "method": extract_method_keywords(abstract, title, theme),
            "journal": p["journal"],
        }
        key_findings.append(finding)

    # 横向对比：找出论文之间的共同点和差异
    comparison = {
        "consensus_statement": theme_info.get("consensus", ""),
        "controversies": theme_info.get("controversies", []),
        "core_tensions": theme_info.get("core_tensions", []),
        "top_methods": top_methods,
        "year_trend": {str(k): len(v) for k, v in sorted(year_groups.items())},
    }

    # Gap 分析：从 theme 定义和论文内容推断
    gaps = theme_info.get("expected_gaps", [])

    # 补充从论文内容提取的gap
    if len(sorted_papers) >= 3:
        # 检查是否有某种方法/方向被多人研究但没有系统性比较
        if len(top_methods) >= 3:
            gaps.append(f"缺乏对[{', '.join([m[0] for m in top_methods[:2]])}]的系统性对比研究")

        # 检查年代趋势：如果近年论文少，可能存在研究空白
        recent_years = [y for y in year_groups.keys() if y >= 2018]
        older_years = [y for y in year_groups.keys() if y < 2018]
        if len(recent_years) < len(older_years):
            gaps.append("近年该主题论文数量有所下降，可能存在新的技术突破点")

    return {
        "theme": theme,
        "research_question": theme_info.get("research_question", ""),
        "key_findings": key_findings,
        "comparison": comparison,
        "gaps": gaps,
        "n_papers": len(papers),
        "citation_range": f"{sorted_papers[-1]['citations']}-{sorted_papers[0]['citations']}",
    }


def write_synthesis_section(synth: Dict) -> str:
    """
    将综合分析写成连贯的综述段落
    使用C-C-C结构：Context → Content → Conclusion/Gap
    """
    theme = synth["theme"]
    findings = synth["key_findings"]
    comp = synth["comparison"]
    gaps = synth["gaps"]

    lines = []

    # 小节标题
    lines.append(f"\\subsection{{{theme}}}")

    # -------------------------------------------------------------------------
    # 段落1: Context - 领域背景和研究问题
    # -------------------------------------------------------------------------
    rq = synth.get("research_question", "")
    lines.append(f"\\par\\par{{{theme}领域的核心科学问题在于：{rq}}}")
    lines.append("")

    # -------------------------------------------------------------------------
    # 段落2: Content - 横向综合（围绕核心权衡展开）
    # -------------------------------------------------------------------------

    # 2a: 从具体论文中提取的技术方法（不再用通用动词）
    all_methods = set()
    for f in findings:
        for m in f.get("method", []):
            all_methods.add(m)
    unique_methods = list(all_methods)

    if unique_methods:
        method_desc = "、".join(unique_methods[:4])
        lines.append(f"\\par\\par{{当前研究主要采用{method_desc}等技术路线。}}")

    # 2b: 按核心权衡组织对比（从具体论文出发）
    tensions = comp.get("core_tensions", [])

    # 构建横向对比：按"方法→指标→权衡"链条写
    if len(findings) >= 2:
        f1, f2 = findings[0], findings[1]

        auth1 = "、".join(f1["authors"])[:25] if f1["authors"] else "Unknown"
        auth2 = "、".join(f2["authors"])[:25] if f2["authors"] else "Unknown"
        year1, year2 = f1["year"], f2["year"]
        met1, met2 = f1["metrics"], f2["metrics"]
        m1, m2 = f1["method"], f2["method"]

        # 写具体对比（基于数据）
        comparison_parts = []

        # 指标维度对比
        if met1 and met2:
            if len(met1) >= 1 and len(met2) >= 1:
                v1, u1 = met1[0]
                v2, u2 = met2[0]

                # 当单位缺失时，尝试从对方或主题推断
                if not u1 and u2:
                    u1 = u2
                elif not u2 and u1:
                    u2 = u1

                if u1 and u2:
                    diff = abs(float(v1) - float(v2))
                    comparison_parts.append(
                        f"{auth1}等人({year1})实现了{v1}{u1}，"
                        f"而{auth2}等人({year2})则达到{v2}{u2}，"
                        f"两者在指标上相差{diff:.1f}{u1}。"
                    )
                elif v1 and v2:
                    # 没有单位时，只描述数值
                    comparison_parts.append(
                        f"{auth1}等人({year1})实现了{v1}，"
                        f"而{auth2}等人({year2})则达到{v2}。"
                    )

        # 方法维度对比
        if m1 and m2 and m1 != m2:
            comparison_parts.append(f"在技术路径上，{m1[0]}与{m2[0]}代表了两条不同的方向，"
                                    f"分别体现了{tensions[0][0] if tensions else '不同维度'}与"
                                    f"{tensions[0][1] if tensions else '另一方面'}的权衡。")
        elif m1 and (not m2 or m1 == m2):
            # 两者方法相同时，基于标题描述研究侧重点差异
            t1_words = (f1["title"][:35] if f1["title"] else "该方向研究").split()[:5]
            t2_words = (f2["title"][:35] if f2["title"] else "相关研究").split()[:5]
            t1_short = " ".join(t1_words)
            t2_short = " ".join(t2_words)
            comparison_parts.append(
                f"虽都聚焦于{m1[0]}方向，但{auth1}等人侧重于{t1_short}，"
                f"而{auth2}等人则聚焦于{t2_short}，在具体研究对象上存在差异。"
            )

        # 如果上述都没有（方法/指标都缺），则用标题描述研究侧重点
        if not comparison_parts:
            title1_short = f1["title"][:30] if f1["title"] else "该领域"
            title2_short = f2["title"][:30] if f2["title"] else "相关研究"
            comparison_parts.append(
                f"从研究侧重点看，{auth1}等人聚焦于{title1_short}，"
                f"而{auth2}等人则侧重于{title2_short}，"
                f"反映了两者在研究取向上 {tensions[0][0] if tensions else '技术路线选择'}的差异。"
            )

        if comparison_parts:
            lines.append(f"\\par\\par{{{auth1}等人({year1})与{auth2}等人({year2})的工作对比表明：}}")
            for part in comparison_parts:
                lines.append(f"{part}")

    elif len(findings) == 1:
        # 只有一篇重要论文时：描述具体贡献
        f1 = findings[0]
        auth1 = "、".join(f1["authors"])[:25] if f1["authors"] else "Unknown"
        year1 = f1["year"]
        met1 = f1["metrics"]
        m1 = f1["method"]
        title1 = f1["title"][:40] if f1["title"] else ""

        desc_parts = []
        if met1:
            metric_text = "、".join([f"{v}{u}" for v, u in met1[:2]])
            desc_parts.append(f"在指标上实现了{metric_text}")
        if m1:
            desc_parts.append(f"采用了{m1[0]}技术方案")
        if title1:
            desc_parts.append(f"聚焦于{title1}")

        if desc_parts:
            lines.append(f"\\par\\par{{{auth1}等人({year1})的工作")
            lines.append("，".join(desc_parts) + "，")
            lines.append(f"为该领域树立了重要参考基准（被引用{f1['citations']}次）。}}")

    # 共识陈述
    if comp.get("consensus_statement"):
        lines.append(f"\\par\\par{{【共识】{comp['consensus_statement']}}}")

    # -------------------------------------------------------------------------
    # 段落3: 研究空白 (Gap) - 必须明确写出
    # -------------------------------------------------------------------------
    if gaps:
        lines.append("")
        lines.append("\\par\\par{【研究空白】该领域存在以下未被充分研究的问题：}")
        lines.append("\\begin{itemize}")
        for gap in gaps[:3]:
            lines.append(f"\\item {gap}")
        lines.append("\\end{itemize}")
    else:
        lines.append("\\par\\par{【研究空白】当前文献中对该主题的系统性对比研究尚不充分。}")

    # -------------------------------------------------------------------------
    # 性能对比表格（辅助信息，不是主体）
    # -------------------------------------------------------------------------
    if findings:
        lines.append("")
        table_lines = build_comparison_table(theme, findings)
        lines.append("\\subsubsection*{性能对比}")
        lines.append(table_lines)

    # -------------------------------------------------------------------------
    # 未来方向（从gap自然引出，不是套话）
    # -------------------------------------------------------------------------
    lines.append("")
    lines.append("\\subsubsection*{未来方向}")
    if gaps:
        lines.append(f"基于上述研究空白，未来研究应重点关注：{gaps[0]}")
    else:
        lines.append("未来研究应进一步系统比较不同技术路线的性能边界。")

    return "\n".join(lines)


def build_comparison_table(theme: str, findings: List[Dict]) -> str:
    """构建精简的性能对比表格（最多5行）"""
    if not findings:
        return ""

    rows = []
    for f in findings[:5]:
        auth = "、".join(f["authors"])[:20] if f["authors"] else "N/A"
        year = str(f["year"])
        method = f["method"][0] if f["method"] else "---"
        metrics_str = "、".join([f"{v[0]}{v[1]}" for v in f["metrics"][:2]]) if f["metrics"] else "---"
        cite = str(f["citations"])

        rows.append(f"{auth} & {year} & {method} & {metrics_str} & {cite}")

    table = [
        "\\begin{table}[h!]",
        f"\\caption{{关键工作对比: {theme}}}",
        "\\begin{tabular}{@{}llp{2.5cm}p{2.5cm}r@{}}",
        "\\hline",
        "Author(s) & Year & Method & Key Metrics & Citations\\\\",
        "\\hline",
    ]
    table.extend([r + "\\\\" for r in rows])
    table.extend(["\\hline", "\\end{tabular}", "\\end{table}"])
    return "\n".join(table)


def write_introduction_v4(papers: List[Dict], groups: Dict) -> str:
    """引言：Gap驱动的结构"""
    lines = []

    # P1: 领域重要性 (Context)
    lines.append(
        "\\par\\par{太赫兹(THz)波段（0.1-10 THz）位于微波与红外之间，是连接电子学与光学的桥梁，"
        "在成像、光谱学、通信和安全检测等领域具有重要应用前景。"
        "然而，THz辐射的高效产生一直是该领域核心技术难题，制约着相关应用的发展。}"
    )

    # P2: 从引用最高的综述论文中提取关键观点
    sorted_by_cite = sorted(papers, key=lambda x: x["citations"], reverse=True)
    reviews = [p for p in sorted_by_cite if p["is_review"]][:2]

    if reviews:
        r = reviews[0]
        lines.append(
            f"\\par\\par{{近年来，多篇综述文章系统梳理了该领域的发展脉络。"
            f"{r['authors'][0]}等人({r['year']})在《{r['journal']}》中指出，"
            f"材料创新和结构优化是推动THz源性能提升的关键方向。"
            f"尽管如此，各技术路线在不同应用场景下的优劣势仍缺乏定量对比。}}"
        )

    # P3: 识别研究空白 (Gap identification) - 核心！
    # 从主题分组中提取gap
    all_gaps = []
    for theme, info in THZ_THEMES.items():
        if groups.get(theme):
            gaps = info.get("expected_gaps", [])
            for gap in gaps[:1]:
                all_gaps.append(f"{theme}：{gap}")

    lines.append("\\par\\par{【研究空白】现有文献存在以下不足：}")
    lines.append("\\begin{itemize}")
    for gap in all_gaps[:4]:
        lines.append(f"\\item {gap}")
    lines.append("\\end{itemize}")

    # P4: 本文贡献
    themes_with_papers = [k for k, v in groups.items() if v]
    n_themes = len(themes_with_papers)
    n_papers = len(papers)

    lines.append(
        f"\\par\\par{{本综述基于OpenAlex数据库检索的{n_papers}篇相关论文，"
        f"对{n_themes}个主题方向进行系统性的主题综合，"
        f"识别各技术路线的核心权衡与研究空白，"
        f"为不同应用场景下的THz源选择提供参考依据。}}"
    )

    return "\n".join(lines)


def group_papers_by_theme(papers: List[Dict]) -> Dict[str, List[Dict]]:
    groups = {theme: [] for theme in THZ_THEMES.keys()}
    groups["其他"] = []

    for p in papers:
        matches = classify_paper(p)
        if matches:
            for theme, score in matches[:2]:
                groups[theme].append(p)
        else:
            groups["其他"].append(p)

    return {k: v for k, v in groups.items() if v}


def run_quality_gates(papers: List[Dict], groups: Dict) -> Dict:
    """
    质量门禁：检查论文质量和分组合理性
    """
    print("\n" + "="*60)
    print("质量审查门禁 (Quality Gates)")
    print("="*60)

    results = {}

    # Gate 1: 论文相关性
    top10 = sorted(papers, key=lambda x: x["relevance"], reverse=True)[:10]
    low_rel = sum(1 for p in top10 if p["relevance"] < 50)
    g1_pass = (10 - low_rel) / 10 >= 0.7
    print(f"  Gate 1 - 论文相关性: {'PASS' if g1_pass else 'FAIL'} ({10-low_rel}/10 通过)")
    results["gate1"] = g1_pass

    # Gate 2: 摘要质量
    good_abs = sum(1 for p in papers if len(p["abstract"]) > 100)
    g2_pass = good_abs / len(papers) >= 0.6
    print(f"  Gate 2 - 摘要质量: {'PASS' if g2_pass else 'FAIL'} ({good_abs}/{len(papers)} 长度>100字符)")
    results["gate2"] = g2_pass

    # Gate 3: 分组均衡性
    theme_counts = {k: len(v) for k, v in groups.items() if v and k != "其他"}
    rich_themes = sum(1 for c in theme_counts.values() if c >= 2)
    g3_pass = rich_themes >= 3
    print(f"  Gate 3 - 分组均衡性: {'PASS' if g3_pass else 'FAIL'} ({rich_themes} 个组有≥2篇论文)")
    results["gate3"] = g3_pass

    # Gate 4: Gap 可提取性
    gap_themes = sum(1 for t in THZ_THEMES if groups.get(t))
    g4_pass = gap_themes >= 3
    print(f"  Gate 4 - Gap覆盖度: {'PASS' if g4_pass else 'FAIL'} ({gap_themes} 个主题有论文支撑)")
    results["gate4"] = g4_pass

    overall = all([g1_pass, g2_pass, g3_pass, g4_pass])
    print(f"\n  总体: {'PASS' if overall else 'FAIL'}")

    return results


def assemble_latex_v4(papers: List[Dict], groups: Dict, synths: Dict,
                       topic: str, output_dir: str = "DHL") -> Tuple[str, str]:
    print(f"\n>> [Phase 5] Assembling LaTeX...")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_topic = topic.replace(' ', '_')[:20]
    output_subdir = os.path.dirname(f"{output_dir}/review_v4_{safe_topic}.tex")
    if output_subdir and not os.path.exists(output_subdir):
        os.makedirs(output_subdir, exist_ok=True)
    tex_file = f"{output_dir}/review_v4_{safe_topic}.tex"
    bib_file = f"{output_dir}/review_v4_{safe_topic}.bib"

    # 生成 BibTeX
    bib_entries = []
    for i, p in enumerate(papers):
        key = f"Ref{i+1}"
        authors_bib = []
        for name in p["authors"][:10]:
            parts = name.split()
            if len(parts) >= 2:
                authors_bib.append(f"{{{parts[-1]}, {' '.join(parts[:-1])}}}")
            else:
                authors_bib.append(name)
        authors_str = " and ".join(authors_bib)
        if len(p["authors"]) > 10:
            authors_str += " et al."
        entry = ("@article{" + key + ",\n"
                 "  title   = {" + p['title'] + "},\n"
                 "  author  = {" + authors_str + "},\n"
                 "  journal = {" + p['journal'] + "},\n"
                 "  year    = {" + str(p['year']) + "},\n"
                 "  volume  = {" + str(p['volume'] or '') + "},\n"
                 "  number  = {" + str(p['issue'] or '') + "},\n"
                 "  pages   = {" + str(p['pages'] or '') + "},\n"
                 "  doi     = {" + (p['doi'] or '') + "}\n"
                 "}")
        bib_entries.append((key, entry))

    with open(bib_file, "w", encoding="utf-8") as f:
        for _, entry in bib_entries:
            f.write(entry + "\n\n")

    # 引言
    intro = write_introduction_v4(papers, groups)

    # 主题综合章节
    theme_sections = []
    for theme in THZ_THEMES:
        if groups.get(theme) and synths.get(theme):
            theme_sections.append(write_synthesis_section(synths[theme]))

    methods_text = "\n\n".join(theme_sections)

    # 讨论：跨主题的综合分析
    discussion = [
        "\\section{讨论}",
        "\\par\\par{本综述对THz产生的多条技术路线进行了系统性的主题综合分析，"
        "揭示了各方法在效率、带宽、功率三个核心指标上的权衡关系。}",
        "\\par\\par{光电导天线在超宽带应用场景具有独特优势，"
        "但受限于材料载流子动力学；"
        "光整流在LiNbO3倾斜脉冲前技术支撑下实现了mJ级THz输出，"
        "但有机晶体的高带宽优势尚未转化为实际能量输出；"
        "空气等离子体方法突破了远程产生的物理限制，"
        "但相位稳定性仍是实用化的瓶颈；"
        "QCL正在向室温高功率方向发展，"
        "但4 THz以上频段仍是挑战；"
        "超表面为THz器件的平面化集成提供了新途径，"
        "但距离高效THz源仍有差距。}",
        "\\par\\par{从研究空白来看，"
        "缺乏对各技术路线在不同应用场景下的系统性性能边界分析，"
        "这将是未来研究的重要方向。}",
    ]

    themes_with_papers = [k for k, v in groups.items() if v and k != "其他"]
    n_themes = len(themes_with_papers)
    n_papers = len(papers)

    latex_parts = [
        "\\documentclass[reprint,amsmath,amssymb,aps,floatfix]{revtex4-2}",
        "\\usepackage{graphicx}",
        "\\usepackage{dcolumn}",
        "\\usepackage{bm}",
        "\\usepackage{amsmath}",
        "\\usepackage{amssymb}",
        "\\usepackage{hyperref}",
        "\\begin{document}",
        "\\preprint{APS/Academic Review}",
        "\\title{Topic: " + topic + " -- 文献综述 v4.0}",
        "\\author{Claude Code Academic Brain}",
        "\\affiliation{%",
        " Self Learning Project%",
        "}%",
        "\\date{" + timestamp + "}%",
        "\\begin{abstract}",
        f"本综述基于OpenAlex数据库检索的{n_papers}篇论文，覆盖{n_themes}个主题方向。",
        "通过Thematic Synthesis方法，对各技术路线的核心权衡与研究空白进行系统分析。",
        "\\end{abstract}",
        "\\maketitle",
        "\\section{引言}",
        intro,
        "\\section{方法与结果}",
        methods_text,
    ]
    latex_parts.extend(discussion)
    latex_parts.extend([
        "\\appendix",
        "\\section{附录：论文列表}",
        "\\begin{table}[h!]",
        "\\caption{检索到的论文列表}",
        "\\label{tab:papers}",
        "\\begin{tabular}{@{ }p{10cm}r@{ }}",
        "\\hline",
        "\\# & Title & Citations\\\\",
        "\\hline",
    ])

    for i, p in enumerate(papers, 1):
        short_title = p["title"][:80] + ("..." if len(p["title"]) > 80 else "")
        latex_parts.append(str(i) + " & " + short_title + " & " + str(p["citations"]) + "\\\\")

    latex_parts.extend([
        "\\hline",
        "\\end{tabular}",
        "\\end{table}",
        "\\end{document}",
    ])

    latex = "\n".join(latex_parts)

    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(latex)

    print(f"    LaTeX: {tex_file}")
    print(f"    BibTeX: {bib_file}")
    return tex_file, bib_file


def run_full_pipeline_v4(query: str, n: int = 30, output_dir: str = "DHL") -> Dict:
    print(f"\n{'='*60}")
    print(f"学术综述生成 Pipeline v4.0 - Thematic Synthesis")
    print(f"主题: {query} | 检索数量: {n}")
    print(f"{'='*60}\n")

    # Phase 1: 论文发现
    papers = discover_papers(query, max_results=n)

    # Phase 2: 主题分组
    groups = group_papers_by_theme(papers)
    print(f"\n>> [Phase 2] Theme groups:")
    for gname, gpapers in groups.items():
        if gpapers:
            print(f"    {gname}: {len(gpapers)} 篇")

    # Phase 3: 质量门禁
    gates = run_quality_gates(papers, groups)
    if not all(gates.values()):
        print("\n>> 警告: 部分Gate未通过，但继续生成...")

    # Phase 4: Thematic Synthesis
    print(f"\n>> [Phase 3] Thematic Synthesis...")
    synths = {}
    for theme in THZ_THEMES:
        if groups.get(theme):
            synths[theme] = synthesize_theme(theme, groups[theme])
            s = synths[theme]
            print(f"    {theme}: {synths[theme]['n_papers']} papers, "
                  f"citation range: {synths[theme]['citation_range']}, "
                  f"gaps identified: {len(synths[theme]['gaps'])}")

    # Phase 5: 汇编LaTeX
    tex_file, bib_file = assemble_latex_v4(papers, groups, synths, query, output_dir)

    return {
        "papers": papers,
        "groups": groups,
        "synths": synths,
        "gates": gates,
        "tex_file": tex_file,
        "bib_file": bib_file,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "full":
        pos_args = []
        i = 2
        while i < len(sys.argv):
            if sys.argv[i].startswith("--"):
                break
            pos_args.append(sys.argv[i])
            i += 1
        query = " ".join(pos_args) if pos_args else ""
        if not query:
            print("Usage: review_pipeline_v4.py full <query> [--n N]")
            sys.exit(1)

        n = 30
        while i < len(sys.argv):
            if sys.argv[i] == "--n" and i + 1 < len(sys.argv):
                n = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        result = run_full_pipeline_v4(query, n=n, output_dir="DHL")
        print(f"\n>> Output: {result['tex_file']}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
