#!/usr/bin/env python3
"""
Multi-Source Academic Paper Writing System v4.3 (论文级结构 + Tavily深度集成 + PDF全文提取)

核心改进 vs v4.2:
1. Tavily 深度集成 - 提取研究空白和最新趋势
2. PDF 全文分析 - 提取key_metrics和physical_insight
3. LLM-assisted 分析增强 - 更全面的论文内容提取
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
import json as json_module
import codecs
import sqlite3
import requests
json = json_module
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
import openai as openai_module

class MultiLLMClient:
    """多源LLM客户端 - 自动切换可用 provider"""
    def __init__(self, providers):
        self.providers = providers
        self.client = None
        self.current_provider = None
        self._init_client()

    def _init_client(self):
        import requests
        for p in self.providers:
            try:
                headers = {
                    'Authorization': f'Bearer {p["api_key"]}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': p['model'],
                    'messages': [{'role': 'user', 'content': 'OK'}],
                    'max_tokens': 5
                }
                r = requests.post(f'{p["base_url"]}/chat/completions', json=data, headers=headers, timeout=15)
                if r.status_code == 200:
                    self.client = p
                    self.current_provider = p['name']
                    print(f"  [LLM] Connected to {p['name']}: {p['model']}")
                    return
            except:
                continue
        print(f"  [LLM] No LLM provider available")

    def chat_completions_create(self, messages, temperature=0.1, max_tokens=1500):
        import requests
        if not self.client:
            raise Exception("No LLM client available")

        headers = {
            'Authorization': f'Bearer {self.client["api_key"]}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': self.client['model'],
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        r = requests.post(f'{self.client["base_url"]}/chat/completions', json=data, headers=headers, timeout=60)
        r.raise_for_status()
        return r.json()

# 全局LLM客户端
_llm_client = None

def get_llm_client():
    global _llm_client
    if _llm_client is None:
        _llm_client = MultiLLMClient(LLM_PROVIDERS)
    return _llm_client

# =============================================================================
# 模板系统 (Template System) - v5.1 新增
# =============================================================================

TEMPLATE_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'DHL', 'templates'))

class TemplateFiller:
    """模板填充器 - 支持 LaTeX 和 Markdown 模板"""

    def __init__(self, template_path: str = None, template_type: str = 'md'):
        self.template_path = template_path
        self.template_type = template_type
        self.template_content = ''
        if template_path and os.path.exists(template_path):
            self.load_template(template_path)
        elif template_type == 'tex':
            # 默认使用 LaTeX 模板
            default_path = os.path.join(TEMPLATE_DIR, 'academic_review_template.tex')
            if os.path.exists(default_path):
                self.load_template(default_path)
            else:
                print(f"  [Template] WARNING: LaTeX template not found at {default_path}")
        else:
            # 默认使用 Markdown 模板
            default_path = os.path.join(TEMPLATE_DIR, 'academic_review_template.md')
            if os.path.exists(default_path):
                self.load_template(default_path)

    def load_template(self, path: str):
        """加载模板文件"""
        with open(path, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
        self.template_path = path
        print(f"  [Template] Loaded: {os.path.basename(path)}")

    def fill(self, **kwargs) -> str:
        """填充模板占位符"""
        if not self.template_content:
            print("  [Template] WARNING: No template loaded, using default markdown")
            return self._default_formatter(**kwargs)

        content = self.template_content

        # 如果是LaTeX模板，先转换content从markdown到LaTeX
        if self.template_type == 'tex' and 'content' in kwargs:
            kwargs['content'] = self._md_to_latex(kwargs['content'])

        for key, value in kwargs.items():
            placeholder = f"${{{key}}}"
            if placeholder in content:
                content = content.replace(placeholder, str(value))

        # 处理未填充的占位符
        import re
        unfilled = re.findall(r'\$\{[^}]+\}', content)
        if unfilled:
            print(f"  [Template] WARNING: {len(unfilled)} unfilled placeholders")

        return content

    def _md_to_latex(self, md_text: str) -> str:
        """将Markdown文本转换为LaTeX格式"""
        import re

        lines = md_text.split('\n')
        result = []
        in_itemize = False
        skip_abstract = True  # 跳过 ## 摘要 因为模板已有 abstract 环境

        for line in lines:
            # 跳过一级标题（# 开头），模板已有标题
            if re.match(r'^#\s', line):
                if in_itemize:
                    result.append('\\end{itemize}')
                    in_itemize = False
                continue

            # 跳过 ## 摘要 章节 - 模板的 abstract 环境会处理
            if skip_abstract and re.match(r'^##\s', line):
                section_name = re.sub(r'^##\s+', '', line).strip()
                # 检测是否是摘要章节 - 如果是，开始跳过内容直到下一个 ## 章节
                if '摘要' in section_name or section_name == 'Abstract':
                    skip_abstract = False  # 找到摘要章节了
                    if in_itemize:
                        result.append('\\end{itemize}')
                        in_itemize = False
                    continue  # 跳过摘要标题本身
                else:
                    # 不是摘要章节，说明已经跳过了摘要
                    skip_abstract = False

            # 如果还没跳过摘要，且当前不是标题，则跳过（摘要内容不需要）
            if skip_abstract:
                continue

            # 转换二级标题 ## 为 \section
            if re.match(r'^##\s', line):
                if in_itemize:
                    result.append('\\end{itemize}')
                    in_itemize = False
                section_name = re.sub(r'^##\s+', '', line).strip()
                result.append(f'\\section{{{section_name}}}')
                continue
            # 转换三级标题 ### 为 \subsection
            elif re.match(r'^###\s', line):
                if in_itemize:
                    result.append('\\end{itemize}')
                    in_itemize = False
                section_name = re.sub(r'^###\s+', '', line).strip()
                result.append(f'\\subsection{{{section_name}}}')
                continue
            # 转换四级标题 #### 为 \subsubsection
            elif re.match(r'^####\s', line):
                if in_itemize:
                    result.append('\\end{itemize}')
                    in_itemize = False
                section_name = re.sub(r'^####\s+', '', line).strip()
                result.append(f'\\subsubsection{{{section_name}}}')
                continue
            # 转换五级标题 ##### 为 \paragraph
            elif re.match(r'^#####\s', line):
                if in_itemize:
                    result.append('\\end{itemize}')
                    in_itemize = False
                section_name = re.sub(r'^#####\s+', '', line).strip()
                result.append(f'\\paragraph{{{section_name}}}')
                continue

            # 检测列表项
            item_match = re.match(r'^[-*]\s+(.*)', line)
            if item_match:
                if not in_itemize:
                    result.append('\\begin{itemize}')
                    in_itemize = True
                result.append(f'\\item {item_match.group(1)}')
                continue
            else:
                if in_itemize:
                    result.append('\\end{itemize}')
                    in_itemize = False

            # 转换粗体 **text** 为 \textbf{text}
            line = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', line)
            # 转换斜体 *text* 为 \textit{text}
            line = re.sub(r'\*(.+?)\*', r'\\textit{\1}', line)
            # 转换行内代码 `code` 为 \texttt{code}
            line = re.sub(r'`(.+?)`', r'\\texttt{\1}', line)
            result.append(line)

        # 清理：如果最后还在itemize中，关闭它
        if in_itemize:
            result.append('\\end{itemize}')

        return '\n'.join(result)

    def _default_formatter(self, **kwargs) -> str:
        """默认格式化 - 当无模板时使用"""
        return kwargs.get('content', '')


# =============================================================================
# 质量门禁 (Quality Gate) - 改进版 v4.1
# =============================================================================

class QualityGate:
    """模拟审稿人质量门禁"""

    def __init__(self):
        self.llm_client = None
        try:
            self.llm_client = get_llm_client()
        except:
            pass

    def review(self, review_text: str, theme: str) -> Dict:
        """模拟审稿人审查生成内容"""
        if not self.llm_client:
            return {'score': 50, 'issues': [], 'passed': False}

        prompt = f"""你是一位严苛的光学/太赫兹领域资深审稿人。请审查以下学术综述内容。

**主题**: {theme}

请从以下5个维度分别评分(0-100)，然后给出综合评分：
1. **结构完整性** (20分): 是否有清晰的C-C-C结构？是否包含所有必要章节？
2. **研究空白识别** (25分): 是否正确识别并分类了5类研究空白？Gap描述是否具体？
3. **内容深度** (25分): 是否有深度的技术分析？是否避免了文献堆砌？
4. **代表性工作质量** (15分): 引用的论文是否相关？关键发现是否准确？
5. **写作质量** (15分): 是否学术规范？逻辑是否清晰？

**综述内容** (前4000字):
{review_text[:4000]}

请严格评分，返回JSON格式：
{{
    "score": 综合评分数字(0-100),
    "dimension_scores": {{
        "structure": 结构完整性分数(0-20),
        "gap_identification": 研究空白识别分数(0-25),
        "depth": 内容深度分数(0-25),
        "citations": 代表性工作质量分数(0-15),
        "writing": 写作质量分数(0-15)
    }},
    "issues": ["具体问题1", "问题2", "问题3"],
    "passed": true或false
}}

注意：严格评分，不要给出过高分数。"""

        try:
            messages = [
                {"role": "system", "content": "你是严苛的学术审稿人，评分标准高，不会给虚假高分。"},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_client.chat_completions_create(messages, temperature=0.1, max_tokens=600)
            content = response['choices'][0]['message']['content']

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json_module.loads(json_match.group(0))
                score = result.get('score', 0)
                passed = result.get('passed', False) or score >= 70
                print(f"  [QualityGate] Score: {score}, Passed: {passed}")
                return {'score': score, 'issues': result.get('issues', []), 'passed': passed}

        except Exception as e:
            print(f"  [QualityGate] Error: {e}")

        return {'score': 50, 'issues': [], 'passed': False}

    def polish(self, content: str, issues: List[str], theme: str = "") -> str:
        """根据审稿意见润色内容"""
        if not self.llm_client or not issues:
            return content

        section = content[:6000]

        prompt = f"""你是一位学术写作润色专家。请根据审稿意见深度润色学术综述。

**主题**: {theme}

**审稿意见**:
{chr(10).join(f"审稿人{i+1}: {issue}" for i, issue in enumerate(issues[:3]))}

**当前内容**:
{section}

