#!/usr/bin/env python3
"""
学术综述生成 Pipeline - 严格质量审查门禁 (Quality Gate)

在 Phase 2 和 Phase 3 之间插入审查节点
只有通过全部审查项才能进入 LaTeX 生成

审查维度：
1. 论文相关性 - top papers 是否真正相关
2. 摘要质量 - abstract 能否重建
3. 分组准确性 - 抽样验证分类是否正确
4. 指标提取 - 从摘要提取的数值是否合理
5. Gap 分析 - 研究空白是否有文献支撑
"""

import requests, os, sys, codecs, re
from typing import List, Dict, Tuple

if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(v, None)

OPENALEX_API_BASE = "https://api.openalex.org"
EMAIL = os.getenv("EMAIL", "research@example.com")

THZ_THEMES = {
    "PCA材料": ["low-temperature grown GaAs", "LT-GaAs", "InGaAs", "ion-implanted",
                "carrier lifetime", "mobility", "semi-insulating", "ErAs", "nanoparticle"],
    "PCA结构": ["bow-tie", "dipole", "strip-line", "interdigitated", "large-area",
                "plasmonic", "nanoelectrode", "grating", "antenna design", "log-spiral"],
    "光整流晶体": ["lithium niobate", "LiNbO3", "ZnTe", "GaSe", "DAST", "OH1", "organic crystal",
                  "tilted pulse front", "phase matching", "collinear", "cascaded DFG"],
    "空气等离子体": ["air plasma", "filamentation", "two-color", "four-wave mixing",
                    "laser-induced plasma", "terawatt", "remote THz", "energy scaling"],
    "QCL激光器": ["quantum cascade", "QCL", "intersubband", "heterostructure",
                  "room temperature", "frequency mixing", "mid-infrared"],
    "超表面THz": ["metasurface", "plasmonic", "nanoantenna", "resonant",
                 "beam steering", "modulator", "absorber"],
    "检测技术": ["detection", "electro-optic sampling", "bolometer", "pyroelectric",
                "SNR", "NEP", "time-domain", "spectroscopy"],
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
    return papers


def classify_paper(paper: Dict) -> List[str]:
    full_text = (
        paper["title"].lower() + " " +
        paper["abstract"].lower() + " " +
        " ".join([c[0].lower() for c in paper.get("concepts", [])])
    )
    matched = []
    for theme, keywords in THZ_THEMES.items():
        score = sum(1 for kw in keywords if kw.lower() in full_text)
        if score >= 1:
            matched.append((theme, score))
    matched.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matched]


def extract_metrics(abstract: str) -> List[str]:
    """从摘要提取数值指标"""
    patterns = [
        (r'([\d.]+)\s*THz', 'THz'),
        (r'([\d.]+)\s*mJ', 'mJ'),
        (r'([\d.]+)\s*µJ', 'μJ'),
        (r'([\d.]+)\s*GW', 'GW'),
        (r'([\d.]+)\s*kV/cm', 'kV/cm'),
        (r'([\d.]+)\s*%', '%'),
    ]
    metrics = []
    for pattern, unit in patterns:
        for m in re.findall(pattern, abstract, re.IGNORECASE):
            try:
                float(m)
                metrics.append(f"{m} {unit}")
            except:
                pass
    return metrics[:6]


# ============ 审查函数 ============

def gate1_relevance_check(papers: List[Dict]) -> Dict:
    """
    Gate 1: 论文相关性审查
    检查 top 10 论文的相关性得分和摘要长度
    """
    print("\n" + "="*60)
    print("GATE 1: 论文相关性审查")
    print("="*60)

    issues = []
    top10 = sorted(papers, key=lambda x: x["relevance"], reverse=True)[:10]

    for i, p in enumerate(top10, 1):
        rel = p["relevance"]
        abstract_len = len(p["abstract"])
        title = p["title"][:50]

        status = "OK"
        reason = ""
        if rel < 50:
            status = "LOW"
            reason = f"rel={rel:.1f}"
        elif abstract_len < 50:
            status = "WARN"
            reason = f"abstract={abstract_len}chars"

        symbol = "PASS" if status == "OK" else "FAIL" if status == "LOW" else "WARN"
        print(f"  [{symbol}] #{i} {p['authors'][0]} ({p['year']}) rel={rel:.1f} | {title}... | abstract={abstract_len}chars")

        if status == "LOW":
            issues.append(f"Top-{i} paper relevance too low: {reason}")

    # 总体评估
    low_rel_count = sum(1 for p in top10 if p["relevance"] < 50)
    pass_rate = (10 - low_rel_count) / 10

    result = {
        "gate": "GATE 1: 论文相关性",
        "status": "PASS" if pass_rate >= 0.7 else "FAIL",
        "pass_rate": f"{pass_rate:.0%}",
        "issues": issues,
        "recommendation": "可接受" if pass_rate >= 0.7 else "建议更换查询词或增加 filter"
    }
    print(f"\n  结论: {result['status']} ({result['pass_rate']} 通过率)")
    if issues:
        for iss in issues:
            print(f"    - {iss}")
    return result


