#!/usr/bin/env python3
"""
OpenAlex 学术论文检索脚本 v2.0
按相关性排序 + 多源组合策略

使用方法:
    python openalex_search.py search "关键词"                    # 相关性排序
    python openalex_search.py search "关键词" --recent 5        # 最近5年
    python openalex_search.py doi "DOI号"                       # DOI精确查找
    python openalex_search.py related "DOI号"                    # 相关论文
    python openalex_search.py combo "关键词"                     # 组合策略（OpenAlex + Tavily）
    python openalex_search.py ref "DOI1 DOI2 DOI3"              # 文献调研
"""

import requests
import sys
import os
import json
from typing import List, Dict, Optional

# Windows 编码兼容
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 清除代理环境变量（避免代理干扰 OpenAlex/Tavily API 调用）
for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(v, None)

# 加载环境变量（手动读取避免dotenv警告）
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                try:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
                except:
                    pass

# OpenAlex API 配置
OPENALEX_API_BASE = "https://api.openalex.org"
EMAIL = os.getenv("EMAIL", "research@example.com")
OPENALEX_API_KEY = os.getenv("OpenAlex_API_KEY", "")


def build_headers() -> Dict:
    """构建请求头"""
    headers = {
        "User-Agent": f"Mozilla/5.0 (Python AcademicResearchBot/1.0; mailto:{EMAIL})",
        "Accept": "application/json"
    }
    return headers


def build_params(api_key: str = "") -> Dict:
    """构建查询参数"""
    params = {"mailto": EMAIL}
    if api_key:
        params["api_key"] = api_key
    return params


def search_papers(query: str, max_results: int = 10, years: Optional[int] = None,
                   sort_by: str = "relevance") -> List[Dict]:
    """
    搜索论文 - 默认按相关性排序
    """
    # 清除代理环境变量
    for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(v, None)

    url = f"{OPENALEX_API_BASE}/works"
    params = build_params(OPENALEX_API_KEY)
    params["search"] = query
    params["per_page"] = min(max_results, 100)

    if sort_by == "relevance":
        params["sort"] = "relevance_score:desc"
    elif sort_by == "citations":
        params["sort"] = "cited_by_count:desc"
    elif sort_by == "year":
        params["sort"] = "publication_year:desc"

    if years:
        import datetime
        current_year = datetime.datetime.now().year
        params["filter"] = f"publication_year:>{current_year-years}"

    response = requests.get(url, params=params, headers=build_headers(), timeout=30)
    response.raise_for_status()
    return response.json().get("results", [])


def get_paper_by_doi(doi: str) -> Optional[Dict]:
    """通过 DOI 获取论文详情"""
    for v in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(v, None)
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
    url = f"{OPENALEX_API_BASE}/works/https://doi.org/{doi}"
    params = build_params(OPENALEX_API_KEY)
    try:
        response = requests.get(url, params=params, headers=build_headers(), timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except:
        return None


def get_related_papers(doi: str, max_results: int = 5) -> List[Dict]:
    """获取相关论文"""
    paper = get_paper_by_doi(doi)
    if not paper:
        return []
    related = []
    for work_id in paper.get("related_works", [])[:max_results]:
        if "doi.org/" in work_id:
            paper_doi = work_id.split("doi.org/")[-1]
            data = get_paper_by_doi(paper_doi)
            if data:
                related.append(data)
    return related


def get_similar_by_title(title: str, max_results: int = 5) -> List[Dict]:
    """通过标题搜索相似论文"""
    url = f"{OPENALEX_API_BASE}/works"
    params = build_params(OPENALEX_API_KEY)
    params["search"] = title
    params["per_page"] = max_results
    params["sort"] = "relevance_score:desc"
    try:
        response = requests.get(url, params=params, headers=build_headers(), timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])
    except:
        return []


def format_bibtex(work: Dict) -> str:
    """转换为 BibTeX 格式"""
    authors = work.get("authorships", [])
    author_list = []
    for auth in authors[:10]:
        name = auth.get("author", {}).get("display_name", "Unknown")
        parts = name.split()
        if len(parts) >= 2:
            bib = f"{{{parts[-1]}, {' '.join(parts[:-1])}}}"
        else:
            bib = name
        author_list.append(bib)

    authors_str = " and ".join(author_list)
    if len(authors) > 10:
        authors_str += " et al."

    title = work.get("title", "Untitled")
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    journal = source.get("display_name", "")
    year = work.get("publication_year", "")
    biblio = work.get("biblio", {})
    volume = biblio.get("volume", "")
    issue = biblio.get("issue", "")
    pages = biblio.get("first_page", "")
    doi = work.get("doi", "")

    first_author = author_list[0].split(",")[0].replace("{", "").replace("}", "") if author_list else "Unknown"
    key = f"{first_author}{year}"

    return f"""@article{{{key},
  title   = {{{title}}},
  author  = {{{authors_str}}},
  journal = {{{journal}}},
  year    = {{{year}}},
  volume  = {{{volume}}},
  number  = {{{issue}}},
  pages   = {{{pages}}},
  doi     = {{{doi}}}
}}"""