请进行深度润色，重点解决以上问题。返回润色后的完整内容（保持所有markdown格式）。"""

        try:
            messages = [
                {"role": "system", "content": "你是学术写作润色专家，擅长提升论文质量。"},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_client.chat_completions_create(messages, temperature=0.2, max_tokens=4000)
            polished = response['choices'][0]['message']['content']
            if len(content) > 6000:
                return polished + content[6000:]
            return polished
        except:
            return content

if os.name == 'nt':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# =============================================================================
# 配置
# =============================================================================

ZOTERO_DB_BAK = "E:/PostGraduate/Science_softwares/Zotero/data/zotero.sqlite.bak"
ZOTERO_STORAGE = "E:/PostGraduate/Science_softwares/Zotero/data/storage"
OUTPUT_DIR = "DHL"
EMAIL = "research@example.com"
OPENALEX_API_BASE = "https://api.openalex.org"

# LLM API
ZCHAT_API_KEY = os.getenv("ZCHAT_API_KEY", "sk-uK1cqmlDbsRaUyNS2lkcUGC6FRewPLUZ7GWbEvjrhDMzM6Rf")
ZCHAT_BASE_URL = os.getenv("ZCHAT_BASE_URL", "https://api.zchat.tech/v1")
ZCHAT_MODEL = "gpt-5-thinking"

DUCKCODING_API_KEY = os.getenv("DUCKCODING_API_KEY", "sk-p4O8ENsDylgdGfnSwwDAJAaQVNghknzz3uITiSiL4DaN1V2L")
DUCKCODING_BASE_URL = os.getenv("DUCKCODING_BASE_URL", "https://www.duckcoding.ai/v1")
DUCKCODING_MODEL = "gpt-4o-mini"

LLM_PROVIDERS = [
    {'name': 'DuckCoding', 'api_key': DUCKCODING_API_KEY, 'base_url': DUCKCODING_BASE_URL, 'model': DUCKCODING_MODEL},
    {'name': 'ZChat', 'api_key': ZCHAT_API_KEY, 'base_url': ZCHAT_BASE_URL, 'model': ZCHAT_MODEL},
]

GAP_TYPES = {
    'Methodological': '研究方法的空白或不足',
    'Parameter': '参数空间/条件范围的空白',
    'Comparative': '系统性对比的空白',
    'Theoretical': '理论框架/机理的空白',
    'Condition': '适用条件/范围的空白',
}

TECH_ROUTES = {
    'PCA (光电导天线)': ['photoconductive', 'PCA', 'Auston switch', 'bow-tie', 'dipole antenna', 'strip-line', 'interdigitated', '光电导', '光载流子'],
    '光整流': ['optical rectification', 'second-harmonic', 'difference frequency', 'DFG', 'LiNbO3', 'ZnTe', 'GaSe', 'DAST', 'tilted pulse front', '光整流', '倾斜波前', '铌酸锂', '钽酸锂', 'ZnTe晶体', 'LiNbO3'],
    '激光等离子体': ['laser plasma', 'filamentation', 'two-color', 'four-wave mixing', 'FWM', 'air plasma', 'laser-induced', '双色激光', '激光光丝', '飞秒激光光丝', '四波混频', '光丝辐射'],
    'QCL (量子级联激光器)': ['quantum cascade', 'QCL', 'intersubband', 'heterostructure', 'QWIP', '量子级联'],
    '超表面/等离子体': ['metasurface', 'plasmonic', 'nanoantenna', 'resonant', 'split-ring', 'SRR', '超表面', '等离子体', '纳米天线', '微纳结构'],
    '自旋THz': ['自旋电子', 'spintronic', 'spin THz', '自旋太赫兹', '铁磁异质结'],
}


# =============================================================================
# 数据结构
# =============================================================================

@dataclass
class Paper:
    """论文完整元数据"""
    id: str = ""
    zotero_key: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    journal: str = ""
    doi: str = ""
    abstract: str = ""
    citations: int = 0
    relevance: float = 0.0

    # 深度分析
    research_question: str = ""
    approach: str = ""
    tech_routes: List[str] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)
    key_metrics: List[str] = field(default_factory=list)
    physical_insight: str = ""

    # 来源追踪
    sources: List[str] = field(default_factory=list)

    def add_source(self, source: str):
        if source not in self.sources:
            self.sources.append(source)


@dataclass
class ThemeSynthesis:
    """主题综合"""
    theme: str = ""
    context: str = ""
    research_questions: List[str] = field(default_factory=list)
    tech_routes: Dict[str, List[str]] = field(default_factory=dict)
    key_findings: List[str] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)
    tradeoffs: List[str] = field(default_factory=list)
    future_directions: List[str] = field(default_factory=list)
    representative_papers: List[Dict] = field(default_factory=list)
    latest_trends: str = ""


# =============================================================================
# 数据源 1: Zotero 数据库
# =============================================================================

class ZoteroDBReader:
    """读取 Zotero .bak 数据库"""

    def __init__(self, db_path: str = ZOTERO_DB_BAK):
        self.db_path = db_path
        self._conn = None

    def connect(self):
        try:
            self._conn = sqlite3.connect(f'file:{self.db_path}?mode=ro', uri=True)
            print(f"  [Zotero] Connected to {self.db_path}")
            return True
        except Exception as e:
            print(f"  [Zotero] Connection failed: {e}")
            return False

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def get_all_journal_articles(self) -> List[Dict]:
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT
                i.key as zotero_key,
                i.itemID,
                (SELECT value FROM itemDataValues WHERE valueID = (
                    SELECT valueID FROM itemData WHERE itemID = i.itemID AND fieldID = 1
                )) as title,
                (SELECT value FROM itemDataValues WHERE valueID = (
                    SELECT valueID FROM itemData WHERE itemID = i.itemID AND fieldID = 2
                )) as abstract,
                (SELECT value FROM itemDataValues WHERE valueID = (
                    SELECT valueID FROM itemData WHERE itemID = i.itemID AND fieldID = 6
                )) as date,
                (SELECT value FROM itemDataValues WHERE valueID = (
                    SELECT valueID FROM itemData WHERE itemID = i.itemID AND fieldID = 59
                )) as doi,
                (SELECT value FROM itemDataValues WHERE valueID = (
                    SELECT valueID FROM itemData WHERE itemID = i.itemID AND fieldID = 38
                )) as publicationTitle
            FROM items i
            WHERE i.itemTypeID = 22
        ''')

        articles = []
        for row in cursor.fetchall():
            key, item_id, title, abstract, date, doi, journal = row
            if not title:
                continue

            year = 0
            if date:
                match = re.search(r'(20\d{2}|19\d{2})', str(date))
                if match:
                    year = int(match.group(1))

            articles.append({
                'zotero_key': key,
                'itemID': item_id,
                'title': title,
                'abstract': abstract or '',
                'date': date or '',
                'year': year,
                'doi': doi or '',
                'journal': journal or '',
            })

        return articles

    def get_authors(self, itemID: int) -> List[str]:
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT c.firstName, c.lastName, c.fieldMode
            FROM creators c
            JOIN itemCreators ic ON c.creatorID = ic.creatorID
            WHERE ic.itemID = ?
            ORDER BY ic.orderIndex
        ''', (itemID,))

        authors = []
        for first, last, mode in cursor.fetchall():
            if mode == 1:
                authors.append(last)
            else:
                if first and last:
                    authors.append(f"{first} {last}")
                elif last:
                    authors.append(last)

        return authors

    def get_pdf_attachment(self, itemID: int) -> Optional[str]:
        cursor = self._conn.cursor()
        cursor.execute('''
            SELECT ia.path, i.key
            FROM itemAttachments ia
            JOIN items i ON ia.itemID = i.itemID
            WHERE ia.parentItemID = ? AND ia.contentType = 'application/pdf'
        ''', (itemID,))

        result = cursor.fetchone()
        if result:
            path_rel, attachment_key = result
            if path_rel:
                pdf_filename = os.path.basename(path_rel)
                pdf_path = os.path.join(ZOTERO_STORAGE, attachment_key, pdf_filename)
                if os.path.exists(pdf_path):
                    return pdf_path
            pdf_dir = os.path.join(ZOTERO_STORAGE, attachment_key)
            if os.path.isdir(pdf_dir):
                pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
                if pdfs:
                    return os.path.join(pdf_dir, pdfs[0])

        return None

    def search_articles(self, query: str, limit: int = 20) -> List[Dict]:
        articles = self.get_all_journal_articles()
        query_lower = query.lower()

        scored = []
        for a in articles:
            score = 0
            title_lower = a['title'].lower()
            abstract_lower = (a['abstract'] or '').lower()

            if query_lower in title_lower:
                score += 10
            if query_lower in abstract_lower:
                score += 5
            for word in query_lower.split():
                if word in title_lower:
                    score += 2
                if word in abstract_lower:
                    score += 1

            if score > 0:
                scored.append((score, a))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:limit]]


# =============================================================================
# 数据源 2: OpenAlex API
# =============================================================================

class OpenAlexReader:
    """从 OpenAlex 获取论文数据"""

    # Unpaywall API for PDF downloads
    UNPAYWALL_API = "https://api.unpaywall.org/v2/"
    EMAIL = "your@email.com"  # Used for Unpaywall polite pooling

    def search(self, query: str, max_results: int = 30) -> List[Dict]:
        params = {
            "search": query,
            "per_page": min(max_results, 100),
            "sort": "relevance_score:desc",
            "mailto": EMAIL
        }

        try:
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

                papers.append({
                    'openalex_id': w.get('id', '').split('/')[-1],
                    'doi': w.get('doi', ''),
                    'title': w.get('title', 'Untitled'),
                    'authors': [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:5]],
                    'year': w.get('publication_year', 0),
                    'journal': src.get('display_name', 'N/A'),
                    'abstract': abstract,
                    'citations': w.get('cited_by_count', 0),
                    'relevance': w.get('relevance_score', 0),
                })

            print(f"  [OpenAlex] Found {len(papers)} for '{query}'")
            return papers

        except Exception as e:
            print(f"  [OpenAlex] Error: {e}")
            return []

    def get_pdf_url(self, doi: str) -> Optional[str]:
        """从 Unpaywall 获取 PDF 下载链接"""
        if not doi:
            return None
        try:
            params = {"email": EMAIL}
            r = requests.get(f"{self.UNPAYWALL_API}{doi}", params=params, timeout=30)
            if r.status_code == 200:
                data = r.json()
                oa_location = data.get("best_oa_location", {})
                if oa_location:
                    return oa_location.get("url_for_pdf")
        except:
            pass
        return None

    def download_pdf(self, doi: str, output_dir: str) -> Optional[str]:
        """下载论文 PDF 到指定目录"""
        if not doi:
            return None

        pdf_url = self.get_pdf_url(doi)
        if not pdf_url:
            print(f"  [Unpaywall] No free PDF available for DOI: {doi}")
            return None

        try:
            os.makedirs(output_dir, exist_ok=True)
            # 生成安全文件名
            safe_doi = re.sub(r'[^a-zA-Z0-9]', '_', doi[:50])
            pdf_path = os.path.join(output_dir, f"{safe_doi}.pdf")

            if os.path.exists(pdf_path):
                print(f"  [PDF] Already exists: {pdf_path}")
                return pdf_path

            r = requests.get(pdf_url, timeout=120, stream=True)
            r.raise_for_status()

            with open(pdf_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"  [PDF] Downloaded: {os.path.basename(pdf_path)}")
            return pdf_path

        except Exception as e:
            print(f"  [PDF] Download failed: {e}")
            return None

    def get_latest_trends(self, query: str, max_results: int = 10) -> str:
        """从 OpenAlex 获取最新研究趋势（2024-2026年论文）

        当 Tavily 不可用时，作为替代方案
        """
        params = {
            "search": query,
            "per_page": max_results,
            "sort": "publication_date:desc",  # 最新论文优先
            "filter": "from_publication_date:2024-01-01",  # 只看2024年以来的
            "mailto": EMAIL
        }

        try:
            r = requests.get(f"{OPENALEX_API_BASE}/works", params=params, timeout=60)
            r.raise_for_status()
            data = r.json()

            trends = []
            for w in data.get("results", [])[:5]:
                title = w.get('title', 'Untitled')
                year = w.get('publication_year', '')
                authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:2]]
                author_str = ', '.join(authors) if authors else 'Unknown'
                citations = w.get('cited_by_count', 0)

                inv = w.get('abstract_inverted_index', {})
                abstract = ""
                if inv:
                    words = []
                    for word, positions in inv.items():
                        for pos in positions:
                            words.append((pos, word))
                    words.sort()
                    abstract = " ".join([x[1] for x in words])[:150]

                trend = f"- [{year}] {title[:60]}... ({author_str}, {citations} citations)"
                if abstract:
                    trend += f"\n  摘要: {abstract[:100]}..."
                trends.append(trend)

            if trends:
                print(f"  [OpenAlex-Trends] Extracted {len(trends)} latest trends (2024-2026)")

            return "\n".join(trends) if trends else ""

        except Exception as e:
            print(f"  [OpenAlex-Trends] Error: {e}")
            return ""


# =============================================================================
# 数据源 3: Tavily Search - 深度集成版本
# =============================================================================

class TavilySearcher:
    """从 Tavily 获取最新研究进展"""

    def __init__(self):
        self.api_key = os.getenv('TAVILY_API_KEY', '')
        self.llm_client = None
        try:
            self.llm_client = get_llm_client()
        except:
            pass

    def search(self, query: str, max_results: int = 8) -> List[Dict]:
        if not self.api_key:
            print(f"  [Tavily] No API key")
            return []

        try:
            r = requests.post(
                'https://api.tavily.com/search',
                json={
                    'api_key': self.api_key,
                    'query': query,
                    'max_results': max_results,
                    'include_answer': True,
                    'include_raw_content': True,
                },
                timeout=45
            )

            if r.status_code == 200:
                data = r.json()
                results = []
                for item in data.get('results', []):
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'content': item.get('content', ''),
                        'score': item.get('score', 0),
                        'answer': item.get('answer', ''),
                    })
                print(f"  [Tavily] Found {len(results)} results for '{query}'")
                return results

        except Exception as e:
            print(f"  [Tavily] Error: {e}")

        return []

    def extract_research_gaps(self, tavily_results: List[Dict], theme: str) -> List[Dict]:
        """从 Tavily 结果中提取研究空白"""
        if not self.llm_client or not tavily_results:
            return []

        content_parts = []
        for r in tavily_results[:5]:
            if r.get('content'):
                content_parts.append(f"标题: {r.get('title', '')}\n内容: {r.get('content', '')[:500]}")

        combined = "\n---\n".join(content_parts)

        prompt = f"""你是光学/太赫兹领域的研究专家。从以下最新研究动态中提取：
1. 目前研究的主要空白和挑战
2. 领域内公认的技术瓶颈
3. 未来研究的重点方向

主题: {theme}

研究动态:
{combined[:2000]}

请以JSON格式返回：
{{
    "identified_gaps": [
        {{"type": "Methodological/Parameter/Comparative/Theoretical/Condition", "description": "具体描述"}}
    ],
    "key_challenges": ["挑战1", "挑战2"],
    "research_trends": ["趋势1", "趋势2"]
}}

只返回JSON，不要有其他文字。"""

        try:
            messages = [
                {"role": "system", "content": "你是光学太赫兹领域的学术研究专家，擅长分析研究空白。"},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_client.chat_completions_create(messages, temperature=0.1, max_tokens=800)
            content = response['choices'][0]['message']['content']

            json_match = re.search(r'\[[\s\S]*\]|\{[\s\S]*\}', content)
            if json_match:
                result = json_module.loads(json_match.group(0))
                gaps = []
                for g in result.get('identified_gaps', []):
                    if isinstance(g, dict):
                        gaps.append(g)
                    elif isinstance(g, str):
                        gaps.append({'type': 'Condition', 'description': g})
                print(f"  [Tavily-Gap] Extracted {len(gaps)} gaps from Tavily results")
                return gaps

        except Exception as e:
            print(f"  [Tavily-Gap] Error: {e}")

        return []

    def get_latest_trends(self, tavily_results: List[Dict]) -> str:
        """从 Tavily 结果提取最新趋势摘要"""
        if not tavily_results:
            return ""

        trends = []
        for r in tavily_results[:3]:
            title = r.get('title', '')
            answer = r.get('answer', '')
            if answer:
                trends.append(f"- {answer[:200]}")
            elif title:
                trends.append(f"- {title[:100]}")

        return "\n".join(trends) if trends else ""


# =============================================================================
# 数据源 4: PDF 深度分析 - 全面提取论文内容
# =============================================================================

class PDFAnalyzer:
    """深度分析 PDF 论文"""

    def __init__(self):
        self.llm_client = None
        try:
            self.llm_client = get_llm_client()
        except:
            pass

    def analyze(self, pdf_path: str, metadata: Dict) -> Dict:
        """分析 PDF - 提取全文关键内容"""
        try:
            import fitz
        except ImportError:
            return {'error': 'PyMuPDF not installed'}

        if not os.path.exists(pdf_path):
            return {'error': 'PDF not found'}

        try:
            doc = fitz.open(pdf_path)

            if metadata.get('title'):
                title = metadata['title']
            else:
                title = self._extract_title(doc[0].get_text() if len(doc) > 0 else "")

            all_text = ""
            for page in doc:
                all_text += page.get_text() + "\n"
            doc.close()

            sections = self._extract_sections(all_text)
            intro = sections.get('introduction', '')
            abstract = sections.get('abstract', '')
            method = sections.get('methods', '') or sections.get('experimental', '')
            results = sections.get('results', '') or sections.get('discussion', '')
            conclusion = sections.get('conclusion', '')

            key_metrics = self._extract_quantitative_results(results + conclusion)
            tech_routes = self._detect_tech_routes(all_text)

            if self.llm_client and abstract:
                llm_result = self._analyze_with_llm(
                    title, abstract, intro, method, results, conclusion
                )
                if llm_result:
                    return {
                        'title': title,
                        'abstract': abstract[:500] if abstract else '',
                        'sections': sections,
                        'research_question': llm_result.get('research_question', ''),
                        'approach': llm_result.get('approach', ''),
                        'tech_routes': tech_routes,
                        'key_findings': llm_result.get('key_findings', []) + key_metrics,
                        'limitations': llm_result.get('limitations', []),
                        'gaps': llm_result.get('gaps', []),
                        'contribution': llm_result.get('contribution', ''),
                        'key_metrics': key_metrics,
                        'physical_insight': llm_result.get('physical_insight', ''),
                        'intro_sample': intro[:800] if intro else '',
                        'full_text_sample': all_text[:4000],
                        'success': True,
                        'analysis_mode': 'llm',
                    }

            return {
                'title': title,
                'abstract': abstract[:500] if abstract else '',
                'sections': sections,
                'research_question': self._extract_rq(intro),
                'approach': self._extract_approach(method + intro),
                'tech_routes': tech_routes,
                'key_findings': key_metrics + self._extract_findings(results),
                'limitations': self._extract_limitations(results + conclusion),
                'gaps': self._extract_gaps(intro + conclusion),
                'contribution': self._extract_contribution(intro),
                'key_metrics': key_metrics,
                'intro_sample': intro[:800] if intro else '',
                'full_text_sample': all_text[:4000],
                'success': True,
                'analysis_mode': 'regex',
            }

        except Exception as e:
            return {'error': str(e), 'success': False}

    def _extract_title(self, first_page: str) -> str:
        lines = first_page.split('\n')
        for line in lines[3:20]:
            stripped = line.strip()
            if (len(stripped) > 30 and len(stripped.split()) > 5 and
                any(c.isupper() for c in stripped) and
                not any(x in stripped.lower() for x in ['http://', 'doi:', 'figure', 'tab.', 'copyright'])):
                return re.sub(r'\s+', ' ', stripped)[:200]
        return "Unknown"

    def _extract_quantitative_results(self, text: str) -> List[str]:
        """提取关键量化指标"""
        metrics = []
        patterns = [
            r'(\d+(?:\.\d+)?\s*(?:THz|GHz))\s*(?:peak|output|bandwidth|range|tuning)?',
            r'(\d+(?:\.\d+)?\s*(?:mW|μW|W|mJ|μJ))\s*(?:peak|average|output|pulse|energy)?',
            r'(\d+(?:\.\d+)?%)\s*(?:efficiency|conversion|quantum)?',
            r'(\d+(?:\.\d+)?\s*(?:nm|μm|mm|cm))\s*(?:resolution|size|thickness)?',
            r'(\d+(?:\.\d+)?\s*(?:ps|fs|ns))\s*(?:pulse|duration|lifetime)?',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                m = m.strip()
                if m and len(m) > 2 and m not in metrics:
                    metrics.append(m)

        seen = set()
        unique_metrics = []
        for m in metrics:
            key = re.sub(r'\s+', '', m.lower())
            if key not in seen:
                seen.add(key)
                unique_metrics.append(m)

        return unique_metrics[:12]

    def _analyze_with_llm(self, title: str, abstract: str, intro: str, method: str, results: str, conclusion: str) -> Optional[Dict]:
        """LLM深度分析"""
        if not self.llm_client:
            return None

        prompt = f"""你是一位光学/太赫兹领域的博士研究生，需要从论文中提取深度信息。

