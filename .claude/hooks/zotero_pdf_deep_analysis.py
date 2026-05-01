#!/usr/bin/env python3
"""
Zotero PDF Deep Analysis - 基于 Zotero 本地库的深度论文分析

功能：
1. 通过 DOI 或标题搜索 Zotero 数据库
2. 映射到本地 PDF 存储路径
3. 使用 PyMuPDF 提取全文
4. 结构化解析：引言、方法、结果、讨论、结论
5. 深度提取：研究问题、技术方法、关键发现、局限性、Gap 自述

Zotero 存储路径: E:/PostGraduate/Science_softwares/Zotero/data/storage/
"""

import os
import re
import sqlite3
import json
import codecs
import sys
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# 设置标准输出编码
if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Zotero 数据库和存储路径
ZOTERO_DB = "E:/PostGraduate/Science_softwares/Zotero/data/zotero.sqlite"
ZOTERO_STORAGE = "E:/PostGraduate/Science_softwares/Zotero/data/storage"


@dataclass
class PaperInfo:
    """论文完整信息"""
    zotero_key: str
    title: str
    authors: List[str]
    year: int
    journal: str
    doi: str
    pdf_path: Optional[str]
    full_text: str
    sections: Dict[str, str]


class ZoteroPDFSearcher:
    """Zotero 本地库搜索器"""

    def __init__(self):
        self.db_path = ZOTERO_DB
        self.storage_path = ZOTERO_STORAGE

    def connect(self) -> sqlite3.Connection:
        """连接 Zotero 数据库"""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def find_item_by_doi(self, doi: str) -> Optional[Dict]:
        """通过 DOI 查找 Zotero 条目"""
        if not os.path.exists(self.db_path):
            return None

        try:
            conn = self.connect()
            cursor = conn.cursor()

            # DOI 存储在 itemData 表中，通过 itemID 关联
            # 先查找包含 DOI 的 item
            cursor.execute("""
                SELECT DISTINCT itemID FROM itemData
                WHERE fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'DOI')
                AND valueID IN (SELECT valueID FROM itemDataValues WHERE text LIKE ?)
            """, (f"%{doi}%",))

            rows = cursor.fetchall()
            conn.close()

            if rows:
                return self._get_item_info(rows[0]['itemID'])
        except Exception as e:
            print(f"Database error: {e}")

        return None

    def find_item_by_title(self, title: str, max_results: int = 5) -> List[Dict]:
        """通过标题模糊搜索 Zotero 条目"""
        if not os.path.exists(self.db_path):
            return []

        try:
            conn = self.connect()
            cursor = conn.cursor()

            # 搜索标题
            cursor.execute("""
                SELECT itemID, title FROM items
                WHERE title LIKE ? AND itemTypeID = 1
                ORDER BY dateAdded DESC
                LIMIT ?
            """, (f"%{title[:30]}%", max_results))

            rows = cursor.fetchall()
            conn.close()

            results = []
            for row in rows:
                item_info = self._get_item_info(row['itemID'])
                if item_info:
                    results.append(item_info)

            return results
        except Exception as e:
            print(f"Database error: {e}")
            return []

    def _get_item_info(self, item_id: int) -> Optional[Dict]:
        """获取单个条目的完整信息"""
        try:
            conn = self.connect()
            cursor = conn.cursor()

            # 基本信息
            cursor.execute("""
                SELECT title, itemTypeID, dateAdded FROM items WHERE itemID = ?
            """, (item_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None

            item_info = {
                'itemID': item_id,
                'title': row['title'],
                'dateAdded': row['dateAdded']
            }

            # 获取字段数据
            cursor.execute("""
                SELECT fieldName, text FROM itemData
                JOIN fields ON itemData.fieldID = fields.fieldID
                JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
                WHERE itemID = ?
            """, (item_id,))

            for field_row in cursor.fetchall():
                fname = field_row['fieldName']
                fvalue = field_row['text']
                if fname == 'DOI':
                    item_info['doi'] = fvalue
                elif fname == 'date':
                    item_info['year'] = int(fvalue[:4]) if fvalue and len(fvalue) >= 4 else 0
                elif fname == 'publicationTitle':
                    item_info['journal'] = fvalue

            # 获取作者
            cursor.execute("""
                SELECT firstName, lastName FROM itemCreators WHERE itemID = ? AND creatorTypeID = 1
            """, (item_id,))
            authors = []
            for auth_row in cursor.fetchall():
                if auth_row['lastName']:
                    authors.append(f"{auth_row['lastName']}, {auth_row['firstName'] or ''}".strip())
            item_info['authors'] = authors[:5]

            # 查找附件（PDF）
            cursor.execute("""
                SELECT key, path FROM itemAttachments
                JOIN items ON itemAttachments.parentItemID = items.itemID
                WHERE items.itemID = ?
                AND path LIKE '%.pdf'
            """, (item_id,))

            attachment = cursor.fetchone()
            if attachment:
                key = attachment['key']
                # PDF 实际存储在 storage/<key>/<filename>
                pdf_rel_path = attachment['path']
                if pdf_rel_path:
                    # 提取文件名
                    filename = os.path.basename(pdf_rel_path)
                    full_pdf_path = os.path.join(self.storage_path, key, filename)
                    if os.path.exists(full_pdf_path):
                        item_info['pdf_path'] = full_pdf_path
                    else:
                        # 尝试直接查找
                        alt_path = os.path.join(self.storage_path, key)
                        if os.path.exists(alt_path):
                            # 列出目录内容
                            files = os.listdir(alt_path)
                            pdfs = [f for f in files if f.endswith('.pdf')]
                            if pdfs:
                                item_info['pdf_path'] = os.path.join(alt_path, pdfs[0])

            conn.close()
            return item_info

        except Exception as e:
            print(f"Error getting item info: {e}")
            return None

    def list_all_items(self, limit: int = 50) -> List[Dict]:
        """列出所有条目（用于调试）"""
        if not os.path.exists(self.db_path):
            return []

        try:
            conn = self.connect()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT itemID, title FROM items
                WHERE itemTypeID = 1
                ORDER BY dateAdded DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                info = self._get_item_info(row['itemID'])
                if info:
                    results.append(info)

            conn.close()
            return results

        except Exception as e:
            print(f"Database error: {e}")
            return []


class PDFDeepAnalyzer:
    """PDF 深度分析器"""

    def __init__(self):
        self.papers_db_path = None  # 将从 Zotero 获取
        self._check_pymupdf()

    def _check_pymupdf(self):
        """检查 PyMuPDF 是否可用"""
        try:
            import fitz
            self.has_pymupdf = True
            print("PyMuPDF available")
        except ImportError:
            self.has_pymupdf = False
            print("PyMuPDF not installed. Run: pip install pymupdf")

    def analyze_pdf(self, pdf_path: str) -> Dict:
        """
        深度分析 PDF 内容
        返回结构化的论文内容
        """
        if not os.path.exists(pdf_path):
            return {'error': f'PDF not found: {pdf_path}'}

        if not self.has_pymupdf:
            return {'error': 'PyMuPDF not available'}

        import fitz

        try:
            doc = fitz.open(pdf_path)
            all_text = ""
            pages_text = []

            for i, page in enumerate(doc):
                text = page.get_text()
                all_text += f"\n--- Page {i+1} ---\n{text}"
                pages_text.append(text)

            # 结构化解析
            sections = self._extract_sections(all_text)

            # 深度提取
            analysis = {
                'full_text': all_text,
                'sections': sections,
                'research_question': self._extract_research_question(sections),
                'approach': self._extract_approach(sections),
                'key_findings': self._extract_key_findings(sections),
                'limitations': self._extract_limitations(sections),
                'gap_identified': self._extract_gap(sections),
                'comparison': self._extract_comparison(sections),
                'success': True
            }

            return analysis

        except Exception as e:
            return {'error': str(e), 'success': False}

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """提取论文各章节内容"""
        sections = {
            'title': '',
            'abstract': '',
            'introduction': '',
            'methods': '',
            'results': '',
            'discussion': '',
            'conclusion': ''
        }

        # 分割行
        lines = text.split('\n')

        # 定义章节标记（常见变体）
        section_markers = {
            'abstract': ['abstract', '摘要', 'summary'],
            'introduction': ['introduction', '1.', 'i.', '背景', '研究背景'],
            'methods': ['method', 'experimental', 'setup', 'procedure', '实验', '原理'],
            'results': ['result', 'experiment', 'observation', '结果', '实验结果'],
            'discussion': ['discussion', 'analysis', '分析', '讨论'],
            'conclusion': ['conclusion', 'summary', 'conclude', '总结', '结论']
        }

        current_section = None
        current_content = []

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            # 检测标题行（较短且居中或加粗格式）
            is_title = len(line_stripped) < 200 and len(line_stripped.split()) < 15

            # 检测章节转换
            new_section = None
            for sec_name, markers in section_markers.items():
                for marker in markers:
                    if marker.lower() in line_lower:
                        new_section = sec_name
                        break
                if new_section:
                    break

            if new_section and new_section != current_section:
                # 保存之前的内容
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content)

                current_section = new_section
                current_content = []
                current_content.append(line_stripped)
            elif current_section:
                current_content.append(line_stripped)

        # 保存最后一个章节
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)

        # 尝试提取标题（通常在最开始）
        if sections.get('introduction') or sections.get('abstract'):
            # 标题一般在文本最开头
            first_lines = text.split('\n')[:20]
            potential_title = ' '.join([l.strip() for l in first_lines if len(l.strip()) < 150 and len(l.strip()) > 10])
            if potential_title:
                sections['title'] = potential_title[:200]

        # 如果没有找到 abstract，尝试从开头提取
        if not sections['abstract'] and text:
            # 假设 abstract 在前 500 字内
            first_500 = text[:2000].lower()
            if 'abstract' in first_500:
                start_idx = text[:2000].find('abstract')
                end_idx = min(start_idx + 1000, len(text))
                # 找到下一个章节标记
                for marker in ['introduction', '1.', 'background', '背景']:
                    idx = text.lower().find(marker, start_idx + 10)
                    if idx > 0 and idx < end_idx:
                        end_idx = idx
                sections['abstract'] = text[start_idx:end_idx].strip()

        return {k: v[:10000] for k, v in sections.items()}  # 限制长度

    def _extract_research_question(self, sections: Dict) -> str:
        """提取研究问题"""
        text = sections.get('introduction', '') + sections.get('abstract', '')

        patterns = [
            r"(?:We|Here|This paper|This work) (?:investigate|study|demonstrate|propose|develop|present)\s+(?:the\s+)?([^.]+)",
            r"(?:goal|objective|purpose)\s+(?:of|is|was)?\s*:?\s*([^.]+)",
            r"(?:aim|focus)\s+(?:to|on)\s+([^.]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]

        return "Not explicitly stated"

    def _extract_approach(self, sections: Dict) -> str:
        """提取技术方法"""
        text = sections.get('methods', '') + sections.get('introduction', '')

        # 学术论文常见技术词汇
        tech_patterns = [
            r"(?:using|via|with|by means of)\s+([^,.\n]+)",
            r"(?:laser|pump|wavelength|frequency|THz|GHz|nm|fs|ps)\s*:?\s*([0-9][^,.\n]*)",
            r"(?:tilted pulse front|optical rectification|photoconductive|filamentation|two-color|QCL|quantum cascade)",
        ]

        found_tech = []
        text_lower = text.lower()

        tech_keywords = [
            'tilted pulse front', 'optical rectification', 'photoconductive',
            'filamentation', 'two-color', 'QCL', 'quantum cascade',
            'LiNbO3', 'GaAs', 'ZnTe', 'GaSe', 'DAST', 'LT-GaAs',
            'plasmonic', 'metasurface', 'bolometer', 'electro-optic'
        ]

        for kw in tech_keywords:
            if kw.lower() in text_lower:
                found_tech.append(kw)

        if found_tech:
            return "Uses: " + ", ".join(found_tech[:8])

        # 尝试提取数值参数
        params = re.findall(r"(\d+(?:\.\d+)?\s*(?:nm|μm|THz|GHz|mJ|μJ|fs|ps|MW|GW))", text)
        if params:
            return f"Parameters: {', '.join(params[:6])}"

        return "Method not clearly specified"

    def _extract_key_findings(self, sections: Dict) -> List[str]:
        """提取关键发现"""
        findings = []
        text = sections.get('results', '') + sections.get('discussion', '')

        # 数值发现
        patterns = [
            r"(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ|MW|GW|cm²/Vs|%|nm|fs|ps))\s*(?:peak|output|bandwidth|efficiency|field)?",
            r"achieved\s+(?:a\s+)?(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ|MW|GW))",
            r"(?:reach|reach|obtain|demonstrate)\s+(?:of\s+)?(\d+(?:\.\d+)?\s*(?:THz|GHz|mJ|μJ|MW|GW))",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                if m not in findings and len(m) > 2:
                    findings.append(m)

        return findings[:8]

    def _extract_limitations(self, sections: Dict) -> List[str]:
        """提取局限性（作者自述）"""
        limitations = []
        text = sections.get('discussion', '') + sections.get('conclusion', '')

        patterns = [
            r"(?:limitation|drawback|disadvantage|challenge)\s+(?:of|is|are|with|for)\s+([^.]+)",
            r"(?:However|Nevertheless)\s+[^,]+,\s*([^.]+)\s+(?:limit|restrict|prevent)",
            r"future\s+(?:work|research|study)\s+(?:should|needs|will)\s+([^.]+)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                if len(m) > 20 and len(m) < 200 and m not in limitations:
                    limitations.append(m.strip())

        return limitations[:3]

    def _extract_gap(self, sections: Dict) -> str:
        """提取作者指出的研究空白"""
        text = sections.get('introduction', '') + sections.get('discussion', '') + sections.get('conclusion', '')

        patterns = [
            r"(?:gap|lack|missing|unexplored|unresolved|unanswered)\s+(?:of|in|for|with)\s+([^.]+)",
            r"(?:remains|still)\s+(?:to\s+be\s+)?(investigated|studied|explored|resolved|answered)",
            r"no\s+(?:systematic\s+)?(?:study|research|work)\s+(?:has\s+been\s+)?(?:done|conducted|performed|on)\s+([^.]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)[:200]

        return ""

    def _extract_comparison(self, sections: Dict) -> str:
        """提取与其他工作的比较"""
        text = sections.get('discussion', '') + sections.get('introduction', '')

        patterns = [
            r"(?:compared to|compared with|versus|vs\.)\s+([^.]+)",
            r"(?:higher|lower|better|worse|more|less)\s+than\s+([^.]+)",
            r"(?:whereas|while)\s+([^.]+?)\s+(?:achieves|shows|provides|demonstrates)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)[:150]

        return ""


def search_and_analyze(doi: str = None, title: str = None) -> Dict:
    """
    搜索 Zotero 并深度分析 PDF

    使用方式:
        python zotero_pdf_deep_analysis.py --doi "10.1038/nphoton.2007.177"
        python zotero_pdf_deep_analysis.py --title "Coherent control of terahertz supercontinuum"
    """
    searcher = ZoteroPDFSearcher()
    analyzer = PDFDeepAnalyzer()

    result = {
        'zotero_item': None,
        'pdf_analysis': None,
        'success': False
    }

    # 搜索 Zotero
    if doi:
        item = searcher.find_item_by_doi(doi)
        if item:
            result['zotero_item'] = item
            print(f"Found Zotero item: {item.get('title', 'N/A')[:60]}")
            print(f"  Authors: {', '.join(item.get('authors', [])[:2])}")
            print(f"  Year: {item.get('year', 'N/A')}")
            print(f"  DOI: {item.get('doi', 'N/A')}")

            if item.get('pdf_path'):
                print(f"  PDF: {item['pdf_path'][:80]}")

                # 分析 PDF
                analysis = analyzer.analyze_pdf(item['pdf_path'])
                result['pdf_analysis'] = analysis

                if analysis.get('success'):
                    print("\n=== PDF Analysis Results ===")
                    print(f"Research Question: {analysis.get('research_question', 'N/A')[:100]}")
                    print(f"Approach: {analysis.get('approach', 'N/A')[:100]}")
                    print(f"Key Findings: {analysis.get('key_findings', [])}")
                    print(f"Gap Identified: {analysis.get('gap_identified', 'N/A')[:100]}")
                    result['success'] = True
                else:
                    print(f"PDF analysis failed: {analysis.get('error')}")
            else:
                print("No PDF found in Zotero")

        else:
            print(f"No Zotero item found for DOI: {doi}")

    elif title:
        items = searcher.find_item_by_title(title)
        if items:
            print(f"Found {len(items)} Zotero items:")
            for i, item in enumerate(items):
                print(f"  {i+1}. {item.get('title', 'N/A')[:60]}")
                print(f"     Authors: {', '.join(item.get('authors', [])[:2])}")
                print(f"     PDF: {item.get('pdf_path', 'N/A')[:60] if item.get('pdf_path') else 'No PDF'}")

            # 分析第一个有 PDF 的
            for item in items:
                if item.get('pdf_path'):
                    result['zotero_item'] = item
                    analysis = analyzer.analyze_pdf(item['pdf_path'])
                    result['pdf_analysis'] = analysis
                    if analysis.get('success'):
                        result['success'] = True
                    break
        else:
            print(f"No Zotero items found for title: {title}")

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Zotero PDF Deep Analysis')
    parser.add_argument('--doi', help='Search by DOI')
    parser.add_argument('--title', help='Search by title')
    parser.add_argument('--list', action='store_true', help='List all Zotero items')
    parser.add_argument('--storage', help='Storage path (overrides default)')

    args = parser.parse_args()

    global ZOTERO_DB, ZOTERO_STORAGE

    if args.storage:
        ZOTERO_STORAGE = args.storage
        ZOTERO_DB = os.path.join(os.path.dirname(args.storage), 'zotero.sqlite')

    if args.list:
        searcher = ZoteroPDFSearcher()
        items = searcher.list_all_items(limit=20)
        print(f"\n=== Zotero Items ({len(items)} shown) ===")
        for item in items:
            print(f"- {item.get('title', 'N/A')[:60]}")
            print(f"  Authors: {', '.join(item.get('authors', [])[:2])}")
            print(f"  Year: {item.get('year', 'N/A')}")
            print(f"  PDF: {item.get('pdf_path', 'N/A')[:60] if item.get('pdf_path') else 'No PDF'}")
            print()

    elif args.doi or args.title:
        result = search_and_analyze(doi=args.doi, title=args.title)
        if result['success']:
            print("\n=== Full Analysis ===")
            print(json.dumps(result['pdf_analysis'], indent=2, ensure_ascii=False)[:2000])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()