def print_paper(work: Dict, num: int = None, show_abstract: bool = False) -> None:
    """打印论文信息"""
    prefix = f"[{num}] " if num else ""
    print(f"\n{prefix}{'='*60}")
    print(f"Title: {work.get('title', 'N/A')}")

    authors = work.get("authorships", [])
    names = [a.get("author", {}).get("display_name", "Unknown") for a in authors[:5]]
    more = f", ... +{len(authors)-5}" if len(authors) > 5 else ""
    print(f"Authors: {', '.join(names)}{more}")

    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    print(f"Year: {work.get('publication_year', 'N/A')}")
    print(f"Journal: {source.get('display_name', 'N/A')}")
    print(f"DOI: {work.get('doi', 'N/A')}")
    print(f"Citations: {work.get('cited_by_count', 0)}")
    print(f"Relevance: {work.get('relevance_score', 'N/A')}")

    if show_abstract:
        abstract = work.get("abstract_inverted_index", {})
        if abstract:
            words = []
            for word, positions in abstract.items():
                for pos in positions:
                    words.append((pos, word))
            words.sort(key=lambda x: x[0])
            abstract_text = " ".join([w[1] for w in words])
            print(f"Abstract: {abstract_text[:300]}...")


def export_results(papers: List[Dict], output_file: str = None, fmt: str = "bibtex") -> str:
    """
    导出论文结果为指定格式

    Args:
        papers: 论文列表
        output_file: 输出文件路径（None则只返回字符串）
        fmt: "bibtex" | "doi" | "json"
    """
    lines = []
    if fmt == "bibtex":
        for w in papers:
            lines.append(format_bibtex(w))
    elif fmt == "doi":
        for w in papers:
            lines.append(w.get("doi", ""))
    elif fmt == "json":
        import json
        # 只保留关键字段
        compact = []
        for w in papers:
            authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:3]]
            compact.append({
                "title": w.get("title", ""),
                "authors": authors,
                "year": w.get("publication_year", ""),
                "journal": ((w.get("primary_location") or {}).get("source") or {}).get("display_name", ""),
                "doi": w.get("doi", ""),
                "citations": w.get("cited_by_count", 0),
            })
        lines.append(json.dumps(compact, indent=2, ensure_ascii=False))

    output = "\n\n".join(lines)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f">> Exported {len(papers)} results to {output_file}")
    return output


def combo_search(query: str) -> Dict:
    """
    组合策略：OpenAlex 相关性 + 最近5年

    注意：Tavily 网络搜索通过 MCP tool 单独调用:
        mcp__tavily-search__search --query "关键词" --max_results 5

    Returns:
        综合检索结果字典
    """
    results = {
        "query": query,
        "openalex": [],
        "recent": [],
        "summary": ""
    }

    # 1. OpenAlex 相关性搜索
    print("\n>> [1/2] OpenAlex (相关性排序)...")
    papers = search_papers(query, max_results=10, sort_by="relevance")
    results["openalex"] = papers[:5]
    print(f"    找到 {len(papers)} 篇，取前5")

    # 2. OpenAlex 最近5年
    print("\n>> [2/2] OpenAlex (最近5年)...")
    url = f"{OPENALEX_API_BASE}/works"
    import datetime
    current_year = datetime.datetime.now().year
    params = build_params(OPENALEX_API_KEY)
    params["search"] = query
    params["per_page"] = 5
    params["filter"] = f"publication_year:>{current_year-5}"
    params["sort"] = "relevance_score:desc"
    try:
        response = requests.get(url, params=params, headers=build_headers(), timeout=30)
        response.raise_for_status()
        recent = response.json().get("results", [])
    except:
        recent = []
    results["recent"] = recent
    print(f"    最近5年 {len(recent)} 篇")

    return results


def print_combo_results(results: Dict) -> None:
    """打印组合检索结果"""
    print(f"\n{'='*60}")
    print(f"组合检索结果: '{results['query']}'")
    print(f"{'='*60}")

    print("\n>>> OpenAlex (按相关性排序):")
    for i, w in enumerate(results.get("openalex", []), 1):
        print_paper(w, i)

    print(f"\n>>> OpenAlex (最近5年):")
    for i, w in enumerate(results.get("recent", []), 1):
        print(f"[{i}] {w.get('title', 'N/A')[:60]}... ({w.get('publication_year', 'N/A')})")

    print("\n>>> Tavily (网络搜索): 请使用 MCP tool 单独调用")
    print("    mcp__tavily-search__search --query \"{}\" --max_results 5".format(results['query']))