论文标题: {title[:150]}
论文摘要: {abstract[:1000] if abstract else '无'}
引言前800词: {intro[:800] if intro else '无'}
方法章节前500词: {method[:500] if method else '无'}
结果章节前500词: {results[:500] if results else '无'}
结论章节前300词: {conclusion[:300] if conclusion else '无'}

请提取以下信息（直接返回JSON，不要有其他文字）：
{{
    "research_question": "这篇论文要解决什么具体问题？一句话描述，越具体越好",
    "approach": "采用了什么方法/技术路线？列出关键技术（用逗号分隔）",
    "key_findings": ["关键结果1（如：输出功率0.5mW，带宽2.5THz）", "关键结果2"],
    "limitations": ["本文的局限性1（如：仅在低温下工作）", "本文的局限性2"],
    "gaps": ["本文指出的研究空白1（如：缺乏系统性比较）", "研究空白2"],
    "contribution": "本文的主要贡献是什么？一句话描述",
    "key_metrics": ["具体数值1（如：峰值功率1.2mW）", "具体数值2"],
    "physical_insight": "论文的核心物理洞察是什么？"
}}

要求：
- research_question 要具体，基于论文原文
- limitations 要基于论文原文的描述
- gaps 要指出论文自己提到的空白
- key_findings 要包含具体数值
- 如果信息缺失，字段填 "未明确" """

        try:
            messages = [
                {"role": "system", "content": "你是一位光学太赫兹领域的学术论文分析专家。"},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_client.chat_completions_create(messages, temperature=0.1, max_tokens=1500)
            content = response['choices'][0]['message']['content']

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json_module.loads(json_match.group(0))

                if 'gaps' in result and isinstance(result['gaps'], list):
                    formatted_gaps = []
                    for g in result['gaps']:
                        if isinstance(g, str):
                            g_lower = g.lower()
                            if 'method' in g_lower or 'approach' in g_lower:
                                gap_type = 'Methodological'
                            elif 'compare' in g_lower:
                                gap_type = 'Comparative'
                            elif 'theory' in g_lower or 'mechanism' in g_lower:
                                gap_type = 'Theoretical'
                            elif 'range' in g_lower or 'parameter' in g_lower:
                                gap_type = 'Parameter'
                            else:
                                gap_type = 'Condition'
                            formatted_gaps.append({'type': gap_type, 'description': g[:200], 'evidence': g})
                    result['gaps'] = formatted_gaps

                print(f"  [LLM] OK: {title[:35]}...")
                return result

        except Exception as e:
            print(f"  [LLM] Error: {e}")

        return None

    def _extract_sections(self, text: str) -> Dict[str, str]:
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

    def _extract_rq(self, text: str) -> str:
        patterns = [
            r"(?:We|Here|This paper|This work)\s+(?:investigate|study|demonstrate|propose|develop)\s+(?:the\s+)?(?:of\s+)?([^.]+?)(?:\.|,)",
            r"(?:goal|objective|purpose)\s+(?:of|is|was)?\s*:?\s*([^.]+?)(?:\.|,)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return re.sub(r'\s+', ' ', match.group(1).strip())[:200]
        return ""

    def _extract_approach(self, text: str) -> str:
        found = []
        keywords = ['tilted pulse front', 'optical rectification', 'photoconductive', 'filamentation',
            'two-color', 'QCL', 'quantum cascade', 'LiNbO3', 'GaAs', 'ZnTe', 'GaSe', 'DAST',
            'electro-optic sampling', 'bolometer', 'plasmonic', 'metasurface', 'LT-GaAs']
        text_lower = text.lower()
        for kw in keywords:
            if kw.lower() in text_lower:
                found.append(kw)
        return "Methods: " + ", ".join(found[:10]) if found else ""

    def _detect_tech_routes(self, text: str) -> List[str]:
        text_lower = text.lower()
        matched = []
        for route, keywords in TECH_ROUTES.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    matched.append(route)
                    break
        return list(set(matched)) if matched else ['其他']

    def _extract_findings(self, text: str) -> List[str]:
        findings = []
        patterns = [r'(\d+(?:\.\d+)?\s*(?:THz|GHz))\s*(?:peak|output|bandwidth)?',
            r'(\d+(?:\.\d+)?\s*(?:mJ|μJ))\s*(?:pulse|energy)?',
            r'(\d+(?:\.\d+)?%)\s*(?:efficiency|conversion)?']
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                if m and len(m) > 2 and m not in findings:
                    findings.append(m)
        return findings[:8]

    def _extract_limitations(self, text: str) -> List[str]:
        limitations = []
        patterns = [r"(?:limitation|drawback)\s+(?:of|is|are)\s+([^.]+)",
            r"future\s+(?:work|research)\s+(?:should|needs)\s+([^.]+)"]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                m = m.strip()
                if len(m) > 30 and len(m) < 300 and m not in limitations:
                    limitations.append(m)
        return limitations[:3]

    def _extract_gaps(self, text: str) -> List[Dict]:
        gaps = []
        text_lower = text.lower()

        gap_keywords = {
            'Methodological': ['lack of systematic', 'no rigorous method', 'without systematic', 'method has not been', 'experimental technique', 'no established method'],
            'Parameter': ['limited range', 'restricted parameter', 'narrow range', 'not explored', 'parameter space', '调谐范围'],
            'Comparative': ['no direct comparison', 'lack of systematic comparison', 'not compared with', 'no comprehensive', 'without comparison', '缺乏比较'],
            'Theoretical': ['theoretical framework', 'mechanism remains', 'not well understood', 'physical origin', 'underlying physics', 'lacks theoretical', 'no complete theory'],
            'Condition': ['only valid for', 'applicable only', 'limited to', 'restricted to', 'works only when', '材料依赖'],
        }

        for gap_type, keywords in gap_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    for sentence in text.split('.'):
                        if kw in sentence.lower():
                            gap_text = sentence.strip()[:250]
                            if len(gap_text) > 30 and not any(g.get('description', '')[:50] == gap_text[:50] for g in gaps):
                                gaps.append({'type': gap_type, 'description': gap_text, 'evidence': kw})
                                break

        return gaps[:5] if gaps else [{'type': 'Theoretical', 'description': '现有文献未系统比较不同技术路线在宽参数范围内的性能表现', 'evidence': 'inferred'}]

    def _extract_contribution(self, text: str) -> str:
        patterns = [r"(?:We|This paper)\s+(?:demonstrate|propose|develop|present|show|introduce)\s+([^.]+)",
            r"(?:The main|key)\s+(?:contribution|innovation)\s+(?:of|is)\s+:?\s*([^.]+)"]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return re.sub(r'\s+', ' ', match.group(0)[:200])
        return ""


# =============================================================================
# 知识收集
# =============================================================================

class KnowledgeCuration:
    """多源知识收集"""

    def __init__(self):
        self.zotero = ZoteroDBReader()
        self.openalex = OpenAlexReader()
        self.tavily = TavilySearcher()
        self.pdf_analyzer = PDFAnalyzer()

    def curate(self, query: str, max_papers: int = 50) -> Tuple[List[Paper], List[Dict]]:
        """从多源收集论文和最新研究动态"""
        print("\n>> Stage 1: 知识收集 (Multi-Source + Tavily)")
        papers = []
        tavily_results = []

        # Source 1: Zotero
        print("\n  [1/4] Zotero 数据库...")
        if self.zotero.connect():
            zotero_articles = self.zotero.search_articles(query, limit=max_papers)
            print(f"      找到 {len(zotero_articles)} 篇 Zotero 论文")

            for art in zotero_articles[:20]:
                authors = self.zotero.get_authors(art['itemID'])
                pdf_path = self.zotero.get_pdf_attachment(art['itemID'])

                paper = Paper(
                    id=f"zotero_{art['zotero_key']}",
                    zotero_key=art['zotero_key'],
                    title=art['title'],
                    authors=authors,
                    year=art['year'],
                    journal=art['journal'],
                    doi=art['doi'],
                    abstract=art['abstract'],
                    citations=0,
                )
                paper.add_source('zotero_db')

                if pdf_path:
                    print(f"      Analyzing PDF: {art['title'][:50]}...")
                    metadata = {
                        'title': art['title'],
                        'authors': authors,
                        'year': art['year'],
                    }
                    pdf_result = self.pdf_analyzer.analyze(pdf_path, metadata)
                    if pdf_result.get('success'):
                        paper.research_question = pdf_result.get('research_question', '')
                        paper.approach = pdf_result.get('approach', '')
                        paper.tech_routes = pdf_result.get('tech_routes', [])
                        paper.key_findings = pdf_result.get('key_findings', [])
                        paper.limitations = pdf_result.get('limitations', [])
                        paper.gaps = pdf_result.get('gaps', [])
                        paper.key_metrics = pdf_result.get('key_metrics', [])
                        paper.physical_insight = pdf_result.get('physical_insight', '')
                        paper.add_source('zotero_pdf')

                papers.append(paper)

            self.zotero.close()

        # Source 2: OpenAlex
        print("\n  [2/4] OpenAlex API...")
        openalex_papers = self.openalex.search(query, max_results=max_papers)
        print(f"      找到 {len(openalex_papers)} 篇 OpenAlex 论文")

        for op in openalex_papers:
            existing = None
            for p in papers:
                if p.doi and op.get('doi') and p.doi == op['doi']:
                    existing = p
                    break

            if existing:
                if not existing.citations and op.get('citations'):
                    existing.citations = op['citations']
                if not existing.abstract and op.get('abstract'):
                    existing.abstract = op['abstract']
                existing.add_source('openalex')
            else:
                paper = Paper(
                    id=f"openalex_{op['openalex_id']}",
                    title=op['title'],
                    authors=op['authors'],
                    year=op['year'],
                    journal=op['journal'],
                    doi=op.get('doi', ''),
                    abstract=op.get('abstract', ''),
                    citations=op.get('citations', 0),
                    relevance=op.get('relevance', 0),
                )
                paper.add_source('openalex')
                # 自动检测tech_route（基于title+abstract）
                combined_text = f"{op['title']} {op.get('abstract', '')}"
                paper.tech_routes = PDFAnalyzer()._detect_tech_routes(combined_text)
                papers.append(paper)

        # 下载PDF并深度分析（仅对有DOI的OpenAlex论文）
        pdf_dir = f"{OUTPUT_DIR}/pdfs"
        print(f"\n  [2.5/4] 下载并分析论文PDF...")
        for paper in papers:
            if 'openalex' in paper.sources and paper.doi and not paper.tech_routes:
                # 有DOI但tech_route为空或为"其他"，尝试下载PDF分析
                pdf_path = self.openalex.download_pdf(paper.doi, pdf_dir)
                if pdf_path:
                    metadata = {
                        'title': paper.title,
                        'authors': paper.authors,
                        'year': paper.year,
                    }
                    pdf_result = self.pdf_analyzer.analyze(pdf_path, metadata)
                    if pdf_result.get('success'):
                        paper.research_question = pdf_result.get('research_question', '')
                        paper.approach = pdf_result.get('approach', '')
                        paper.tech_routes = pdf_result.get('tech_routes', [])
                        paper.key_findings = pdf_result.get('key_findings', [])
                        paper.limitations = pdf_result.get('limitations', [])
                        paper.gaps = pdf_result.get('gaps', [])
                        paper.key_metrics = pdf_result.get('key_metrics', [])
                        paper.physical_insight = pdf_result.get('physical_insight', '')
                        paper.add_source('openalex_pdf')
                        # 清理"其他"分类
                        if paper.tech_routes and '其他' in paper.tech_routes:
                            paper.tech_routes.remove('其他')

        # Source 3: Tavily (最新进展)
        print("\n  [3/4] Tavily 最新研究...")
        tavily_results = self.tavily.search(query, max_results=8)
        if tavily_results:
            print(f"      找到 {len(tavily_results)} 条 Tavily 结果")
        else:
            print(f"      Tavily 未返回结果")

        print(f"\n  [4/4] 合计收集 {len(papers)} 篇论文")

        return papers, tavily_results


# =============================================================================
# 增强版主题综合 v5.1 - 解决分析深度不足问题
# =============================================================================

class EnhancedThematicSynthesis:
    """
    增强版主题综合 - v5.1 核心改进

    核心改进:
    1. 每篇论文生成独特的"一句话贡献"
    2. Gap智能识别 - 从局限反推，而非依赖论文声明
    3. 研究问题独特化 - 提取每篇论文具体RQ
    4. 动态Context生成 - 基于实际论文内容
    5. 技术路线对比 - 横向对比各路线的独特优势
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        if not self.llm_client:
            try:
                self.llm_client = get_llm_client()
            except:
                pass

    def synthesize(self, papers: List[Paper], tavily_results: List[Dict] = None) -> Dict[str, ThemeSynthesis]:
        route_groups = defaultdict(list)
        for paper in papers:
            for route in paper.tech_routes:
                route_groups[route].append(paper)

        themes = {}
        for route, route_papers in route_groups.items():
            if len(route_papers) < 1:
                continue

            synth = ThemeSynthesis()
            synth.theme = route

            # 核心改进1: 动态Context生成
            synth.context = self._generate_context_v2(route, route_papers)

            # 核心改进2: 研究问题独特化
            synth.research_questions = self._extract_unique_rqs(route, route_papers)

            synth.tech_routes = {route: [p.id for p in route_papers]}

            # 核心改进3: 关键发现去重但保留多样性
            synth.key_findings = self._aggregate_diverse_findings(route_papers)

            # 核心改进4: Gap智能识别
            synth.gaps = self._smart_gap_identification(route, route_papers)

            # 技术路线对比
            synth.tradeoffs = self._generate_route_specific_tradeoffs(route, route_papers)
            synth.future_directions = self._generate_route_specific_futures(route, route_papers)

            # 核心改进5: 代表性工作带独特贡献
            synth.representative_papers = self._select_diverse_representative(route_papers)

            # 最新趋势 - Tavily优先，若无结果则用OpenAlex
            if tavily_results:
                tavily = TavilySearcher()
                synth.latest_trends = tavily.get_latest_trends(tavily_results)
            else:
                # Tavily无结果时，用OpenAlex最新论文作为替代
                openalex = OpenAlexReader()
                synth.latest_trends = openalex.get_latest_trends(route, max_results=5)

            themes[route] = synth

        return themes

    def _generate_context_v2(self, theme: str, papers: List[Paper]) -> str:
        """动态Context生成 - 基于实际论文内容"""
        # 分析论文中的方法关键词
        methods = set()
        for p in papers:
            if p.approach:
                methods.add(p.approach[:50])

        years = [p.year for p in papers if p.year]
        year_range = f"{min(years)}-{max(years)}" if years else "未知"

        # 基于theme选择基础context
        contexts = {
            'PCA (光电导天线)': "光电导天线(PCA)基于超快光载流子注入产生瞬态电流",
            '光整流': "光整流效应通过飞秒激光与非线性晶体相互作用实现频率转换",
            '激光等离子体': "激光等离子体利用强场激光与气体介质相互作用通过四波混频产生THz波",
            'QCL (量子级联激光器)': "量子级联激光器(QCL)基于半导体异质结构中的子带间跃迁",
            '超表面/等离子体': "超表面和等离子体结构通过亚波长谐振单元实现电磁波调控",
        }

        base = contexts.get(theme, f"{theme}是THz技术的重要路线")
        method_str = "、".join(list(methods)[:3]) if methods else "相关方法"

        return f"{base}。本主题涵盖{len(papers)}篇论文({year_range})，主要涉及{method_str}等方法。"

    def _extract_unique_rqs(self, theme: str, papers: List[Paper]) -> List[str]:
        """研究问题独特化 - 基于路线特征生成独特的RQ"""
        # 路线特定的研究问题模板
        route_rq_templates = {
            'PCA (光电导天线)': [
                '如何设计低噪声高增益的光电导天线结构以提升THz辐射功率？',
                '不同电极几何形状对PCA辐射效率的影响规律是什么？',
                '如何实现PCA在高温环境下的稳定工作？',
            ],
            '光整流': [
                '倾斜脉冲前阵技术的理论效率极限取决于哪些关键参数？',
                '有机晶体材料（如DAST）的THz产生最优泵浦条件是什么？',
                '如何抑制光整流过程中的热效应以提升平均功率？',
            ],
            '激光等离子体': [
                '气体介质组分和压强如何影响THz产生效率？',
                '双色激光脉冲的时空同步特性对THz辐射有何影响？',
                '如何实现激光等离子体THz源的远程高功率探测？',
            ],
            'QCL (量子级联激光器)': [
                '如何突破室温连续波QCL的输出功率瓶颈？',
                '多波长QCL同时输出的技术方案有哪些？',
                'QCL与倍频技术结合能否扩展THz频段覆盖范围？',
            ],
            '超表面/等离子体': [
                '超表面单元几何参数如何优化以实现高效THz调制？',
                '动态可调超表面在真实环境中的响应稳定性如何提升？',
                '超表面与THz波的强耦合效应有哪些独特应用？',
            ],
            '自旋THz': [
                '自旋电子THz辐射的物理机制如何优化以提升效率？',
                '如何在无外磁场条件下实现高效自旋THz发射？',
                '纳米尺度自旋电流如何影响THz发射性能？',
            ],
        }

        # 如果主题不在模板中，基于论文内容动态生成RQ
        if theme not in route_rq_templates:
            # 从论文abstract提取关键主题词来生成特定RQ
            key_terms = set()
            for p in papers:
                abstract = p.abstract or ''
                title = p.title or ''
                combined = f"{abstract} {title}"
                # 提取技术相关词汇
                import re
                terms = re.findall(r'(?:THz|太赫兹|激光|晶体|超快|脉冲|光谱|成像)', combined)
                key_terms.update(terms[:3])

            term_str = '、'.join(list(key_terms)[:3]) if key_terms else theme
            templates = [
                f'如何利用{term_str}提升THz辐射效率？',
                f'{term_str}相关技术的性能优化空间在哪里？',
                f'如何解决{term_str}技术在实际应用中的瓶颈？',
            ]
        else:
            templates = route_rq_templates.get(theme, [
                f'如何提升{theme}的THz产生效率?',
                f'{theme}技术的关键性能瓶颈在哪里?',
                f'{theme}与其他技术路线相比有何独特优势?',
            ])

        # 从论文中提取真实的RQ来补充
        rqs = []
        seen_patterns = set()

        for p in papers:
            if p.research_question and p.research_question != '未明确':
                rq = p.research_question.strip()
                # 确保RQ与当前路线相关
                if any(theme_word in rq.lower() or p.approach.lower() in rq.lower()
                       for theme_word in theme.lower().split()):
                    pattern_key = rq[:30].lower()
                    if pattern_key not in seen_patterns:
                        rqs.append(rq)
                        seen_patterns.add(pattern_key)

        # 补充路线特定的RQ
        for t in templates:
            if t not in rqs and len(rqs) < 5:
                rqs.append(t)

        return rqs[:5]

    def _aggregate_diverse_findings(self, papers: List[Paper]) -> List[str]:
        """关键发现聚合 - 保留多样性，避免趋同"""
        findings = []
        seen_values = set()

        for p in papers:
            # 从key_metrics提取独特指标
            for m in p.key_metrics:
                # 提取数值作为去重依据
                value_key = ''.join(c for c in m if c.isdigit() or c == '.')
                if value_key and value_key not in seen_values:
                    findings.append(m)
                    seen_values.add(value_key)

            # 从key_findings提取
            for f in p.key_findings:
                key = f[:20].lower()
                if key not in seen_values:
                    findings.append(f)
                    seen_values.add(key)

        return findings[:12]

    def _smart_gap_identification(self, theme: str, papers: List[Paper]) -> List[Dict]:
        """Gap智能识别 - 从局限反推，而非依赖论文声明"""
        gaps = []

        # 分析论文的局限描述
        limitations = []
        for p in papers:
            for lim in p.limitations:
                if lim and lim != '未明确':
                    limitations.append(lim)

        # 分析研究问题中暗示的gap
        implied_gaps = []
        for p in papers:
            rq = p.research_question or ''
            # 如果RQ包含"如何"但没有答案，暗示这是一个gap
            if '如何' in rq and not any(x in rq for x in ['提出', '实现', '证明']):
                implied_gaps.append(f"尚无有效方法{rq[2:40] if len(rq) > 2 else rq}")

        # 为每个主题生成独特的gap
        theme_specific_gaps = {
            'PCA (光电导天线)': [
                {'type': 'Parameter', 'description': '现有PCA在高温/高功率条件下的性能退化机制尚未系统研究'},
                {'type': 'Methodological', 'description': '缺乏对不同电极结构对辐射效率影响的系统性比较'},
                {'type': 'Condition', 'description': '柔性基底PCA的室温工作性能仍待提升'},
            ],
            '光整流': [
                {'type': 'Theoretical', 'description': '倾斜脉冲前阵技术的理论效率极限尚未明确'},
                {'type': 'Parameter', 'description': '有机晶体材料的THz产生效率最优参数窗口有待确定'},
                {'type': 'Comparative', 'description': '不同非线性晶体的THz产生性能缺乏系统对比'},
            ],
            '激光等离子体': [
                {'type': 'Methodological', 'description': '缺乏实时测量DFB激光器温度的系统'},
                {'type': 'Theoretical', 'description': '四波混频产生THz的转换效率理论模型仍需完善'},
                {'type': 'Condition', 'description': '高功率长距离THz传输的可行性尚未验证'},
            ],
            'QCL (量子级联激光器)': [
                {'type': 'Parameter', 'description': '室温连续波输出功率距离实用化仍有差距'},
                {'type': 'Methodological', 'description': '低噪声QCL驱动的技术方案尚未成熟'},
                {'type': 'Condition', 'description': '多波长QCL同时输出技术仍属挑战'},
            ],
            '超表面/等离子体': [
                {'type': 'Theoretical', 'description': '超表面-THz相互作用的理论模型尚不完善'},
                {'type': 'Comparative', 'description': '不同超表面设计的THz调制性能缺乏系统对比'},
                {'type': 'Condition', 'description': '动态可调超表面在真实环境中的稳定性待验证'},
            ],
            '自旋THz': [
                {'type': 'Theoretical', 'description': '自旋电子THz辐射的深层物理机制尚不完全清晰'},
                {'type': 'Parameter', 'description': '无外磁场条件下自旋THz辐射效率的最优参数窗口待确定'},
                {'type': 'Methodological', 'description': '纳米尺度自旋电流的超快探测方法仍需创新'},
            ],
        }

        # 如果主题不在预定义列表中，动态生成gap
        if theme not in theme_specific_gaps:
            # 基于论文内容动态生成gap
            key_issues = set()
            for p in papers:
                abstract = p.abstract or ''
                limitations = p.limitations or []
                gaps = p.gaps or []
                # 从论文中提取关键词
                import re
                terms = re.findall(r'(?:效率|功率|带宽|噪声|稳定性|成本| miniaturization|compact)', abstract.lower())
                key_issues.update(terms[:2])

                for gap in gaps:
                    if isinstance(gap, dict):
                        key_issues.add(gap.get('type', 'Methodological'))

            issue_str = '、'.join(list(key_issues)[:3]) if key_issues else '系统性能'
            theme_gaps = [
                {'type': 'Theoretical', 'description': f'{issue_str}相关的理论模型尚不完善'},
                {'type': 'Parameter', 'description': f'{issue_str}的最优参数范围有待系统研究'},
                {'type': 'Methodological', 'description': f'缺乏对{issue_str}的系统性比较研究'},
                {'type': 'Comparative', 'description': f'{theme}与其他技术路线的综合性能对比尚未开展'},
            ]
        else:
            theme_gaps = theme_specific_gaps.get(theme, [
                {'type': 'Methodological', 'description': f'{theme}的研究方法有待创新'},
                {'type': 'Comparative', 'description': f'{theme}与其他技术路线的系统比较尚未开展'},
            ])

        # 从论文局限推断的额外gap
        for lim in limitations[:2]:
            if lim and lim != '未明确':
                theme_gaps.append({
                    'type': 'Theoretical',
                    'description': f'现有方法在处理{lim[:30]}方面的局限性'
                })

        # 添加隐含gap
        for ig in implied_gaps[:1]:
            if ig:
                theme_gaps.append({
                    'type': 'Methodological',
                    'description': ig[:80]
                })

        # 去重
        seen = set()
        for g in theme_gaps:
            key = g['description'][:30]
            if key not in seen:
                gaps.append(g)
                seen.add(key)

        return gaps[:4]

    def _generate_route_specific_tradeoffs(self, theme: str, papers: List[Paper]) -> List[str]:
        """生成主题特定的tradeoff"""
        # 基于论文中实际提到的权衡动态生成
        mentioned_tradeoffs = set()
        for p in papers:
            for f in p.key_findings:
                if any(x in f.lower() for x in ['效率', '功率', '带宽', '频率']):
                    mentioned_tradeoffs.add(f[:30])

        # 主题特定的常见tradeoff
        common_tradeoffs = {
            'PCA (光电导天线)': ['天线尺寸 vs 辐射功率', '工作频率 vs 衬底材料', '载流子寿命 vs 响应速度'],
            '光整流': ['转换效率 vs 带宽', '晶体损伤阈值 vs 输入能量', '相位匹配 vs 角度调谐范围'],
            '激光等离子体': ['THz能量 vs 激光对比度', '系统复杂度 vs 输出稳定性', '远程 vs 近场测量'],
            'QCL (量子级联激光器)': ['工作温度 vs 输出功率', '频率调谐 vs 模式稳定性', '器件寿命 vs 工作电流'],
            '超表面/等离子体': ['调制深度 vs 响应速度', '制造精度 vs 成本', '效率 vs 调控灵活性'],
        }

        base = common_tradeoffs.get(theme, ['性能 vs 实现难度'])
        return base[:4]

    def _generate_route_specific_futures(self, theme: str, papers: List[Paper]) -> List[str]:
        """生成主题特定的未来方向"""
        # 分析论文limitation暗示的未来方向
        future_hints = []
        for p in papers:
            for lim in p.limitations:
                if lim and lim != '未明确':
                    future_hints.append(f"解决{lim[:30]}" if len(lim) > 30 else f"解决{lim}")

        common_futures = {
            'PCA (光电导天线)': ['开发低温柔性PCA扩展工作场景', '结合纳米结构提升辐射效率', '探索新型宽禁带半导体材料'],
            '光整流': ['优化倾斜脉冲前阵技术', '探索新型有机晶体材料', '实现波长可调谐THz源'],
            '激光等离子体': ['提高激光-等离子体能量转换效率', '实现远程高功率THz检测', '探索气体压强和组分优化'],
            'QCL (量子级联激光器)': ['提升室温输出功率', '扩展频率调谐范围', '实现低噪声特性'],
            '超表面/等离子体': ['开发高速THz调制器', '实现超薄高效THz源', '探索可编程超表面'],
        }

        futures = common_futures.get(theme, ['系统性优化现有方案'])
        return futures[:3]

    def _select_diverse_representative(self, papers: List[Paper]) -> List[Dict]:
        """选择多样的代表性工作 - 确保各论文贡献不趋同"""
        # 按年份排序，确保多样性
        sorted_papers = sorted(papers, key=lambda x: x.year if x.year else 0, reverse=True)

        result = []
        seen_methods = set()

        for p in sorted_papers:
            # 获取论文独特的一句话贡献
            contribution = self._extract_paper_contribution(p)

            # 确保方法不重复
            method_key = p.approach[:20] if p.approach else 'unknown'
            if method_key not in seen_methods or len(result) < 3:
                seen_methods.add(method_key)

                paper_dict = {
                    'id': p.id,
                    'title': p.title[:70] + ('...' if len(p.title) > 70 else ''),
                    'authors': ', '.join(p.authors[:2]) if p.authors else 'Unknown',
                    'year': p.year,
                    'citations': p.citations,
                    'approach': contribution,  # 使用独特贡献替代泛化方法
                    'findings': p.key_findings[:2] if p.key_findings else [],
                    'metrics': p.key_metrics[:3] if p.key_metrics else [],
                    'sources': p.sources,
                }
                result.append(paper_dict)

            if len(result) >= 5:
                break

        return result

    def _extract_paper_contribution(self, paper: Paper) -> str:
        """提取论文独特的一句话贡献"""
        # 优先使用physical_insight
        if paper.physical_insight:
            return paper.physical_insight[:80]

        # 其次使用具体指标
        if paper.key_metrics:
            return paper.key_metrics[0][:80]

        # 使用方法+发现的组合
        if paper.approach and paper.key_findings:
            finding = paper.key_findings[0][:40] if paper.key_findings else ''
            return f"通过{paper.approach[:40]}实现了{finding}"

        return paper.approach[:80] if paper.approach else '相关研究'


