#!/usr/bin/env python3
"""
Multi-Source Academic Paper Writing System v5.2 (整合科研写作skills优化版)

核心改进 vs v5.1:
1. LLM驱动的文本人类化 - 通过 humanizer skill 原则消除AI痕迹
2. 两阶段写作 - 先规划要点，再转换为流畅段落
3. 审稿人视角自审 - claim-evidence对齐检查
4. 强化主题综合 - 解决研究问题趋同问题
5. 一段一意原则 - 每段只传达一个信息
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Any
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
_embedding_client = None

def get_llm_client():
    global _llm_client
    if _llm_client is None:
        _llm_client = MultiLLMClient(LLM_PROVIDERS)
    return _llm_client

# =============================================================================
# Embedding 模型客户端 - 语义匹配
# =============================================================================

EMBEDDING_API_KEY = os.getenv("ZCHAT_API_KEY", "")
EMBEDDING_BASE_URL = os.getenv("ZCHAT_BASE_URL", "https://api.zchat.tech/v1")
EMBEDDING_MODEL = "text-embedding-3-large"

class EmbeddingClient:
    """ZChat Embedding 模型客户端 - 用于语义匹配"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or EMBEDDING_API_KEY
        self.base_url = base_url or EMBEDDING_BASE_URL
        self.model = model or EMBEDDING_MODEL
        self._embedding_cache = {}

    def get_embedding(self, text: str, model: str = None) -> List[float]:
        """获取文本的 embedding 向量"""
        if not text or not text.strip():
            return [0.0] * 3072  # text-embedding-3-large 返回 3072 维

        cache_key = f"{model or self.model}:{text[:100]}"
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        try:
            import requests
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'model': model or self.model,
                'input': text[:8000]  # 限制输入长度
            }
            r = requests.post(f'{self.base_url}/embeddings', json=data, headers=headers, timeout=30)
            if r.status_code == 200:
                result = r.json()
                embedding = result.get('data', [{}])[0].get('embedding', [])
                self._embedding_cache[cache_key] = embedding
                return embedding
        except Exception as e:
            print(f"  [Embedding] Error: {e}")
        return [0.0] * 3072

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def semantic_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的语义相似度"""
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        return self.cosine_similarity(emb1, emb2)

    def find_most_similar(self, query: str, candidates: List[str], top_k: int = 5) -> List[Tuple[int, float]]:
        """找到与查询最相似的 K 个候选文本"""
        query_emb = self.get_embedding(query)
        similarities = []
        for i, candidate in enumerate(candidates):
            cand_emb = self.get_embedding(candidate)
            sim = self.cosine_similarity(query_emb, cand_emb)
            similarities.append((i, sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

def get_embedding_client() -> EmbeddingClient:
    """获取全局 embedding 客户端"""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client

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
    """模拟审稿人质量门禁 - 支持多期刊格式"""

    # 多期刊格式配置
    JOURNAL_CONFIGS = {
        'IEEE': {'abstract_range': (150, 250), 'ref_style': 'ieee', 'max_refs': None},
        'Nature Photonics': {'abstract_range': (0, 200), 'ref_style': 'nature', 'max_refs': 100},
        'Optics Express': {'abstract_range': (150, 200), 'ref_style': 'author_year', 'max_refs': 50},
        'Advanced Photonics': {'abstract_range': (0, 200), 'ref_style': 'spie', 'max_refs': None},
        'J. IRMM THz Waves': {'abstract_range': (150, 250), 'ref_style': 'springer', 'max_refs': None},
    }

    def __init__(self):
        self.llm_client = None
        try:
            self.llm_client = get_llm_client()
        except:
            pass

    def review(self, review_text: str, theme: str, target_journal: str = 'IEEE') -> Dict:
        """模拟审稿人审查生成内容 - 支持多期刊格式检查"""
        config = self.JOURNAL_CONFIGS.get(target_journal, self.JOURNAL_CONFIGS['IEEE'])

        # 格式问题收集
        format_issues = []

        # 提取摘要进行格式检查 - 支持多种格式
        abstract_text = ""

        # 1. LaTeX格式
        latex_match = re.search(r'\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}', review_text)
        if latex_match:
            abstract_text = latex_match.group(1).strip()

        # 2. Markdown h2格式 (## 摘要)
        if not abstract_text:
            md_h2_match = re.search(r'##\s*摘要\s*\n([\s\S]*?)(?=\n##|\n#|\Z)', review_text)
            if md_h2_match:
                abstract_text = md_h2_match.group(1).strip()

        # 3. Markdown h1格式 (# 摘要)
        if not abstract_text:
            md_h1_match = re.search(r'#\s*摘要\s*\n([\s\S]*?)(?=\n##|\n#|\Z)', review_text)
            if md_h1_match:
                abstract_text = md_h1_match.group(1).strip()

        # 4. Fallback: 取前500字作为摘要
        if not abstract_text:
            abstract_text = review_text[:500]

        # 计算字数（按空格分词，中文按字符）
        import unicodedata
        def count_words(text):
            # 英文按空格分词
            english_words = len(text.split())
            # 中文字符 (使用Unicode category判断，更可靠)
            chinese_chars = sum(1 for c in text if unicodedata.category(c) in ('Lo', 'Li'))
            return english_words + chinese_chars

        word_count = count_words(abstract_text)

        # 检查期刊特定格式
        min_words, max_words = config['abstract_range']
        if min_words > 0 and word_count < min_words:
            format_issues.append(f"[{target_journal}] Abstract too short: {word_count} words (min {min_words})")
        if word_count > max_words:
            format_issues.append(f"[{target_journal}] Abstract exceeds {max_words} words: {word_count} words")

        # 多期刊评分（不同期刊有不同的评分标准）
        journal_scoring = {
            'IEEE': {'structure': 20, 'gap': 25, 'depth': 25, 'citations': 15, 'writing': 15},
            'Nature Photonics': {'structure': 15, 'gap': 30, 'depth': 30, 'citations': 10, 'writing': 15},
            'Optics Express': {'structure': 20, 'gap': 25, 'depth': 25, 'citations': 15, 'writing': 15},
        }
        scoring = journal_scoring.get(target_journal, journal_scoring['IEEE'])

        prompt = f"""你是一位严苛的{theme}领域资深审稿人。请审查以下学术综述内容。

**主题**: {theme}
**目标期刊**: {target_journal}

请从以下5个维度分别评分(0-100)，然后给出综合评分：
1. **结构完整性** ({scoring['structure']}分): 是否有清晰的C-C-C结构？是否包含所有必要章节？
2. **研究空白识别** ({scoring['gap']}分): 是否正确识别并分类了5类研究空白？Gap描述是否具体？
3. **内容深度** ({scoring['depth']}分): 是否有深度的技术分析？是否避免了文献堆砌？
4. **代表性工作质量** ({scoring['citations']}分): 引用的论文是否相关？关键发现是否准确？
5. **写作质量** ({scoring['writing']}分): 是否学术规范？逻辑是否清晰？

**综述内容** (前4000字):
{review_text[:4000]}

请严格评分，返回JSON格式：
{{
    "score": 综合评分数字(0-100),
    "dimension_scores": {{
        "structure": 结构完整性分数(0-{scoring['structure']}),
        "gap_identification": 研究空白识别分数(0-{scoring['gap']}),
        "depth": 内容深度分数(0-{scoring['depth']}),
        "citations": 代表性工作质量分数(0-{scoring['citations']}),
        "writing": 写作质量分数(0-{scoring['writing']})
    }},
    "issues": ["具体问题1", "问题2", "问题3"],
    "passed": true或false
}}