def literature_review(dois: List[str]) -> None:
    """
    文献调研：从已有DOI出发，扩展检索相关文献

    Args:
        dois: 已有文献的 DOI 列表
    """
    print(f"\n{'='*60}")
    print(f"文献调研模式: {len(dois)} 篇输入文献")
    print(f"{'='*60}")

    all_related = []
    for doi in dois:
        paper = get_paper_by_doi(doi)
        if paper:
            print(f"\n>> 基础文献: {paper.get('title', 'N/A')[:50]}...")
            print(f"   Citations: {paper.get('cited_by_count', 0)}")

            # 获取相关论文
            related = get_related_papers(doi, max_results=3)
            print(f"   相关论文: {len(related)} 篇")
            all_related.extend(related)

    # 去重并按引用数排序
    seen = set()
    unique = []
    for r in all_related:
        doi = r.get("doi", "")
        if doi and doi not in seen:
            seen.add(doi)
            unique.append(r)

    unique.sort(key=lambda x: x.get("cited_by_count", 0), reverse=True)

    print(f"\n>>> 扩展检索 (去重后 {len(unique)} 篇, 按引用数排序):")
    for i, w in enumerate(unique[:10], 1):
        print_paper(w, i)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "search":
        # 过滤掉 -- 开头的参数及其值，保留真正query
        filtered_args = []
        i = 0
        raw = sys.argv[2:]
        while i < len(raw):
            arg = raw[i]
            if arg.startswith('--'):
                # 跳过这个flag和它的值（如果有的话）
                if i + 1 < len(raw) and not raw[i+1].startswith('--'):
                    i += 2
                else:
                    i += 1
                continue
            filtered_args.append(arg)
            i += 1
        query = " ".join(filtered_args) if filtered_args else ""
        if not query:
            print("Usage: openalex_search.py search <query>")
            sys.exit(1)

        recent_years = None
        if "--recent" in sys.argv:
            idx = sys.argv.index("--recent")
            if idx + 1 < len(sys.argv):
                try:
                    recent_years = int(sys.argv[idx + 1])
                except ValueError:
                    pass

        sort_by = "relevance"
        if "--citations" in sys.argv:
            sort_by = "citations"
        elif "--year" in sys.argv:
            sort_by = "year"

        print(f"\n>> Searching: '{query}' (sort={sort_by}, recent={recent_years})")
        papers = search_papers(query, years=recent_years, sort_by=sort_by)
        if not papers:
            print(">> No results found.")
            return
        print(f">> Found {len(papers)} results:")
        for i, w in enumerate(papers, 1):
            print_paper(w, i)

    elif cmd == "doi":
        doi = sys.argv[2] if len(sys.argv) > 2 else ""
        if not doi:
            print("Usage: openalex_search.py doi <DOI>")
            sys.exit(1)
        print(f"\n>> Fetching DOI: {doi}")
        paper = get_paper_by_doi(doi)
        if paper:
            print_paper(paper)
            print("\n>> BibTeX:")
            print(format_bibtex(paper))
        else:
            print(">> Paper not found.")

    elif cmd == "related":
        doi = sys.argv[2] if len(sys.argv) > 2 else ""
        if not doi:
            print("Usage: openalex_search.py related <DOI>")
            sys.exit(1)
        print(f"\n>> Finding related to: {doi}")
        papers = get_related_papers(doi)
        if not papers:
            print(">> No related papers found.")
            return
        for i, w in enumerate(papers, 1):
            print_paper(w, i)

    elif cmd == "combo":
        # 复用 search 的解析逻辑
        filtered_args = []
        i = 0
        raw = sys.argv[2:]
        while i < len(raw):
            arg = raw[i]
            if arg.startswith('--'):
                if i + 1 < len(raw) and not raw[i+1].startswith('--'):
                    i += 2
                else:
                    i += 1
                continue
            filtered_args.append(arg)
            i += 1
        query = " ".join(filtered_args) if filtered_args else ""
        if not query:
            print("Usage: openalex_search.py combo <query>")
            sys.exit(1)
        results = combo_search(query)
        print_combo_results(results)

    elif cmd == "export":
        if len(sys.argv) < 3:
            print("Usage: openalex_search.py export <query> [--bibtex|--doi|--json] [--file <output.txt>]")
            sys.exit(1)
        filtered_args = []
        i = 0
        raw = sys.argv[2:]
        output_file = None
        fmt = "bibtex"
        while i < len(raw):
            arg = raw[i]
            if arg == "--bibtex":
                fmt = "bibtex"
                i += 1
            elif arg == "--doi":
                fmt = "doi"
                i += 1
            elif arg == "--json":
                fmt = "json"
                i += 1
            elif arg == "--file" and i + 1 < len(raw):
                output_file = raw[i + 1]
                i += 2
            else:
                filtered_args.append(arg)
                i += 1
        query = " ".join(filtered_args)
        if not query:
            print("Usage: openalex_search.py export <query> [--bibtex|--doi|--json] [--file <output.txt>]")
            sys.exit(1)
        print(f">> Searching: '{query}'")
        papers = search_papers(query, max_results=20, sort_by="relevance")
        if not papers:
            print(">> No results found.")
            return
        export_results(papers, output_file, fmt)

    elif cmd == "ref":
        if len(sys.argv) < 3:
            print("Usage: openalex_search.py ref <DOI1> <DOI2> ...")
            sys.exit(1)
        dois = sys.argv[2:]
        literature_review(dois)

    elif cmd == "bibtex":
        if len(sys.argv) < 3:
            print("Usage: openalex_search.py bibtex <DOI>")
            sys.exit(1)
        paper = get_paper_by_doi(sys.argv[2])
        if paper:
            print(format_bibtex(paper))
        else:
            print(">> Paper not found.")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