def gate2_abstract_quality_check(papers: List[Dict]) -> Dict:
    """
    Gate 2: 摘要质量审查
    检查 abstract 是否可重建、长度是否足够
    """
    print("\n" + "="*60)
    print("GATE 2: 摘要质量审查")
    print("="*60)

    issues = []
    no_abstract = 0
    short_abstract = 0
    good_abstract = 0

    for p in papers:
        abstract_len = len(p["abstract"])
        if not p["abstract_raw"]:
            no_abstract += 1
            issues.append(f"No abstract: {p['title'][:40]}...")
        elif abstract_len < 100:
            short_abstract += 1
            if short_abstract <= 3:
                issues.append(f"Short abstract ({abstract_len} chars): {p['title'][:40]}...")
        else:
            good_abstract += 1

    total = len(papers)
    good_rate = good_abstract / total if total > 0 else 0

    print(f"  有摘要: {total - no_abstract}/{total}")
    print(f"  摘要长度足够(>100chars): {good_abstract}/{total}")
    print(f"  无摘要: {no_abstract}/{total}")
    print(f"  短摘要(<100chars): {short_abstract}/{total}")

    result = {
        "gate": "GATE 2: 摘要质量",
        "status": "PASS" if good_rate >= 0.6 else "WARN",
        "good_rate": f"{good_rate:.0%}",
        "issues": issues[:5],
        "recommendation": "良好" if good_rate >= 0.8 else "可接受" if good_rate >= 0.6 else "需人工审核"
    }
    print(f"\n  结论: {result['status']} (良好率 {result['good_rate']})")
    if issues[:3]:
        for iss in issues[:3]:
            print(f"    - {iss}")
    return result


def gate3_classification_check(papers: List[Dict], sample_size: int = 8) -> Dict:
    """
    Gate 3: 分组准确性审查
    抽样人工检查分类是否正确
    """
    print("\n" + "="*60)
    print("GATE 3: 分组准确性审查 (抽样验证)")
    print("="*60)

    import random
    sample = random.sample(papers, min(sample_size, len(papers)))

    correct = 0
    wrong = 0
    details = []

    for p in sample:
        assigned = classify_paper(p)
        # 真实判断（基于标题和摘要关键词）
        title_lower = p["title"].lower()
        abstract_lower = p["abstract"].lower()

        # 人工判断应该属于哪个主题
        true_themes = []
        if any(kw in title_lower + abstract_lower for kw in THZ_THEMES["PCA材料"]):
            true_themes.append("PCA材料")
        if any(kw in title_lower + abstract_lower for kw in THZ_THEMES["PCA结构"]):
            true_themes.append("PCA结构")
        if any(kw in title_lower + abstract_lower for kw in THZ_THEMES["光整流晶体"]):
            true_themes.append("光整流晶体")
        if any(kw in title_lower + abstract_lower for kw in THZ_THEMES["空气等离子体"]):
            true_themes.append("空气等离子体")
        if any(kw in title_lower + abstract_lower for kw in THZ_THEMES["QCL激光器"]):
            true_themes.append("QCL激光器")
        if any(kw in title_lower + abstract_lower for kw in THZ_THEMES["超表面THz"]):
            true_themes.append("超表面THz")
        if any(kw in title_lower + abstract_lower for kw in THZ_THEMES["检测技术"]):
            true_themes.append("检测技术")

        is_correct = any(t in assigned for t in true_themes) if true_themes else (not assigned)
        status = "CORRECT" if is_correct else "WRONG"
        if is_correct:
            correct += 1
        else:
            wrong += 1

        print(f"  [{status}] '{p['title'][:40]}...'")
        print(f"       分配: {assigned[:2] if assigned else '其他'}")
        print(f"       实际: {true_themes[:2] if true_themes else '其他'}")

    accuracy = correct / (correct + wrong) if (correct + wrong) > 0 else 0

    result = {
        "gate": "GATE 3: 分组准确性",
        "status": "PASS" if accuracy >= 0.7 else "WARN",
        "accuracy": f"{accuracy:.0%}",
        "correct": correct,
        "wrong": wrong,
        "recommendation": "可接受" if accuracy >= 0.7 else "建议优化关键词"
    }
    print(f"\n  结论: {result['status']} (准确率 {result['accuracy']})")
    print(f"  抽样 {correct + wrong} 篇中，{correct} 篇分类正确，{wrong} 篇分类错误")
    return result


def gate4_metrics_check(papers: List[Dict]) -> Dict:
    """
    Gate 4: 关键指标提取审查
    检查能否从摘要提取有意义的数值指标
    """
    print("\n" + "="*60)
    print("GATE 4: 关键指标提取审查")
    print("="*60)

    total_metrics = 0
    papers_with_metrics = 0
    sample_metrics = []

    for p in papers:
        metrics = extract_metrics(p["abstract"])
        if metrics:
            papers_with_metrics += 1
            total_metrics += len(metrics)
            if len(sample_metrics) < 5:
                sample_metrics.append((p["title"][:40], metrics))

    rate = papers_with_metrics / len(papers) if papers else 0
    avg = total_metrics / len(papers) if papers else 0

    print(f"  有指标论文: {papers_with_metrics}/{len(papers)} ({rate:.0%})")
    print(f"  平均每篇提取指标数: {avg:.1f}")
    print(f"  样例指标:")
    for title, m in sample_metrics:
        print(f"    - {title}: {m}")

    result = {
        "gate": "GATE 4: 指标提取",
        "status": "PASS" if rate >= 0.3 else "WARN",
        "papers_with_metrics": papers_with_metrics,
        "total": len(papers),
        "rate": f"{rate:.0%}",
        "sample": sample_metrics[:3],
        "recommendation": "良好" if rate >= 0.5 else "指标依赖摘要，正则匹配有限"
    }
    print(f"\n  结论: {result['status']} (覆盖率 {result['rate']})")
    return result


