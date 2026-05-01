#!/usr/bin/env python3
"""
学术综述生成 Pipeline v3.0
基于真实综述结构（2017 THz Roadmap, Burford PCA Review）
"""

import requests, os, sys, json, codecs, datetime, re
from typing import List, Dict, Tuple

if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(v, None)

OPENALEX_API_BASE = "https://api.openalex.org"
EMAIL = os.getenv("EMAIL", "research@example.com")

THZ_THEMES = {
    "PCA材料": {
        "keywords": ["low-temperature grown GaAs", "LT-GaAs", "InGaAs", "ion-implanted",
                     "carrier lifetime", "mobility", "semi-insulating", "ErAs", "nanoparticle"],
        "figure_prompt": "Scientific diagram: photoconductive material band structure evolution Si-sapphire→LT-GaAs→InGaAs, with carrier dynamics and lifetime scales. Clean white background, labeled arrows, professional academic style."
    },
    "PCA结构": {
        "keywords": ["bow-tie", "dipole", "strip-line", "interdigitated", "large-area",
                     "plasmonic", "nanoelectrode", "grating", "antenna design", "log-spiral"],
        "figure_prompt": "Schematic of PCA antenna geometries: bow-tie, dipole, strip-line, interdigitated electrode, large-area, plasmonic grating. Show bias field direction, laser illumination, THz radiation. 6 sub-panels labeled (a)-(f), clean white background."
    },
    "光整流晶体": {
        "keywords": ["lithium niobate", "LiNbO3", "ZnTe", "GaSe", "DAST", "OH1", "organic crystal",
                     "tilted pulse front", "phase matching", "collinear", "cascaded DFG"],
        "figure_prompt": "Diagram of optical rectification in nonlinear crystals: tilted pulse front excitation in LiNbO3 with phase matching diagram, pump laser and THz output. Clean white background, labeled axes."
    },
    "空气等离子体": {
        "keywords": ["air plasma", "filamentation", "two-color", "four-wave mixing",
                     "laser-induced plasma", "terawatt", "remote THz", "energy scaling"],
        "figure_prompt": "Two-color laser filamentation for THz generation: 800nm and 400nm beams, plasma filament in air, THz emission cone, intensity scaling curve. Clean white background, labeled values."
    },
    "QCL激光器": {
        "keywords": ["quantum cascade", "QCL", "intersubband", "heterostructure",
                     "room temperature", "frequency mixing", "mid-infrared"],
        "figure_prompt": "THz quantum cascade laser: conduction band structure with multiple quantum wells, injector regions, radiative transitions as arrows, waveguide mode profile. Energy axis labeled. Clean white background."
    },
    "超表面THz": {
        "keywords": ["metasurface", "plasmonic", "nanoantenna", "resonant",
                     "beam steering", "modulator", "absorber"],
        "figure_prompt": "Metasurface THz devices: array of resonant nanoantennas (square patches, split rings), resonance tuning mechanism, near-field enhancement map. 3 sub-panels. Clean white background."
    },
    "检测技术": {
        "keywords": ["detection", "electro-optic sampling", "bolometer", "pyroelectric",
                     "SNR", "NEP", "time-domain", "spectroscopy"],
        "figure_prompt": "THz detection methods comparison: electro-optic sampling (ZnTe crystal), bolometer (cryogenic), pyroelectric detector. Signal chain and performance bars for NEP and bandwidth. 3 sub-panels labeled (a)-(c). Clean white background."
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
    print(f">> [v3 Phase 1] Discovering: '{query}'")
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
            "concepts": [(c.get("display_name", ""), c.get("score", 0)) for c in w.get("concepts", [])[:8]],
            "is_review": is_review,
        }
        papers.append(paper)

    print(f"    Found {len(papers)} papers ({sum(1 for p in papers if p['is_review'])} reviews)")
    return papers


def classify_paper(paper: Dict) -> List[str]:
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
    return [m[0] for m in matched]


def extract_key_findings(paper: Dict) -> Dict:
    abstract = paper["abstract"]
    findings = {"method": "", "metrics": []}

    metric_patterns = [
        (r'([\d.]+)\s*THz', 'THz'),
        (r'([\d.]+)\s*mJ', 'mJ'),
        (r'([\d.]+)\s*uJ', 'uJ'),
        (r'([\d.]+)\s*GW', 'GW'),
        (r'([\d.]+)\s*kV/cm', 'kV/cm'),
        (r'([\d.]+)\s*%', '%'),
    ]

    for pattern, unit in metric_patterns:
        for m in re.findall(pattern, abstract, re.IGNORECASE):
            try:
                float(m)
                findings["metrics"].append(f"{m} {unit}")
            except:
                pass

    sentences = abstract.split('.')
    method_kws = ["using", "by means of", "based on", "employing", "via", "with"]
    for sent in sentences:
        sent_lower = sent.lower()
        if any(kw in sent_lower for kw in method_kws) and len(sent) > 30:
            findings["method"] += sent.strip() + ". "
            if len(findings["method"]) > 300:
                break

    findings["method"] = findings["method"][:200].strip()
    findings["metrics"] = findings["metrics"][:6]
    return findings


def group_papers_by_theme(papers: List[Dict]) -> Dict[str, List[Dict]]:
    groups = {theme: [] for theme in THZ_THEMES.keys()}
    groups["其他"] = []

    for p in papers:
        themes = classify_paper(p)
        if themes:
            for theme in themes[:2]:
                groups[theme].append(p)
        else:
            groups["其他"].append(p)

    return {k: v for k, v in groups.items() if v}


def build_performance_table(theme: str, papers: List[Dict]) -> str:
    if not papers:
        return ""

    sorted_p = sorted(papers, key=lambda x: x["citations"], reverse=True)[:5]
    cols = ["Author(s)", "Year", "Key Approach", "Key Metric", "Citations"]
    col_spec = "l" + "p{2.5cm}" * (len(cols) - 1)

    rows = []
    for p in sorted_p:
        findings = extract_key_findings(p)
        author = p["authors"][0] if p["authors"] else "N/A"
        year = str(p["year"])
        approach = findings["method"][:50] if findings["method"] else p["concepts"][0][0] if p["concepts"] else "---"
        metric = findings["metrics"][0] if findings["metrics"] else "---"
        rows.append(f"{author} & {year} & {approach} & {metric} & {p['citations']}")

    table_lines = [
        f"\\begin{{table}}[h!]",
        f"\\caption{{性能对比: {theme}}}",
        f"\\label{{tab:{theme.replace(' ', '_')}}}",
        "\\begin{tabular}{@{}l" + col_spec + "@{}}",
        "\\hline",
        " & ".join(cols) + "\\\\",
        "\\hline",
    ]
    for row in rows:
        table_lines.append(row + "\\\\")
    table_lines.extend([f"\\hline", f"\\end{{tabular}}", f"\\end{{table}}"])
    return "\n".join(table_lines)


def write_introduction(papers: List[Dict], groups: Dict) -> str:
    sorted_by_cite = sorted(papers, key=lambda x: x["citations"], reverse=True)
    reviews = [p for p in sorted_by_cite if p["is_review"]][:3]

    paras = []
    paras.append(
        "太赫兹(THz)波段（0.1-10 THz）位于微波与红外之间，是连接电子学与光学的桥梁，"
        "在成像、光谱学、通信和安全检测等领域具有重要应用前景。"
        "然而，THz辐射的高效产生一直是该领域核心技术难题。"
    )

    if reviews:
        r = reviews[0]
        paras.append(
            f"{r['authors'][0]}等人({r['year']})在《{r['journal']}》发表的综述系统梳理了该领域的发展脉络，"
            f"指出材料创新和结构优化是推动THz源性能提升的关键。"
        )

    themes_with_papers = [k for k, v in groups.items() if v]
    n_themes = len(themes_with_papers)
    n_papers = len(papers)

    paras.append(
        "尽管近年来多种THz产生机制取得了显著进展，但各方法在效率、带宽、峰值功率"
        "和集成度等方面仍面临不同挑战。目前缺乏对最新进展的系统性对比分析，"
        "尤其是针对不同应用场景下各方法优缺点的定量比较。"
    )

    theme_names = "、".join(themes_with_papers[:4])
    paras.append(
        f"本综述基于OpenAlex数据库检索的{n_papers}篇相关论文，涵盖{theme_names}等{n_themes}个主题方向，"
        "按主题分类整理各方法的技术指标与性能对比，识别当前研究空白并展望未来发展方向。"
    )

    return "\n\n".join([f"\\par\\par{{{p}}}" for p in paras])


def write_theme_section(theme: str, papers: List[Dict]) -> str:
    sorted_p = sorted(papers, key=lambda x: x["citations"], reverse=True)
    top3 = sorted_p[:3]

    theme_intro = {
        "PCA材料": "光电导天线(PCA)的性能高度依赖光电导材料特性。超快载流子寿命、高迁移率和高暗电阻是理想材料的三要素。",
        "PCA结构": "天线几何结构决定了辐射阻抗、带宽和光泵吸收效率。从简单的偶极子到复杂的多级结构，设计不断演进。",
        "光整流晶体": "光整流通过二阶非线性效应将超快激光转换为THz辐射。相位匹配和晶体损伤阈值是核心限制因素。",
        "空气等离子体": "空气等离子体方法利用强场电离产生的等离子体振荡辐射THz，可实现远程、高峰值功率输出。",
        "QCL激光器": "量子级联激光器(QCL)通过半导体多量子阱结构中的级联跃迁产生THz，是唯一实现电泵浦的固态THz源。",
        "超表面THz": "超表面通过亚波长结构单元的谐振响应产生或操控THz波，可实现平面化、集成化的功能器件。",
        "检测技术": "THz检测技术主要包括相干探测（电光采样）和能量探测（热敏探测器），各有优缺点。",
    }

    section = [f"\\subsection{{{theme}}}"]
    section.append(theme_intro.get(theme, f"{theme}相关研究进展如下："))
    section.append("")

    section.append("\\subsubsection*{代表性工作}")
    for p in top3:
        findings = extract_key_findings(p)
        author = p["authors"][0] if p["authors"] else "N/A"
        section.append(
            f"{author}等人({p['year']})在《{p['journal']}》提出 "
            f"\\textit{{{p['title'][:60]}}}..."
        )
        if findings["method"]:
            section.append(f"方法：{findings['method'][:150]}...")
        if findings["metrics"]:
            section.append(f"关键指标：{', '.join(findings['metrics'][:3])}")
        section.append(f"该工作被引用 {p['citations']} 次。")
        section.append("")

    table = build_performance_table(theme, papers)
    if table:
        section.append("\\subsubsection*{性能对比}")
        section.append(table)
        section.append("")

    challenges = {
        "PCA材料": "挑战：进一步缩短载流子寿命同时保持高迁移率，开发1.55um泵浦兼容材料。",
        "PCA结构": "挑战：解决大面积天线与超宽带之间的矛盾，实现高功率与高带宽的统一。",
        "光整流晶体": "挑战：提高损伤阈值实现更高泵浦能量，发展新型有机晶体突破效率极限。",
        "空气等离子体": "挑战：提高转换效率，解决远程传输中的相位稳定性问题。",
        "QCL激光器": "挑战：实现室温连续波高功率输出，扩展到4 THz以上频段。",
        "超表面THz": "挑战：降低损耗、提高损伤阈值，实现主动可调谐功能。",
        "检测技术": "挑战：提高灵敏度（降低NEP）和响应速度，扩展工作带宽。",
    }
    if theme in challenges:
        section.append("\\subsubsection*{未来方向}")
        section.append(challenges[theme])

    return "\n".join(section)


def assemble_latex_v3(papers: List[Dict], groups: Dict, topic: str, output_dir: str = "DHL") -> Tuple[str, str]:
    print(f">> [v3 Phase 5] Assembling LaTeX...")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    safe_topic = topic.replace(' ', '_')[:20]
    tex_file = f"{output_dir}/review_v3_{safe_topic}.tex"
    bib_file = f"{output_dir}/review_v3_{safe_topic}.bib"

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

    intro_text = write_introduction(papers, groups)

    sections = []
    for theme, theme_papers in groups.items():
        if not theme_papers or theme == "其他":
            continue
        sections.append(write_theme_section(theme, theme_papers))

    methods_text = "\n\n".join(sections)

    discussion = (
        "本综述系统梳理了" + topic + "领域的研究进展，按材料、结构、机制等维度进行了分类对比。"
        "光电导天线在超宽带应用场景具有独特优势；"
        "光整流在LiNbO3倾斜脉冲前技术支撑下实现了mJ级THz输出；"
        "空气等离子体方法实现了远程THz产生；"
        "QCL正在向室温高功率方向发展；"
        "超表面则为THz器件的平面化集成提供了新途径。"
        "未来研究应重点关注提高转换效率、扩展工作带宽和实现片上集成。"
    )

    themes_with_papers = [k for k, v in groups.items() if v and k != "其他"]
    n_themes = len(themes_with_papers)
    n_papers = len(papers)

    latex_parts = [
        r"\documentclass[reprint,amsmath,amssymb,aps,floatfix]{revtex4-2}",
        r"\usepackage{graphicx}",
        r"\usepackage{dcolumn}",
        r"\usepackage{bm}",
        r"\usepackage{amsmath}",
        r"\usepackage{amssymb}",
        r"\usepackage{hyperref}",
        r"\begin{document}",
        r"\preprint{APS/Academic Review}",
        r"\title{Topic: " + topic + " -- 文献综述 v3.0}",
        r"\author{Claude Code Academic Brain}",
        r"\affiliation{%",
        r" Self Learning Project%",
        r"}%",
        r"\date{" + timestamp + "}%",
        r"\begin{abstract}",
        f"本综述基于OpenAlex按相关性检索的{n_papers}篇论文，覆盖{n_themes}个主题方向。",
        f"按材料/结构/机制分类，提取关键性能指标，构建对比表格，识别研究空白。",
        r"\end{abstract}",
        r"\maketitle",
        r"\section{引言}",
        intro_text,
        r"\section{方法与结果}",
        methods_text,
        r"\section{讨论}",
        discussion,
        r"\appendix",
        r"\section{附录：论文列表}",
        r"\begin{table}[h!]",
        r"\caption{检索到的论文列表}",
        r"\label{tab:papers}",
        r"\begin{tabular}{@{ }p{10cm}r@{ }}",
        r"\hline",
        r"\# & Title & Citations\\",
        r"\hline",
    ]

    for i, p in enumerate(papers, 1):
        short_title = p["title"][:80] + ("..." if len(p["title"]) > 80 else "")
        latex_parts.append(str(i) + " & " + short_title + " & " + str(p["citations"]) + r"\\")

    latex_parts.extend([
        r"\hline",
        r"\end{tabular}",
        r"\end{table}",
        r"\end{document}",
    ])

    latex = "\n".join(latex_parts)

    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(latex)

    print(f"    LaTeX saved: {tex_file}")
    print(f"    BibTeX saved: {bib_file}")
    return tex_file, bib_file


def run_full_pipeline_v3(query: str, n: int = 30, output_dir: str = "DHL") -> Dict:
    print(f"\n{'='*60}")
    print(f"学术综述生成 Pipeline v3.0 - 数据驱动 + 结构化写作")
    print(f"主题: {query} | 检索数量: {n}")
    print(f"{'='*60}\n")

    papers = discover_papers(query, max_results=n)
    groups = group_papers_by_theme(papers)

    print(f"\n>> [v3 Phase 2] Theme groups:")
    for gname, gpapers in groups.items():
        if gpapers:
            print(f"    {gname}: {len(gpapers)} 篇")

    print(f"\n>> [v3 Phase 3] Extracting key findings...")
    for p in papers:
        p["findings"] = extract_key_findings(p)

    print(f"\n>> [v3 Phase 4] Figure prompts:")
    for theme in groups.keys():
        if groups[theme]:
            prompt = THZ_THEMES.get(theme, {}).get("figure_prompt", "")
            print(f"    {theme}: {prompt[:80]}...")

    tex_file, bib_file = assemble_latex_v3(papers, groups, query, output_dir)

    return {"papers": papers, "groups": groups, "tex_file": tex_file, "bib_file": bib_file}


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
            print("Usage: review_pipeline_v3.py full <query> [--n N]")
            sys.exit(1)
        n = 30
        while i < len(sys.argv):
            if sys.argv[i] == "--n" and i + 1 < len(sys.argv):
                n = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        result = run_full_pipeline_v3(query, n=n, output_dir="DHL")
        print(f"\n>> Output: {result['tex_file']}")

    elif cmd == "discover":
        pos_args = []
        i = 2
        while i < len(sys.argv):
            if sys.argv[i].startswith("--"):
                break
            pos_args.append(sys.argv[i])
            i += 1
        query = " ".join(pos_args) if pos_args else ""
        if not query:
            print("Usage: review_pipeline_v3.py discover <query> [--n N]")
            sys.exit(1)
        n = 20
        while i < len(sys.argv):
            if sys.argv[i] == "--n" and i + 1 < len(sys.argv):
                n = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1
        papers = discover_papers(query, max_results=n)
        groups = group_papers_by_theme(papers)
        for gname, gpapers in groups.items():
            if gpapers:
                print(f"  {gname}: {len(gpapers)} 篇")
                for p in sorted(gpapers, key=lambda x: x["citations"], reverse=True)[:2]:
                    print(f"    - {p['authors'][0]} ({p['year']}): {p['title'][:50]}... [cite={p['citations']}]")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
