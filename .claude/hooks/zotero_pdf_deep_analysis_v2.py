#!/usr/bin/env python3
"""
Zotero PDF Deep Analysis v2 - 改进版

基于 PyMuPDF 的深度论文分析
- 自动扫描 Zotero 本地存储路径
- 结构化解析论文各部分
- 深度提取：研究问题、技术方法、关键发现、局限性、Gap

路径: E:/PostGraduate/Science_softwares/Zotero/data/storage/
"""

import os
import re
import codecs
import sys
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# 路径配置
ZOTERO_STORAGE = "E:/PostGraduate/Science_softwares/Zotero/data/storage"

def analyze_paper(pdf_path: str) -> Dict:
    """
    深度分析单篇论文 PDF

    Returns:
        {
            'title': str,
            'authors': str,
            'year': int,
            'abstract': str,
            'sections': {name: content},
            'research_question': str,
            'approach': str,
            'key_findings': List[str],
            'limitations': List[str],
            'gap_identified': str,
            'comparison': str,
            'full_text': str (first 20000 chars)
        }
    """
    try:
        import fitz
    except ImportError:
        return {'error': 'PyMuPDF not installed. Run: pip install pymupdf'}

    if not os.path.exists(pdf_path):
        return {'error': f'PDF not found: {pdf_path}'}

    try:
        doc = fitz.open(pdf_path)

        # 提取全文
        all_text = ""
        pages_text = []
        for i, page in enumerate(doc):
            text = page.get_text()
            all_text += f"\n--- Page {i+1} ---\n{text}"
            pages_text.append(text)

        # 提取标题（从首行）
        title = extract_title(pages_text[0] if pages_text else "")

        # 提取摘要
        abstract = extract_abstract(all_text)

        # 提取章节
        sections = extract_sections(all_text)

        # 深度提取
        intro_text = sections.get('introduction', '') + abstract
        method_text = sections.get('methods', '') + sections.get('experimental', '')
        results_text = sections.get('results', '') + sections.get('discussion', '')

        return {
            'title': title,
            'abstract': abstract,
            'sections': sections,
            'research_question': extract_rq(intro_text),
            'approach': extract_approach(method_text + intro_text),
            'key_findings': extract_findings(results_text),
            'limitations': extract_limitations(results_text + sections.get('conclusion', '')),
            'gap_identified': extract_gap(intro_text + sections.get('conclusion', '')),
            'comparison': extract_comparison(sections.get('discussion', '')),
            'full_text': all_text[:20000],
            'success': True
        }

    except Exception as e:
        return {'error': str(e), 'success': False}


def extract_title(first_page_text: str) -> str:
    """提取论文标题"""
    lines = first_page_text.split('\n')

    # 跳过开头噪音行，找第一行较长的英文
    for line in lines[3:20]:  # 通常标题在前几行
        stripped = line.strip()
        # 标题通常较长(>10词)，包含字母，可能有大写
        if (len(stripped) > 30 and len(stripped.split()) > 5 and
            any(c.isupper() for c in stripped) and
            not any(x in stripped.lower() for x in ['http://', 'doi:', 'figure', 'tab.'])):
            # 清理
            title = re.sub(r'\s+', ' ', stripped)
            return title[:200]

    return "Title not detected"


def extract_abstract(text: str) -> str:
    """提取摘要"""
    # 找 "abstract" 关键词后的内容，到下一个章节标记
    text_lower = text.lower()

    # 方法1: 找 Abstract 标题
    abstract_idx = text_lower.find('abstract')
    if abstract_idx >= 0:
        # 找到 abstract 后的内容
        start = text.find('\n', abstract_idx) + 1
        if start > abstract_idx:
            # 找下一个章节（通常是大写标题或数字）
            end_text = text_lower[start:start+5000]
            # 常见的章节结束标记
            for marker in ['\n1.', '\nintroduction', '\nbackground', '\n i.', '\n1 ']:
                idx = end_text.find(marker)
                if idx > 50:  # 确保有内容
                    return text[start:start+idx].strip()

            # 如果没找到章节结束，取前1000字
            return text[start:start+1000].strip()

    # 方法2: 找第一段较长的文字（假设是摘要）
    paragraphs = text.split('\n\n')
    for p in paragraphs[:5]:
        p = p.strip()
        if len(p) > 200 and len(p) < 2000:
            # 检查是否包含研究相关词汇
            if any(x in p.lower() for x in ['we', 'this paper', 'study', 'investigate', 'demonstrate', 'method']):
                return p[:1500]

    return ""