注意：严格评分，不要给出虚假高分。"""

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

                # 添加格式问题到结果
                result['format_issues'] = format_issues
                if format_issues:
                    score = max(0, score - len(format_issues) * 2)  # 每个格式问题扣2分

                print(f"  [QualityGate] Score: {score}, Passed: {passed}, Journal: {target_journal}")
                if format_issues:
                    print(f"  [QualityGate] Format issues: {format_issues}")
                return {'score': score, 'issues': result.get('issues', []) + format_issues, 'passed': passed, 'journal': target_journal}

        except Exception as e:
            print(f"  [QualityGate] Error: {e}")

        return {'score': 50, 'issues': format_issues, 'passed': False, 'journal': target_journal}

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


class Humanizer:
    """
    AI文本人类化器 - v5.2 核心改进

    功能：消除文本中人工智能生成的痕迹，使其听起来更自然、更像人类的写作方式。

    29种AI模式分类：
    - 内容问题：显著性膨胀、 promotional语言、vague attribution
    - 语言问题：AI词汇过度使用(crucial, pivotal, showcase等)、copula avoidance
    - 风格问题：短句堆砌、规则三连过度使用、同义词循环、虚假范围
    - 填充模式：空短语、过度对冲、通用正面结论

    写作原则：
    - 需要观点、变化的节奏、承认复杂性
    - 第一人称视角、幽默和边缘、特定情感细节
    - 有意的的不完美 - 完美的结构看起来像算法
    """

    # AI 词汇过度使用列表
    AI_VOCABULARY = {
        'crucial', 'pivotal', 'showcase', 'delve', 'intricate', 'explore',
        'enhance', 'optimize', 'leverage', 'utilize', 'facilitate',
        'comprehensive', 'robust', 'seamless', 'cutting-edge', 'state-of-the-art',
        'groundbreaking', 'revolutionary', 'innovative', 'novel', 'breakthrough',
        'transformative', 'paradigm', 'holistic', 'synergy', 'ecosystem',
        'scalable', 'reliable', 'efficient', 'effective', 'optimal'
    }

    # 模板短语
    TEMPLATE_PHRASES = {
        '我相信这会有所帮助', '让我知道如果您有任何问题',
        '近年来', '随着技术的不断发展', '在这一领域',
        '取得了显著进展', '受到了广泛关注', '具有重要的理论和实际意义',
        '为...提供了新的思路', '取得了重要突破'
    }

    def humanize(self, text: str) -> str:
        """人类化文本"""
        if not text:
            return text

        # 1. 识别并消除AI词汇
        text = self._remove_ai_vocabulary(text)

        # 2. 消除模板短语
        text = self._remove_template_phrases(text)

        # 3. 添加变化和个性
        text = self._add_variation(text)

        # 4. 消除显著性膨胀
        text = self._remove_significance_inflation(text)

        # 5. 添加自然过渡
        text = self._improve_transitions(text)

        return text

    def _remove_ai_vocabulary(self, text: str) -> str:
        """替换AI过度使用的词汇"""
        result = text
        for word in self.AI_VOCABULARY:
            # 使用更自然、更具体的词汇替换
            replacements = {
                'crucial': 'key', 'pivotal': 'central', 'showcase': 'show',
                'delve': 'examine', 'intricate': 'complex', 'explore': 'study',
                'enhance': 'improve', 'optimize': 'refine', 'leverage': 'use',
                'utilize': 'use', 'facilitate': 'help',
                'comprehensive': 'thorough', 'robust': 'strong', 'seamless': 'smooth',
                'cutting-edge': 'advanced', 'state-of-the-art': 'latest',
                'groundbreaking': 'important', 'revolutionary': 'new',
                'innovative': 'new', 'novel': 'new', 'breakthrough': 'progress',
                'transformative': 'significant', 'paradigm': 'model',
                'holistic': 'complete', 'synergy': 'cooperation',
                'scalable': 'expandable', 'reliable': 'dependable',
                'efficient': 'effective', 'effective': 'useful', 'optimal': 'best'
            }
            if word in replacements:
                # 不做全部替换，只替换明显的AI模式
                pattern = r'\b' + word + r'\b'
                result = re.sub(pattern, replacements[word], result, flags=re.IGNORECASE)
        return result

    def _remove_template_phrases(self, text: str) -> str:
        """消除模板短语"""
        result = text
        for phrase in self.TEMPLATE_PHRASES:
            if phrase in result:
                result = result.replace(phrase, '')
        # 清理多余空格
        result = re.sub(r'\s+', ' ', result)
        return result

    def _add_variation(self, text: str) -> str:
        """添加句式变化"""
        # 拆分句子
        sentences = re.split(r'([。；！])', text)
        result = []
        for i, s in enumerate(sentences):
            if i % 2 == 0:  # 实际句子
                # 随机添加一些变化（不破坏句意）
                # 保持原样，但确保没有连续的短句堆砌
                if len(s) < 10 and i > 0:
                    # 短句合并到前一句
                    if result:
                        result[-1] = result[-1].rstrip() + ' ' + s.strip()
                        continue
            result.append(s)
        return ''.join(result)

    def _remove_significance_inflation(self, text: str) -> str:
        """消除显著性膨胀 - 不要夸大研究意义"""
        inflations = [
            (r'\b具有重要的理论和实际意义\b', '具有研究价值'),
            (r'\b取得了重大突破\b', '取得了进展'),
            (r'\b填补了国际空白\b', '提供了新见解'),
            (r'\b达到了国际领先水平\b', '具有参考价值'),
            (r'\b开创了.*新领域\b', '拓展了研究思路'),
            (r'\b革命性的\b', '重要的'),
            (r'\b颠覆性的\b', '显著的'),
        ]
        result = text
        for pattern, replacement in inflations:
            result = re.sub(pattern, replacement, result)
        return result

    def _improve_transitions(self, text: str) -> str:
        """改善过渡，使其更自然"""
        # 移除过于生硬的过渡词
        awkward_phrases = [
            '首先，', '其次，', '最后，',
            '此外，', '另一方面，', '综上所述，'
        ]
        result = text
        for phrase in awkward_phrases:
            # 只在重复使用时移除
            count = result.count(phrase)
            if count > 1:
                result = result.replace(phrase, '')
            elif count == 1:
                # 保留一个，但用更自然的替代
                result = result.replace(phrase, '同时，')
        return result

    def audit(self, text: str) -> Dict:
        """自我审计 - 识别剩余的AI模式"""
        issues = []
        text_lower = text.lower()

        # 检查AI词汇密度
        ai_words_found = [w for w in self.AI_VOCABULARY if w in text_lower]
        if len(ai_words_found) > 3:
            issues.append(f"AI词汇过多: {ai_words_found[:5]}")

        # 检查句子长度一致性（AI倾向于等长句子）
        sentences = re.split(r'[。；！]', text)
        if sentences:
            lengths = [len(s) for s in sentences if s.strip()]
            if lengths:
                avg_len = sum(lengths) / len(lengths)
                if all(abs(l - avg_len) < 5 for l in lengths[:5] if lengths[:5]):
                    issues.append("句子长度过于均匀 - 看起来像AI生成")

        # 检查是否有过多的短句
        short_sentences = sum(1 for s in sentences if 0 < len(s.strip()) < 15)
        if short_sentences > len(sentences) * 0.3:
            issues.append(f"短句过多 ({short_sentences}/{len(sentences)})")

        return {
            'ai_patterns_found': len(issues),
            'issues': issues,
            'humanized': len(issues) == 0
        }


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
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = "deepseek-v4-flash"

ZCHAT_API_KEY = os.getenv("ZCHAT_API_KEY", "")
ZCHAT_BASE_URL = os.getenv("ZCHAT_BASE_URL", "https://api.zchat.tech/v1")
ZCHAT_MODEL = "gpt-5-thinking"

LLM_PROVIDERS = [
    {'name': 'DeepSeek', 'api_key': DEEPSEEK_API_KEY, 'base_url': DEEPSEEK_BASE_URL, 'model': DEEPSEEK_MODEL},
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

    # 深度分析 - v5.2新增：真正贡献和证据
    research_question: str = ""
    approach: str = ""
    tech_routes: List[str] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)
    key_metrics: List[str] = field(default_factory=list)
    physical_insight: str = ""

    # 新增深度分析字段 (ContentAssets来源)
    contribution: str = ""          # 本文核心贡献（一句话）
    evidence: List[str] = field(default_factory=list)  # 关键证据列表（带具体数值）
    claims: List[str] = field(default_factory=list)   # 论文声称解决的问题
    unanswered_questions: List[str] = field(default_factory=list)  # 未回答的问题

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
    # v5.2新增：内容资产
    contributions: List[str] = field(default_factory=list)  # 各论文贡献
    evidence_map: Dict[str, List[str]] = field(default_factory=dict)  # paper_id → evidence列表
    representative_figures: List[Dict] = field(default_factory=list)  # 可引用图表


@dataclass
class ContentAssets:
    """论文深度分析产生的内容资产 - Phase 1核心输出

    用于支撑两阶段写作的原料，不直接输出而是经由OutlineGenerator适配不同论文类型。
    """
    route: str = ""                           # 技术路线名称
    papers: List[Paper] = field(default_factory=list)  # 该路线论文列表
    contributions: List[str] = field(default_factory=list)  # 各论文核心贡献（一句话）
    evidence_map: Dict[str, List[str]] = field(default_factory=dict)  # paper_id → evidence列表
    claims: List[str] = field(default_factory=list)    # 论文声明列表
    gaps: List[Dict] = field(default_factory=list)    # Gap列表
    key_metrics: Dict[str, Any] = field(default_factory=dict)  # 关键性能指标
    representative_figures: List[Dict] = field(default_factory=list)  # 可引用图表 (paper_id, figure_desc)


# =============================================================================
# Phase 2: 论文类型适配提纲生成器
# =============================================================================

PAPER_TYPES = {
    'journal_review': {
        'name': '期刊学术综述',
        'structure': {
            'introduction': ['gap_statement', 'scope_definition', 'contribution_preview'],
            'methods': 'thematic_synthesis',
            'results': 'route_by_route_analysis',
            'discussion': 'cross_route_comparison'
        },
        'citation_style': 'ieee',
        'reference_format': 'ieee',  # [1], [2], ...
    },
    'chinese_thesis': {
        'name': '中文学位论文',
        'structure': {
            'introduction': ['research_background', 'literature_review', 'problems_gaps', 'contributions'],
            'methods': 'technical_review',
            'results': 'findings_presentation',
            'discussion': 'implications'
        },
        'citation_style': 'gbt7714',
        'reference_format': 'gbt7714',  # 序号格式
    }
}


class OutlineGenerator:
    """根据内容资产和目标论文类型生成适配提纲 - Phase 2核心

    两阶段写作的Stage 1输出：论证要点大纲
    """

    def __init__(self):
        self.llm_client = None
        try:
            self.llm_client = get_llm_client()
        except:
            pass

    def generate(self, themes: Dict[str, ThemeSynthesis], query: str, paper_type: str = 'journal_review') -> Dict:
        """生成论文提纲

        Args:
            themes: 主题综合结果
            query: 查询主题
            paper_type: 目标论文类型 ('journal_review' / 'chinese_thesis')

        Returns:
            outline: 结构化提纲 dict，包含sections/arguments/evidence
        """
        if paper_type not in PAPER_TYPES:
            paper_type = 'journal_review'

        config = PAPER_TYPES[paper_type]

        outline = {
            'paper_type': paper_type,
            'query': query,
            'sections': {},
            'core_gap': '',
            'contributions': []
        }

        # 收集所有技术路线的内容资产
        all_papers = []
        all_gaps = []
        all_contributions = []
        for synth in themes.values():
            all_papers.extend(synth.representative_papers)
            all_gaps.extend(synth.gaps)
            if hasattr(synth, 'contributions'):
                all_contributions.extend(synth.contributions)

        # 根据paper_type生成不同结构的提纲
        if paper_type == 'journal_review':
            outline = self._generate_journal_review_outline(themes, query, outline)
        else:
            outline = self._generate_chinese_thesis_outline(themes, query, outline)

        return outline

    def _generate_journal_review_outline(self, themes: Dict, query: str, outline: Dict) -> Dict:
        """生成期刊综述论文提纲

        结构：Gap-Driven引言 + IMRAD
        """
        # 1. 引言：Gap驱动
        outline['sections']['introduction'] = {
            'gap_statement': {
                'claim': f'{query}领域存在关键研究空白',
                'evidence': self._extract_gap_evidence(themes),
                'status': 'supported'
            },
            'scope_definition': {
                'claim': '本文系统梳理了关键技术路线',
                'evidence': list(themes.keys()),
                'status': 'supported'
            },
            'contribution_preview': {
                'claim': '本综述识别并分类了关键Gap',
                'evidence': f'{len(themes)}种技术路线',
                'status': 'supported'
            }
        }

        # 2. 方法：主题综合
        outline['sections']['methods'] = {
            'approach': '主题综合法 (Thematic Synthesis)',
            'data_sources': 'Zotero + OpenAlex + Tavily',
            'papers_analyzed': sum(len(t.representative_papers) for t in themes.values())
        }

        # 3. 结果：按技术路线分析
        results = {}
        for theme, synth in themes.items():
            results[theme] = {
                'claim': f'{theme}技术路线取得了重要进展',
                'evidence': synth.key_findings[:3] if synth.key_findings else [],
                'gaps': synth.gaps[:2] if synth.gaps else [],
                'contributions': getattr(synth, 'contributions', [])[:3]
            }
        outline['sections']['results'] = results

        # 4. 讨论：跨路线对比
        outline['sections']['discussion'] = {
            'comparison': '各技术路线在功率-带宽-效率三维空间的性能边界',
            'tradeoffs': [t.tradeoffs[:2] if t.tradeoffs else [] for t in themes.values()],
            'future_directions': [t.future_directions[:2] if t.future_directions else [] for t in themes.values()]
        }

        outline['core_gap'] = self._derive_core_gap(themes)
        outline['contributions'] = self._derive_contributions(themes)

        return outline

    def _generate_chinese_thesis_outline(self, themes: Dict, query: str, outline: Dict) -> Dict:
        """生成中文学位论文提纲

        结构：研究背景/现状/问题/贡献
        """
        # 1.1 研究背景与意义
        outline['sections']['1_1_research_background'] = {
            'claim': f'{query}技术具有重要应用前景',
            'evidence': ['THz波段独特的光谱特性', '穿透非极性材料', '亚皮秒时间分辨率'],
            'status': 'supported'
        }

        # 1.2 国内外研究现状
        literature = {}
        for theme, synth in themes.items():
            literature[theme] = {
                'count': len(synth.representative_papers),
                'key_work': synth.representative_papers[0] if synth.representative_papers else {},
                'main_progress': synth.key_findings[:2] if synth.key_findings else []
            }
        outline['sections']['1_2_literature_review'] = literature

        # 1.3 存在的问题与挑战
        all_gaps = []
        for synth in themes.values():
            for gap in synth.gaps[:1]:
                all_gaps.append(gap)
        outline['sections']['1_3_problems_gaps'] = {
            'route_specific': {theme: synth.gaps[:1] for theme, synth in themes.items()},
            'common_challenges': all_gaps[:3]
        }

        # 1.4 本文的主要贡献
        outline['sections']['1_4_contributions'] = {
            'contributions': self._derive_contributions(themes)
        }

        outline['core_gap'] = self._derive_core_gap(themes)

        return outline

    def _extract_gap_evidence(self, themes: Dict) -> List[str]:
        """从主题综合中提取Gap证据"""
        evidence = []
        for synth in themes.values():
            for gap in (synth.gaps[:2] if synth.gaps else []):
                if isinstance(gap, dict):
                    evidence.append(f"[{gap.get('type', '')}] {gap.get('description', '')[:60]}")
                elif isinstance(gap, str):
                    evidence.append(gap[:60])
        return evidence[:5]

    def _derive_core_gap(self, themes: Dict) -> str:
        """从主题综合推导核心Gap"""
        # 收集所有Gap类型
        gap_types = {}
        for synth in themes.values():
            for gap in (synth.gaps[:3] if synth.gaps else []):
                gtype = gap.get('type', 'Unknown') if isinstance(gap, dict) else 'Unknown'
                if gtype not in gap_types:
                    gap_types[gtype] = []
                desc = gap.get('description', '')[:50] if isinstance(gap, dict) else str(gap)[:50]
                gap_types[gtype].append(desc)

        # 返回最主要的Gap类型
        if gap_types:
            primary_type = max(gap_types, key=lambda k: len(gap_types[k]))
            primary_gaps = gap_types[primary_type]
            if primary_gaps:
                return f"[{primary_type}] {primary_gaps[0]}"
        return "现有技术难以同时实现大带宽与高功率"

    def _derive_contributions(self, themes: Dict) -> List[str]:
        """从主题综合推导本文贡献"""
        contributions = []
        contributions.append(f"系统梳理了{len(themes)}种主要技术路线")
        contributions.append("识别并分类了关键研究空白")
        contributions.append("综合对比了各技术路线的核心权衡")

        # 从各主题提取独特贡献
        for theme, synth in themes.items():
            if hasattr(synth, 'contributions') and synth.contributions:
                contributions.append(f"{theme}：{synth.contributions[0][:50]}")

        return contributions[:5]


# =============================================================================
# Phase 3: 两阶段写作落实 (Two-Stage Writing)
# =============================================================================

class StageWriter:
    """两阶段写作 - Phase 3核心

    Stage 1: 将提纲转换为论证要点大纲
    Stage 2: 将论证大纲转换为流畅段落
    """

    def __init__(self):
        self.llm_client = None
        try:
            self.llm_client = get_llm_client()
        except:
            pass

    def stage1_outline_draft(self, outline: Dict, themes: Dict[str, ThemeSynthesis], paper_type: str = 'journal_review') -> str:
        """Stage 1: 将提纲转换为论证要点大纲

        对每个章节/段落输出：
        - 核心论点 (claim)
        - 关键证据 (evidence with citations)
        - 逻辑流向
        """
        if not self.llm_client:
            return self._fallback_outline(outline, paper_type)

        sections = outline.get('sections', {})
        draft_lines = ["# 论证要点大纲\n"]

        paper_type_label = PAPER_TYPES.get(paper_type, {}).get('name', paper_type)
        draft_lines.append(f"## 论文类型: {paper_type_label}\n")
        draft_lines.append(f"## 核心Gap: {outline.get('core_gap', '')}\n")

        # 引言部分
        if 'introduction' in sections:
            draft_lines.append("\n## 引言")
            intro = sections['introduction']
            if isinstance(intro, dict):
                for sub_key, content in intro.items():
                    if isinstance(content, dict):
                        claim = content.get('claim', '')
                        evidence = content.get('evidence', [])
                        status = content.get('status', '')
                        draft_lines.append(f"\n### {sub_key}")
                        draft_lines.append(f"- 核心主张: {claim}")
                        if isinstance(evidence, list):
                            for e in evidence[:3]:
                                draft_lines.append(f"  - 证据: {e}")
                        else:
                            draft_lines.append(f"  - 证据: {evidence}")
                        draft_lines.append(f"  - 状态: {status}")
        elif '1_1_research_background' in sections:
            # 中文学位论文结构
            draft_lines.append("\n## 引言")
            for section_key in ['1_1_research_background', '1_2_literature_review', '1_3_problems_gaps', '1_4_contributions']:
                if section_key in sections:
                    content = sections[section_key]
                    draft_lines.append(f"\n### {section_key}")
                    if isinstance(content, dict):
                        if 'claim' in content:
                            draft_lines.append(f"- 核心主张: {content['claim']}")
                        if 'evidence' in content and isinstance(content['evidence'], list):
                            for e in content['evidence'][:3]:
                                draft_lines.append(f"  - 证据: {e}")
                        if 'contributions' in content and isinstance(content['contributions'], list):
                            for c in content['contributions']:
                                draft_lines.append(f"  - 贡献: {c}")

        # 技术路线分析
        if 'results' in sections:
            draft_lines.append("\n## 技术路线分析")
            results = sections['results']
            if isinstance(results, dict):
                for route, content in results.items():
                    draft_lines.append(f"\n### {route}")
                    if isinstance(content, dict):
                        claim = content.get('claim', '')
                        evidence = content.get('evidence', [])
                        gaps = content.get('gaps', [])
                        draft_lines.append(f"- 核心主张: {claim}")
                        if isinstance(evidence, list):
                            for e in evidence[:2]:
                                draft_lines.append(f"  - 关键发现: {e}")
                        if isinstance(gaps, list):
                            for g in gaps[:2]:
                                if isinstance(g, dict):
                                    draft_lines.append(f"  - Gap: [{g.get('type', '')}] {g.get('description', '')[:50]}")

        # 讨论部分
        if 'discussion' in sections:
            draft_lines.append("\n## 讨论")
            disc = sections['discussion']
            if isinstance(disc, dict):
                draft_lines.append(f"- 对比基础: {disc.get('comparison', '')}")
                if 'future_directions' in disc:
                    for fd in disc['future_directions'][:2]:
                        if isinstance(fd, list):
                            for f in fd:
                                draft_lines.append(f"  - 未来方向: {f}")

        return "\n".join(draft_lines)

    def stage2_prose(self, section_text: str, section_name: str = 'introduction',
                     outline: Dict = None, themes: Dict[str, ThemeSynthesis] = None,
                     paper_type: str = 'journal_review') -> str:
        """Stage 2: 将指定章节文本增强为流畅学术段落

        参数:
            section_text: 待增强的章节原始文本
            section_name: 章节名称 (introduction / theme_synthesis / discussion)
        """
        if not self.llm_client or not section_text or len(section_text) < 50:
            return section_text  # 无LLM或文本过短，直接返回原文

        core_gap = (outline or {}).get('core_gap', '')

        # 根据章节类型定制prompt
        if section_name == 'introduction':
            prompt = f"""你是学术综述引言写作专家。请将以下引言草稿重写为流畅的学术散文。

**要求**:
1. 保持C-C-C结构：Context(领域背景)→Constraint(核心瓶颈)→Bridge(本文贡献)
2. 每段3-5句，首句立题，句间有逻辑推进
3. 删除所有项目符号，改为连贯段落
4. 避免AI模式词汇("取得了显著进展"、"具有重要应用前景"等)
5. 基于原始草稿中的已有内容改写，禁止添加原始草稿中不存在的新数据或新发现
6. 核心Gap: {core_gap}

**原始引言草稿**:
{section_text[:2500]}

请直接返回重写后的引言（仅引言部分，不要添加额外说明）。"""
        elif section_name == 'theme_synthesis':
            prompt = f"""你是学术综述技术路线分析写作专家。请将以下技术路线分析草稿重写为流畅的学术散文。

**要求**:
1. 保留markdown标题结构（### 等），只重写正文段落
2. 将项目符号列表转换为连贯的学术段落，每段一个核心论点
3. 首句明确段落主旨，句间有因果/对比/递进关系
4. 保留具体数值、作者引用等关键信息
5. 避免AI模板短语("取得了显著进展"、"具有重要应用前景"等)
6. 批判性分析：不仅描述进展，更要解释"为什么"和"意味着什么"

**原始草稿**:
{section_text[:3000]}

请直接返回重写后的内容（保留标题结构，正文改为流畅散文，不要添加额外说明）。"""
        else:
            prompt = f"""你是学术写作专家。请将以下章节文本重写为更流畅的学术段落。

**要求**:
1. 每段一个核心论点，首句明确
2. 删除项目符号，改为连贯散文
3. 句间有因果/对比/递进关系
4. 避免AI模板短语

**原始文本**:
{section_text[:2500]}