class ThematicSynthesis:
    """主题综合分析"""

    def synthesize(self, papers: List[Paper], tavily_results: List[Dict] = None) -> Dict[str, ThemeSynthesis]:
        route_groups = defaultdict(list)
        for paper in papers:
            for route in paper.tech_routes:
                route_groups[route].append(paper)

        themes = {}
        for route, route_papers in route_groups.items():
            if len(route_papers) < 1:
                continue

            synth = ThemeSynthesis()
            synth.theme = route
            synth.context = self._generate_context(route, route_papers)
            synth.research_questions = self._extract_rqs(route_papers)
            synth.tech_routes = {route: [p.id for p in route_papers]}
            synth.key_findings = self._aggregate_findings(route_papers)
            synth.gaps = self._aggregate_gaps(route_papers)
            synth.tradeoffs = self._get_tradeoffs(route)
            synth.future_directions = self._get_futures(route)
            synth.representative_papers = self._select_representative(route_papers)

            # 添加 Tavily 最新趋势
            if tavily_results:
                tavily = TavilySearcher()
                synth.latest_trends = tavily.get_latest_trends(tavily_results)

            themes[route] = synth

        return themes

    def _generate_context(self, theme: str, papers: List[Paper]) -> str:
        contexts = {
            'PCA (光电导天线)': "光电导天线(PCA)是太赫兹时域光谱系统的核心辐射源，基于超快光载流子注入产生瞬态电流。",
            '光整流': "光整流效应通过飞秒激光与非线性晶体相互作用实现频率转换，是产生太赫兹辐射的重要非线性光学方法。",
            '激光等离子体': "激光等离子体太赫兹辐射利用强场激光与气体介质相互作用，通过四波混频产生宽带太赫兹波。",
            'QCL (量子级联激光器)': "量子级联激光器(QCL)基于半导体异质结构中的子带间跃迁，是固态电泵浦太赫兹源的重要选择。",
            '超表面/等离子体': "超表面和等离子体结构通过亚波长谐振单元实现电磁波调控，为太赫兹调制提供紧凑高效的解决方案。",
        }

        years = [p.year for p in papers if p.year]
        year_range = f"{min(years)}-{max(years)}" if years else "未知"
        citations = sum(p.citations for p in papers)

        base = contexts.get(theme, f"{theme}是太赫兹技术的重要研究方向。")
        return f"{base}本主题涵盖{len(papers)}篇论文({year_range})，总引用{citations}次。"

    def _extract_rqs(self, papers: List[Paper]) -> List[str]:
        rqs = []
        for p in papers:
            if p.research_question and p.research_question not in rqs:
                rqs.append(p.research_question)
        return rqs[:5]

    def _aggregate_findings(self, papers: List[Paper]) -> List[str]:
        findings = []
        for p in papers:
            for f in p.key_findings:
                if f not in findings:
                    findings.append(f)
            for m in p.key_metrics:
                if m not in findings:
                    findings.append(m)
        return findings[:15]

    def _aggregate_gaps(self, papers: List[Paper]) -> List[Dict]:
        gap_dict = defaultdict(list)
        for p in papers:
            for g in p.gaps:
                gap_dict[g.get('type', 'Unknown')].append(g)

        gaps = []
        for gap_type, type_gaps in gap_dict.items():
            if type_gaps:
                gaps.append({
                    'type': gap_type,
                    'description': type_gaps[0].get('description', ''),
                    'evidence': type_gaps[0].get('evidence', ''),
                })
        return gaps[:5]

    def _get_tradeoffs(self, theme: str) -> List[str]:
        tradeoffs = {
            'PCA (光电导天线)': ['带宽 vs 功率', '工作频率 vs 衬底选择', '天线设计 vs 辐射效率'],
            '光整流': ['转换效率 vs 带宽', '晶体损伤阈值 vs 输出能量', '相位匹配 vs 角度调谐'],
            '激光等离子体': ['能量 vs 带宽', '系统复杂度 vs 稳定性', '远程 vs 近场'],
            'QCL (量子级联激光器)': ['工作温度 vs 输出功率', '频率可调 vs 模式稳定性', '成本 vs 性能'],
            '超表面/等离子体': ['调制深度 vs 响应速度', '效率 vs 带宽', '制备成本 vs 性能'],
        }
        return tradeoffs.get(theme, ['性能 vs 实现难度'])

    def _get_futures(self, theme: str) -> List[str]:
        futures = {
            'PCA (光电导天线)': ['开发低温柔性PCA扩展工作场景', '结合纳米等离子体结构提升辐射效率', '探索新型宽禁带半导体材料'],
            '光整流': ['优化倾斜脉冲前阵技术提升能量转换效率', '探索新型有机晶体材料', '实现波长可调谐太赫兹源'],
            '激光等离子体': ['提高激光-等离子体能量转换效率', '实现远程高功率太赫兹检测', '探索气体压强和组分优化'],
            'QCL (量子级联激光器)': ['提升室温输出功率', '扩展频率调谐范围', '实现低噪声特性'],
            '超表面/等离子体': ['开发高速太赫兹调制器', '实现超薄高效太赫兹源', '探索可编程超表面'],
        }
        return futures.get(theme, ['系统性优化现有方案', '探索新型材料/结构'])

    def _select_representative(self, papers: List[Paper]) -> List[Dict]:
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
                'metrics': p.key_metrics[:3] if p.key_metrics else [],
                'sources': p.sources,
            })
        return result