def extract_sections(text: str) -> Dict[str, str]:
    """提取论文各章节"""
    sections = {
        'abstract': '',
        'introduction': '',
        'methods': '',
        'experimental': '',
        'results': '',
        'discussion': '',
        'conclusion': ''
    }

    # 定义章节标记（按优先级排序）
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

        # 检测新章节
        new_section = None
        for sec_name, marker_list in markers:
            for marker in marker_list:
                # 精确匹配开头（避免误匹配页面中间的词）
                if line_lower.startswith(marker) or line_lower == marker:
                    new_section = sec_name
                    break
            if new_section:
                break

        # 检测 "1. Introduction" 格式
        if re.match(r'^\s*\d+\.\s+(?:introduction|background|method|experimental|result|discussion|conclusion)', line_lower):
            for sec_name in ['introduction', 'methods', 'results', 'discussion', 'conclusion']:
                if sec_name in line_lower:
                    new_section = sec_name
                    break

        if new_section and new_section != current_section:
            # 保存之前章节
            if current_section and current_lines:
                sections[current_section] = '\n'.join(current_lines)

            current_section = new_section
            current_lines = [line_stripped]
        elif current_section:
            current_lines.append(line_stripped)

    # 保存最后一个章节
    if current_section and current_lines:
        sections[current_section] = '\n'.join(current_lines)

    # 限制每个章节的长度
    for k in sections:
        if len(sections[k]) > 15000:
            sections[k] = sections[k][:15000]

    return sections