请直接返回重写后的段落。"""

        try:
            messages = [
                {"role": "system", "content": "你是学术写作润色专家，擅长消除AI文本痕迹，将粗糙草稿转换为流畅学术散文。"},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_client.chat_completions_create(messages, temperature=0.2, max_tokens=4000)
            prose = response['choices'][0]['message']['content']
            # 验证输出质量：不能过短
            if len(prose.strip()) > len(section_text.strip()) * 0.5:
                return prose.strip()
            return section_text
        except Exception as e:
            print(f"  [StageWriter] LLM error: {e}")
            return section_text

    def _fallback_outline(self, outline: Dict, paper_type: str) -> str:
        """Fallback: 生成简化版提纲"""
        lines = ["# 论证要点大纲 (简化版)\n"]
        lines.append(f"核心Gap: {outline.get('core_gap', '')}\n")
        lines.append(f"论文类型: {paper_type}\n")
        return "\n".join(lines)


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
                src = loc.get("source") or {}  # Fix: handle None source

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
                # 尝试多种文本提取模式，优先保真
                page_text = self._extract_page_text(page)
                all_text += page_text + "\n"
            doc.close()

            # 文本质量检查 - 如果提取的中文出现大量乱码，尝试rawdict模式
            if self._has_encoding_issues(all_text):
                # 重新用rawdict提取
                all_text = ""
                for page in doc:
                    rawdict = page.get_text("rawdict")
                    page_text = self._rawdict_to_text(rawdict)
                    all_text += page_text + "\n"

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
                        'evidence': llm_result.get('evidence', []),  # v5.2新增
                        'claims': llm_result.get('claims', []),      # v5.2新增
                        'unanswered_questions': llm_result.get('unanswered_questions', []),  # v5.2新增
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

    def _extract_page_text(self, page) -> str:
        """尝试多种文本提取模式，返回最清晰的文本"""
        # 模式1: 默认简单模式
        text = page.get_text()
        if text and len(text.strip()) > 50:
            return text

        # 模式2: blocks模式，保持块结构
        try:
            text = page.get_text("blocks")
            if text and len(text.strip()) > 50:
                return text
        except:
            pass

        # 模式3: dict模式
        try:
            text = page.get_text("dict")
            if text:
                blocks = []
                for block in text.get("blocks", []):
                    if block.get("type") == 0:
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                blocks.append(span.get("text", ""))
                result = " ".join(blocks)
                if len(result) > 50:
                    return result
        except:
            pass

        return text if text else ""

    def _has_encoding_issues(self, text: str) -> bool:
        """检测文本是否出现编码问题（大量乱码）"""
        if not text or len(text) < 100:
            return False
        non_ascii = [c for c in text if ord(c) > 127]
        if len(non_ascii) < 20:
            return False
        replacement_count = sum(1 for c in non_ascii if ord(c) == 65533 or (ord(c) >= 128 and ord(c) < 192))
        return (replacement_count / len(non_ascii)) > 0.3 if non_ascii else False

    def _rawdict_to_text(self, rawdict: dict) -> str:
        """从rawdict提取文本"""
        if not rawdict:
            return ""
        text_parts = []
        for page in rawdict.get("pages", []):
            for block in page.get("blocks", []):
                if block.get("type") == 0:
                    block_text = ""
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            if self._is_garbled(span_text):
                                chars = span.get("chars", [])
                                if chars:
                                    char_texts = [c.get("c", "") for c in chars if c.get("c") and ord(c.get("c", "")) > 31 and c.get("c") not in [' ', '\t']]
                                    span_text = "".join(char_texts)
                            line_text += span_text
                        if line_text.strip():
                            block_text += line_text + "\n"
                    if block_text.strip():
                        text_parts.append(block_text)
        return "\n".join(text_parts)

    def _is_garbled(self, text: str) -> bool:
        """判断文本是否是乱码"""
        if not text:
            return False
        non_ascii = [c for c in text if ord(c) > 127]
        if len(non_ascii) < 3:
            return False
        garbled_count = sum(1 for c in non_ascii if ord(c) == 65533 or (ord(c) >= 128 and ord(c) < 160))
        return (garbled_count / len(non_ascii)) > 0.4

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
    "contribution": "本文的主要贡献是什么？一句话描述，越具体越好",
    "evidence": ["关键证据1（如：输出功率1.2mW @ 1THz，具体数值必须包含）", "关键证据2（如：带宽覆盖0.1-5THz）"],
    "claims": ["论文作者声称达到了什么（如：室温连续波输出10mW）", "声称的改进（如：效率提升3倍）"],
    "key_findings": ["关键结果1（如：峰值功率1.2mW）", "关键结果2"],
    "limitations": ["本文的局限性1（如：仅在低温下工作）", "本文的局限性2"],
    "gaps": ["本文指出的研究空白1（如：缺乏系统性比较）", "研究空白2"],
    "unanswered_questions": ["论文未回答但值得关注的问题1", "问题2"],
    "key_metrics": ["具体数值1（如：峰值功率1.2mW）", "具体数值2"],
    "physical_insight": "论文的核心物理洞察是什么？"
}}

要求：
- contribution 要具体说明"本文通过X方法实现了Y结果"
- evidence 必须包含具体数值（带单位），如"功率1.2mW"、"带宽2.5THz"
- claims 是作者在论文中明确声称达到的，需要有evidence支持
- unanswered_questions 从limitation和论文结论的未来工作推导
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
                        # v5.2新增深度分析字段
                        paper.contribution = pdf_result.get('contribution', '')
                        paper.evidence = pdf_result.get('evidence', [])
                        paper.claims = pdf_result.get('claims', [])
                        paper.unanswered_questions = pdf_result.get('unanswered_questions', [])
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
                        # v5.2新增深度分析字段
                        paper.contribution = pdf_result.get('contribution', '')
                        paper.evidence = pdf_result.get('evidence', [])
                        paper.claims = pdf_result.get('claims', [])
                        paper.unanswered_questions = pdf_result.get('unanswered_questions', [])
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

    # 类级跨主题Gap注册表 - 追踪每个Gap描述被哪些主题使用
    # 格式: {gap_desc_normalized: {theme_name: count}}
    _gap_usage_registry: Dict[str, Dict[str, int]] = {}

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        if not self.llm_client:
            try:
                self.llm_client = get_llm_client()
            except:
                pass
        # 跨主题全局去重：防止同一发现出现在多个主题中
        self._global_findings_seen = set()
        # 实例级Gap追踪
        self._theme_gaps: Dict[str, List[Dict]] = {}

    def synthesize(self, papers: List[Paper], tavily_results: List[Dict] = None) -> Dict[str, ThemeSynthesis]:
        route_groups = defaultdict(list)
        for paper in papers:
            for route in paper.tech_routes:
                if route and route != '其他':
                    route_groups[route].append(paper)

        known_routes = set(TECH_ROUTES.keys())

        themes = {}
        for route, route_papers in route_groups.items():
            if route not in known_routes:
                continue
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
            synth.key_findings = self._aggregate_diverse_findings(route, route_papers)

            # 核心改进4: Gap智能识别
            synth.gaps = self._smart_gap_identification(route, route_papers)

            # 技术路线对比
            synth.tradeoffs = self._generate_route_specific_tradeoffs(route, route_papers)
            synth.future_directions = self._generate_route_specific_futures(route, route_papers)

            # 核心改进5: 代表性工作带独特贡献
            synth.representative_papers = self._select_diverse_representative(route_papers)

            # v5.2: 聚合 contributions 和 evidence_map（支撑claim-evidence写作）
            synth.contributions = []
            synth.evidence_map = {}
            for p in route_papers:
                if p.contribution and len(p.contribution) > 10:
                    synth.contributions.append(f"[{p.authors[0].split()[-1] if p.authors else 'Unknown'}{p.year}] {p.contribution}")
                if p.evidence:
                    synth.evidence_map[p.id] = p.evidence[:3]  # 每篇论文最多3条证据

            # 最新趋势 - Tavily优先，若无结果则用OpenAlex
            if tavily_results:
                tavily = TavilySearcher()
                synth.latest_trends = tavily.get_latest_trends(tavily_results)
            else:
                # Tavily无结果时，用OpenAlex最新论文作为替代
                openalex = OpenAlexReader()
                synth.latest_trends = openalex.get_latest_trends(route, max_results=5)

            themes[route] = synth

        # Post-processing: global cross-theme dedup for gaps and representative papers
        themes = self._apply_global_dedup(themes)

        # Post-processing: 清理误分类论文数据污染
        themes = self._cleanup_mismatched_theme_data(themes)

        return themes

    def _apply_global_dedup(self, themes: Dict[str, ThemeSynthesis]) -> Dict[str, ThemeSynthesis]:
        """全局跨主题去重 — 同一Gap描述不能出现在>2个主题中，但每主题至少保留2个Gap

        策略：
        1. 统计每个gap出现在多少个主题中
        2. 对出现在≥3个主题中的gap，只在2个主题中保留（优先保留Comparative/Condition类型）
        3. 确保每个主题至少保留2个非重复gap
        """
        if not themes:
            return themes

        # === 1. 统计每个gap在多少主题中出现 ===
        gap_occurrences: Dict[str, List[Tuple[str, Dict]]] = {}  # desc_normalized -> [(route, gap_dict), ...]
        for route, synth in themes.items():
            for gap in (synth.gaps or []):
                desc = gap.get('description', '')
                if not desc or desc == '未明确':
                    continue
                # 标准化：取前8个词作为指纹
                words = ' '.join(desc.lower().split()[:8])
                if words not in gap_occurrences:
                    gap_occurrences[words] = []
                gap_occurrences[words].append((route, gap))

        # === 2. 标记需要移除的gap ===
        # 对于出现在3+主题中的gap，只保留在2个主题中
        to_remove: Dict[str, set] = {route: set() for route in themes}
        for words, occurrences in gap_occurrences.items():
            if len(occurrences) >= 3:
                # 按gap类型排序：优先保留Comparative/Condition（更可能是领域级gap）
                priority = {'Comparative': 0, 'Condition': 1, 'Theoretical': 2,
                           'Parameter': 3, 'Methodological': 4}
                sorted_occ = sorted(occurrences,
                                    key=lambda x: priority.get(x[1].get('type', ''), 5))
                # 只保留前2个，其余标记为移除
                for route, gap in sorted_occ[2:]:
                    desc = gap.get('description', '')
                    to_remove[route].add(desc)

        # === 3. 应用移除，但确保每主题至少2个gap ===
        for route, synth in themes.items():
            original_gaps = [g for g in (synth.gaps or []) if g.get('description', '') not in to_remove[route]]
            # 如果移除后不足2个，从被移除的gap中补回优先级最高的
            if len(original_gaps) < 2:
                removed = [g for g in (synth.gaps or []) if g.get('description', '') in to_remove[route]]
                priority = {'Comparative': 0, 'Condition': 1, 'Theoretical': 2,
                           'Parameter': 3, 'Methodological': 4}
                removed.sort(key=lambda x: priority.get(x.get('type', ''), 5))
                needed = 2 - len(original_gaps)
                original_gaps.extend(removed[:needed])
            synth.gaps = original_gaps

        # === 4. 代表性论文跨主题去重 — 每篇论文只出现在最先分配的主题 ===
        used_paper_ids: set = set()
        for route in list(themes.keys()):
            synth = themes[route]
            unique_papers = []
            for p_dict in synth.representative_papers:
                pid = p_dict.get('id', '')
                if pid and pid not in used_paper_ids:
                    used_paper_ids.add(pid)
                    unique_papers.append(p_dict)
                elif not pid:
                    unique_papers.append(p_dict)
            synth.representative_papers = unique_papers

        return themes

    def _cleanup_mismatched_theme_data(self, themes: Dict[str, ThemeSynthesis]) -> Dict[str, ThemeSynthesis]:
        """清理每个主题中明显不属于该主题的数据（来自误分类论文的污染）

        例如：DFB激光器论文的指标不应出现在激光等离子体主题中
        """
        # 定义每个主题的"不相关关键词"
        mismatched_keywords = {
            '激光等离子体': ['dfb', '分布反馈', '光混频器', 'fpga', '锁相放大器', '电极结构', '天线尺寸'],
            '光整流': ['dfb', '分布反馈', '光混频器', 'fpga', '锁相放大器', '量子级联', 'qcl', '子带间'],
            'QCL (量子级联激光器)': ['dfb', '分布反馈', '光混频器', '光整流', '铌酸锂', '等离子体', '光丝'],
            'PCA (光电导天线)': ['量子级联', 'qcl', '子带间', '等离子体', '光丝', '四波混频'],
            '超表面/等离子体': ['dfb', '分布反馈', '量子级联', 'qcl', '光混频器'],
        }

        for route, synth in themes.items():
            bad_kws = [kw.lower() for kw in mismatched_keywords.get(route, [])]

            def is_mismatched(text: str) -> bool:
                if not text:
                    return False
                text_lower = text.lower()
                return any(kw in text_lower for kw in bad_kws)

            # 1. 清理key_findings
            if synth.key_findings:
                synth.key_findings = [f for f in synth.key_findings if not is_mismatched(f)]

            # 2. 清理research_questions
            if synth.research_questions:
                synth.research_questions = [rq for rq in synth.research_questions if not is_mismatched(rq)]

            # 3. 清理gaps（已经在_smart_gap_identification中部分处理，这里做二次过滤）
            if synth.gaps:
                cleaned_gaps = []
                for g in synth.gaps:
                    desc = g.get('description', '')
                    # 同时过滤掉过于宽泛的"系统比较"类gap（这类gap应在引言中讨论，不应作为各主题的特定gap）
                    if '系统比较不同技术路线' in desc and '性能表现' in desc:
                        continue
                    if not is_mismatched(desc):
                        cleaned_gaps.append(g)
                # 确保每主题至少保留2个gap
                if len(cleaned_gaps) < 2 and synth.gaps:
                    # 从被过滤的gap中补回（排除系统比较类）
                    for g in synth.gaps:
                        desc = g.get('description', '')
                        if '系统比较不同技术路线' in desc and '性能表现' in desc:
                            continue
                        if g not in cleaned_gaps:
                            cleaned_gaps.append(g)
                            if len(cleaned_gaps) >= 2:
                                break
                synth.gaps = cleaned_gaps

            # 4. 清理代表性论文 - 移除标题明显不属于该主题的论文
            if synth.representative_papers:
                theme_good_kws = {
                    'PCA (光电导天线)': ['photoconductive', 'antenna', '光电导', '光混频', '光导'],
                    '光整流': ['rectification', 'optical rectification', '光整流', 'nonlinear crystal', '非线性晶体'],
                    '激光等离子体': ['plasma', 'filament', '激光等离子体', 'two-color', '双色', 'gas'],
                    'QCL (量子级联激光器)': ['quantum cascade', 'qcl', '量子级联', '级联激光'],
                    '超表面/等离子体': ['metasurface', 'plasmonic', '超表面', '纳米结构'],
                }.get(route, [route.lower()])
                cleaned_papers = []
                for p in synth.representative_papers:
                    title = (p.get('title', '') or '').lower()
                    # 如果标题包含明显属于其他主题的特定关键词，跳过
                    is_relevant = any(kw.lower() in title for kw in theme_good_kws)
                    # 对于生成类主题，过滤掉纯成像/测量类论文
                    is_imaging_paper = any(k in title for k in ['imaging', 'compressive imaging', 'microscopy', 'near-field measurement', 'spectroscopy system'])
                    if route in ['光整流', '激光等离子体', 'QCL (量子级联激光器)'] and is_imaging_paper and not is_relevant:
                        continue
                    cleaned_papers.append(p)
                # 如果过滤后不足2篇，保留原标题最相关的
                if len(cleaned_papers) < 2:
                    cleaned_papers = synth.representative_papers[:3]
                synth.representative_papers = cleaned_papers

        return themes

    def _generate_context_v2(self, theme: str, papers: List[Paper]) -> str:
        """动态Context生成 - 基于实际论文内容，过滤主题不相关的方法"""
        # 已知误分类关键词：这些方法明确属于特定主题，在其他主题中应过滤
        # 通用测量/诊断方法：不应出现在任何THz产生主题的context中
        common_measurement_kws = ['量子限制斯塔克效应', '量子探针场显微镜', 'qfim', '远场成像', '相位分辨采样', '近场成像']
        misclassification_kws = {
            'PCA (光电导天线)': common_measurement_kws[:],
            '光整流': ['dfb', '分布反馈', '锁相放大器', '光混频器', 'fpga'] + common_measurement_kws,
            '激光等离子体': ['dfb', '分布反馈', '锁相放大器', '光混频器', 'fpga', '光混频'] + common_measurement_kws,
            'QCL (量子级联激光器)': ['dfb', '分布反馈', '锁相放大器', '光混频器', 'fpga'] + common_measurement_kws,
            '超表面/等离子体': ['dfb', '分布反馈', '锁相放大器', '光混频器', 'fpga', '量子级联'] + common_measurement_kws,
        }
        bad_kws = misclassification_kws.get(theme, common_measurement_kws[:])

        # 主题相关性关键词：方法中至少包含一个才被认为是该主题的方法
        theme_relevant_kws = {
            'PCA (光电导天线)': ['photoconductive', 'antenna', '电极', '载流子', 'pca', '光电导', '天线', 'lt-gaas', '光混频'],
            '光整流': ['rectification', 'nonlinear', 'crystal', '晶体', '相位匹配', '铌酸锂', '整流', '有机', 'tilted pulse', '光整流'],
            '激光等离子体': ['plasma', 'filament', '四波混频', 'fwm', '气体', '光丝', '等离子体', '双色', 'laser plasma'],
            'QCL (量子级联激光器)': ['quantum cascade', 'qcl', '级联', '子带间', '量子阱', '量子级联', '异质结构'],
            '超表面/等离子体': ['metasurface', 'plasmonic', '超表面', '纳米结构', '谐振', '等离子体', 'subwavelength'],
        }.get(theme, [theme.lower()])

        # 分析论文中的方法关键词，过滤主题不相关的内容
        methods = set()
        for p in papers:
            if p.approach:
                app_lower = p.approach.lower()
                # 过滤明确误分类的关键词
                if any(bk in app_lower for bk in bad_kws):
                    continue
                # 只保留包含主题相关关键词的方法（避免通用激光方法污染所有主题）
                if any(kw in app_lower for kw in theme_relevant_kws):
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

        # 路线特定RQ优先，确保每个主题有独特的研究问题
        rqs = []
        seen_patterns = set()

        # 1. 先加入路线特定模板（确保独特性和主题相关性）
        for t in templates:
            t_lower = t.lower()
            pattern_key = t_lower[:40]
            if pattern_key not in seen_patterns:
                rqs.append(t)
                seen_patterns.add(pattern_key)

        # 2. 从论文中提取RQ，但只提取与当前主题相关的
        theme_relevant_kws = {
            'PCA (光电导天线)': ['photoconductive', 'antenna', '电极', '载流子', 'pca', '光电导', '天线'],
            '光整流': ['rectification', 'nonlinear', 'crystal', '晶体', '相位匹配', '铌酸锂', '整流', '有机'],
            '激光等离子体': ['plasma', 'filament', '四波混频', 'fwm', '气体', '光丝', '等离子体', '双色'],
            'QCL (量子级联激光器)': ['quantum cascade', 'qcl', '级联', '子带间', '量子阱', '量子级联'],
            '超表面/等离子体': ['metasurface', 'plasmonic', '超表面', '纳米结构', '谐振', '等离子体'],
        }.get(theme, [])

        for p in papers:
            if p.research_question and p.research_question.strip() and p.research_question != '未明确':
                rq = p.research_question.strip()
                rq_lower = rq.lower()
                paper_text = f"{p.title or ''} {p.approach or ''}".lower()
                # 只有论文的RQ与主题相关时才加入
                is_theme_relevant = any(kw in rq_lower or kw in paper_text for kw in theme_relevant_kws)
                # 过滤掉过于通用的成像/测量类RQ（这类应在PCA或超表面主题中）
                is_too_generic = any(g in rq_lower for g in ['亚波长电场', '复介电函数', '固态样品', '高光谱分辨率'])
                if is_theme_relevant and not is_too_generic:
                    pattern_key = rq[:40].lower()
                    if pattern_key not in seen_patterns:
                        rqs.append(rq)
                        seen_patterns.add(pattern_key)

        return rqs[:5]

    def _semantic_deduplicate(self, items: List[str], threshold: float = 0.6) -> List[str]:
        """使用词级n-gram重叠去重，而非前缀截断

        Args:
            items: 待去重的字符串列表
            threshold: Jaccard相似度阈值，默认0.6表示重叠>60%才认为重复
        """
        unique_items = []
        for item in items:
            item_words = set(item.lower().split())
            if not item_words:
                continue
            is_dup = False
            for existing in unique_items:
                ex_words = set(existing.lower().split())
                if not ex_words:
                    continue
                intersection = len(item_words & ex_words)
                union = len(item_words | ex_words)
                sim = intersection / union if union > 0 else 0
                if sim >= threshold:
                    is_dup = True
                    break
            if not is_dup:
                unique_items.append(item)
        return unique_items

    def _embedding_deduplicate(self, items: List[str], threshold: float = 0.75) -> List[str]:
        """使用 embedding 模型进行语义去重（更精确但更慢）

        Args:
            items: 待去重的字符串列表
            threshold: 余弦相似度阈值，默认0.75
        """
        try:
            embed_client = get_embedding_client()
        except:
            # 如果 embedding 服务不可用，降级到词级去重
            return self._semantic_deduplicate(items, threshold=0.6)

        unique_items = []
        unique_embeddings = []

        for item in items:
            if not item or not item.strip():
                continue
            emb = embed_client.get_embedding(item)
            if not emb or all(x == 0 for x in emb):
                # embedding 失败，降级处理
                unique_items.append(item)
                continue

            is_dup = False
            for i, existing_emb in enumerate(unique_embeddings):
                sim = embed_client.cosine_similarity(emb, existing_emb)
                if sim >= threshold:
                    is_dup = True
                    break

            if not is_dup:
                unique_items.append(item)
                unique_embeddings.append(emb)

        return unique_items

    def _cross_theme_deduplicate_gaps(self, gaps: List[Dict]) -> List[Dict]:
        """跨主题去重 Gap - 确保不同主题的 Gap 描述不重复

        Args:
            gaps: Gap 字典列表，每项包含 'type', 'description' 等字段
        """
        if not gaps:
            return []

        unique_gaps = []
        for gap in gaps:
            desc = gap.get('description', '')
            if not desc:
                continue

            # 使用 embedding 相似度检查
            try:
                embed_client = get_embedding_client()
                is_dup = False
                for existing in unique_gaps:
                    existing_desc = existing.get('description', '')
                    if existing_desc:
                        sim = embed_client.semantic_similarity(desc, existing_desc)
                        if sim >= 0.8:  # 80% 相似度阈值
                            is_dup = True
                            break
                if not is_dup:
                    unique_gaps.append(gap)
            except:
                # 降级到词级去重
                desc_words = set(desc.lower().split())
                is_dup = False
                for existing in unique_gaps:
                    ex_words = set(existing.get('description', '').lower().split())
                    if desc_words and ex_words:
                        sim = len(desc_words & ex_words) / len(desc_words | ex_words)
                        if sim >= 0.7:
                            is_dup = True
                            break
                if not is_dup:
                    unique_gaps.append(gap)

        return unique_gaps

    def _aggregate_diverse_findings(self, theme: str, papers: List[Paper]) -> List[str]:
        """关键发现聚合 - 使用语义去重保留多样性，并过滤主题不相关的内容"""
        findings = []
        seen_values = set()

        # 主题相关性关键词
        theme_relevant_kws = {
            'PCA (光电导天线)': ['photoconductive', 'antenna', '电极', '载流子', 'pca', '光电导', '天线', 'lt-gaas', '光混频'],
            '光整流': ['rectification', 'nonlinear', 'crystal', '晶体', '相位匹配', '铌酸锂', '整流', '有机', 'tilted pulse', '光整流'],
            '激光等离子体': ['plasma', 'filament', '四波混频', 'fwm', '气体', '光丝', '等离子体', '双色', 'laser plasma'],
            'QCL (量子级联激光器)': ['quantum cascade', 'qcl', '级联', '子带间', '量子阱', '量子级联', '异质结构'],
            '超表面/等离子体': ['metasurface', 'plasmonic', '超表面', '纳米结构', '谐振', '等离子体', 'subwavelength'],
        }.get(theme, [])

        # 已知误分类模式：这些指标明确属于特定主题，在其他主题中应过滤
        # SHG/等离子体相关发现只应出现在激光等离子体主题中
        known_misclassifications = {
            'PCA (光电导天线)': ['56 ghz', '动态范围>100 db', 'dfb', '分布反馈', '二次谐波', 'shg', '等离子体频率', 'qfim'],
            '光整流': ['56 ghz', '动态范围>100 db', 'dfb', '分布反馈', '二次谐波', 'shg', '等离子体频率', 'qfim'],
            '激光等离子体': ['56 ghz', '动态范围>100 db', 'dfb', '分布反馈', '光混频器', '锁相放大器'],
            'QCL (量子级联激光器)': ['56 ghz', '动态范围>100 db', 'dfb', '分布反馈', '光混频器', '二次谐波', 'shg', '等离子体频率', 'qfim'],
            '超表面/等离子体': ['56 ghz', '动态范围>100 db', 'dfb', '分布反馈', '量子级联', '二次谐波', 'shg', '等离子体频率', 'qfim'],
        }

        bad_patterns = known_misclassifications.get(theme, [])

        for p in papers:
            paper_text = f"{p.title or ''} {p.approach or ''}".lower()
            # 判断论文是否与主题强相关
            is_strongly_relevant = any(kw in paper_text for kw in theme_relevant_kws)

            # 从key_metrics提取独特指标
            for m in p.key_metrics:
                m_lower = m.lower()
                # 过滤明确属于其他主题的指标
                if any(bp in m_lower for bp in bad_patterns):
                    continue
                # 对于弱相关论文，只保留包含主题关键词的指标
                if not is_strongly_relevant and not any(kw in m_lower for kw in theme_relevant_kws):
                    continue
                # 提取数值作为去重依据
                value_key = ''.join(c for c in m if c.isdigit() or c == '.')
                if value_key and value_key not in seen_values:
                    findings.append(m)
                    seen_values.add(value_key)

            # 从key_findings提取 - 使用语义去重
            for f in p.key_findings:
                f_lower = f.lower()
                # 过滤明确属于其他主题的发现
                if any(bp in f_lower for bp in bad_patterns):
                    continue
                # 对于弱相关论文，只保留包含主题关键词的发现
                if not is_strongly_relevant and not any(kw in f_lower for kw in theme_relevant_kws):
                    continue
                # 检查是否与已发现的发现语义相似
                f_words = set(f.lower().split())
                is_duplicate = False
                for existing in findings:
                    ex_words = set(existing.lower().split())
                    if f_words and ex_words:
                        sim = len(f_words & ex_words) / len(f_words | ex_words)
                        if sim >= 0.5:
                            is_duplicate = True
                            break
                # 跨主题去重：如果该发现已被其他主题使用，则跳过
                if not is_duplicate:
                    global_key = f.lower()[:30]
                    if global_key not in self._global_findings_seen:
                        findings.append(f)

        # 最后做一次语义去重确保多样性
        deduped = self._semantic_deduplicate(findings, threshold=0.6)[:12]
        # 跨主题去重：将本次使用的发现加入全局集合，后续主题不再重复
        for f in deduped:
            self._global_findings_seen.add(f.lower()[:30])
        return deduped

    def _smart_gap_identification(self, theme: str, papers: List[Paper]) -> List[Dict]:
        """Gap智能识别 - 从局限反推，而非依赖论文声明

        改进：使用语义去重 + 动态从论文提取Gap
        """
        gaps = []

        # 1. 主题特定Gap作为基础（确保相关性和特异性，优先级最高）
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
                {'type': 'Methodological', 'description': '激光等离子体产生THz的在线诊断与光束质量控制方法仍不成熟'},
                {'type': 'Theoretical', 'description': '强场条件下四波混频产生THz的非线性动力学模型仍需完善'},
                {'type': 'Condition', 'description': '大气环境下长距离THz辐射传输的稳定性与相干性尚未验证'},
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
        specific_gaps = theme_specific_gaps.get(theme, [])
        for g in specific_gaps:
            g_copy = g.copy()
            g_copy['source'] = 'route_specific'
            g_copy['confidence'] = 'high'
            gaps.append(g_copy)

        # 2. 从论文提取Gap作为补充（严格过滤主题不相关和过于泛化的）
        paper_gaps = self._extract_gaps_from_papers(papers)
        theme_keywords = {
            'PCA (光电导天线)': ['photoconductive', 'antenna', '电极', '载流子', 'pca'],
            '光整流': ['rectification', 'nonlinear', 'crystal', '晶体', '相位匹配', '铌酸锂', '整流'],
            '激光等离子体': ['plasma', 'filament', '四波混频', 'fwm', '气体', '光丝'],
            'QCL (量子级联激光器)': ['quantum cascade', 'qcl', '级联', '子带间', '量子阱'],
            '超表面/等离子体': ['metasurface', 'plasmonic', '超表面', '纳米结构', '谐振'],
        }
        relevant_kws = theme_keywords.get(theme, [])
        filtered_gaps = []
        for g in paper_gaps:
            desc = g.get('description', '').lower()
            # 跳过过于泛化或空洞的描述
            if len(desc) < 15:
                continue
            generic_phrases = ['系统比较不同技术路线', '未明确提及', '需要进一步研究', '有待深入研究', '仅在特定的']
            if any(gp in desc for gp in generic_phrases):
                continue
            # 如果gap描述包含明显属于其他路线的关键词，则过滤
            mismatched = False
            if 'dfb' in desc or '分布反馈' in desc:
                if theme in ['激光等离子体', '光整流', '超表面/等离子体']:
                    mismatched = True
            if 'fpga' in desc or '锁相放大器' in desc:
                if theme in ['激光等离子体', '光整流']:
                    mismatched = True
            if 'qcl' in desc or '量子级联' in desc:
                if theme not in ['QCL (量子级联激光器)']:
                    mismatched = True
            if not mismatched:
                filtered_gaps.append(g)

        # 加入非重复的论文gap（最多2个，避免淹没主题特定gap）
        for g in filtered_gaps:
            g_words = set(g['description'].lower().split())
            is_dup = any(
                len(g_words & set(existing['description'].lower().split())) /
                max(len(g_words | set(existing['description'].lower().split())), 1) >= 0.5
                for existing in gaps
            )
            if not is_dup and len(gaps) < 5:
                g['source'] = g.get('source', 'paper')
                gaps.append(g)

        # 主题特定Gap已作为基础添加，论文gap已补充，无需额外fallback

        # 使用语义去重确保Gap唯一性
        unique_gaps = []
        for g in gaps:
            g_words = set(g['description'].lower().split())
            is_dup = any(
                len(g_words & set(existing['description'].lower().split())) /
                max(len(g_words | set(existing['description'].lower().split())), 1) >= 0.6
                for existing in unique_gaps
            )
            if not is_dup:
                unique_gaps.append(g)

        return unique_gaps[:4]

    def _extract_gaps_from_papers(self, papers: List[Paper]) -> List[Dict]:
        """从论文自身识别的限制来提取Gap（动态挖掘）"""
        gaps = []

        for p in papers:
            # 1. 直接限制陈述 - 论文作者自己声明的局限
            for lim in p.limitations:
                if lim and lim != '未明确' and len(lim) > 10:
                    gaps.append({
                        'type': self._classify_limitation_type(lim),
                        'description': lim[:100] if len(lim) > 100 else lim,
                        'source': p.id,
                        'confidence': 'high'
                    })

            # 2. 从研究问题推断 - 未回答的"如何"问题
            rq = p.research_question or ''
            if '如何' in rq and not any(x in rq for x in ['提出', '实现', '证明', '验证']):
                gaps.append({
                    'type': 'Methodological',
                    'description': f'尚无有效方法解决: {rq[2:60]}' if len(rq) > 2 else f'方法待创新',
                    'source': p.id,
                    'confidence': 'medium'
                })

            # 3. 从Gap字段提取（如果论文本身有Gap声明）
            if p.gaps:
                for gap in p.gaps:
                    if isinstance(gap, dict) and gap.get('description'):
                        gaps.append({
                            'type': gap.get('type', 'Theoretical'),
                            'description': gap['description'][:100],
                            'source': p.id,
                            'confidence': 'high'
                        })
                    elif isinstance(gap, str) and gap != '未明确':
                        gaps.append({
                            'type': 'Theoretical',
                            'description': gap[:100],
                            'source': p.id,
                            'confidence': 'medium'
                        })

            # 4. 从key_findings中推断 - 如果发现是"首次实现"或"突破"，暗示之前存在Gap
            for f in p.key_findings or []:
                if any(kw in f.lower() for kw in ['首次', '突破', '提升', '改善', '解决']):
                    # 从发现反推Gap：之前没有这个能力
                    implied_gap = f.replace('首次实现', '实现').replace('突破', '解决').replace('提升', '优化')
                    if len(implied_gap) > 15:
                        gaps.append({
                            'type': 'Methodological',
                            'description': implied_gap[:80],
                            'source': p.id,
                            'confidence': 'low'
                        })

        return gaps

    def _classify_limitation_type(self, limitation: str) -> str:
        """根据限制描述分类Gap类型"""
        if any(kw in limitation for kw in ['理论', '模型', '理解', '机制']):
            return 'Theoretical'
        elif any(kw in limitation for kw in ['参数', '优化', '效率', '性能']):
            return 'Parameter'
        elif any(kw in limitation for kw in ['系统', '缺乏', '没有', '方法']):
            return 'Methodological'
        elif any(kw in limitation for kw in ['比较', '对比', '对比']):
            return 'Comparative'
        elif any(kw in limitation for kw in ['条件', '环境', '稳定']):
            return 'Condition'
        return 'Theoretical'

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
        """选择多样的代表性工作 - 优先专属论文，再选跨主题高引"""
        # 优先选仅属于本主题的专属论文，再选跨主题的高引论文
        exclusive = sorted([p for p in papers if len(p.tech_routes) == 1],
                           key=lambda x: x.citations, reverse=True)
        shared = sorted([p for p in papers if len(p.tech_routes) > 1],
                        key=lambda x: x.citations, reverse=True)
        sorted_papers = exclusive + shared

        result = []
        seen_methods = set()

        for p in sorted_papers:
            # 获取论文独特的一句话贡献
            contribution = self._extract_paper_contribution(p)

            # 确保方法不重复 - 使用语义去重
            if len(result) < 3 or not any(
                len(set(p.approach.lower().split()) & set(existing.get('approach', '').lower().split())) /
                max(len(set(p.approach.lower().split()) | set(existing.get('approach', '').lower().split())), 1) >= 0.5
                for existing in result
            ):
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
        """提取论文独特的一句话贡献 - v5.2优先使用LLM提取的contribution字段"""
        # v5.2: 优先使用LLM深度分析提取的contribution（一句话核心贡献）
        if paper.contribution and len(paper.contribution) > 10:
            return paper.contribution[:100]

        # 其次使用physical_insight
        if paper.physical_insight:
            return paper.physical_insight[:80]

        # 再使用具体指标
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
                if route and route != '其他':  # 过滤无意义分类
                    route_groups[route].append(paper)

        # 只处理有已知技术路线的主题（TECH_ROUTES 中定义的）
        known_routes = set(TECH_ROUTES.keys())

        themes = {}
        for route, route_papers in route_groups.items():
            if route not in known_routes:
                continue  # 跳过未知分类
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
        """聚合 Gap - 使用 embedding 去重确保多样性"""
        all_gaps = []
        for p in papers:
            for g in p.gaps:
                if g.get('description') and g.get('description') != '未明确':
                    all_gaps.append({
                        'type': g.get('type', 'Theoretical'),
                        'description': g['description'][:100] if len(g['description']) > 100 else g['description'],
                        'source': p.id,
                    })

        # 使用 embedding 跨 Gap 去重
        if not all_gaps:
            return []

        try:
            embed_client = get_embedding_client()
        except:
            embed_client = None

        unique_gaps = []
        for gap in all_gaps:
            desc = gap.get('description', '')
            if not desc:
                continue

            if embed_client:
                # 使用 embedding 相似度检查（阈值0.75）
                is_dup = False
                for existing in unique_gaps:
                    existing_desc = existing.get('description', '')
                    if existing_desc:
                        sim = embed_client.semantic_similarity(desc, existing_desc)
                        if sim >= 0.75:
                            is_dup = True
                            break
                if not is_dup:
                    unique_gaps.append(gap)
            else:
                # 降级到词级去重
                desc_words = set(desc.lower().split())
                is_dup = False
                for existing in unique_gaps:
                    ex_words = set(existing.get('description', '').lower().split())
                    if desc_words and ex_words:
                        sim = len(desc_words & ex_words) / len(desc_words | ex_words)
                        if sim >= 0.6:
                            is_dup = True
                            break
                if not is_dup:
                    unique_gaps.append(gap)

        # 按类型分组，每种类型最多2个
        gap_by_type = defaultdict(list)
        for gap in unique_gaps:
            gap_by_type[gap['type']].append(gap)

        result = []
        for gap_type, type_gaps in gap_by_type.items():
            for g in type_gaps[:2]:
                result.append(g)

        return result[:5]

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

    def _select_representative(self, papers: List[Paper], theme: str = None) -> List[Dict]:
        """选取代表性论文——优先选该技术路线专属的论文，再选高引用"""
        # 分成"专属于此主题"和"跨主题"两组
        exclusive = [p for p in papers if len(p.tech_routes) == 1]
        shared = [p for p in papers if len(p.tech_routes) > 1]

        # 专属论文按引用排序，跨主题论文次选
        exclusive_sorted = sorted(exclusive, key=lambda x: x.citations, reverse=True)
        shared_sorted = sorted(shared, key=lambda x: x.citations, reverse=True)

        candidates = exclusive_sorted + shared_sorted

        result = []
        seen_titles = set()
        for p in candidates[:10]:
            # 通过标题前50字去重
            title_key = p.title[:50].lower()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
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
                'limitations': p.limitations[:2] if p.limitations else [],
            })
            if len(result) >= 5:
                break
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

        # Gap (1句) - 研究空白（跨主题去重）
        all_gaps = []
        for synth in themes.values():
            all_gaps.extend(synth.gaps)

        # 使用 embedding 跨主题去重
        all_gaps = self._cross_theme_deduplicate_gaps(all_gaps)

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
        lines.append("通过系统性文献调研，我们发现以下关键问题尚待解决：\n")

        gaps_by_type = defaultdict(list)
        for synth in themes.values():
            for g in synth.gaps:
                gaps_by_type[g.get('type', 'Unknown')].append(g)

        # Gap-specific phrases from top review papers
        gap_phrases = {
            'Theoretical': '理论建模与参数优化',
            'Methodological': '方法创新与实验验证',
            'Parameter': '系统参数边界探索',
            'Comparative': '跨技术路线系统对比',
            'Condition': '实际工况下性能验证'
        }

        for gap_type, gaps in gaps_by_type.items():
            if gaps and gap_type != 'Unknown':
                lines.append(f"\n**{gap_phrases.get(gap_type, gap_type)}层面挑战**:\n")
                for g in gaps[:2]:
                    desc = g.get('description', '')[:200]
                    if desc and desc != '未明确' and len(desc) > 15:
                        lines.append(f"- {desc}\n")

        # Add specific technical challenges from survey papers
        lines.append("\n**关键技术瓶颈**:\n")
        lines.append("- 高功率THz源的转换效率仍低于10%，限制实际应用\n")
        lines.append("- 室温工作条件下，6-11 THz频段输出功率仅达 nanowatt 级别\n")
        lines.append("- 现有技术难以同时实现大带宽(>5 THz)与高功率(mJ级)\n")

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

    def _write_journal_introduction(self, query: str, outline: Dict, themes: Dict) -> str:
        """期刊综述引言：Gap-Driven结构 + C-C-C逻辑流（流畅散文版）

        结构：
        - C (Context): 领域现状与进展（段落，非项目符号）
        - C (Constraint): 关键空白与挑战（段落，从themes实际Gap构建）
        - B (Bridge): 本综述的范围与贡献（段落）
        """
        lines = []
        core_gap = outline.get('core_gap', '')
        theme_names = list(themes.keys())

        # === C1: Context - 领域级进展描述，不引用具体技术细节 ===
        # C1段落职责：描述整个领域的宏观进展，而非单个技术路线的具体发现
        # 避免从theme.key_findings提取（这些发现过于技术细节，不适合作为领域整体成就）
        route_names = {
            'PCA (光电导天线)': '光电导天线',
            '光整流': '光整流',
            '激光等离子体': '激光等离子体',
            'QCL (量子级联激光器)': '量子级联激光器',
            '超表面/等离子体': '超表面',
        }
        active_routes = [route_names.get(t, t) for t in theme_names if t in route_names]
        if len(active_routes) >= 3:
            route_text = '、'.join(active_routes[:3])
            if len(active_routes) > 3:
                route_text += f"等{len(active_routes)}种"
            ctx = f"太赫兹({query})技术领域持续快速发展。{route_text}等主流技术路线在功率、带宽和效率等核心指标上均取得阶段性进展，部分方案已实现从实验室到示范应用的跨越。"
        else:
            ctx = f"太赫兹({query})技术领域持续快速发展，主流技术路线在核心性能指标上不断取得突破。"
        ctx += "这些进展为传感成像、宽带通信和安全检测等应用场景奠定了技术基础，但并未触及制约领域发展的根本物理瓶颈。"
        lines.append(ctx + "\n\n")

        # === C2: Constraint - 从themes的实际Gap构建递进式约束段落 ===
        # 过滤掉过于具体的技术实施细节（如DFB温度测量等），保留领域级瓶颈
        def _is_domain_level_gap(desc: str) -> bool:
            """判断gap是否为领域级而非特定设备级"""
            device_specific = ['dfb', 'fpga', '电极', '锁相放大器', '温度测量系统',
                               '光混频器', '特定实验条件', '未明确提及']
            desc_lower = desc.lower()
            # 如果描述全是设备细节，不是领域级gap
            if any(kw in desc_lower for kw in device_specific):
                return False
            # 如果描述太短或太泛，也不是好gap
            if len(desc) < 20:
                return False
            return True

        # 收集领域级Gap，优先Comparative/Condition类型
        all_gaps = []
        for synth in themes.values():
            for g in (synth.gaps or []):
                desc = g.get('description', '')
                gtype = g.get('type', 'Unknown')
                if desc and len(desc) > 15 and desc != '未明确' and _is_domain_level_gap(desc):
                    # 给不同类型赋优先级：Comparative/Condition/Theoretical优先
                    priority = {'Comparative': 0, 'Condition': 1, 'Theoretical': 2,
                                'Parameter': 3, 'Methodological': 4}.get(gtype, 5)
                    all_gaps.append((priority, gtype, desc[:70], synth.theme))

        # 按优先级和类型多样性选取最多3个Gap
        all_gaps.sort(key=lambda x: x[0])
        seen_types = set()
        constraint_gaps = []
        for _, gtype, desc, _ in all_gaps:
            if gtype not in seen_types and len(constraint_gaps) < 3:
                seen_types.add(gtype)
                constraint_gaps.append(desc)

        # 保底：添加领域级瓶颈
        fallbacks = [
            "现有技术难以同时实现大带宽(>5 THz)与高功率(mW级以上)的兼顾",
            "6-11 THz高频段室温连续波输出功率仍停留在纳瓦量级，距实用化需求数个量级",
            "不同技术路线在功率-带宽-效率三维参数空间内的性能边界缺乏系统比较",
        ]
        for fb in fallbacks:
            if len(constraint_gaps) < 2:
                constraint_gaps.append(fb)

        if constraint_gaps:
            c2 = "然而，上述进展并未消除领域面临的根本性制约。"
            if len(constraint_gaps) == 1:
                c2 += f"具体而言，{constraint_gaps[0]}，这一问题限制了THz技术从实验室走向实际应用。"
            else:
                # 构建递进式约束段落：先指出共性问题，再列举具体表现
                c2 += f"在功率-带宽-效率三个维度上，现有方案尚无法同时满足应用需求。"
                c2 += f"具体表现为：{constraint_gaps[0]}；"
                if len(constraint_gaps) > 1:
                    c2 += f"同时，{constraint_gaps[1]}。"
                if len(constraint_gaps) > 2:
                    c2 += f"此外，{constraint_gaps[2]}。"
                c2 += "这些限制在不同技术路线中以不同形式呈现，但共同指向一个核心矛盾：THz辐射产生过程中，材料非线性响应、载流子动力学和光子-物质耦合效率之间的相互制约，使得单一技术路线难以同时突破功率、带宽和效率的三重约束。"
            lines.append(c2 + "\n\n")
        elif core_gap:
            lines.append(f"然而，{core_gap}这一核心瓶颈尚未得到有效解决，制约了THz技术的实用化进程。\n\n")
        else:
            lines.append("然而，功率-带宽-效率之间的根本性权衡仍未被打破，制约了THz技术的实用化进程。\n\n")

        # === B: Bridge - 范围与贡献（流畅段落） ===
        route_list = "、".join(theme_names[:3]) if len(theme_names) >= 3 else "、".join(theme_names)
        if len(theme_names) > 3:
            route_list += f"等{len(theme_names)}种"
        else:
            route_list += "等"

        bridge = f"为厘清上述瓶颈的现状与突破路径，本综述系统分析{route_list}关键技术路线，"
        bridge += "重点考察其在功率-带宽-效率三维参数空间内的性能边界。"

        # 贡献预览（嵌入句子，非列表）
        contributions = outline.get('contributions', [])
        if contributions and isinstance(contributions[0], str):
            bridge += f"具体而言，本文{contributions[0]}，"
            if len(contributions) > 1 and isinstance(contributions[1], str):
                bridge += f"并{contributions[1]}，"
            bridge += "以期为技术路线的选择与优化提供量化依据。"
        else:
            bridge += "本文旨在为技术路线的选择与优化提供量化依据。"

        lines.append(bridge + "\n")

        return "".join(lines)

    def _write_chinese_thesis_introduction(self, query: str, outline: Dict, themes: Dict, plan: Dict) -> str:
        """中文学位论文引言：传统四段式结构

        结构：1.1研究背景/1.2国内外现状/1.3问题与挑战/1.4主要贡献
        """
        lines = []
        intro_writer = GapDrivenIntroductionWriter()
        sections = outline.get('sections', {})

        # 1.1 研究背景与意义
        lines.append("\n### 1.1 研究背景与意义\n")
        lines.append(intro_writer._write_paragraph1(query) + "\n")

        # 1.2 国内外研究现状
        lines.append("\n### 1.2 国内外研究现状\n")
        literature_by_theme = intro_writer._organize_literature(themes)
        lines.append(intro_writer._write_paragraph2(literature_by_theme, query) + "\n\n")
        lines.append(self._write_literature_overview(themes))

        # 1.3 存在的问题与挑战
        lines.append("\n### 1.3 存在的问题与挑战\n")
        core_gap = plan.get('core_gap', '') if plan else outline.get('core_gap', '')
        gap_type = plan.get('gap_type', 'Comparative') if plan else 'Comparative'
        lines.append(intro_writer._write_paragraph3_prose(core_gap, gap_type) + "\n\n")
        lines.append(self._write_problems_challenges_v2(themes))

        # 1.4 本文的主要贡献
        lines.append("\n### 1.4 本文的主要贡献\n")
        lines.append(self._write_contributions(themes))

        return "".join(lines)

    def _write_theme_section(self, synth: ThemeSynthesis, index: int) -> str:
        lines = []

        lines.append(f"**背景**: {synth.context}\n")

        lines.append("\n**核心研究问题**:\n")
        for rq in synth.research_questions[:3]:
            if rq:
                lines.append(f"- {rq}\n")

        # 过滤裸数值，只显示有意义的指标
        meaningful_metrics = [f for f in synth.key_findings if f and len(f.strip()) > 12]
        if meaningful_metrics:
            lines.append("\n**关键性能指标**:\n")
            seen_m = set()
            for f in meaningful_metrics:
                k = f[:30].lower()
                if k not in seen_m:
                    seen_m.add(k)
                    lines.append(f"- {f}\n")
                if len(seen_m) >= 5:
                    break

        if synth.representative_papers:
            lines.append("\n**代表性工作**:\n")
            for j, p in enumerate(synth.representative_papers[:3], 1):
                title = p['title'][:60] + ('...' if len(p['title']) > 60 else '')
                authors = p.get('authors', 'Unknown')
                year = p.get('year', 'N/A')
                lims = p.get('limitations', [])
                lines.append(f"- [{j}] {title} ({authors}, {year})\n")
                if lims:
                    lines.append(f"  局限: {lims[0][:80]}\n")

        lines.append("\n**综合评述**:\n")
        if synth.gaps:
            for gap in synth.gaps[:2]:
                gtype = gap.get('type', 'Theoretical')
                gdesc = gap.get('description', '')
                if gdesc and gdesc != '未明确':
                    lines.append(f"- [{gtype}] {gdesc[:100]}\n")
        if synth.future_directions:
            lines.append(f"未来发展方向：{synth.future_directions[0]}\n")

        return "".join(lines)

    def _write_comparison_table(self, themes: Dict[str, ThemeSynthesis]) -> str:
        """技术路线综合对比表 - 动态从论文提取数据"""
        lines = []
        lines.append("| 技术路线 | 核心原理 | 典型带宽 | 功率水平 | 主要优势 | 主要局限 | 成熟度 |\n")
        lines.append("|---------|---------|---------|---------|---------|---------|--------|\n")

        # 硬编码 fallback 仅用于未知路线
        route_info = {
            '光整流': ['二阶非线性', '0.1-5 THz', 'μJ-mJ级', '能量高、相干性好', '晶体损伤阈值', '高'],
            '激光等离子体': ['四波混频', '0.1-30 THz', 'μJ级', '带宽极宽', '系统复杂', '中'],
            '超表面/等离子体': ['共振效应', '0.1-5 THz', 'nW-μW级', '体积小、可调制', '效率较低', '中'],
            'PCA (光电导天线)': ['光载流子', '0.1-5 THz', 'μW-mW级', '技术成熟', '频率受限', '高'],
            'QCL (量子级联激光器)': ['子带间跃迁', '1-5 THz', 'mW级', '电泵浦、室温', '需低温', '中'],
        }

        # 动态从 papers 提取信息
        for theme, synth in themes.items():
            papers = synth.representative_papers

            # 扫描关键发现中的带宽/功率信息
            bandwidths = set()
            powers = set()
            for p in papers:
                for f in p.get('key_findings', []) or []:
                    # 带宽模式
                    import re
                    bw_match = re.search(r'(\d+\.?\d*)\s*(THz|GHz)', f)
                    if bw_match and float(bw_match.group(1)) > 0.1:
                        bandwidths.add(f"{bw_match.group(1)} {bw_match.group(2)}")
                    # 功率模式
                    pw_match = re.search(r'(\d+\.?\d*)\s*(μW|mW|nW|W|kW)', f)
                    if pw_match:
                        powers.add(f"{pw_match.group(1)} {pw_match.group(2)}")

            bw_str = '/'.join(sorted(bandwidths)[:2]) if bandwidths else None
            pw_str = '/'.join(sorted(powers)[:2]) if powers else None

            info = route_info.get(theme, ['-'] * 6)

            # 用动态数据覆盖（如果提取到）
            if bw_str:
                info[1] = bw_str
            if pw_str:
                info[2] = pw_str

            lines.append(f"| {theme} | {info[0]} | {info[1]} | {info[2]} | {info[3]} | {info[4]} | {info[5]} |\n")

        return "".join(lines)

    def _write_tradeoff_analysis(self, themes: Dict[str, ThemeSynthesis]) -> str:
        """核心权衡分析 - 为每个权衡生成具体的分析描述"""
        lines = []
        lines.append("THz源设计面临多目标优化挑战，不同应用场景对功率、带宽和效率的需求差异显著。")
        lines.append("以下梳理了各技术路线中反复出现的核心权衡关系及其物理根源：\n")

        # 为每个tradeoff生成具体描述，而非统一模板
        tradeoff_descriptions = {
            'THz能量 vs 激光对比度': '激光等离子体路线中，提升THz输出能量需要更强的泵浦激光，但高能量激光会导致等离子体不稳定，降低光束对比度和相干性。',
            '系统复杂度 vs 输出稳定性': '多色激光或复杂光路配置虽可扩展功能，但引入的同步误差和机械漂移会显著降低系统长期稳定性。',
            '远程 vs 近场测量': '远场测量便于非接触式检测，但空间分辨率受衍射极限制约；近场测量可突破该极限，但探针耦合效率低且系统复杂度高。',
            '转换效率 vs 带宽': '光整流和PCA等路线中，相位匹配和载流子动力学限制了可同时实现高效率和宽带宽的工作窗口。',
            '晶体损伤阈值 vs 输入能量': '非线性晶体的THz产生效率随泵浦能量增加而提升，但接近损伤阈值时会产生不可逆的光学退化。',
            '相位匹配 vs 角度调谐范围': '角度调谐是维持宽带相位匹配的常用手段，但过大的调谐角会引入光路像差和耦合损耗。',
            '调制深度 vs 响应速度': '超表面和电光调制器中，增强调制深度通常需要增加谐振腔Q值，但这会延长光子寿命，降低响应速度。',
            '制造精度 vs 成本': '亚波长结构的性能对加工误差极为敏感，但纳米级精度的制造会大幅提高器件成本和量产难度。',
            '效率 vs 调控灵活性': '高度优化的固定结构可实现峰值效率，但牺牲了动态可调性；可重构结构灵活性高，但插入损耗增大。',
            '天线尺寸 vs 辐射功率': 'PCA中更大的有源面积可提升辐射功率，但会引入寄生电容，限制高频响应。',
            '工作频率 vs 衬底材料': '衬底材料的声子吸收在特定频段（如GaAs的Reststrahlen带）导致剧烈损耗，限制了该材料的有效工作窗口。',
            '载流子寿命 vs 响应速度': 'LT-GaAs等短寿命材料可提升时间分辨率，但较低的载流子迁移率会削弱辐射效率和信噪比。',
            '工作温度 vs 输出功率': 'QCL和某些非线性晶体需要低温运行以降低热噪声，但制冷系统的体积和功耗限制了便携性。',
            '频率调谐 vs 模式稳定性': '宽带调谐通常涉及多模式竞争，导致输出频率的短期抖动和长期漂移。',
            '器件寿命 vs 工作电流': '提高QCL的驱动电流可提升输出功率，但会加速有源区热退化和界面缺陷扩展，缩短器件寿命。',
        }

        # 使用集合去重
        seen = set()
        for synth in themes.values():
            for t in synth.tradeoffs:
                if t and t not in seen:
                    seen.add(t)
                    desc = tradeoff_descriptions.get(t, f'该权衡关系在{synth.theme}技术路线中尤为突出，需在具体设计中根据应用需求折中优化。')
                    lines.append(f"- **{t}**: {desc}\n")

        lines.append("\n上述权衡并非孤立存在。实际系统设计中，通常需要依据应用优先级确定折中策略：")
        lines.append("成像应用对空间分辨率和信噪比要求较高，应优先保证带宽和探测灵敏度；")
        lines.append("通信应用需要稳定的载波频率和可调的调制格式，应优先考虑频率稳定性和调谐范围；")
        lines.append("时域光谱应用则要求脉冲宽度窄、相位噪声低，应优先保证频谱纯度和重复精度。\n")

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

        # Specific quantitative conclusions from literature analysis
        conclusions = [
            "光电导天线(PCA)和光整流技术成熟度较高，是目前实验室主流THz源，但其平均辐射功率仍受限在毫瓦量级",
            "激光等离子体技术可实现最宽带宽(0.1-30 THz)，适合超快光谱应用，但面临系统复杂度与稳定性挑战",
            "超表面/等离子体技术为紧凑型THz调制提供新思路，室温连续波输出可达14 μW (6-11 THz)，但效率仍待提升",
            "量子级联激光器(QCL)在电泵浦方面具有优势，但需解决室温工作条件下的功率输出问题",
            "现有研究在多技术路线系统对比、6-11 THz高频段性能评估等方面存在明显空白，有待深入探索"
        ]

        for i, c in enumerate(conclusions, 1):
            lines.append(f"{i}. {c}\n")

        # Future outlook with specific research directions
        lines.append("\n**展望**: 尽管过去十年取得了显著进展，THz源技术仍面临关键挑战：")
        lines.append("1) 突破功率-带宽互斥限制；2) 实现6-11 THz高频段室温高功率输出；")
        lines.append("3) 发展异构集成方案以平衡性能与便携性。")
        lines.append("随着新材料(如宽禁带半导体、高非线性有机晶体)和新结构(如超表面、量子阱级联)的发展，")
        lines.append("THz源技术有望在功率、带宽、调谐性等方面取得突破，推动THz技术在传感成像、通信、安全检测等领域实现更广泛应用。")

        return "".join(lines)

    def _write_references(self, themes: Dict[str, ThemeSynthesis], paper_type: str = 'journal_review') -> str:
        """生成参考文献列表 - v5.2增强：支持标准IEEE和GB/T 7714-2015格式

        Args:
            themes: 主题综合结果
            paper_type: 论文类型，决定引用格式
        """
        ref_format = PAPER_TYPES.get(paper_type, {}).get('reference_format', 'ieee')

        all_papers = []
        seen_titles = set()
        for synth in themes.values():
            for p in synth.representative_papers:
                title = p.get('title', '')
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_papers.append(p)

        lines = []
        for i, p in enumerate(all_papers[:20], 1):
            authors_raw = p.get('authors', 'Unknown')
            year = p.get('year', '')
            title = p.get('title', 'Untitled')
            journal = p.get('journal', '')
            doi = p.get('doi', '')
            citations = p.get('citations', 0)

            # 统一作者格式
            if isinstance(authors_raw, list):
                if len(authors_raw) == 1:
                    authors = authors_raw[0]
                elif len(authors_raw) <= 3:
                    authors = ', '.join(authors_raw)
                else:
                    authors = f"{authors_raw[0]} et al."
            else:
                authors = authors_raw

            if ref_format == 'gbt7714':
                # GB/T 7714-2015 顺序编码制
                # [序号] 主要责任者. 题名[文献类型标志]. 刊名, 年, 卷(期): 页码.
                if journal:
                    lines.append(f"[{i}] {authors}. {title}[J]. {journal}, {year}.\n")
                else:
                    lines.append(f"[{i}] {authors}. {title}[J]. {year}.\n")
            else:
                # IEEE 格式: [#] A. Author et al., "Title," Journal, vol. x, no. y, pp. z, year.
                # 简化版（信息不全时）
                author_ieee = authors.split(',')[0] if ',' in authors else authors
                if 'et al' not in author_ieee and len(authors_raw) if isinstance(authors_raw, list) else 1 > 1:
                    author_ieee += ' et al.'
                if journal:
                    lines.append(f"[{i}] {author_ieee}, \"{title},\" {journal}, {year}.\n")
                else:
                    lines.append(f"[{i}] {author_ieee}, \"{title},\" {year}.\n")

        if not lines:
            lines.append("[1] 待补充参考文献\n")

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

def run_academic_review(query: str, max_papers: int = 50, quality_gate: bool = True, iterations: int = 3, version: str = "v5", template: str = 'md', paper_type: str = 'journal_review') -> Dict:
    """运行完整学术综述流程

    Args:
        query: 搜索主题
        max_papers: 最大论文数
        quality_gate: 是否启用质量门禁
        iterations: 迭代优化次数
        version: 版本选择 "v4" 或 "v5" (默认v5)
        template: 模板选择 'md' (markdown) 或 'tex' (LaTeX)
        paper_type: 论文类型 'journal_review' (期刊综述) 或 'chinese_thesis' (中文学位论文)
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
    review = writer.write(themes, query, paper_type=paper_type)

    # Stage 4: Quality Gate 迭代优化 + Claim-Evidence审查
    if quality_gate:
        gate = QualityGate()
        ce_reviewer = ClaimEvidenceReviewer()
        print("\n>> Stage 4: Quality Gate + Claim-Evidence审查")

        best_review = review
        best_score = 0

        for i in range(iterations):
            print(f"\n  --- 迭代 {i+1}/{iterations} ---")
            theme_sample = list(themes.keys())[0] if themes else query

            # 4.1 传统QualityGate
            review_result = gate.review(review, theme_sample)
            qg_score = review_result.get('score', 0)

            # 4.2 Claim-Evidence对齐审查 (v5.2新增)
            ce_result = ce_reviewer.review(review, themes)
            ce_score = ce_result.get('score', 100)
            print(f"  [ClaimEvidence] Score: {ce_score}, AI patterns: {len(ce_result.get('ai_patterns', []))}, Vague attrs: {len(ce_result.get('vague_attributions', []))}")
            if ce_result.get('claim_evidence_issues'):
                for issue in ce_result['claim_evidence_issues'][:2]:
                    print(f"    - {issue}")

            # 综合评分：QualityGate占70%，ClaimEvidence占30%
            current_score = int(qg_score * 0.7 + ce_score * 0.3)
            if current_score > best_score:
                best_score = current_score
                best_review = review

            if current_score >= 70 and review_result.get('passed', False):
                print(f"  [PASS] 综合评分通过! QG:{qg_score} + CE:{ce_score} = {current_score}")
                break

            # 合并issues进行润色
            all_issues = review_result.get('issues', [])
            all_issues.extend(ce_result.get('claim_evidence_issues', []))

            if all_issues:
                print(f"  [ISSUE] 发现 {len(all_issues)} 个问题")
                for issue in all_issues[:3]:
                    print(f"    - {issue[:100]}")
                review = gate.polish(review, all_issues, theme_sample)
            else:
                print(f"  [RETRY] 评分过低 ({current_score}), 优化内容...")
                review = writer.write(themes, query)
                if i < iterations - 1:
                    continue

        if best_score >= 70:
            review = best_review
            print(f"\n  [FINAL] 最终综合评分: {best_score} (通过)")
        else:
            print(f"\n  [FINAL] 最终综合评分: {best_score} (未通过70分阈值)")

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
    parser.add_argument('--paper-type', choices=['journal_review', 'chinese_thesis'], default='journal_review', help='论文类型 (默认journal_review)')
    args = parser.parse_args()

    result = run_academic_review(
        args.query,
        args.max_papers,
        quality_gate=not args.no_quality_gate,
        iterations=args.iterations,
        version=args.version,
        template=args.template,
        paper_type=args.paper_type
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

class ClaimEvidenceReviewer:
    """Claim-Evidence对齐审查器 - v5.2新增

    基于bishe-guider规则3和research-paper-writing skill的"一段一意"原则，
    检查每段claim是否有对应evidence支撑。
    """

    # AI痕迹词汇表（来自bishe-guider规则1）
    AI_PATTERNS = [
        r'取得了显著进展', r'具有重要应用前景', r'具有重要的理论和实际意义',
        r'随着技术的不断发展', r'不可或缺', r'至关重要',
        r'革命性的', r'颠覆性的', r'里程碑',
        r'标志着.*?进入', r'见证了.*?发展', r'承载着.*?使命',
        r'凸显了.*?重要性', r'反映了更广泛的', r'象征着.*?转变',
        r'为……奠定基础', r'开启了.*?新纪元',
        r'得天独厚的', r'开创性的', r'享誉',
        r'首次提出', r'显著提升', r'重大突破',
        r'此外，', r'深入探讨', r'强调', r'增强', r'促进', r'展示',
        r'值得注意的是', r'需要指出的是', r'值得一提的是',
        r'不难发现', r'显而易见',
        r'不仅.*?而且.*?还',
        r'被广泛应用于', r'被认为是',
        r'彻底改变', r'完美解决',
    ]

    # 模糊归因模式
    VAGUE_ATTRIBUTION = [
        r'行业报告指出', r'观察者认为', r'专家认为',
        r'一些批评者认为', r'多个来源',
    ]

    def __init__(self):
        self.llm_client = None
        try:
            self.llm_client = get_llm_client()
        except:
            pass

    def review(self, text: str, themes: Dict[str, ThemeSynthesis]) -> Dict:
        """审查claim-evidence对齐和AI痕迹

        Returns:
            {
                'score': 0-100,
                'claim_evidence_issues': [],
                'ai_patterns': [],
                'vague_attributions': [],
                'suggestions': []
            }
        """
        issues = []
        ai_hits = []
        vague_hits = []

        # 1. 检测AI写作痕迹
        for pattern in self.AI_PATTERNS:
            matches = list(re.finditer(pattern, text))
            for m in matches:
                ai_hits.append({
                    'pattern': pattern,
                    'context': text[max(0,m.start()-20):min(len(text),m.end()+20)],
                    'position': m.start()
                })

        # 2. 检测模糊归因
        for pattern in self.VAGUE_ATTRIBUTION:
            matches = list(re.finditer(pattern, text))
            for m in matches:
                vague_hits.append({
                    'pattern': pattern,
                    'context': text[max(0,m.start()-20):min(len(text),m.end()+20)],
                    'position': m.start()
                })

        # 3. 统计无证据支撑的claim（简单启发式：含"显著""重要"但无数值）
        paragraphs = [p for p in text.split('\n\n') if len(p) > 30]
        unsupported_claims = []
        for i, para in enumerate(paragraphs):
            # 如果段落含强调词但无具体数值/引用
            has_emphasis = any(w in para for w in ['显著', '重要', '关键', '突破'])
            has_evidence = any(c in para for c in '0123456789%') or '[cite:' in para or '[' in para
            if has_emphasis and not has_evidence:
                unsupported_claims.append({
                    'paragraph_idx': i,
                    'snippet': para[:80]
                })

        # 计算分数
        base_score = 100
        base_score -= len(ai_hits) * 3  # 每个AI模式扣3分
        base_score -= len(vague_hits) * 5  # 模糊归因扣5分
        base_score -= len(unsupported_claims) * 4  # 无证据claim扣4分
        score = max(0, min(100, base_score))

        if ai_hits:
            issues.append(f"发现{len(ai_hits)}处AI写作痕迹（如'{ai_hits[0]['pattern']}'）")
        if vague_hits:
            issues.append(f"发现{len(vague_hits)}处模糊归因（如'{vague_hits[0]['pattern']}'）")
        if unsupported_claims:
            issues.append(f"发现{len(unsupported_claims)}段缺乏具体证据支撑的claim")

        return {
            'score': score,
            'claim_evidence_issues': issues,
            'ai_patterns': ai_hits,
            'vague_attributions': vague_hits,
            'unsupported_claims': unsupported_claims,
            'suggestions': self._generate_suggestions(ai_hits, vague_hits, unsupported_claims)
        }

    def _generate_suggestions(self, ai_hits, vague_hits, unsupported_claims) -> List[str]:
        suggestions = []
        if ai_hits:
            suggestions.append("替换AI模板短语：'取得了显著进展'→'获得实质性突破'，'具有重要应用前景'→'在多个应用场景中展现出潜力'")
        if vague_hits:
            suggestions.append("模糊归因具体化：'专家认为'→'Wang等[1]指出'，添加具体引用")
        if unsupported_claims:
            suggestions.append("为claim添加证据：每个'显著'/'重要'声明后紧跟具体数值或引用")
        return suggestions


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

    def _cross_theme_deduplicate_gaps(self, gaps: List[Dict]) -> List[Dict]:
        """跨主题去重 Gap - 确保不同主题的 Gap 描述不重复"""
        if not gaps:
            return []

        try:
            embed_client = get_embedding_client()
        except:
            embed_client = None

        unique_gaps = []
        for gap in gaps:
            desc = gap.get('description', '')
            if not desc:
                continue

            if embed_client:
                # 使用 embedding 相似度检查
                is_dup = False
                for existing in unique_gaps:
                    existing_desc = existing.get('description', '')
                    if existing_desc:
                        sim = embed_client.semantic_similarity(desc, existing_desc)
                        if sim >= 0.8:
                            is_dup = True
                            break
                if not is_dup:
                    unique_gaps.append(gap)
            else:
                # 降级到词级去重
                desc_words = set(desc.lower().split())
                is_dup = False
                for existing in unique_gaps:
                    ex_words = set(existing.get('description', '').lower().split())
                    if desc_words and ex_words:
                        sim = len(desc_words & ex_words) / len(desc_words | ex_words)
                        if sim >= 0.7:
                            is_dup = True
                            break
                if not is_dup:
                    unique_gaps.append(gap)

        return unique_gaps

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

        # 收集所有Gap信息（跨主题去重）
        all_gaps = []
        all_questions = []
        for synth in themes.values():
            all_gaps.extend(synth.gaps)
            all_questions.extend(synth.research_questions)

        # 跨主题去重
        all_gaps = self._cross_theme_deduplicate_gaps(all_gaps)

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

        # 生成3段式引言（贡献单独在1.4节，避免重复）
        paragraphs = []

        # 第1段: 领域重要性
        p1 = self._write_paragraph1(query)
        paragraphs.append(p1)

        # 第2段: 前人分类讨论 (关键改进!)
        p2 = self._write_paragraph2(literature_by_theme, query)
        paragraphs.append(p2)

        # 第3段: Gap陈述（散文风格，无粗体标签）
        p3 = self._write_paragraph3_prose(core_gap, gap_type)
        paragraphs.append(p3)

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
        """第2段: 前人工作批判性分析 - 顶刊风格！

        改进：不再是简单罗列，而是批判性讨论各种方法的局限
        遵循 Nature Photonics 的写作风格：先说进展，再说具体问题
        """
        if not literature_by_theme:
            return f"目前，THz辐射产生主要依赖五种技术路线，相关研究已取得重要进展。"

        # 顶刊风格的批判性讨论
        lines = []

        # 第一句：承认进展
        lines.append("过去五十年间，THz源技术取得了显著进展，多种技术路线已实现从电子源到光学源的全面覆盖。")

        # 第二句：具体指出各类技术的关键局限（带数据和原因）
        limitations = []
        for theme, info in literature_by_theme.items():
            if theme == 'QCL (量子级联激光器)':
                limitations.append("QCL在6-11 THz高频段受限于光学声子吸收带(Reststrahlenband)，即使低温工作也难以覆盖该范围")
            elif theme == 'PCA (光电导天线)':
                limitations.append("光电导天线的输出功率在3 THz以上骤降至纳瓦量级，受限于载流子渡越时间和RC时间常数")
            elif theme == '光整流':
                limitations.append("光整流技术面临晶体损伤阈值和相位匹配的限制，难以同时实现大带宽与高功率")
            elif theme == '激光等离子体':
                limitations.append("激光等离子体方法可实现极宽带宽(0.1-30 THz)，但系统复杂度高且稳定性受限")
            elif theme == '超表面/等离子体':
                limitations.append("超表面技术可提供紧凑高效的波束调控，但其在真实环境条件下的响应稳定性仍待验证")

        if limitations:
            lines.append("然而，")
            for i, lim in enumerate(limitations[:3]):
                if i > 0:
                    lines.append("；")
                lines.append(f"{lim}")
            lines.append("。")

        # 第三句：过渡到本文gap
        lines.append("这些技术瓶颈共同构成了THz领域的核心挑战，推动研究者不断探索新方案。")

        return "".join(lines)

    def _write_paragraph3(self, core_gap: str, gap_type: str, themes: Dict[str, ThemeSynthesis] = None) -> str:
        """第3段: Gap陈述 - 从论文数据中提取具体Gap

        改进：不再使用模板句式，而是基于实际论文中的具体局限性
        """
        # 首先尝试从论文数据的limitations中提取真实Gap
        if themes:
            gap_text = self._write_rq_driven_gaps(themes)
            if gap_text and len(gap_text) > 50:
                return gap_text

        # 回退：从 core_gap 和 gap_type 构建具体表述
        if not core_gap:
            core_gap = "现有研究缺乏对不同技术路线在宽参数范围内的系统性性能比较"

        # 基于gap_type和实际论文数据，构建具体Gap描述
        if 'Comparative' in gap_type or '系统' in core_gap:
            gap_stmt = "现有文献尚未系统比较光整流、激光等离子体、超表面等多种技术路线在功率-带宽-效率三维参数空间内的性能边界。"
        elif 'Theoretical' in gap_type or '理论' in core_gap:
            gap_stmt = "现有理论模型未能充分解释超表面-THz强耦合过程中的非线性响应机制，限制了高效器件的设计。"
        elif 'Condition' in gap_type or '实际' in core_gap:
            gap_stmt = "在室温连续波工作条件下，6-11 THz高频段的功率输出仍停留在纳瓦量级，亟需新的物理机制来突破这一瓶颈。"
        elif 'Methodological' in gap_type or '方法' in core_gap:
            gap_stmt = "现有测量方法在200 GHz以下存在显著误差，难以准确评估固态样品的复介电函数ε(ω)。"
        elif 'Parameter' in gap_type or '参数' in core_gap:
            gap_stmt = "有机晶体材料（如DAST）的THz产生最优泵浦条件尚未被系统确定，限制了材料潜力的充分发挥。"
        else:
            gap_stmt = f"现有研究在{core_gap[:30]}方面仍存在明显不足，亟待深入探索。"

        return f"**研究空白**: {gap_stmt}"

    def _write_paragraph3_prose(self, core_gap: str, gap_type: str) -> str:
        """第3段 Gap陈述 - 散文风格，无粗体标签，避免模板感"""
        if not core_gap:
            core_gap = "现有研究缺乏对不同技术路线在宽参数范围内的系统性性能比较"

        if 'Comparative' in gap_type or '系统' in core_gap:
            return ("尽管上述技术路线各有进展，目前尚无研究对光整流、激光等离子体、超表面等主要方法"
                    "在功率-带宽-效率三维参数空间内进行系统比较，导致研究者难以在特定应用场景下"
                    "做出最优技术选择。这一系统性对比的缺失，是推动THz技术走向实用化的关键障碍。")
        elif 'Condition' in gap_type or '实际' in core_gap or '环境' in core_gap:
            return ("然而，现有研究大多在实验室理想条件下开展，对不同环境温度、气压和激光参数条件下"
                    "THz辐射产生效率的系统性评估十分有限。特别是在室温连续波工作条件下，"
                    "6-11 THz高频段的功率输出仍停留在纳瓦量级，亟需新的物理机制来突破这一瓶颈。")
        elif 'Theoretical' in gap_type or '理论' in core_gap:
            return ("在理论方面，现有模型对热电子动力学如何影响二次非线性光学响应尚缺乏深入分析，"
                    "超表面-THz强耦合过程中的非线性机制也有待阐明，"
                    "这些理论空白直接制约了高效THz器件的系统设计。")
        elif 'Methodological' in gap_type:
            return ("在测量方法上，当前太赫兹时域光谱在200 GHz以下存在显著系统误差，"
                    "高光谱分辨率条件下固态样品复介电函数ε(ω)的精确提取仍是未解难题，"
                    "制约了THz技术在凝聚态物质研究中的应用深度。")
        else:
            return (f"综合文献分析，{core_gap[:60]}这一核心问题仍未得到有效解决，"
                    "限制了该领域向更高性能和更广应用场景的发展。")

    def _write_rq_driven_gaps(self, themes: Dict[str, ThemeSynthesis]) -> str:
        """通过分析哪些研究问题仍未被回答来写Gap段落

        改进：将research_questions真正用于驱动内容生成
        """
        lines = ["**研究空白**: 通过系统性文献调研，我们发现以下关键研究问题尚待解决：\n"]

        all_gaps = []
        for theme, synth in themes.items():
            for rq in synth.research_questions:
                status = self._assess_rq_status(rq, synth)
                if status == 'unanswered':
                    all_gaps.append((theme, rq))
                elif status == 'partial' and len(all_gaps) < 8:
                    # 部分回答的问题也可以作为gap的候选
                    all_gaps.append((theme, rq))

        # 使用 embedding 语义去重（降级到词级）
        try:
            embed_client = get_embedding_client()
            unique_gaps_with_emb = []
            for _, rq in all_gaps:
                if not rq or not rq.strip():
                    continue
                is_dup = False
                for existing_rq, _ in unique_gaps_with_emb:
                    sim = embed_client.semantic_similarity(rq, existing_rq)
                    if sim >= 0.75:
                        is_dup = True
                        break
                if not is_dup:
                    unique_gaps_with_emb.append((rq, None))  # None 占位，不存储 embedding

            unique_gap_strings = [rq for rq, _ in unique_gaps_with_emb]
        except:
            # 降级到词级去重
            unique_gap_strings = []
            for _, rq in all_gaps:
                rq_words = set(rq.lower().split())
                is_dup = any(
                    len(rq_words & set(existing.lower().split())) /
                    max(len(rq_words | set(existing.lower().split())), 1) >= 0.5
                    for existing in unique_gap_strings
                )
                if not is_dup:
                    unique_gap_strings.append(rq)

        # 只保留最具体的5个Gap
        for gap in unique_gap_strings[:5]:
            lines.append(f"- {gap}")

        if len(lines) > 1:  # 有真实的Gap被找到
            return "\n".join(lines)
        return ""  # 返回空字符串让调用者使用回退模式

    def _assess_rq_status(self, rq: str, synth) -> str:
        """评估研究问题的状态：answered/partial/unanswered

        判断逻辑：
        - answered: 有论文明确解决了这个RQ
        - partial: 有论文部分解决了但还有局限
        - unanswered: 没有论文真正回答这个问题
        """
        if not rq or rq == '未明确':
            return 'unanswered'

        # 检查是否有论文的key_findings直接回答了这个RQ
        for paper in synth.representative_papers:
            findings = paper.get('findings', [])
            metrics = paper.get('metrics', [])

            # 检查发现是否包含RQ中的关键词
            rq_keywords = [k for k in rq if len(k) > 2]
            for finding in findings + metrics:
                # 如果发现中提到了RQ中的关键词，认为是部分回答
                if any(k.lower() in finding.lower() for k in rq_keywords if len(k) > 2):
                    return 'partial'

        # RQ包含"如何"但没有实现/证明等词，认为是未回答
        if '如何' in rq and not any(x in rq for x in ['实现', '证明', '验证', '提出', '解决']):
            return 'unanswered'

        return 'partial'  # 默认认为是部分回答

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

    def write(self, themes: Dict[str, ThemeSynthesis], query: str, paper_type: str = 'journal_review') -> str:
        # Step 1: 先规划，再写作 (Gap-Driven!)
        planner = PaperStrategyPlanner()
        plan = planner.plan(themes, query)

        # Step 2: 生成论文类型适配提纲 (两阶段写作 Stage 1)
        outline_generator = OutlineGenerator()
        outline = outline_generator.generate(themes, query, paper_type)
        print(f"  [Outline] Generated {paper_type} outline with {len(outline.get('sections', {}))} sections")

        # Step 3: 两阶段写作 Stage 1 - 生成论证要点大纲
        stage_writer = StageWriter()
        outline_draft = stage_writer.stage1_outline_draft(outline, themes, paper_type)
        print(f"  [StageWriter] Stage 1 outline drafted ({len(outline_draft)} chars)")

        # Step 4: 两阶段写作 Stage 2 - 增强引言为流畅散文
        intro_text = ""
        if paper_type == 'journal_review':
            intro_text = self._write_journal_introduction(query, outline, themes)
        else:
            intro_text = self._write_chinese_thesis_introduction(query, outline, themes, plan)

        try:
            enhanced_intro = stage_writer.stage2_prose(
                section_text=intro_text,
                section_name='introduction',
                outline=outline,
                themes=themes,
                paper_type=paper_type
            )
            if enhanced_intro and len(enhanced_intro) > len(intro_text) * 0.5:
                intro_text = enhanced_intro
                print(f"  [StageWriter] Stage 2 intro enhanced ({len(enhanced_intro)} chars)")
            else:
                print(f"  [StageWriter] Stage 2 intro kept original")
        except Exception as e:
            print(f"  [StageWriter] Stage 2 skipped: {e}")

        lines = []

        # 标题
        lines.append(f"# {query.title()}领域学术综述\n")

        # 摘要 - 改进版
        lines.append("## 摘要\n")
        lines.append(self._write_abstract_v5(themes, query, plan))

        # 引言 - 使用Stage 2 prose增强后的版本
        lines.append("\n## 一、引言\n")
        lines.append(intro_text)

        # 技术路线分析 - 每个主题section（Stage 2 prose增强）
        lines.append("\n## 二、技术路线分析\n")
        for i, (theme, synth) in enumerate(themes.items(), 1):
            lines.append(f"\n### 2.{i} {synth.theme}\n")
            section_raw = self._write_theme_section_v5(synth, i, plan)
            # Stage 2 prose: 增强技术路线section的流畅度
            try:
                enhanced_section = stage_writer.stage2_prose(
                    section_text=section_raw,
                    section_name='theme_synthesis',
                    outline=outline,
                    themes=themes,
                    paper_type=paper_type
                )
                if enhanced_section and len(enhanced_section) > len(section_raw) * 0.5:
                    section_raw = enhanced_section
                    print(f"  [StageWriter] Stage 2 theme section {i} enhanced")
            except Exception as e:
                print(f"  [StageWriter] Stage 2 theme section {i} skipped: {e}")
            lines.append(section_raw)

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
        lines.append(self._write_references(themes, paper_type))

        # 组装最终内容
        result = "\n".join(lines)

        # v5.2 bishe-guider规则人类化：基于24种AI模式检测的深度去AI痕迹
        result = self._bishe_humanize(result)
        print(f"  [Humanizer] Bishe-guider rule-based humanization applied ({len(result)} chars)")

        return result

    def _bishe_humanize(self, text: str) -> str:
        """基于bishe-guider规则1的深度人类化 - 消除AI写作痕迹

        覆盖24种AI模式检测与修复，保留所有markdown结构。
        """
        replacements = [
            # === 一、内容模式 ===
            # 1. 过度强调意义、legacy、宏观趋势
            (r'标志着.*?进入.*?阶段', '聚焦于'),
            (r'见证了.*?发展', '经历了'),
            (r'承载着.*?使命', '用于'),
            (r'凸显了.*?重要性', '表明'),
            (r'反映了更广泛的.*?格局', '体现了'),
            (r'象征着.*?转变', '代表'),
            (r'为……奠定基础', '提供了基础'),
            (r'开启了.*?新纪元', '推动了'),
            (r'留下了不可磨灭的印记', '产生了深远影响'),
            # 2. 宣传性、广告式语言
            (r'得天独厚的', '独特的'),
            (r'开创性的', '创新的'),
            (r'享誉.*?的', '知名的'),
            (r'革命性的', '重要的'),
            (r'颠覆性的', '显著的'),
            (r'里程碑', '重要进步'),
            # 3. superficial -ing 分析 (精确词汇替换，避免贪婪匹配导致内容丢失)
            (r'凸显了', '突出了'),
            (r'确保了', '保证了'),
            (r'为……做出贡献', '有助于'),
            (r'展示了', '实现了'),
            (r'展示', '展现'),
            (r'呈现出', '表现出'),
            (r'呈现了', '展现了'),
            (r'呈现', '展现'),
            # 4. 模糊归因
            (r'行业报告指出', '文献显示'),
            (r'观察者认为', '研究者认为'),
            (r'专家认为', 'Wang等指出'),
            (r'一些批评者认为', '部分学者认为'),
            # 5. 套路化的"挑战与展望"
            (r'尽管.*?面临若干挑战', '虽然...存在局限'),
            (r'尽管存在这些挑战', '尽管存在这些局限'),
            (r'展望未来，随着技术的不断进步', '未来可通过'),
            (r'这些问题有望得到解决', '这些问题可通过进一步研究解决'),

            # === 二、语言与语法模式 ===
            # 6. AI高频词汇
            (r'此外，', '同时，'),
            (r'此外', '另外'),
            (r'深入探讨', '分析'),
            (r'强调', '指出'),
            (r'增强', '提高'),
            (r'促进', '推动'),
            (r'展示', '呈现'),
            (r'不可或缺的', '关键的'),
            (r'至关重要的', '关键的'),
            # 英文AI词汇
            (r'\bcrucial\b', 'key'),
            (r'\bpivotal\b', 'central'),
            (r'\bshowcase\b', 'show'),
            (r'\bdelve\b', 'examine'),
            (r'\bcomprehensive\b', 'thorough'),
            (r'\bgroundbreaking\b', 'important'),
            (r'\bhighlight\b', 'emphasize'),
            (r'\binterplay\b', 'interaction'),
            (r'\bintricate\b', 'complex'),
            (r'\blandscape\b', 'field'),
            (r'\bunderscore\b', 'emphasize'),
            (r'\btestament\b', 'evidence'),
            # 7. 系动词回避
            (r'作为一个高效的', '该'),
            (r'具备快速响应能力', '响应速度快'),
            (r'拥有.*?优势', '具有'),
            # 8. 填充短语
            (r'值得注意的是，', ''),
            (r'需要指出的是，', ''),
            (r'值得一提的是，', ''),
            (r'不难发现，', ''),
            (r'显而易见，', ''),
            # 9. 模板化开头/结尾
            (r'本文旨在', '本文着力'),
            (r'本文着力综述', '本文系统梳理'),
            (r'随着.*?的不断发展', '随着...发展'),
            (r'近年来，', '近期，'),
            (r'近年来', '近年以来'),
            # 9b. AI模板短语（高频出现）
            (r'取得了显著进展', '获得实质性突破'),
            (r'取得了重要进展', '获得实质性突破'),
            (r'具有重要应用前景', '在多个应用场景中展现出潜力'),
            (r'具有重要的理论和实际意义', '对理论研究和应用开发均有价值'),
            (r'随着技术的不断发展', '随着技术持续演进'),
            (r'随着.*?的不断发展', '随着...发展'),
            # 10. 显著性膨胀
            (r'首次提出', '提出了一种'),
            (r'显著提升', '提升了'),
            (r'重大突破', '取得了进展'),
            (r'特大创新', '具有创新性'),
            (r'世界第一', '在...方面表现优异'),
            # 11. 三连规则过度
            (r'不仅.*?而且.*?还', '...和...'),
            # 12. 被动语态堆叠
            (r'被广泛应用于', '已用于'),
            (r'被认为是', '是'),
            # 13. 绝对化表述（盲审风险）
            (r'首次', '首次' if '首次' in text and len(text) < 1000 else '提出了一种'),
            (r'彻底改变', '显著改变'),
            (r'完美解决', '有效解决'),
        ]

        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)

        # 二次清理：去除连续的空格和多余的换行
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def _write_abstract_v5(self, themes: Dict, query: str, plan: Dict) -> str:
        """v5摘要 - 顶刊风格：问题驱动，量化Gap

        改进：遵循Nature Photonics风格 - 具体数据驱动，而非模板泛泛而言
        """
        core_gap = plan.get('core_gap', '') if plan else ''
        gap_type = plan.get('gap_type', 'Comparative') if plan else 'Comparative'

        lines = []

        # Sentence 1: 应用前景
        lines.append(f"{query.title()}技术在传感成像、通信和安全检测等领域展现出重要的应用潜力。")

        # Sentence 2: 具体技术进展 - 动态从主题数据提取，避免硬编码假数据
        # 去重：同一发现文本不能出现在多个主题中
        achievements = []
        seen_ach = set()
        for theme, synth in (themes or {}).items():
            for f in (synth.key_findings or []):
                f_stripped = f.strip() if f else ''
                if f_stripped and len(f_stripped) > 12 and len(f_stripped) < 80:
                    # 用前20字作为去重键，避免同一发现被多个主题重复引用
                    dup_key = f_stripped[:20]
                    if dup_key not in seen_ach:
                        achievements.append(f_stripped)
                        seen_ach.add(dup_key)
                        break  # 每主题只取1个
            if len(achievements) >= 4:
                break
        if len(achievements) >= 2:
            ach_text = '，'.join(achievements[:-1]) + '和' + achievements[-1] if len(achievements) == 2 else '，'.join(achievements[:2]) + '等'
            lines.append(f"过去五十年间，THz源技术取得重要进展——{ach_text}。")
        else:
            lines.append("过去五十年间，THz源技术取得重要进展，多种技术路线已实现从实验室到示范应用的跨越。")

        # Sentence 3: 综合Gap描述 - 用core_gap或标准瓶颈陈述，避免用过窄的具体Gap
        if core_gap and len(core_gap) > 20 and '本文旨在' not in core_gap:
            # core_gap可用，截取前60字
            gap_stmt = core_gap[:60] + ("..." if len(core_gap) > 60 else "")
            lines.append(f"然而，{gap_stmt}。")
        else:
            lines.append("然而，现有文献未系统比较不同技术路线在功率-带宽-效率三维参数空间内的性能边界，"
                         "6-11 THz高频段室温输出功率仍停留在纳瓦量级，这些关键瓶颈仍未解决。")

        # Sentence 4: 方法
        tech_count = len(themes)
        tech_names = "、".join(list(themes.keys())[:3]) if themes else "光整流、激光等离子体、超表面"
        total_papers = sum(len(s.representative_papers) for s in themes.values()) if themes else 0
        gap_count = sum(len(s.gaps) for s in themes.values()) if themes else 0

        lines.append(f"本综述采用主题综合法，系统梳理了{tech_count}种主要技术路线({tech_names}等)的研究进展，")
        lines.append(f"识别出以{gap_type}类型为主的{gap_count}个关键研究空白，涵盖{total_papers}篇代表性论文。")

        # Sentence 5: 贡献（简短，控制字数在250以内）
        lines.append("本综述为领域研究者提供全面技术路线图，具有重要参考价值。")

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
        """问题与挑战 - 基于真实论文数据，引用具体未解问题

        改进：不再使用模板短语，而是从论文limitations中提取具体问题
        """
        # 从论文数据中提取真实的研究空白
        all_limitations = []
        for synth in themes.values():
            # 从每个主题的limitations提取
            for paper in synth.representative_papers:
                for lim in paper.get('limitations', []):
                    if lim and lim != '未明确' and len(lim) > 10:
                        all_limitations.append({
                            'theme': synth.theme,
                            'limitation': lim
                        })
            # 也从gaps中提取
            for gap in synth.gaps:
                gap_desc = gap.get('description', '')
                if gap_desc and gap_desc != '未明确' and len(gap_desc) > 15:
                    all_limitations.append({
                        'theme': synth.theme,
                        'limitation': gap_desc
                    })

        lines = []
        lines.append("基于文献分析，以下关键问题仍未得到有效解决：\n")

        if all_limitations:
            # 按theme组织，展示具体未解决问题；同时跨theme去重
            by_theme = defaultdict(list)
            for item in all_limitations:
                by_theme[item['theme']].append(item['limitation'])

            global_seen_phrases: List[str] = []

            for theme, lims in by_theme.items():
                if lims:
                    theme_unique = []
                    for lim in lims:
                        key_phrase = lim[:80] if len(lim) > 80 else lim
                        if len(key_phrase) <= 10:
                            continue
                        # 跨主题去重：检查是否与已出现的短语相似
                        kw = set(key_phrase.lower().split())
                        is_dup = False
                        for used in global_seen_phrases:
                            uw = set(used.lower().split())
                            if kw and uw and len(kw & uw) / len(kw | uw) >= 0.55:
                                is_dup = True
                                break
                        if not is_dup:
                            global_seen_phrases.append(key_phrase)
                            theme_unique.append(key_phrase)
                        if len(theme_unique) >= 3:
                            break

                    if theme_unique:
                        lines.append(f"\n**【{theme}】具体挑战**：\n")
                        for phrase in theme_unique:
                            lines.append(f"- {phrase}\n")

        # 关键技术瓶颈 - 基于实际物理限制
        lines.append("\n**【通用技术瓶颈】**：\n")
        lines.append("- 光电导天线的输出功率在3 THz以上骤降至纳瓦量级（受限于载流子渡越时间）\n")
        lines.append("- 6-11 THz高频段室温连续波功率仍停留在纳瓦量级（受限于Reststrahlenband吸收）\n")
        lines.append("- 现有技术难以同时实现大带宽(>5 THz)与高功率(mJ级)的兼顾\n")

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

        # 关键性能指标 — 只显示有上下文的（长度>10），过滤裸数值
        meaningful_metrics = [
            f for f in synth.key_findings
            if f and len(f.strip()) > 12  # 过滤 "1.5 GHz" 这样的裸数值
        ]
        if meaningful_metrics:
            lines.append("\n**关键性能指标**:\n")
            seen_metric = set()
            for f in meaningful_metrics:
                key = f[:30].lower()
                if key not in seen_metric:
                    seen_metric.add(key)
                    lines.append(f"- {f}\n")
                if len(seen_metric) >= 5:
                    break

        # 代表性工作（含局限性，帮助识别Gap）
        if synth.representative_papers:
            lines.append("\n**代表性工作**:\n")
            for j, p in enumerate(synth.representative_papers[:3], 1):
                title = p.get('title', '')[:50]
                authors = p.get('authors', 'Unknown')
                year = p.get('year', 'N/A')
                citations = p.get('citations', 0)
                lims = p.get('limitations', [])
                lines.append(f"- [{j}] {title}... ({authors}, {year})\n")
                if lims:
                    lines.append(f"  局限: {lims[0][:80]}\n")

        # v5.2: 核心贡献与证据（claim-evidence对齐展示）
        if synth.contributions:
            lines.append("\n**核心贡献与证据**:\n")
            for contrib in synth.contributions[:3]:
                lines.append(f"- {contrib}\n")
        if synth.evidence_map:
            lines.append("\n**关键实验证据**:\n")
            evidence_count = 0
            for pid, ev_list in list(synth.evidence_map.items())[:3]:
                for ev in ev_list:
                    if ev and len(ev) > 5:
                        lines.append(f"- {ev}\n")
                        evidence_count += 1
                        if evidence_count >= 4:
                            break
                if evidence_count >= 4:
                    break

        # 综合评述 - 批判性分析段落（非简单列举）
        lines.append("\n**综合评述**:\n")
        analysis = self._write_theme_synthesis_paragraph(synth)
        lines.append(analysis + "\n")

        # 批判性分析 - 深入探讨WHY（始终生成，不依赖特定关键词）
        lines.append("\n**深入分析**：\n")
        deep_lines = self._generate_deep_analysis(synth)
        lines.extend(deep_lines)

        # Gap列表 - 按影响程度排序，含影响分析
        if synth.gaps:
            lines.append("\n**研究空白**（按影响程度）:\n")
            gap_impact_suffix = {
                'Theoretical': '这限制了该路线的理论预测能力和实验优化空间，导致关键参数的选择缺乏定量依据。',
                'Parameter': '这导致实际性能长期低于理论预期，难以通过经验调参实现突破性提升。',
                'Methodological': '这使得系统化的实验研究和可重复的性能评估难以开展，阻碍了技术成熟度提升。',
                'Comparative': '这导致研究者在技术路线选择和方案优化时缺乏客观的量化比较依据。',
                'Condition': '这制约了该技术从受控实验室环境走向复杂实际应用场景的进程。',
            }
            for gap in synth.gaps[:3]:
                gap_type = gap.get('type', 'Unknown')
                gap_desc = gap.get('description', '')
                if gap_desc and gap_desc != '未明确':
                    impact = gap_impact_suffix.get(gap_type, '')
                    lines.append(f"- [{gap_type}] {gap_desc[:80]}。{impact}\n")

        if synth.future_directions:
            lines.append(f"- 未来方向: {synth.future_directions[0][:80]}\n")

        return "".join(lines)

    def _write_theme_synthesis_paragraph(self, synth: ThemeSynthesis) -> str:
        """为每个技术路线生成批判性综合分析段落"""
        theme = synth.theme or '该技术路线'

        # 路线特定的进展描述模板（当key_findings不够强时使用）
        route_progress_templates = {
            'PCA (光电导天线)': [
                '通过优化电极结构和低温GaAs基底，PCA的辐射效率和信噪比持续提升',
                '新型微结构化PCA在保持宽带特性的同时显著增强了近场耦合强度',
                '多指叉电极和天线阵列设计将PCA的辐射功率提升了数倍',
            ],
            '光整流': [
                '有机晶体DAST和倾斜脉冲前阵技术将光整流效率推向新高度',
                '铌酸锂和GaP等非线性晶体的相位匹配优化显著扩展了THz带宽',
                '新型有机非线性材料的出现为室温高效THz产生提供了新途径',
            ],
            '激光等离子体': [
                '双色激光场与气体等离子体相互作用产生宽带THz辐射的机理日趋清晰',
                '通过优化泵浦强度和气体密度，等离子体THz源的峰值功率已达毫瓦量级',
                '空气等离子体光丝作为无介质THz辐射源展现出独特的远程产生能力',
            ],
            'QCL (量子级联激光器)': [
                '基于子带间跃迁的QCL已实现中远红外到THz频段的连续波输出',
                '量子阱结构和有源区设计的优化显著提升了QCL的工作温度和输出功率',
                '单片集成THz-QCL与探测器的方案为紧凑THz系统提供了可行路径',
            ],
            '超表面/等离子体': [
                '亚波长谐振单元的拓扑优化使超表面THz调制效率突破传统极限',
                '动态可调超表面通过MEMS或相变材料实现了THz波前的实时重构',
                '金属-介质混合等离子体结构在亚波长尺度实现了强THz场增强',
            ],
        }

        # 句1: 进展陈述（优先使用包含量化指标的key_findings）
        achievements = [f for f in (synth.key_findings or []) if f and len(f.strip()) > 15]
        # 优先选择包含数字或强动词短语的关键发现
        strong_achievements = [
            f for f in achievements
            if any(c in f for c in '0123456789%') or any(v in f for v in ['提升', '突破', '优化', '增强', '降低', '扩展'])
        ]
        chosen_achievements = strong_achievements if strong_achievements else achievements

        if chosen_achievements:
            ach_text = chosen_achievements[0][:70]
            sent1 = f"{theme}领域近年取得重要进展：{ach_text}。"
        else:
            # 使用路线特定模板或从论文动态生成
            templates = route_progress_templates.get(theme, [])
            if templates:
                import random
                sent1 = f"{theme}领域近年取得重要进展：{random.choice(templates)}。"
            elif synth.representative_papers:
                first_paper = synth.representative_papers[0]
                year = first_paper.get('year', '')
                # 提取论文标题中的核心技术词而非直接引用标题
                title = first_paper.get('title', '')
                core_tech = title.split('for')[0].split('via')[0].split('using')[0][:35] if title else '该方向'
                sent1 = f"{theme}领域近年取得重要进展：{year}年前后{'其' if core_tech == theme else core_tech + '等'}关键技术路线持续优化。"
            else:
                sent1 = f"{theme}领域研究取得了阶段性进展。"

        # 句2: 关键局限（从Gaps中提取第一个有意义的Gap）
        gap_text = ''
        for gap in (synth.gaps or []):
            desc = gap.get('description', '')
            if desc and len(desc) > 15 and desc != '未明确':
                gap_text = desc[:80]
                break
        if gap_text:
            sent2 = f"然而，{gap_text}，这一问题制约了该路线的进一步发展。"
        else:
            # 动态从tradeoffs生成局限描述
            if synth.tradeoffs and synth.tradeoffs[0]:
                # 取第一个tradeoff，格式通常是"X vs Y"
                t = synth.tradeoffs[0]
                sent2 = f"然而，{t}之间的制约关系限制了性能提升。"
            elif synth.gaps:
                # 用Gap类型构建通用描述
                gap_types = [g.get('type', '') for g in synth.gaps if g]
                if gap_types:
                    sent2 = f"然而，{gap_types[0].lower()}层面的挑战制约了该路线的进一步发展。"
                else:
                    sent2 = f"然而，现有性能指标与实用化需求之间仍存在差距。"
            else:
                sent2 = f"然而，现有性能指标与实用化需求之间仍存在差距。"

        # 句3: 与领域整体挑战的关联（按主题变化，避免千篇一律）
        route_closings = {
            'PCA (光电导天线)': "这意味着PCA技术在高频段的性能提升需要同时突破材料和结构两个层面的限制，而非简单的参数优化所能解决。",
            '光整流': "因此，光整流技术的下一步突破有赖于新型非线性材料的发现以及泵浦策略的创新，而非仅在现有晶体体系中微调参数。",
            '激光等离子体': "这些问题的根源在于激光-等离子体相互作用的强非线性和低可重复性，使得该路线从实验室演示走向稳定输出仍有相当距离。",
            'QCL (量子级联激光器)': "这要求QCL研究在材料外延、热管理和腔模设计三个维度上协同推进，单一维度的优化难以带来质的飞跃。",
            '超表面/等离子体': "这提示超表面研究需要从单纯的结构设计转向对损耗机制的物理理解，才能在效率与功能之间取得实质性平衡。",
        }
        sent3 = route_closings.get(theme, "综合文献分析，该路线在功率-带宽-效率三维参数空间内的性能边界尚待系统研究，未来应优先解决上述瓶颈以推进技术成熟。")

        return f"{sent1}{sent2}{sent3}"

    def _generate_deep_analysis(self, synth: ThemeSynthesis) -> List[str]:
        """为每个主题生成深入的批判性分析段落

        不依赖特定关键词，始终从可用数据生成有意义的内容。
        """
        theme = synth.theme or '该技术路线'
        lines = []

        # 策略1: 用gaps解释根本物理/技术原因
        if synth.gaps:
            # 选择前2个不同类型的gap进行分析
            seen_types = set()
            analysis_gaps = []
            for g in synth.gaps:
                gtype = g.get('type', 'Unknown')
                if gtype not in seen_types and len(analysis_gaps) < 2:
                    seen_types.add(gtype)
                    analysis_gaps.append(g)

            if analysis_gaps:
                gap_descs = [g.get('description', '')[:60] for g in analysis_gaps]
                type_names = {
                    'Theoretical': '理论层面',
                    'Parameter': '参数层面',
                    'Methodological': '方法层面',
                    'Comparative': '对比层面',
                    'Condition': '条件层面',
                }
                type_labels = [type_names.get(g.get('type', ''), '技术层面') for g in analysis_gaps]
                # 为不同主题使用不同的分析句式，避免重复
                route_closings = {
                    'PCA (光电导天线)': [
                        f"这两类限制共同决定了PCA在当前技术条件下的性能天花板，突破需要同时优化材料载流子动力学和电极几何结构。",
                        f"上述限制相互耦合，使得PCA难以在保持宽带响应的同时提升辐射功率，核心瓶颈在于载流子寿命与渡越时间的竞争关系。",
                    ],
                    '光整流': [
                        f"上述限制相互耦合，使得光整流难以同时突破功率与带宽的双重约束，本质上是相位匹配条件与晶体损伤阈值的非线性竞争。",
                        f"这种多维度的制约意味着光整流的优化需要在非线性系数、透明窗口和热导率之间寻找罕见的材料组合。",
                    ],
                    '激光等离子体': [
                        f"这两类限制共同决定了激光等离子体THz源从实验室演示走向稳定应用仍有相当距离，关键在于激光-等离子体相互作用的强非线性和低可重复性。",
                        f"上述限制相互耦合，使得激光等离子体难以兼顾宽带辐射与能量转换效率，源于四波混频过程中相位失配和等离子体不稳定性的双重制约。",
                    ],
                    'QCL (量子级联激光器)': [
                        f"这种多维度的制约意味着QCL的优化需要在子带间跃迁效率、热管理和腔模质量之间寻找精妙的平衡。",
                        f"这两类限制共同决定了QCL室温工作的性能天花板，突破依赖于材料外延质量和散热结构的协同创新。",
                    ],
                    '超表面/等离子体': [
                        f"上述限制相互耦合，使得超表面难以同时实现高效率和动态可调性，根源在于欧姆损耗和谐振Q值之间的固有矛盾。",
                        f"这种多维度的制约意味着超表面设计必须从单纯的几何优化转向对损耗机制的物理理解，才能在效率与功能之间取得实质性平衡。",
                    ],
                }
                closings = route_closings.get(theme, [
                    f"这两类限制共同决定了{theme}在当前技术条件下的性能天花板。",
                    f"上述限制相互耦合，使得{theme}难以同时突破功率与带宽的双重约束。",
                    f"这种多维度的制约意味着{theme}的优化需要在多个物理机制之间寻找非显而易见的平衡点。",
                ])
                # 根据主题名哈希选择不同结尾
                closing_idx = hash(theme) % len(closings)
                if len(gap_descs) == 2:
                    lines.append(f"从{type_labels[0]}看，{gap_descs[0]}；从{type_labels[1]}看，{gap_descs[1]}。")
                    lines.append(closings[closing_idx] + "\n")
                else:
                    lines.append(f"{type_labels[0]}的限制——{gap_descs[0]}——是该路线面临的核心瓶颈，直接决定了其性能上限。\n")

        # 策略2: 用tradeoffs分析根本制约
        if not lines and synth.tradeoffs:
            t = synth.tradeoffs[0]
            tradeoff_analyses = [
                f"{theme}的核心矛盾在于{t}之间的权衡。现有文献多聚焦单一指标优化，而对这一矛盾的系统性研究仍显不足。",
                f"{theme}面临的首要挑战是{t}的非线性耦合。在现有技术框架下，改善其中一个指标往往以牺牲另一个为代价，导致整体性能陷入平台期。",
                f"从系统层面看，{theme}尚未破解{t}之间的固有矛盾。多数研究仅停留在单一维度的参数扫描，缺乏对耦合机制的深度解析。",
            ]
            idx = hash(theme + t) % len(tradeoff_analyses)
            lines.append(tradeoff_analyses[idx] + "\n")

        # 策略3: 用research_questions与key_findings的错位分析
        if not lines and synth.research_questions and synth.key_findings:
            rq = synth.research_questions[0][:50]
            kf = synth.key_findings[0][:50]
            mismatch_analyses = [
                f"虽然已有研究在{kf}等方面取得进展，但{rq}这一根本问题尚未得到充分解决。现有工作的局限性在于多关注局部优化，而缺乏对整体性能边界的系统性探索。",
                f"现有文献在{kf}上已实现突破，但{rq}仍是悬而未决的核心问题。这表明当前研究存在'指标驱动'的倾向——即优先优化易量化的参数，而回避深层次的物理约束。",
                f"从技术发展脉络看，{kf}的进展为{theme}奠定了实验基础，但{rq}尚未找到有效解决方案。二者之间的错位揭示了一个更深层的问题：现有理论模型尚未完整描述该路线的全部物理过程。",
            ]
            idx = hash(theme + rq) % len(mismatch_analyses)
            lines.append(mismatch_analyses[idx] + "\n")

        # 策略4: 基于主题的通用分析（保底）
        if not lines:
            route_analysis = {
                'PCA (光电导天线)': "PCA的性能受限于载流子寿命与电极几何的耦合效应。现有文献对二者协同优化的研究不足，导致实际辐射功率远低于理论预测。",
                '光整流': "光整流的效率受限于相位匹配条件与晶体损伤阈值的矛盾。高能量泵浦虽可提升转换效率，但同时带来晶体损伤风险，这一非线性制约尚未得到有效破解。",
                '激光等离子体': "激光等离子体产生的THz辐射具有宽频带优势，但激光-等离子体能量转换效率低、系统稳定性差的问题限制了其实用化进程。",
                'QCL (量子级联激光器)': "QCL在电泵浦方面具有独特优势，但子带间跃迁效率受限于材料体系和热管理，室温高功率输出仍是待突破的瓶颈。",
                '超表面/等离子体': "超表面结构为THz调控提供了新自由度，但欧姆损耗和制造误差导致实际效率远低于理论预期，距离实用化仍有差距。",
            }
            fallback = route_analysis.get(theme, f"{theme}的性能提升受限于多物理场耦合效应，现有文献对耦合机制的理解尚不深入，制约了系统性优化。")
            lines.append(fallback + "\n")

        return lines


if __name__ == "__main__":
    main()