# =============================================================================
# 学术综述写作 - 论文级结构
# =============================================================================

class AcademicReviewWriter:
    """生成论文级学术综述"""

    def write(self, themes: Dict[str, ThemeSynthesis], query: str) -> str:
        lines = []

        lines.append(f"# {query.title()}领域学术综述\n")

        # 摘要
        lines.append("## 摘要\n")
        lines.append(self._write_abstract(themes, query))

        # 引言
        lines.append("\n## 一、引言\n")
        lines.append("### 1.1 研究背景与意义\n")
        lines.append(self._write_background(query))
        lines.append("\n### 1.2 国内外研究现状\n")
        lines.append(self._write_literature_review(themes))
        lines.append("\n### 1.3 存在的问题与挑战\n")
        lines.append(self._write_problems_challenges(themes))
        lines.append("\n### 1.4 本文的主要贡献\n")
        lines.append(self._write_contributions(themes))

        # 技术路线分析
        lines.append("\n## 二、技术路线分析\n")
        for i, (theme, synth) in enumerate(themes.items(), 1):
            lines.append(f"\n### 2.{i} {synth.theme}\n")
            lines.append(self._write_theme_section(synth, i))

        # 讨论
        lines.append("\n## 三、讨论\n")
        lines.append("\n### 3.1 技术路线综合对比\n")
        lines.append(self._write_comparison_table(themes))
        lines.append("\n### 3.2 核心权衡分析\n")
        lines.append(self._write_tradeoff_analysis(themes))
        lines.append("\n### 3.3 未来研究方向\n")
        lines.append(self._write_future_directions(themes))

        # 结论
        lines.append("\n## 四、结论\n")
        lines.append(self._write_conclusion(themes))

        # 参考文献
        lines.append("\n## 参考文献\n")
        lines.append(self._write_references(themes))

        return "\n".join(lines)

    def _write_abstract(self, themes: Dict[str, ThemeSynthesis], query: str) -> str:
        """生成学术摘要 - 遵循标准结构"""
        lines = []

        # Context (1句) - 领域重要性
        lines.append(f"太赫兹(THz)辐射技术在传感成像、通信、安全检测等领域展现出重要应用潜力。")

        # Gap (1句) - 研究空白
        all_gaps = []
        for synth in themes.values():
            all_gaps.extend(synth.gaps)

        gap_types = {}
        for g in all_gaps:
            t = g.get('type', 'Unknown')
            gap_types[t] = gap_types.get(t, 0) + 1

        main_gap_type = max(gap_types, key=gap_types.get) if gap_types else 'Theoretical'
        main_gap_count = gap_types.get(main_gap_type, 0)

        # Objective (1句) - 本文目标
        lines.append(f"然而，现有研究在{synth.theme if themes else '该领域'}的系统性比较方面存在明显不足。")

        # Method (2-3句) - 方法概述
        tech_names = list(themes.keys()) if themes else ['光电导天线', '光整流', '激光等离子体']
        lines.append(f"本综述采用主题综合法，系统梳理了{', '.join(tech_names[:3])}等五种主要THz辐射技术路线的研究进展，")
        lines.append(f"识别出{main_gap_count}个以{main_gap_type}类型为主的关键研究空白。")

        # Results (3-4句) - 主要结果
        total_papers = sum(len(synth.representative_papers) for synth in themes.values())

        if themes:
            for theme, synth in list(themes.items())[:2]:
                if synth.key_findings:
                    lines.append(f"{theme}技术实现了{synth.key_findings[0]}；")
        lines.append(f"共涵盖{total_papers}篇代表性论文。")

        # Conclusion (1-2句) - 结论
        lines.append("本综述为领域研究者提供了全面的技术路线图和未来发展方向参考。")

        return "".join(lines)

    def _write_background(self, query: str) -> str:
        return f"""太赫兹(Terahertz, THz)辐射通常指频率在0.1-10 THz之间的电磁波，位于微波与红外之间。

该频段具有独特的光谱特性：许多生物分子和半导体材料的声子模式位于THz频段；THz波可穿透非极性材料（如纸张、塑料、衣物）而不产生电离损伤；THz脉冲可实现亚皮秒时间分辨率。

这些特性使THz技术在以下领域具有重要应用前景：
- **传感与成像**: 生物组织检测、安全筛查、工业质量控制
- **通信**: 6G候选频段、无线传输
- **光谱分析**: 材料指纹识别、药物质量控制
- **基础研究**: 超快动力学、强场物理

然而，THz辐射的产生和检测仍面临诸多技术挑战，如何实现高功率、宽频带、可调谐、紧凑便携的THz源是该领域的核心问题。"""

    def _write_literature_review(self, themes: Dict[str, ThemeSynthesis]) -> str:
        lines = []
        lines.append("目前，THz辐射产生主要依赖以下五种技术路线：\n")

        for theme, synth in themes.items():
            if synth.representative_papers:
                p = synth.representative_papers[0]
                lines.append(f"**{theme}**: ")
                lines.append(f"基于{p.get('approach', '相关方法')}，")
                if p.get('year'):
                    lines.append(f"以{p['year']}年发表的工作为代表")
                lines.append("。")
                lines.append(f"该方法{'优势在于' if theme in ['光整流', '激光等离子体'] else '特点是'}可实现")
                if synth.key_findings:
                    lines.append(synth.key_findings[0])
                lines.append("。\n")

        return "".join(lines)

    def _write_problems_challenges(self, themes: Dict[str, ThemeSynthesis]) -> str:
        lines = []
        lines.append("尽管已有大量研究投入，该领域仍存在以下关键问题：\n")

        gaps_by_type = defaultdict(list)
        for synth in themes.values():
            for g in synth.gaps:
                gaps_by_type[g.get('type', 'Unknown')].append(g)

        for gap_type, gaps in gaps_by_type.items():
            if gaps:
                lines.append(f"\n**{gap_type}层面挑战**:\n")
                for g in gaps[:2]:
                    desc = g.get('description', '')[:150]
                    if desc and desc != '未明确':
                        lines.append(f"- {desc}\n")

        return "".join(lines)

    def _write_contributions(self, themes: Dict[str, ThemeSynthesis]) -> str:
        lines = []
        lines.append("本综述的主要贡献包括：\n")
        contributions = [
            "系统梳理了THz辐射产生五种技术路线的研究进展",
            "采用主题综合法识别领域内关键研究空白",
            "综合对比各技术路线的核心权衡与发展趋势",
            "提出未来研究方向的建议"
        ]
        for i, c in enumerate(contributions, 1):
            lines.append(f"{i}. {c}\n")
        return "".join(lines)

    def _write_theme_section(self, synth: ThemeSynthesis, index: int) -> str:
        lines = []

        lines.append(f"**背景**: {synth.context}\n")

        lines.append("\n**核心研究问题**:\n")
        for rq in synth.research_questions[:3]:
            if rq:
                lines.append(f"- {rq}\n")

        if synth.key_findings:
            lines.append("\n**关键性能指标**:\n")
            unique = list(dict.fromkeys(synth.key_findings))[:10]
            for f in unique:
                lines.append(f"- {f}\n")

        if synth.representative_papers:
            lines.append("\n**代表性工作**:\n")
            for j, p in enumerate(synth.representative_papers[:3], 1):
                title = p['title'][:60] + ('...' if len(p['title']) > 60 else '')
                authors = p.get('authors', 'Unknown')
                year = p.get('year', 'N/A')
                findings = '; '.join(p.get('findings', [])[:2]) if p.get('findings') else ''
                metrics = '; '.join(p.get('metrics', [])[:2]) if p.get('metrics') else ''
                lines.append(f"- [{j}] {title} ({authors}, {year})")
                if findings or metrics:
                    parts = [x for x in [findings, metrics] if x]
                    lines.append(f" - {'; '.join(parts)}")
                lines.append("\n")

        lines.append("\n**综合评述**:\n")
        if synth.gaps:
            main_gap = synth.gaps[0]
            lines.append(f"该领域主要存在{main_gap.get('type', 'Theoretical')} Gap：{main_gap.get('description', '')[:100]}...\n")
        if synth.future_directions:
            lines.append(f"未来发展方向：{synth.future_directions[0]}\n")

        return "".join(lines)

    def _write_comparison_table(self, themes: Dict[str, ThemeSynthesis]) -> str:
        """技术路线综合对比表"""
        lines = []
        lines.append("| 技术路线 | 核心原理 | 典型带宽 | 功率水平 | 主要优势 | 主要局限 | 成熟度 |\n")
        lines.append("|---------|---------|---------|---------|---------|---------|--------|\n")

        route_info = {
            '光整流': ['二阶非线性', '0.1-5 THz', 'μJ-mJ级', '能量高、相干性好', '晶体损伤阈值', '高'],
            '激光等离子体': ['四波混频', '0.1-30 THz', 'μJ级', '带宽极宽', '系统复杂', '中'],
            '超表面/等离子体': ['共振效应', '0.1-5 THz', 'nW-μW级', '体积小、可调制', '效率较低', '中'],
            'PCA (光电导天线)': ['光载流子', '0.1-5 THz', 'μW-mW级', '技术成熟', '频率受限', '高'],
            'QCL (量子级联激光器)': ['子带间跃迁', '1-5 THz', 'mW级', '电泵浦、室温', '需低温', '中'],
        }

        for theme in themes.keys():
            info = route_info.get(theme, ['-'] * 6)
            lines.append(f"| {theme} | {info[0]} | {info[1]} | {info[2]} | {info[3]} | {info[4]} | {info[5]} |\n")

        return "".join(lines)

    def _write_tradeoff_analysis(self, themes: Dict[str, ThemeSynthesis]) -> str:
        """核心权衡分析 - 去重版本"""
        lines = []
        lines.append("THz源设计面临多目标优化挑战，主要权衡关系如下：\n")

        # 使用集合去重
        all_tradeoffs = []
        seen = set()
        for synth in themes.values():
            for t in synth.tradeoffs:
                if t and t not in seen:
                    seen.add(t)
                    all_tradeoffs.append(t)

        for t in all_tradeoffs:
            lines.append(f"- **{t}**: 需根据具体应用场景取舍\n")

        lines.append("\n实际研究中，通常需要在以上权衡中选择平衡点：\n")
        lines.append("- 成像应用：优先考虑带宽和信噪比\n")
        lines.append("- 通信应用：优先考虑频率调谐范围\n")
        lines.append("- 光谱应用：优先考虑频谱纯度和稳定性\n")

        return "".join(lines)

    def _write_future_directions(self, themes: Dict[str, ThemeSynthesis]) -> str:
        lines = []
        lines.append("基于本综述识别的研究空白，未来研究应关注以下方向：\n")

        future_by_route = defaultdict(list)
        for synth in themes.values():
            for d in synth.future_directions:
                future_by_route[synth.theme].append(d)

        for theme, directions in future_by_route.items():
            if directions:
                lines.append(f"\n**{theme}**:\n")
                for d in directions[:2]:
                    lines.append(f"- {d}\n")

        return "".join(lines)

    def _write_conclusion(self, themes: Dict[str, ThemeSynthesis]) -> str:
        lines = []
        lines.append("本综述系统梳理了THz辐射产生技术的研究现状，主要结论如下：\n")

        conclusions = [
            "光电导天线和光整流技术成熟度较高，是目前实验室主流THz源",
            "激光等离子体技术可实现最宽带宽，适合超快 spectroscopy 应用",
            "超表面/等离子体技术为紧凑型THz调制提供新思路",
            "量子级联激光器在电泵浦方面具有优势，但需解决室温工作问题",
            "现有研究在多技术路线对比、材料系统性研究等方面存在明显空白"
        ]

        for i, c in enumerate(conclusions, 1):
            lines.append(f"{i}. {c}\n")

        lines.append("\n未来随着新材料、新结构的发展，THz源技术有望在功率、带宽、调谐性等方面取得突破，推动THz技术在更多领域实现应用。")

        return "".join(lines)

    def _write_references(self, themes: Dict[str, ThemeSynthesis]) -> str:
        lines = []

        all_papers = []
        seen_titles = set()
        for synth in themes.values():
            for p in synth.representative_papers:
                title = p.get('title', '')[:50]
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_papers.append(p)

        for i, p in enumerate(all_papers[:15], 1):
            authors = p.get('authors', 'Unknown')
            year = p.get('year', 'N/A')
            title = p.get('title', 'Untitled')
            citations = p.get('citations', 0)
            sources = p.get('sources', [])
            source_str = f" [{', '.join(sources)}]" if sources else ""

            lines.append(f"[{i}] {authors} ({year}). {title}. (Citations: {citations}){source_str}\n")

        return "".join(lines)

    def _generate_bibtex(self, themes: Dict[str, ThemeSynthesis], bibfile_path: str) -> int:
        """生成 BibTeX 文件

        Returns:
            生成的参考文献数量
        """
        import re

        all_papers = []
        seen_titles = set()
        for synth in themes.values():
            for p in synth.representative_papers:
                title = p.get('title', '')[:80]  # BibTeX key 使用前80字符
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_papers.append(p)

        bib_entries = []
        for i, p in enumerate(all_papers, 1):
            authors_str = p.get('authors', 'Unknown')
            # 如果 authors 是列表，转换为 "Last, First and Last2, First2" 格式
            if isinstance(authors_str, list):
                author_parts = []
                for author in authors_str[:6]:  # 最多6个作者
                    # 尝试解析 "Last, First" 或 "First Last" 格式
                    parts = author.split()
                    if len(parts) >= 2:
                        author_parts.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
                    else:
                        author_parts.append(author)
                authors_str = " and ".join(author_parts)

            year = p.get('year', '')
            title = p.get('title', 'Untitled')
            journal = p.get('journal', '')
            doi = p.get('doi', '')

            # 生成 BibTeX key: AuthorYear + title word
            title_word = re.sub(r'[^a-zA-Z]', '', title.split()[0] if title.split() else 'unk')
            bib_key = f"{authors_str.split()[0] if authors_str else 'unk'}{year}{title_word}" if year else f"ref{i}"

            entry = f"@article{{{bib_key},\n"
            entry += f"  author = {{{authors_str}}},\n"
            entry += f"  title = {{{title}}},\n"
            if year:
                entry += f"  year = {{{year}}},\n"
            if journal:
                entry += f"  journal = {{{journal}}},\n"
            if doi:
                entry += f"  doi = {{{doi}}},\n"
            entry += "}\n"

            bib_entries.append(entry)

        # 写入 BibTeX 文件
        with open(bibfile_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(bib_entries))

        return len(bib_entries)


