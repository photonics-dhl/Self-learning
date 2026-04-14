#!/usr/bin/env python3
"""
Zotero 文献引用脚本
====================
访问本地 Zotero 数据库，搜索文献并生成引用

功能:
  1. 搜索本地 Zotero SQLite 数据库
  2. 生成 Obsidian 可用的 cite key 格式
  3. 获取文献附件路径
  4. 反向关联：笔记中的引用 → Zotero

使用方式:
    python zotero_ref.py search "keywords"
    python zotero_ref.py info "cite_key"
    python zotero_ref.py attach "cite_key"

依赖:
    - Python 3.8+ (标准库，无需额外安装)
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Windows UTF-8 fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


# ============== 路径配置 ==============

ZOTERO_PATH = Path("E:/PostGraduate/Science_softwares/Zotero")
ZOTERO_DB = ZOTERO_PATH / "data" / "zotero.sqlite"
ZOTERO_STORAGE = ZOTERO_PATH / "data" / "storage"
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
VAULT_PATH = PROJECT_ROOT / "Obsidian-Vault"


# ============== 字段 ID 常量 ==============

FIELD_TITLE = 1
FIELD_ABSTRACT = 2
FIELD_DATE = 6
FIELD_DOI = 59
FIELD_URL = 13
FIELD_PUBLISHER = 23
FIELD_JOURNAL = 38
FIELD_PAGES = 32
FIELD_VOLUME = 19
FIELD_ISSUE = 76


# ============== 核心函数 ==============

def get_connection():
    """获取 Zotero 数据库连接"""
    if not ZOTERO_DB.exists():
        raise FileNotFoundError(f"Zotero database not found: {ZOTERO_DB}")
    return sqlite3.connect(ZOTERO_DB)


def get_item_data(item_id: int, conn: sqlite3.Connection) -> Dict:
    """获取单条文献的完整数据"""
    cursor = conn.cursor()

    # 获取所有字段数据
    cursor.execute("""
        SELECT id.fieldID, idv.value
        FROM itemData id
        JOIN itemDataValues idv ON id.valueID = idv.valueID
        WHERE id.itemID = ?
    """, (item_id,))

    data = {}
    for field_id, value in cursor.fetchall():
        data[field_id] = value

    return data


def search_items(query: str, max_results: int = 10) -> List[Dict]:
    """
    搜索 Zotero 文献

    Args:
        query: 搜索关键词
        max_results: 最大返回数量

    Returns:
        文献列表
    """
    results = []
    conn = get_connection()
    cursor = conn.cursor()

    # 搜索标题和摘要
    cursor.execute("""
        SELECT DISTINCT i.itemID, i.key, i.dateAdded
        FROM items i
        JOIN itemData id ON i.itemID = id.itemID
        JOIN itemDataValues idv ON id.valueID = idv.valueID
        WHERE (id.fieldID = ? AND idv.value LIKE ?)
           OR (id.fieldID = ? AND idv.value LIKE ?)
        LIMIT ?
    """, (FIELD_TITLE, f'%{query}%', FIELD_ABSTRACT, f'%{query}%', max_results))

    item_ids = cursor.fetchall()

    for item_id, key, date_added in item_ids:
        data = get_item_data(item_id, conn)

        # 获取作者
        cursor.execute("""
            SELECT c.firstName, c.lastName, ct.creatorType
            FROM creators c
            JOIN itemCreators ic ON c.creatorID = ic.creatorID
            JOIN creatorTypes ct ON ic.creatorTypeID = ct.creatorTypeID
            WHERE ic.itemID = ?
        """, (item_id,))

        authors = []
        for first, last, ctype in cursor.fetchall():
            if last:
                authors.append(last if not first else f"{first} {last}")

        results.append({
            'key': key,
            'title': data.get(FIELD_TITLE, 'Unknown Title'),
            'abstract': data.get(FIELD_ABSTRACT, ''),
            'date': data.get(FIELD_DATE, ''),
            'doi': data.get(FIELD_DOI, ''),
            'url': data.get(FIELD_URL, ''),
            'journal': data.get(FIELD_JOURNAL, ''),
            'publisher': data.get(FIELD_PUBLISHER, ''),
            'authors': authors,
            'author_str': ', '.join(authors[:3]) + (' et al.' if len(authors) > 3 else ''),
        })

    conn.close()
    return results


def get_item_by_key(cite_key: str) -> Optional[Dict]:
    """
    通过 cite key 获取文献

    Args:
        cite_key: 如 "Zhang2024" 或完整 key

    Returns:
        文献数据或 None
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 通过 key 查找 itemID
    cursor.execute("""
        SELECT itemID FROM items WHERE key = ?
    """, (cite_key,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    item_id = row[0]
    data = get_item_data(item_id, conn)

    # 获取作者
    cursor.execute("""
        SELECT c.firstName, c.lastName
        FROM creators c
        JOIN itemCreators ic ON c.creatorID = ic.creatorID
        WHERE ic.itemID = ?
    """, (item_id,))

    authors = []
    for first, last in cursor.fetchall():
        if last:
            authors.append(last if not first else f"{first} {last}")

    conn.close()

    return {
        'key': cite_key,
        'itemID': item_id,
        'title': data.get(FIELD_TITLE, ''),
        'abstract': data.get(FIELD_ABSTRACT, ''),
        'date': data.get(FIELD_DATE, ''),
        'doi': data.get(FIELD_DOI, ''),
        'url': data.get(FIELD_URL, ''),
        'journal': data.get(FIELD_JOURNAL, ''),
        'authors': authors,
    }


def get_attachment_path(item_id: int) -> Optional[str]:
    """获取文献附件路径 (PDF)"""
    conn = get_connection()
    cursor = conn.cursor()

    # 查找 PDF 附件
    cursor.execute("""
        SELECT path, contentType
        FROM itemAttachments
        WHERE parentItemID = ?
        AND contentType = 'application/pdf'
        LIMIT 1
    """, (item_id,))

    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        # path 格式是 "storage:filename.pdf"
        storage_path = row[0].replace('storage:', '')
        full_path = ZOTERO_STORAGE / storage_path
        if full_path.exists():
            return str(full_path)

    return None


def format_obsidian_citation(item: Dict) -> str:
    """
    格式化 Obsidian 引用

    Args:
        item: 文献数据字典

    Returns:
        Obsidian 格式的引用字符串
    """
    key = item.get('key', '')
    title = item.get('title', 'Unknown')
    authors = item.get('author_str', '')
    date = item.get('date', '')[:4] if item.get('date') else ''
    journal = item.get('journal', '')
    doi = item.get('doi', '')

    # Obsidian 内部引用格式
    cite_ref = f"[[cite:@{key}]]"

    # 完整引用
    citation = f"**{authors} ({date})**. *{title}*"
    if journal:
        citation += f". {journal}"
    if doi:
        citation += f". DOI: [{doi}](https://doi.org/{doi})"

    # PDF 链接 (如果有)
    attach_path = get_attachment_path(item.get('itemID', 0))
    if attach_path:
        citation += f"\n📄 [PDF](file://{attach_path.replace(chr(92), '/')})"

    return f"{cite_ref}\n{citation}"


def format_bibtex(item: Dict) -> str:
    """生成 BibTeX 格式"""
    authors = ' and '.join(item.get('authors', []))
    key = item.get('key', 'Unknown')

    lines = [
        "@article{" + key + ",",
        "  title = {" + item.get('title', '') + "},",
        "  author = {" + authors + "},",
    ]

    if item.get('date'):
        lines.append("  year = {" + item.get('date')[:4] + "},")
    if item.get('journal'):
        lines.append("  journal = {" + item.get('journal') + "},")
    if item.get('doi'):
        lines.append("  doi = {" + item.get('doi') + "},")

    lines.append("}")
    return '\n'.join(lines)


# ============== CLI 接口 ==============

def cmd_search(query: str, max_results: int = 10):
    """搜索文献"""
    print(f"\n🔍 搜索 Zotero: '{query}'\n")

    results = search_items(query, max_results)

    if not results:
        print(f"[无结果] 未找到与 '{query}' 相关的文献")
        return

    print(f"找到 {len(results)} 篇文献:\n")

    for i, item in enumerate(results, 1):
        print(f"{i}. {item['author_str']} ({item['date'][:4] if item['date'] else '?'})")
        print(f"   {item['title']}")
        if item.get('journal'):
            print(f"   [{item['journal']}]")
        print(f"   Key: {item['key']}")
        if item.get('doi'):
            print(f"   DOI: {item['doi']}")
        print()


def cmd_info(cite_key: str):
    """显示文献详情"""
    item = get_item_by_key(cite_key)

    if not item:
        print(f"[错误] 未找到文献: {cite_key}")
        return

    print(f"\n📄 {item['title']}\n")
    print(f"作者: {', '.join(item['authors'])}")
    print(f"年份: {item['date'][:4] if item['date'] else '未知'}")
    print(f"期刊: {item['journal'] or '未知'}")
    print(f"DOI: {item['doi'] or '无'}")
    print(f"Key: {item['key']}")

    if item.get('abstract'):
        print(f"\n摘要:\n{item['abstract'][:500]}...")

    # 附件
    attach = get_attachment_path(item.get('itemID'))
    if attach:
        print(f"\n📎 附件: {attach}")
    else:
        print(f"\n📎 附件: 无")

    print(f"\n---")
    print(format_obsidian_citation(item))


def cmd_add_to_note(cite_key: str, note_path: str = None):
    """添加引用到笔记"""
    item = get_item_by_key(cite_key)

    if not item:
        print(f"[错误] 未找到文献: {cite_key}")
        return

    citation = format_obsidian_citation(item)

    if note_path:
        # 追加到指定笔记
        with open(note_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{citation}")
        print(f"[OK] 已添加到: {note_path}")
    else:
        print(citation)


def main():
    if len(sys.argv) < 2:
        print("""
Zotero 文献引用工具
==================

用法:
    python zotero_ref.py search <关键词>    # 搜索文献
    python zotero_ref.py info <cite_key>   # 查看文献详情
    python zotero_ref.py add <cite_key>     # 格式化引用
    python zotero_ref.py bibtex <cite_key>  # 生成 BibTeX

示例:
    python zotero_ref.py search terahertz
    python zotero_ref.py info Zhang2024
    python zotero_ref.py bibtex @Smith2023
        """)
        return

    cmd = sys.argv[1]

    if cmd == 'search':
        query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''
        if not query:
            print("[错误] 请提供搜索关键词")
            return
        cmd_search(query)

    elif cmd == 'info':
        key = sys.argv[2] if len(sys.argv) > 2 else ''
        if not key:
            print("[错误] 请提供 cite key")
            return
        cmd_info(key)

    elif cmd == 'add':
        key = sys.argv[2] if len(sys.argv) > 2 else ''
        note = sys.argv[3] if len(sys.argv) > 3 else None
        if not key:
            print("[错误] 请提供 cite key")
            return
        cmd_add_to_note(key, note)

    elif cmd == 'bibtex':
        key = sys.argv[2] if len(sys.argv) > 2 else ''
        if not key:
            print("[错误] 请提供 cite key")
            return
        item = get_item_by_key(key)
        if item:
            print(format_bibtex(item))

    else:
        print(f"[错误] 未知命令: {cmd}")


if __name__ == "__main__":
    main()