def extract_rq(text: str) -> str:
    """提取研究问题"""
    patterns = [
        r"(?:We|Here|This paper|This work)\s+(?:investigate|study|demonstrate|propose|develop|present)\s+(?:the\s+)?(?:of\s+)?([^.]+?)(?:\.|,)",  # noqa: E501
        r"(?:goal|objective|purpose)\s+(?:of|is|was)?\s*:?\s*([^.]+?)(?:\.|,)",
        r"(?:aim|focus)\s+(?:to|on)\s+([^.]+?)(?:\.|,)",
        r"investigate\s+(?:the\s+)?(?:of\s+)?([^.]+?)(?:\.|,)",
        r"study\s+(?:the\s+)?(?:of\s+)?([^.]+?)(?:\.|,)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            rq = match.group(1).strip()
            # 清理
            rq = re.sub(r'\s+', ' ', rq)
            if len(rq) > 10:
                return rq[:200]

    return ""


def extract_approach(text: str) -> str:
    """提取技术方法"""
    found = []

    # 学术技术词汇
    tech_keywords = [
        # THz产生方法
        'tilted pulse front', 'optical rectification', 'photoconductive antenna',
        'filamentation', 'laser-induced plasma', 'two-color', 'four-wave mixing',
        'photomixing', 'quantum cascade', 'QCL', 'difference frequency generation',
        # 材料
        'LiNbO3', 'GaAs', 'ZnTe', 'GaSe', 'DAST', 'OH1', 'LT-GaAs',
        'InGaAs', 'ErAs', 'semi-insulating',
        # 检测方法
        'electro-optic sampling', 'bolometer', 'pyroelectric', 'Auston switch',
        'photoconductive', 'time-domain',
        # 结构
        'plasmonic', 'bow-tie', 'dipole', 'metasurface', 'nanoantenna',
    ]

    text_lower = text.lower()
    for kw in tech_keywords:
        if kw.lower() in text_lower:
            found.append(kw)

    if found:
        return "Methods: " + ", ".join(found[:10])

    # 尝试提取参数
    params = []
    param_patterns = [
        r'(\d+(?:\.\d+)?\s*(?:nm|μm|THz|GHz|mJ|μJ|fs|ps|MW|GW|kV/cm))',
        r'(\d+\s*(?:nm|μm|THz))\s+(?:pump|laser|wavelength)',
    ]

    for pattern in param_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        params.extend(matches)

    if params:
        return "Parameters: " + ", ".join(params[:6])

    return ""


def extract_findings(text: str) -> List[str]:
    """提取关键发现（含数值）"""
    findings = []

    patterns = [
        # 带单位的数值
        r'(\d+(?:\.\d+)?\s*(?:THz|GHz))\s*(?:peak|output|bandwidth|center\s+frequency|range)?',
        r'(\d+(?:\.\d+)?\s*(?:mJ|μJ))\s*(?:pulse|output|energy)?',
        r'(\d+(?:\.\d+)?\s*(?:MW|GW|kV/cm))\s*(?:peak|field|intensity)?',
        # 百分比
        r'(\d+(?:\.\d+)?%)\s*(?:efficiency|conversion)?',
        # achievements
        r'achieved\s+(?:a\s+)?(?:peak\s+)?(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ|MW|GW|%)?)',
        r'demonstrated\s+(?:a\s+)?(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ|MW|GW|%)?)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            if m and len(m) > 2 and m not in findings:
                findings.append(m)

    return findings[:8]


def extract_limitations(text: str) -> List[str]:
    """提取局限性"""
    limitations = []

    patterns = [
        r"(?:limitation|drawback|disadvantage)\s+(?:of|is|are)\s+([^.]+)",
        r"(?:However|Nevertheless|Yet)\s+[^,]+,\s*([^.]+?)(?:\s+limit|\s+restrict|\s+prevent)",
        r"future\s+(?:work|research|study)\s+(?:should|needs)\s+([^.]+)",
        r"(?:require|needed)\s+([^,]+)\s+(?:further|more)\s+(?:work|research|study)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            m = m.strip()
            if len(m) > 30 and len(m) < 300 and m not in limitations:
                limitations.append(m)

    return limitations[:3]


def extract_gap(text: str) -> str:
    """提取研究空白"""
    patterns = [
        r"(?:gap|lack|missing|unexplored|unresolved)\s+(?:of|in|for|with)\s+([^.]+?)(?:\.|,|$)",
        r"no\s+(?:systematic\s+)?(?:study|research|work|comparison)\s+(?:has\s+been\s+)?(?:done|conducted|performed)\s+(?:on|for|in)\s+([^.]+?)(?:\.|,|$)",  # noqa: E501
        r"(?:remains|still)\s+(?:to\s+be\s+)?(?:investigated|studied|explored|resolved)\s+([^.]+?)(?:\.|,|$)",
        r"(?:however|but)\s+[^,]+,\s*([^.]+?)\s+(?:has\s+not|hasn't|not\s+been)\s+(?:studied|investigated|explored)",  # noqa: E501
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            gap = match.group(0)[:250]
            gap = re.sub(r'\s+', ' ', gap)
            return gap

    return ""


def extract_comparison(text: str) -> str:
    """提取与其他工作的比较"""
    patterns = [
        r"(?:compared to|compared with|versus|vs\.)\s+([^.]+)",
        r"(?:higher|lower|better|worse|more|less)\s+than\s+([^.]+?)(?:\.|,|$)",
        r"(?:whereas|while)\s+([^,]+)\s+(?:achieves|shows|demonstrates|provides)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            comp = match.group(0)[:150]
            comp = re.sub(r'\s+', ' ', comp)
            return comp

    return ""


def scan_zotero_storage(storage_path: str, max_pdfs: int = 100) -> List[Tuple[str, Dict]]:
    """
    扫描 Zotero 本地存储，深度分析所有 PDF

    Returns:
        List of (pdf_path, analysis_result) tuples
    """
    results = []

    if not os.path.exists(storage_path):
        print(f"Storage path not found: {storage_path}")
        return results

    # 遍历所有子目录
    dirs = os.listdir(storage_path)
    print(f"Found {len(dirs)} items in Zotero storage")

    count = 0
    for item_key in dirs:
        item_dir = os.path.join(storage_path, item_key)
        if not os.path.isdir(item_dir):
            continue

        # 找 PDF 文件
        pdfs = [f for f in os.listdir(item_dir) if f.endswith('.pdf')]
        if not pdfs:
            continue

        pdf_path = os.path.join(item_dir, pdfs[0])

        # 提取标题（用于判断是否是 THz 相关）
        try:
            import fitz
            doc = fitz.open(pdf_path)
            first_page_text = doc[0].get_text() if len(doc) > 0 else ""
            doc.close()
        except:
            continue

        # 快速判断主题
        if 'terahertz' in first_page_text.lower() or 'thz' in first_page_text.lower():
            print(f"Analyzing: {pdfs[0][:60]}...")
            analysis = analyze_paper(pdf_path)
            results.append((pdf_path, analysis))
            count += 1
            if count >= max_pdfs:
                break

    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Zotero PDF Deep Analysis v2')
    parser.add_argument('--scan', action='store_true', help='Scan all Zotero PDFs')
    parser.add_argument('--file', help='Analyze specific PDF file')
    parser.add_argument('--max', type=int, default=50, help='Max PDFs to scan')
    parser.add_argument('--output', help='Output JSON file')

    args = parser.parse_args()

    if args.file:
        # 分析单个文件
        print(f"Analyzing: {args.file}")
        result = analyze_paper(args.file)
        print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])

    elif args.scan:
        # 扫描 Zotero 本地存储
        print(f"Scanning Zotero storage: {ZOTERO_STORAGE}")
        results = scan_zotero_storage(ZOTERO_STORAGE, args.max)

        print(f"\n=== Analysis Results ({len(results)} papers) ===")
        for pdf_path, result in results:
            if result.get('success'):
                print(f"\n--- {result.get('title', 'N/A')[:60]} ---")
                print(f"  Research Q: {result.get('research_question', 'N/A')[:80]}")
                print(f"  Approach: {result.get('approach', 'N/A')[:80]}")
                print(f"  Findings: {result.get('key_findings', [])}")
                gap = result.get('gap_identified', '')
                if gap:
                    print(f"  Gap: {gap[:100]}")
            else:
                print(f"\n--- {pdf_path} ---")
                print(f"  Error: {result.get('error')}")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump([{'path': p, 'analysis': a} for p, a in results], f, indent=2, ensure_ascii=False)
            print(f"\nSaved to: {args.output}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()