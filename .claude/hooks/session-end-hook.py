#!/usr/bin/env python3
"""
会话结束钩子 - 自动保存讨论摘要到 Obsidian
==========================================

触发时机: Claude Code 会话结束时自动调用
工作内容:
  1. 扫描对话中讨论的主题
  2. 检查是否已有相关笔记 (避免重复)
  3. 生成结构化摘要
  4. 更新或创建 Obsidian 笔记
  5. 关联已有知识树

依赖:
  - 已创建的 Obsidian Vault
  - Python 标准库 (无需额外安装)
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Set

# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
VAULT_PATH = PROJECT_ROOT / "Obsidian-Vault"
DISCUSSION_LOG = PROJECT_ROOT / ".claude" / "discussion_log.json"

# 笔记模板
NOTE_TEMPLATE = '''---
title: "{title}"
type: concept
status: studying
field: optics
subfield: {subfield}
tags:
{tag_block}
created: {created}
modified: {modified}

# 对话摘要
prerequisites: [{prerequisites}]
related: [{related}]
children: []

---

# {title}

## 讨论日期
{date}

## 核心概念
{concepts}

## 关键要点

{key_points}

## 知识树关联

```mermaid
{knowledge_graph}
```

## 对话记录摘要

{dialogue_summary}

## 延伸问题

{follow_up_questions}

## 相关笔记

{related_notes}

---

> 本笔记由 Claude Code 会话结束自动生成
'''


def load_discussion_log() -> List[Dict]:
    """加载讨论日志"""
    if DISCUSSION_LOG.exists():
        with open(DISCUSSION_LOG, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_discussion_log(log: List[Dict]) -> None:
    """保存讨论日志"""
    DISCUSSION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DISCUSSION_LOG, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def get_existing_notes() -> Set[str]:
    """获取已有笔记标题集合，避免重复"""
    existing = set()
    if VAULT_PATH.exists():
        for md_file in VAULT_PATH.rglob("*.md"):
            # 提取标题（去掉路径和扩展名）
            title = md_file.stem
            existing.add(title.lower())
    return existing


def extract_topics(discussion: str) -> List[str]:
    """从讨论中提取主题"""
    topics = []
    # 简单的关键词提取
    important_keywords = [
        '太赫兹', 'THz', '光电子学', '光电导', 'QCL', 'PCA',
        '辐射源', '探测', '时域光谱', '成像', '通信',
        '激光', '光学', '电磁波', '频谱', '纳米', '超表面',
        '等离子体', '非线性', '量子'
    ]
    for kw in important_keywords:
        if kw.lower() in discussion.lower():
            if kw not in topics:
                topics.append(kw)
    return topics[:5]  # 最多5个主题


def generate_note_filename(title: str) -> str:
    """生成安全的文件名"""
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    safe = safe.replace(' ', '_')[:50]
    return safe


def check_related_notes(topic: str) -> List[str]:
    """检查相关笔记，返回关联笔记列表"""
    related = []
    if VAULT_PATH.exists():
        for md_file in VAULT_PATH.rglob("*.md"):
            content = md_file.read_text(encoding='utf-8', errors='ignore').lower()
            if topic.lower() in content and topic.lower() not in md_file.stem.lower():
                # 提取标题
                match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if match:
                    related.append(f"[[{match.group(1)}]]")
    return related[:3]  # 最多3个关联


def determine_subfield(topics: List[str]) -> str:
    """根据主题确定子领域"""
    subfield_map = {
        '太赫兹': 'terahertz',
        'THz': 'terahertz',
        '激光': 'laser',
        '超表面': 'metasurface',
        '等离子体': 'plasmonics',
        '量子': 'quantum',
        '纳米': 'nano',
        '光学': 'optics'
    }
    for topic in topics:
        for key, value in subfield_map.items():
            if key.lower() in topic.lower():
                return value
    return 'general'


def format_tags(topics: List[str]) -> str:
    """格式化标签"""
    tags = ['#optics', f'#optics/{determine_subfield(topics)}']
    return '\n'.join(f'  - {t}' for t in tags)


def create_session_summary():
    """创建会话总结"""
    log = load_discussion_log()

    if not log:
        print("[Session Hook] No discussion log found")
        return

    # 合并所有讨论内容
    full_discussion = "\n".join(entry.get('content', '') for entry in log)

    # 提取主题
    topics = extract_topics(full_discussion)
    if not topics:
        topics = ['一般讨论']

    # 检查是否已有相关笔记（避免重复）
    existing = get_existing_notes()
    title = f"讨论_{topics[0]}_{datetime.now().strftime('%Y%m%d')}"

    # 如果已有相同主题的今天笔记，则更新而非创建
    existing_title = None
    for note_title in existing:
        if topics[0].lower() in note_title.lower() and datetime.now().strftime('%Y%m%d') in note_title:
            existing_title = note_title
            break

    # 生成笔记内容
    subfield = determine_subfield(topics)
    related_notes = []
    for topic in topics:
        related_notes.extend(check_related_notes(topic))
    related_notes = list(set(related_notes))[:5]

    content = NOTE_TEMPLATE.format(
        title=title if not existing_title else existing_title,
        subfield=subfield,
        tag_block=format_tags(topics),
        created=datetime.now().strftime('%Y-%m-%d'),
        modified=datetime.now().strftime('%Y-%m-%d'),
        prerequisites='""',
        related=', '.join(f'"{n}"' for n in related_notes[:2]),
        date=datetime.now().strftime('%Y-%m-%d %H:%M'),
        concepts='\n'.join(f'- {t}' for t in topics),
        key_points='\n'.join(f'{i+1}. 详见对话记录' for i in range(len(topics))),
        knowledge_graph=f'graph LR\n    A["{topics[0]}"] --> B["相关概念"]',
        dialogue_summary=f"本次讨论涉及: {', '.join(topics)}",
        follow_up_questions='\n'.join(f'- {t}的深入研究' for t in topics),
        related_notes='\n'.join(f'- {n}' for n in related_notes) if related_notes else '- 暂无直接关联'
    )

    # 保存笔记
    if existing_title:
        # 更新已有笔记
        note_path = VAULT_PATH / "0️⃣ Inbox" / f"{existing_title}.md"
        if note_path.exists():
            # 追加而非覆盖
            with open(note_path, 'a', encoding='utf-8') as f:
                f.write(f"\n\n---\n## 新增讨论 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"\n{content}")
            print(f"[Session Hook] Updated: {note_path}")
            return

    # 创建新笔记
    note_path = VAULT_PATH / "0️⃣ Inbox" / f"{generate_note_filename(title)}.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)

    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"[Session Hook] Created: {note_path}")

    # 记录本次会话
    DISCUSSION_LOG.unlink(missing_ok=True)


def main():
    """入口点 - Claude Code 会话结束时会调用"""
    try:
        create_session_summary()
    except Exception as e:
        print(f"[Session Hook] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