# =============================================================================
# 主流程
# =============================================================================

def run_academic_review(query: str, max_papers: int = 50, quality_gate: bool = True, iterations: int = 3, version: str = "v5", template: str = 'md') -> Dict:
    """运行完整学术综述流程

    Args:
        query: 搜索主题
        max_papers: 最大论文数
        quality_gate: 是否启用质量门禁
        iterations: 迭代优化次数
        version: 版本选择 "v4" 或 "v5" (默认v5)
        template: 模板选择 'md' (markdown) 或 'tex' (LaTeX)
    """

    version_str = "v5" if version == "v5" else "v4.3"
    print("=" * 70)
    print(f"学术综述生成系统 {version_str} - 规划驱动写作 + Gap-Driven Structure")
    print("=" * 70)

    # Stage 1: 知识收集
    curation = KnowledgeCuration()
    papers, tavily_results = curation.curate(query, max_papers)

    # 保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    paper_db_file = f"{OUTPUT_DIR}/paper_db_{query.replace(' ', '_')[:20]}.jsonl"
    with open(paper_db_file, 'w', encoding='utf-8') as f:
        for p in papers:
            f.write(json.dumps(asdict(p), ensure_ascii=False) + '\n')
    print(f"\n>> 论文库已保存: {paper_db_file}")

    # Stage 2: 主题综合
    print("\n>> Stage 2: 主题综合 (Thematic Synthesis)")
    if version == "v5":
        synthesis = EnhancedThematicSynthesis()  # v5.1: 增强版主题综合
        print("    [Synthesis] 使用 EnhancedThematicSynthesis (深度分析)")
    else:
        synthesis = ThematicSynthesis()          # v4.3: 传统主题综合
        print("    [Synthesis] 使用 ThematicSynthesis (传统)")
    themes = synthesis.synthesize(papers, tavily_results)
    print(f"    综合了 {len(themes)} 个主题")

    for theme, synth in themes.items():
        print(f"    - {theme}: {len(synth.representative_papers)} 篇代表性论文")
        # v5: 打印gap类型检查
        if version == "v5" and synth.gaps:
            gap_types = [g.get('type', '') for g in synth.gaps]
            print(f"      Gaps: {', '.join(gap_types)}")

    # Stage 3: 论文级综述生成
    print("\n>> Stage 3: 论文级综述生成")
    if version == "v5":
        writer = AcademicReviewWriterV5()  # v5: 规划驱动写作
        print("    [Writer] 使用 AcademicReviewWriterV5 (Gap-Driven)")
    else:
        writer = AcademicReviewWriter()     # v4: 传统方式
        print("    [Writer] 使用 AcademicReviewWriter (模板填充)")
    review = writer.write(themes, query)

    # Stage 4: Quality Gate 迭代优化
    if quality_gate:
        gate = QualityGate()
        print("\n>> Stage 4: Quality Gate 迭代优化")

        best_review = review
        best_score = 0

        for i in range(iterations):
            print(f"\n  --- 迭代 {i+1}/{iterations} ---")
            theme_sample = list(themes.keys())[0] if themes else query
            review_result = gate.review(review, theme_sample)

            current_score = review_result.get('score', 0)
            if current_score > best_score:
                best_score = current_score
                best_review = review

            if review_result.get('passed', False) and current_score >= 70:
                print(f"  [PASS] 质量门禁通过! 评分: {current_score}")
                break

            if review_result.get('issues'):
                print(f"  [ISSUE] 发现 {len(review_result['issues'])} 个问题")
                for issue in review_result['issues'][:3]:
                    print(f"    - {issue[:100]}")
                review = gate.polish(review, review_result['issues'], theme_sample)
            else:
                print(f"  [RETRY] 评分过低 ({current_score}), 优化内容...")
                review = writer.write(themes, query)
                if i < iterations - 1:
                    continue

        if best_score >= 70:
            review = best_review
            print(f"\n  [FINAL] 最终评分: {best_score} (通过)")
        else:
            print(f"\n  [FINAL] 最终评分: {best_score} (未通过70分阈值)")

    # 保存 - 根据模板类型选择扩展名
    version_suffix = "v5" if version == "v5" else "v4"
    ext = 'tex' if template == 'tex' else 'md'
    review_file = f"{OUTPUT_DIR}/academic_review_{version_suffix}_{query.replace(' ', '_')[:20]}.{ext}"

    # 如果使用 LaTeX 模板，应用模板格式化
    if template == 'tex':
        tf = TemplateFiller(template_type='tex')
        review = tf.fill(
            title=query.title() + '领域学术综述',
            authors='Author Name',
            abstract=themes.get(list(themes.keys())[0], ThemeSynthesis()).context or '学术综述摘要' if themes else '学术综述摘要',
            pacs_codes='42.60.-v, 78.20.-e',  # 默认PACS码
            bibfile=f'academic_review_{version_suffix}_{query.replace(" ", "_")[:20]}',
            acknowledgments='本研究受国家自然科学基金资助。',
            content=review
        )

    with open(review_file, 'w', encoding='utf-8') as f:
        f.write(review)
    print(f"\n>> 综述已保存: {review_file}")

    # 生成 BibTeX 文件 (仅 LaTeX 模板)
    if template == 'tex':
        bibfile_path = f"{OUTPUT_DIR}/academic_review_{version_suffix}_{query.replace(' ', '_')[:20]}.bib"
        try:
            writer_instance = writer if version == "v4" else AcademicReviewWriter()
            num_refs = writer_instance._generate_bibtex(themes, bibfile_path)
            print(f">> 参考文献已保存: {bibfile_path} ({num_refs} 条)")
        except Exception as e:
            print(f">> BibTeX 生成失败: {e}")

    print("\n" + "=" * 70)
    print("完成!")
    print("=" * 70)

    return {
        'papers': papers,
        'themes': themes,
        'review': review,
        'paper_db_file': paper_db_file,
        'review_file': review_file,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Multi-Source Academic Review Generator v5')
    parser.add_argument('query', nargs='?', default='terahertz generation', help='搜索主题')
    parser.add_argument('-n', '--max-papers', type=int, default=50, help='最大论文数')
    parser.add_argument('--no-quality-gate', action='store_true', help='跳过质量门禁')
    parser.add_argument('--iterations', type=int, default=2, help='迭代优化次数')
    parser.add_argument('--version', choices=['v4', 'v5'], default='v5', help='写作版本 (默认v5)')
    parser.add_argument('--template', choices=['md', 'tex'], default='md', help='输出模板 (默认md)')
    args = parser.parse_args()

    result = run_academic_review(
        args.query,
        args.max_papers,
        quality_gate=not args.no_quality_gate,
        iterations=args.iterations,
        version=args.version,
        template=args.template
    )
    print(f"\n收集了 {len(result['papers'])} 篇论文")


# =============================================================================
# 论文笔记生成 - 组织到 Obsidian
# =============================================================================

def create_obsidian_note_for_paper(paper: Paper, vault_path: str, pdf_path: str = None) -> str:
    """为单篇论文创建 Obsidian 笔记

    Args:
        paper: Paper 对象
        vault_path: Obsidian 保险库路径
        pdf_path: PDF 文件路径（可选）

    Returns:
        笔记文件路径
    """
    if not vault_path:
        return None

    # 论文笔记目录
    notes_dir = os.path.join(vault_path, "4️⃣ 文献库")
    os.makedirs(notes_dir, exist_ok=True)

    # 生成文件名
    safe_title = re.sub(r'[<>:"/\\|?*]', '', paper.title)[:60]
    year_str = str(paper.year) if paper.year else ""
    filename = f"{safe_title}_{year_str}.md" if year_str else f"{safe_title}.md"
    filepath = os.path.join(notes_dir, filename)

    # 构建笔记内容
    authors_str = ", ".join(paper.authors[:3]) if paper.authors else "未知作者"
    if len(paper.authors) > 3:
        authors_str += " et al."

    # 核心物理图像
    physical_image = _generate_physical_image_for_paper(paper)

    # 技术路线
    routes_str = ", ".join(paper.tech_routes) if paper.tech_routes else "THz技术"

    # 关键发现
    findings = paper.key_findings[:3] if paper.key_findings else []
    findings_str = "\n".join([f"- {f}" for f in findings]) if findings else "- 待提取"

    # Gap描述
    gaps = paper.gaps[:2] if paper.gaps else []
    gaps_str = "\n".join([f"- [{g.get('type', 'Unknown')}] {g.get('description', '')[:50]}" for g in gaps]) if gaps else "- 未明确"

    # 研究问题
    rq = paper.research_question if paper.research_question and paper.research_question != '未明确' else "尚无明确研究问题"

    content = f'''---
title: "{paper.title}"
type: paper
status: reviewed
field: optics
subfield: terahertz
tags: #THz #{paper.journal if paper.journal else 'paper'} {routes_str.replace(' ', '#')}
created: {datetime.now().strftime('%Y-%m-%d')}
related: []
paper_id: {paper.id}
doi: {paper.doi or 'N/A'}
year: {paper.year}
citations: {paper.citations}
---

# {paper.title}

> [!abstract]+ 一句话物理图像
> {physical_image}

---

## 📚 论文信息

| 属性 | 内容 |
|------|------|
| **作者** | {authors_str} |
| **年份** | {paper.year} |
| **期刊** | {paper.journal or 'N/A'} |
| **DOI** | {paper.doi or 'N/A'} |
| **引用数** | {paper.citations} |
| **技术路线** | {routes_str} |

---

## 🎯 研究问题

{rq}

---

## 💡 核心方法/approach

{paper.approach or '待从全文提取'}

---

## 📊 关键发现

{findings_str}

---

## ⚠️ 研究空白 (Gap)

{gaps_str}

---

## 🔢 关键指标

{', '.join(paper.key_metrics[:5]) if paper.key_metrics else '待提取'}

---

## 🔗 引用

'''
    # 生成 BibTeX key
    first_author = paper.authors[0].split()[-1] if paper.authors else 'Unknown'
    bibtex_key = f"{first_author}{paper.year}"
    bibtex_entry = f'''@article{{{bibtex_key},
  title={{{paper.title}}},
  author={{{', '.join(paper.authors)}}},
  journal={{{paper.journal or 'N/A'}}},
  year={{{paper.year}}},
  doi={{{paper.doi or 'N/A'}}},
}}'''
    content += bibtex_entry + "\n```\n\n'''"

    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  [Obsidian] Created: {os.path.basename(filepath)}")
    return filepath


def _generate_physical_image_for_paper(paper: Paper) -> str:
    """为论文生成一句话物理图像"""
    title = paper.title.lower()
    abstract = paper.abstract.lower() if paper.abstract else ""

    # 基于关键词生成物理图像
    if any(kw in title + abstract for kw in ['optical rectification', '光整流', 'tilted pulse']):
        return "飞秒激光在非线性晶体中像海浪推船一样产生THz波"
    elif any(kw in title + abstract for kw in ['spintronic', 'spin thz', '自旋']):
        return "电子自旋像小磁针在激光冲击下旋转辐射THz波"
    elif any(kw in title + abstract for kw in ['metasurface', '超表面', 'plasmonic']):
        return "纳米天线阵像精心排列的音叉，共振放大THz信号"
    elif any(kw in title + abstract for kw in ['laser plasma', 'filament', '双色']):
        return "强激光在气体中打出一条光丝，像迷你闪电产生THz辐射"
    elif any(kw in title + abstract for kw in ['photoconductive', 'PCA', '光电导']):
        return "光开关像超快闸门，瞬间释放载流子产生THz脉冲"
    elif any(kw in title + abstract for kw in ['quantum cascade', 'QCL', '量子级联']):
        return "量子阱中电子像走楼梯逐级下落，每步释放一个THz光子"
    else:
        return f"这篇论文探讨{paper.tech_routes[0] if paper.tech_routes else 'THz技术'}的创新方法"


def organize_papers_to_obsidian(papers: List[Paper], vault_path: str = None, download_pdfs: bool = True) -> Dict:
    """将论文组织到 Obsidian 系统

    Args:
        papers: Paper 列表
        vault_path: Obsidian 保险库路径（默认使用项目路径）
        download_pdfs: 是否下载 PDF

    Returns:
        组织结果统计
    """
    if not vault_path:
        PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
        vault_path = str(PROJECT_ROOT / "Obsidian-Vault")

    print("\n>> 组织论文到 Obsidian...")

    stats = {
        'total': len(papers),
        'notes_created': 0,
        'pdfs_downloaded': 0,
        'errors': []
    }

    # 收集所有DOI用于批量下载
    dois_with_papers = [(p.doi, p) for p in papers if p.doi]

    # 下载 PDF
    if download_pdfs:
        pdf_dir = f"{OUTPUT_DIR}/pdfs"
        os.makedirs(pdf_dir, exist_ok=True)

        openalex = OpenAlexReader()
        for doi, paper in dois_with_papers:
            if not paper.tech_routes or '其他' in paper.tech_routes:
                # 只下载需要深度分析的论文
                pdf_path = openalex.download_pdf(doi, pdf_dir)
                if pdf_path:
                    paper.pdf_path = pdf_path
                    stats['pdfs_downloaded'] += 1

    # 创建 Obsidian 笔记
    for paper in papers:
        if paper.title:
            try:
                filepath = create_obsidian_note_for_paper(paper, vault_path, getattr(paper, 'pdf_path', None))
                if filepath:
                    stats['notes_created'] += 1
            except Exception as e:
                stats['errors'].append(f"{paper.title[:30]}: {str(e)}")

    print(f"  创建了 {stats['notes_created']} 篇 Obsidian 笔记")
    print(f"  下载了 {stats['pdfs_downloaded']} 篇 PDF")

    if stats['errors']:
        print(f"  错误: {stats['errors'][:3]}")

    return stats
    print(f"综合了 {len(result['themes'])} 个主题")
    print(f"生成了 {len(result['review'])} 字的学术综述")


# =============================================================================
# v5 核心改进: 规划驱动写作 (Gap-Driven Writing)
# =============================================================================

class PaperStrategyPlanner:
    """
    论文写作策略规划器 - v5 核心

    在写作前先分析：
    1. 核心Gap是什么？（必须先确定）
    2. 论文结构如何？（IMRAD vs 综述格式）
    3. 每个section写什么？（具体内容规划）
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        if not self.llm_client:
            try:
                self.llm_client = get_llm_client()
            except:
                pass

    def plan(self, themes: Dict[str, ThemeSynthesis], query: str) -> Dict:
        """
        生成论文写作规划

        返回:
        {
            'core_gap': str,           # 核心Gap一句话
            'gap_type': str,           # Gap分类
            'structure': str,          # 论文结构
            'intro_plan': List[str],   # 引言4段式规划
            'section_emphasis': Dict,  # 每节重点
            'writing_order': List[str], # 写作顺序
        }
        """
        if not self.llm_client:
            return self._default_plan(query)

        # 收集所有Gap信息
        all_gaps = []
        all_questions = []
        for synth in themes.values():
            all_gaps.extend(synth.gaps)
            all_questions.extend(synth.research_questions)

        gaps_text = "\n".join([f"- [{g.get('type', 'Unknown')}]: {g.get('description', '')}" for g in all_gaps[:10]])
        questions_text = "\n".join([f"- {q}" for q in all_questions[:5]])

        prompt = f"""你是学术论文写作策略专家。请分析以下综述的写作策略。

**主题**: {query}

**已识别的Gap**:
{gaps_text}

**核心研究问题**:
{questions_text}

请输出JSON格式的写作规划：
{{
    "core_gap": "用1-2句话描述本文要填补的最核心空白",
    "gap_type": "Methodological/Parameter/Comparative/Theoretical/Condition",
    "structure": "standard_review/imrad/letter",
    "intro_plan": {{
        "paragraph1": "第1段规划: 领域重要性(1-2句)",
        "paragraph2": "第2段规划: 前人工作分类讨论(3-4句)",
        "paragraph3": "第3段规划: 明确Gap陈述(1-2句)",
        "paragraph4": "第4段规划: 本文贡献(2-3句)"
    }},
    "section_emphasis": {{
        "background": "本节重点描述什么",
        "literature_review": "如何分类讨论前人工作",
        "theme_sections": "每个主题section的写作重点",
        "discussion": "讨论部分的批判性分析要点"
    }},
    "writing_order": ["建议的写作顺序"]
}}

只返回JSON。"""

        try:
            messages = [
                {"role": "system", "content": "你是学术论文写作策略专家，擅长Gap-Driven Writing。"},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_client.chat_completions_create(messages, temperature=0.1, max_tokens=1000)
            content = response['choices'][0]['message']['content']

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                plan = json_module.loads(json_match.group(0))
                print(f"  [Planner] Core Gap: {plan.get('core_gap', '')[:50]}...")
                print(f"  [Planner] Gap Type: {plan.get('gap_type', 'Unknown')}")
                return plan

        except Exception as e:
            print(f"  [Planner] Error: {e}")

        return self._default_plan(query)

    def _default_plan(self, query: str) -> Dict:
        """默认规划（当LLM不可用时）"""
        return {
            'core_gap': f'现有研究缺乏对{query}的系统的理论-实验对比分析',
            'gap_type': 'Comparative',
            'structure': 'standard_review',
            'intro_plan': {
                'paragraph1': f'{query}技术的重要性与应用前景',
                'paragraph2': '前人工作按技术路线分类讨论',
                'paragraph3': '现有研究的系统性空白',
                'paragraph4': '本文的综合贡献'
            },
            'section_emphasis': {
                'background': 'THz技术背景和应用',
                'literature_review': '按5种技术路线分类描述',
                'theme_sections': '每种技术的原理、指标、代表工作',
                'discussion': '技术对比和未来方向'
            },
            'writing_order': ['abstract', 'intro', 'themes', 'discussion', 'conclusion']
        }


class GapDrivenIntroductionWriter:
    """
    Gap驱动的引言写作器 - v5 核心改进

    真正实现4段式引言：
    1. 领域重要性 + 经典框架
    2. 前人工作批判性分类讨论
    3. 明确Gap陈述
    4. 本文具体贡献
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        if not self.llm_client:
            try:
                self.llm_client = get_llm_client()
            except:
                pass

    def write(self, themes: Dict[str, ThemeSynthesis], query: str, plan: Dict = None) -> str:
        """生成Gap驱动的引言"""
        if not self.llm_client or not plan:
            return self._fallback_intro(themes, query)

        # 提取规划信息
        core_gap = plan.get('core_gap', '')
        gap_type = plan.get('gap_type', 'Comparative')
        intro_plan = plan.get('intro_plan', {})

        # 收集前人工作用于分类
        literature_by_theme = self._organize_literature(themes)

        # 生成4段式引言
        paragraphs = []

        # 第1段: 领域重要性
        p1 = self._write_paragraph1(query)
        paragraphs.append(p1)

        # 第2段: 前人分类讨论 (关键改进!)
        p2 = self._write_paragraph2(literature_by_theme, query)
        paragraphs.append(p2)

        # 第3段: Gap陈述
        p3 = self._write_paragraph3(core_gap, gap_type)
        paragraphs.append(p3)

        # 第4段: 本文贡献
        p4 = self._write_paragraph4(themes, query)
        paragraphs.append(p4)

        return "\n\n".join(paragraphs)

    def _organize_literature(self, themes: Dict[str, ThemeSynthesis]) -> Dict:
        """按主题组织文献，提取每个主题的核心局限"""
        organized = {}
        for theme, synth in themes.items():
            papers = synth.representative_papers[:3]
            limitations = synth.gaps[:2]

            organized[theme] = {
                'count': len(synth.representative_papers),
                'key_papers': papers,
                'limitations': [g.get('description', '') for g in limitations],
                'approaches': list(set([p.get('approach', '')[:50] for p in papers if p.get('approach')]))
            }
        return organized

    def _write_paragraph1(self, query: str) -> str:
        """第1段: 领域重要性"""
        return f"""太赫兹(Terahertz, THz)辐射通常指频率在0.1-10 THz之间的电磁波，位于微波与红外之间。该频段具有独特的光谱特性：许多生物分子和半导体材料的声子模式位于THz频段；THz波可穿透非极性材料（如纸张、塑料、衣物）而不产生电离损伤；THz脉冲可实现亚皮秒时间分辨率。这些特性使THz技术在传感成像、通信、安全检测等领域具有重要应用前景。"""

    def _write_paragraph2(self, literature_by_theme: Dict, query: str) -> str:
        """第2段: 前人工作一句话定位 - 详细分析留给正文！

        核心原则：引言只给一句话定位，详细比较和局限分析在正文和讨论中进行
        """
        if not literature_by_theme:
            return f"目前，THz辐射产生主要依赖五种技术路线，相关研究已发表大量论文。"

        # 一句话定位每个技术路线（只保留核心特色）
        route_punchlines = {
            'PCA (光电导天线)': '技术成熟，广泛应用于THz时域光谱系统',
            '光整流': '基于二阶非线性效应，是产生宽频带THz脉冲的主流方法',
            '激光等离子体': '通过四波混频产生超宽带THz辐射，是实现远程探测的重要手段',
            'QCL (量子级联激光器)': '唯一的电泵浦固态THz源，在片上集成方面具有独特优势',
            '超表面/等离子体': '通过亚波长结构实现灵活多变的THz波调控，是新型调制技术的重要方向',
        }

        lines = ["针对THz辐射产生，前人已发展了五种主要技术路线："]

        for theme, info in literature_by_theme.items():
            punchline = route_punchlines.get(theme, f'{theme}是重要技术路线')
            count = info.get('count', 0)
            lines.append(f"{punchline}（{count}篇代表性论文）。")

        lines.append("这些技术在实际应用中各具优势与局限，其系统性的性能比较与优化策略尚待深入研究。")

        return "".join(lines)

    def _write_paragraph3(self, core_gap: str, gap_type: str) -> str:
        """第3段: Gap陈述"""
        if not core_gap:
            core_gap = "现有研究缺乏对不同技术路线在宽参数范围内的系统性性能比较"

        GAP_PATTERNS = {
            'Methodological': '尽管实验技术不断进步，但缺乏系统的{对比方法}来评估不同技术路线的性能边界。',
            'Parameter': '现有研究主要集中在特定参数范围，{更宽参数范围}的系统性研究仍属空白。',
            'Comparative': '不同技术路线之间的{直接性能对比}研究尚未系统开展。',
            'Theoretical': '虽然理论模型不断完善，但{理论预测与实验验证的系统性对比}仍有待深入。',
            'Condition': '在{特定条件(如室温/高功率/宽频带)}下的系统研究仍然缺乏。',
        }

        pattern = GAP_PATTERNS.get(gap_type, '现有研究在{核心问题}方面仍存在明显不足。')
        gap_statement = pattern.replace('{核心问题}', core_gap[:50]) if '{核心问题}' in pattern else pattern

        return f"**研究空白**: {gap_statement}"

    def _write_paragraph4(self, themes: Dict[str, ThemeSynthesis], query: str) -> str:
        """第4段: 本文贡献"""
        tech_count = len(themes)
        theme_names = list(themes.keys())[:3] if themes else ['光电导天线', '光整流', '激光等离子体']

        contributions = [
            f"系统梳理了{tech_count}种主要THz辐射技术路线({', '.join(theme_names)}等)的研究进展",
            "采用主题综合法识别领域内关键研究空白",
            "综合对比各技术路线的核心权衡与发展趋势",
            "提出未来研究方向的建议"
        ]

        lines = ["**本文贡献**: " + "本综述的主要贡献包括："]
        for i, c in enumerate(contributions, 1):
            lines.append(f"{i}. {c}")

        return "\n".join(lines)

    def _fallback_intro(self, themes: Dict[str, ThemeSynthesis], query: str) -> str:
        """备用引言（当LLM不可用时）"""
        p1 = self._write_paragraph1(query)
        p2 = "目前，THz辐射产生主要依赖以下技术路线，相关研究已取得重要进展。"
        p3 = "**研究空白**: 现有研究缺乏对不同技术路线在宽参数范围内的系统性性能比较。"
        p4 = self._write_paragraph4(themes, query)
        return "\n\n".join([p1, p2, p3, p4])


class CriticalLiteratureReviewWriter:
    """
    批判性文献综述写作器 - v5 核心改进

    替代简单的文献罗列，实现：
    1. 按主题/方法分类
    2. 每类工作的共同局限
    3. 与其他类工作的差异
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        if not self.llm_client:
            try:
                self.llm_client = get_llm_client()
            except:
                pass

    def write(self, themes: Dict[str, ThemeSynthesis]) -> str:
        """生成批判性文献综述"""
        if not themes:
            return "相关文献综述暂无。"

        lines = []

        # 按技术路线分组
        for theme, synth in themes.items():
            lines.append(f"### {theme}\n")

            # 1. 该技术路线的核心思想
            if synth.context:
                lines.append(f"**核心方法**: {synth.context[:200]}\n")

            # 2. 该技术路线的主要研究问题
            if synth.research_questions:
                lines.append("**主要研究问题**:\n")
                for q in synth.research_questions[:3]:
                    if q:
                        lines.append(f"- {q}\n")
                lines.append("\n")

            # 3. 该技术路线的共同局限（批判性分析！）
            if synth.gaps:
                lines.append("**该技术路线的共同局限**:\n")
                for gap in synth.gaps[:2]:
                    gap_type = gap.get('type', '')
                    gap_desc = gap.get('description', '')
                    if gap_desc and gap_desc != '未明确':
                        lines.append(f"- [{gap_type}] {gap_desc[:100]}\n")
                lines.append("\n")

            # 4. 与其他技术路线的联系与差异
            lines.append("**与其他技术路线的关系**: \n")
            other_themes = [t for t in themes.keys() if t != theme]
            if other_themes:
                lines.append(f"与{other_themes[0]}相比，{theme}具有独特的{ synth.key_findings[0] if synth.key_findings else '性能优势'}，但在{'某些方面' if synth.gaps else '系统集成'}仍有待改进。\n")

        return "".join(lines)


# v5 增强版 AcademicReviewWriter
class AcademicReviewWriterV5(AcademicReviewWriter):
    """
    学术综述写作器 v5 - 规划驱动版本

    核心改进:
    1. 写作前先规划(Gap-Driven)
    2. 引言采用4段式结构
    3. 文献综述采用批判性分析
    """

    def write(self, themes: Dict[str, ThemeSynthesis], query: str) -> str:
        # Step 1: 先规划，再写作 (Gap-Driven!)
        planner = PaperStrategyPlanner()
        plan = planner.plan(themes, query)

        lines = []

        # 标题
        lines.append(f"# {query.title()}领域学术综述\n")

        # 摘要 - 改进版
        lines.append("## 摘要\n")
        lines.append(self._write_abstract_v5(themes, query, plan))

        # 引言 - 核心改进：Gap驱动的4段式（不包含详细文献综述）
        lines.append("\n## 一、引言\n")
        intro_writer = GapDrivenIntroductionWriter()
        lines.append(intro_writer.write(themes, query, plan))

        # 研究现状 - 简洁版本：只列出技术路线，不展开
        lines.append("\n### 1.2 国内外研究现状\n")
        lines.append(self._write_literature_overview(themes))

        # 问题与挑战
        lines.append("\n### 1.3 存在的问题与挑战\n")
        lines.append(self._write_problems_challenges_v2(themes))

        # 主要贡献
        lines.append("\n### 1.4 本文的主要贡献\n")
        lines.append(self._write_contributions(themes))

        # 技术路线分析 - 每个主题section
        lines.append("\n## 二、技术路线分析\n")
        for i, (theme, synth) in enumerate(themes.items(), 1):
            lines.append(f"\n### 2.{i} {synth.theme}\n")
            lines.append(self._write_theme_section_v5(synth, i, plan))

        # 讨论
        lines.append("\n## 三、讨论\n")
        lines.append("\n### 3.1 技术路线综合对比\n")
        lines.append(self._write_comparison_table(themes))
        lines.append("\n### 3.2 核心权衡分析\n")
        lines.append(self._write_tradeoff_analysis(themes))
        lines.append("\n### 3.3 未来研究方向\n")
        lines.append(self._write_future_directions(themes))

        # 结论
        lines.append("\n## 四、结论\n")
        lines.append(self._write_conclusion(themes))

        # 参考文献
        lines.append("\n## 参考文献\n")
        lines.append(self._write_references(themes))

        return "\n".join(lines)

    def _write_abstract_v5(self, themes: Dict, query: str, plan: Dict) -> str:
        """v5摘要 - 包含Gap和贡献"""
        core_gap = plan.get('core_gap', '') if plan else ''
        gap_type = plan.get('gap_type', 'Comparative') if plan else 'Comparative'

        lines = []

        # Context
        lines.append(f"{query.title()}技术在传感成像、通信、安全检测等领域具有重要应用潜力。")

        # Gap
        if core_gap:
            lines.append(f"然而，现有研究在{core_gap[:50]}方面仍存在明显不足。")

        # Method
        tech_count = len(themes)
        lines.append(f"本综述采用主题综合法，系统梳理了{tech_count}种主要技术路线，")

        # Results
        total_papers = sum(len(s.representative_papers) for s in themes.values()) if themes else 0
        lines.append(f"识别出以{gap_type}类型为主的{sum(len(s.gaps) for s in themes.values()) if themes else 0}个关键研究空白，")
        lines.append(f"共涵盖{total_papers}篇代表性论文。")

        # Conclusion
        lines.append("本综述为领域研究者提供了全面的技术路线图和未来发展方向参考。")

        return "".join(lines)

    def _write_literature_overview(self, themes: Dict[str, ThemeSynthesis]) -> str:
        """简洁的研究现状概述 - 只列出一句话，不展开

        核心原则：详细分析在"二、技术路线分析"中进行
        """
        if not themes:
            return "相关研究现状详见技术路线分析章节。"

        route_brief = {
            'PCA (光电导天线)': '光电导天线(PCA)基于超快光载流子注入，是THz时域光谱系统的核心辐射源',
            '光整流': '光整流通过飞秒激光与非线性晶体相互作用，是产生THz脉冲的重要非线性光学方法',
            '激光等离子体': '激光等离子体利用强场激光与气体介质相互作用，通过四波混频产生宽带THz波',
            'QCL (量子级联激光器)': '量子级联激光器(QCL)基于子带间跃迁，是固态电泵浦THz源的重要选择',
            '超表面/等离子体': '超表面通过亚波长谐振单元实现电磁波调控，为THz调制提供紧凑高效方案',
        }

        lines = ["目前，THz辐射产生主要依赖以下五种技术路线：\n"]
        for theme in themes.keys():
            brief = route_brief.get(theme, f'{theme}是THz技术的重要路线')
            lines.append(f"- **{theme}**: {brief}。\n")

        lines.append("\n各技术路线的详细分析、性能指标、代表工作和研究空白见本文第二章。")

        return "".join(lines)

    def _write_problems_challenges_v2(self, themes: Dict[str, ThemeSynthesis]) -> str:
        """精简版问题与挑战 - 按Gap类型分组

        核心原则：不重复正文的内容，只总结最关键的Gap
        """
        # 按Gap类型聚合
        gaps_by_type = defaultdict(list)
        for synth in themes.values():
            for g in synth.gaps:
                gap_type = g.get('type', 'Unknown')
                gap_desc = g.get('description', '')
                if gap_desc and gap_desc != '未明确':
                    gaps_by_type[gap_type].append(gap_desc)

        lines = []
        lines.append("基于主题综合分析，该领域主要存在以下关键研究空白：\n")

        gap_type_names = {
            'Methodological': '方法论层面',
            'Parameter': '参数范围层面',
            'Comparative': '系统比较层面',
            'Theoretical': '理论框架层面',
            'Condition': '适用条件层面',
        }

        for gap_type, gaps in sorted(gaps_by_type.items()):
            if gaps:
                type_name = gap_type_names.get(gap_type, gap_type)
                lines.append(f"\n**{type_name}挑战**:\n")
                # 每类只列2个最重要的gap
                for g in list(dict.fromkeys(gaps))[:2]:
                    lines.append(f"- {g[:100]}\n")

        return "".join(lines)

    def _write_theme_section_v5(self, synth: ThemeSynthesis, index: int, plan: Dict = None) -> str:
        """v5主题section - 增强批判性分析"""
        lines = []

        # 背景（简洁）
        lines.append(f"**背景**: {synth.context[:150] if synth.context else '该技术路线相关研究'}\n")

        # 核心研究问题
        lines.append("\n**核心研究问题**:\n")
        for rq in synth.research_questions[:3]:
            if rq:
                lines.append(f"- {rq}\n")

        # 关键性能指标
        if synth.key_findings:
            lines.append("\n**关键性能指标**:\n")
            unique = list(dict.fromkeys(synth.key_findings))[:8]
            for f in unique:
                lines.append(f"- {f}\n")

        # 代表性工作（简化）
        if synth.representative_papers:
            lines.append("\n**代表性工作**:\n")
            for j, p in enumerate(synth.representative_papers[:3], 1):
                title = p.get('title', '')[:50]
                authors = p.get('authors', 'Unknown')
                year = p.get('year', 'N/A')
                lines.append(f"- [{j}] {title}... ({authors}, {year})\n")

        # 综合评述 - 包含Gap和未来方向
        lines.append("\n**综合评述**:\n")
        if synth.gaps:
            main_gap = synth.gaps[0]
            lines.append(f"- Gap类型: {main_gap.get('type', 'Unknown')}\n")
            gap_desc = main_gap.get('description', '')
            if gap_desc and gap_desc != '未明确':
                lines.append(f"- Gap描述: {gap_desc[:80]}\n")

        if synth.future_directions:
            lines.append(f"- 未来方向: {synth.future_directions[0][:80]}\n")

        return "".join(lines)


if __name__ == "__main__":
    main()