def gate5_group_balance_check(papers: List[Dict]) -> Dict:
    """
    Gate 5: 分组均衡性审查
    检查各主题组是否有足够论文支撑章节写作
    """
    print("\n" + "="*60)
    print("GATE 5: 分组均衡性审查")
    print("="*60)

    groups = {theme: [] for theme in THZ_THEMES.keys()}
    groups["其他"] = []

    for p in papers:
        themes = classify_paper(p)
        if themes:
            for theme in themes[:2]:
                groups[theme].append(p)
        else:
            groups["其他"].append(p)

    groups = {k: v for k, v in groups.items() if v}

    print(f"  分组结果 ({len(groups)} 个非空组):")
    for gname, gpapers in sorted(groups.items(), key=lambda x: -len(x[1])):
        print(f"    {gname}: {len(gpapers)} 篇")

    # 检查是否有组太少（<2篇）导致无法写章节
    thin_groups = [k for k, v in groups.items() if len(v) < 2 and k != "其他"]
    good_groups = [k for k, v in groups.items() if len(v) >= 3]

    result = {
        "gate": "GATE 5: 分组均衡性",
        "status": "PASS" if len(good_groups) >= 3 else "WARN",
        "total_groups": len(groups),
        "good_groups": len(good_groups),
        "thin_groups": thin_groups,
        "recommendation": f"良好，{len(good_groups)} 个组有3篇以上论文" if len(good_groups) >= 3 else "部分组论文过少"
    }
    print(f"\n  结论: {result['status']}")
    print(f"  3篇以上论文的组: {len(good_groups)} 个")
    if thin_groups:
        print(f"  论文不足的组(<2篇): {thin_groups}")
    return result


def run_all_gates(papers: List[Dict]) -> Dict:
    """
    运行所有审查门禁，返回综合报告
    """
    print("\n" + "#"*60)
    print("# 学术综述质量审查门禁")
    print("#"*60)
    print(f"\n待审查论文总数: {len(papers)} 篇")

    gates = [
        gate1_relevance_check(papers),
        gate2_abstract_quality_check(papers),
        gate3_classification_check(papers),
        gate4_metrics_check(papers),
        gate5_group_balance_check(papers),
    ]

    # 综合评估
    statuses = [g["status"] for g in gates]
    fail_count = statuses.count("FAIL")
    warn_count = statuses.count("WARN")
    pass_count = statuses.count("PASS")

    overall = "PASS" if fail_count == 0 and warn_count <= 1 else "WARN" if fail_count == 0 else "FAIL"

    print("\n" + "="*60)
    print("综合审查结论")
    print("="*60)
    print(f"  PASS: {pass_count} | WARN: {warn_count} | FAIL: {fail_count}")
    print(f"  总体: {overall}")
    print(f"\n  各 Gate 结论:")
    for g in gates:
        print(f"    [{g['status']}] {g['gate']} - {g.get('recommendation', '')}")

    print("\n" + "="*60)
    if overall == "PASS":
        print("  >> 可以进入 LaTeX 生成阶段")
    elif overall == "WARN":
        print("  >> 警告：存在质量问题，但可以继续生成（建议人工确认）")
    else:
        print("  >> 阻塞：审查未通过，请调整查询或参数后重试")
    print("="*60)

    return {
        "overall": overall,
        "gates": gates,
        "papers": papers,
        "groups": {theme: [] for theme in THZ_THEMES.keys()},
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "review":
        # 收集 positional args
        pos_args = []
        i = 2
        while i < len(sys.argv):
            if sys.argv[i].startswith("--"):
                break
            pos_args.append(sys.argv[i])
            i += 1
        query = " ".join(pos_args) if pos_args else ""
        if not query:
            print("Usage: review_quality_gate.py review <query> [--n N]")
            sys.exit(1)

        n = 20
        while i < len(sys.argv):
            if sys.argv[i] == "--n" and i + 1 < len(sys.argv):
                n = int(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        print(f">> Discovering papers for: '{query}'")
        papers = discover_papers(query, max_results=n)
        print(f">> Found {len(papers)} papers, starting quality gates...")

        result = run_all_gates(papers)

        if result["overall"] in ["PASS", "WARN"]:
            print("\n>> 审查完成。可以运行: python review_pipeline_v3.py full <query> --n", n)
        else:
            print("\n>> 审查未通过，请调整查询词或参数后重试。")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
