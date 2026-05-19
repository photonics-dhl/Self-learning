#!/usr/bin/env python3
"""
会话结束钩子 - 自动保存讨论摘要到 Obsidian (精美排版版)
==========================================

触发时机: Claude Code 会话结束时自动调用
工作内容:
  1. 从讨论日志读取讨论内容
  2. 智能提取主题和关键概念
  3. 生成精美的Markdown笔记
  4. 自动关联已有知识树
  5. 生成可视化图表(可选)

排版特点:
  - Obsidian callout 语法 (>[!xxx])
  - Mermaid 知识图
  - LaTeX 公式支持
  - Emoji 图标增强可读性
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

# 精美笔记模板
BEAUTIFUL_NOTE_TEMPLATE = '''---
title: "{title}"
type: concept
status: {status}
field: optics
subfield: {subfield}
tags: {tags}
created: {created}
modified: {modified}
prerequisites: [{prerequisites}]
related: [{related}]
---

# {title}

> [!abstract]+ 一句话物理图像
> {physical_image}

---

## 📖 概念定义

{concept_definition}

---

## 🔬 核心原理

{core_principles}

---

## 🧠 知识关联

```mermaid
{knowledge_graph}
```

---

## 📝 关键要点

{key_points}

---

## 💡 延伸思考

{follow_up_questions}

---

## 🔗 相关笔记

{related_notes}

---

> 🏷️ 本笔记由 **Claude Code 学术大脑** 自动生成
> 📅 生成时间: {generated_date}
> 🔄 最后更新: {modified}
'''

# 简短讨论记录模板
DISCUSSION_APPEND_TEMPLATE = '''

---

### 💬 {date} 讨论摘要

> {summary}

**关键结论：**
{conclusions}
'''


def load_discussion_log() -> List[Dict]:
    """加载讨论日志"""
    if DISCUSSION_LOG.exists():
        try:
            with open(DISCUSSION_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Session Hook] Warning: Could not load discussion log: {e}")
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
            title = md_file.stem
            existing.add(title.lower())
            # 同时收集标签和主题
            try:
                content = md_file.read_text(encoding='utf-8', errors='ignore')
                # 提取子领域
                subfield_match = re.search(r'subfield:\s*(\S+)', content)
                if subfield_match:
                    existing.add(f"subfield:{subfield_match.group(1).lower()}")
            except:
                pass
    return existing


def extract_topics(discussion: str) -> List[str]:
    """从讨论中提取主题"""
    topics = []
    important_keywords = [
        '太赫兹', 'THz', '光电子学', '光电导', 'QCL', 'PCA', '量子级联',
        '辐射源', '探测', '时域光谱', 'TDS', '成像', '通信',
        '激光', '光学', '电磁波', '频谱', '纳米', '超表面', '超构表面',
        '等离子体', '表面等离激元', '非线性', '量子点', '量子阱',
        '傅里叶变换', '干涉', '相干', '调制', '调制器',
        '光子学', '光通信', '光检测', '雪崩', 'PIN',
        '半导体', 'GaAs', 'InP', 'ZnSe', 'LT-InGaAs',
        '超快', '飞秒', '皮秒', '载流子', '弛豫'
    ]
    for kw in important_keywords:
        if kw.lower() in discussion.lower():
            if kw not in topics:
                topics.append(kw)
    return topics[:5]


def extract_key_concepts(discussion: str) -> Dict[str, str]:
    """提取关键概念和定义"""
    concepts = {}

    # 提取公式（LaTeX格式）
    formula_pattern = r'\$([^$]+)\$|\\begin\{equation\}([^\\]+)\\end\{equation\}'
    formulas = re.findall(formula_pattern, discussion)
    if formulas:
        concepts['formulas'] = [f[0] or f[1] for f in formulas][:3]

    # 提取数值
    value_pattern = r'(\d+\.?\d*)\s*(nm|μm|mm|cm|THz|GHz|Hz|ps|fs|ns|μs|ms|K|V|W|mW|μm²|cm²)'
    values = re.findall(value_pattern, discussion, re.IGNORECASE)
    if values:
        concepts['values'] = [f"{v[0]} {v[1]}" for v in values[:5]]

    return concepts


def generate_physical_image(topics: List[str], discussion: str) -> str:
    """生成一句话物理图像"""
    if not topics:
        return "这是一个值得深入研究的主题。"

    topic = topics[0]

    # 针对光学领域优化的物理图像模板
    physical_images = {
        '太赫兹': '像高速摄像机捕捉分子振动一样，THz波可以揭示物质内部的集体响应模式',
        'THz': 'THz waves act like a high-speed camera capturing molecular vibrations, revealing collective response patterns inside materials',
        'QCL': '量子阱中的电子像走楼梯一样逐级下落，每一步都释放出特定频率的光子',
        '光电导': '光生载流子像闸门突然打开，让电流在半导体中瞬间涌现',
        '超表面': '人工设计的纳米天线阵，像指挥家一样精确控制光波的相位和振幅',
        '等离子体': '金属表面的自由电子像海浪一样集体振荡，将光压缩到纳米尺度',
        '非线性': '强光让材料的响应不再"听话"，产生倍频、和频等新频率的魔法',
        '时域光谱': '像用超快闪光灯照相机拍摄分子的"动作分解"',
    }

    for key, image in physical_images.items():
        if key.lower() in discussion.lower():
            return image

    return f"这个概念涉及{topic}的深入理解，是光学研究的重要基石。"


def determine_subfield(topics: List[str]) -> str:
    """根据主题确定子领域"""
    subfield_map = {
        '太赫兹': 'terahertz', 'THz': 'terahertz',
        '激光': 'laser', 'QCL': 'quantum-cascade-laser',
        '光电导': 'photoconductivity', 'PCA': 'photoconductive-antenna',
        '超表面': 'metasurface', '超构表面': 'metasurface',
        '等离子体': 'plasmonics', '表面等离激元': 'plasmonics',
        '量子': 'quantum-optics', '量子点': 'quantum-dot',
        '纳米': 'nano-optics', '非线性': 'nonlinear-optics',
        '光子学': 'photonics', '光通信': 'optical-communication'
    }
    for topic in topics:
        for key, value in subfield_map.items():
            if key.lower() in topic.lower():
                return value
    return 'general'


def format_tags(topics: List[str], subfield: str) -> str:
    """格式化标签"""
    tags = ['#optics', f'#optics/{subfield}']
    for topic in topics:
        safe_tag = topic.replace(' ', '-').replace('(', '').replace(')', '')
        if safe_tag not in tags:
            tags.append(f'#{safe_tag}')
    return ', '.join(tags)


def check_related_notes(topic: str) -> List[str]:
    """检查相关笔记，返回关联笔记列表"""
    related = []
    if VAULT_PATH.exists():
        for md_file in VAULT_PATH.rglob("*.md"):
            if md_file.stem.lower() == 'template':  # 跳过模板
                continue
            content = md_file.read_text(encoding='utf-8', errors='ignore').lower()
            if topic.lower() in content and topic.lower() not in md_file.stem.lower():
                match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if match:
                    related.append(f"[[{match.group(1)}]]")
    return list(set(related))[:5]


def generate_knowledge_graph(topics: List[str], related: List[str]) -> str:
    """生成Mermaid知识图"""
    if not topics:
        return "graph LR\n    A[讨论] --> B[待探索]"

    main_topic = topics[0]
    graph = f'graph TB\n'
    graph += f'    A["{main_topic}"]:::main\n'

    if related:
        graph += '    A -->|关联| B["相关概念"]\n'
        for i, rel in enumerate(related[:4], 1):
            clean_rel = rel.replace('[[', '').replace(']]', '')
            graph += f'    B --> C{i}["{clean_rel}"]\n'
    else:
        graph += '    A -->|相关| B["待关联笔记"]\n'

    # 添加子类
    if len(topics) > 1:
        graph += '    A -->|包含| D["子主题"]\n'
        for i, sub in enumerate(topics[1:3], 1):
            graph += f'    D --> E{i}["{sub}"]\n'

    graph += '''
    classDef main fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px
    classDef sub fill:#4ecdc4,stroke:#1a936f,stroke-width:1px'''

    return graph


def generate_note_filename(title: str) -> str:
    """生成安全的文件名"""
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    safe = safe.replace(' ', '_')[:50]
    return safe


def create_session_summary():
    """创建会话总结"""
    log = load_discussion_log()

    if not log:
        print("[Session Hook] No discussion log found")
        return

    # 解析日志格式
    full_discussion = ""
    if isinstance(log, list) and len(log) > 0:
        if "entries" in log[0]:
            full_discussion = "\n".join(
                entry.get('content', '') for entry in log[0].get('entries', [])
            )
        elif "content" in log[0]:
            full_discussion = "\n".join(entry.get('content', '') for entry in log)

    if not full_discussion.strip():
        print("[Session Hook] Empty discussion log")
        DISCUSSION_LOG.unlink(missing_ok=True)
        return

    # 提取主题
    topics = extract_topics(full_discussion)
    if not topics:
        topics = ['一般讨论']

    # 提取关键概念
    concepts = extract_key_concepts(full_discussion)

    # 生成物理图像
    physical_image = generate_physical_image(topics, full_discussion)

    # 检查是否已有相关笔记
    existing = get_existing_notes()
    title = f"讨论_{topics[0]}_{datetime.now().strftime('%Y%m%d')}"

    existing_title = None
    for note_title in existing:
        if topics[0].lower() in note_title.lower() and datetime.now().strftime('%Y%m%d') in note_title:
            existing_title = note_title
            break

    # 确定子领域
    subfield = determine_subfield(topics)
    tags = format_tags(topics, subfield)

    # 查找相关笔记
    related_notes = []
    for topic in topics:
        related_notes.extend(check_related_notes(topic))
    related_notes = list(set(related_notes))

    # 生成知识图
    knowledge_graph = generate_knowledge_graph(topics, related_notes)

    # 生成关键要点
    key_points = []
    for i, topic in enumerate(topics, 1):
        key_points.append(f"{i}. **{topic}** - 详见下方讨论")
    if concepts.get('values'):
        key_points.append(f"📊 涉及数值: {', '.join(concepts['values'])}")
    key_points_str = '\n'.join(key_points)

    # 生成延伸问题
    follow_ups = []
    for topic in topics[:3]:
        follow_ups.append(f"- {topic}的深入机制是什么？")
        follow_ups.append(f"- {topic}有哪些应用场景？")
    follow_ups_str = '\n'.join(follow_ups)

    # 相关笔记字符串
    related_str = '\n'.join(f'- {n}' for n in related_notes) if related_notes else '-暂无直接关联'

    # 内容摘要（用于追加模式）
    summary = full_discussion[:300] + "..." if len(full_discussion) > 300 else full_discussion
    conclusions = "\n".join(f"- {p}" for p in topics)

    if existing_title:
        # 追加到已有笔记
        note_path = VAULT_PATH / "0️⃣ Inbox" / f"{existing_title}.md"
        if note_path.exists():
            append_content = DISCUSSION_APPEND_TEMPLATE.format(
                date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                summary=summary,
                conclusions=conclusions
            )
            with open(note_path, 'a', encoding='utf-8') as f:
                f.write(append_content)
            print(f"[Session Hook] Appended to: {note_path}")
            DISCUSSION_LOG.unlink(missing_ok=True)
            return

    # 创建新笔记
    note_content = BEAUTIFUL_NOTE_TEMPLATE.format(
        title=title,
        status='studying',
        subfield=subfield,
        tags=tags,
        created=datetime.now().strftime('%Y-%m-%d'),
        modified=datetime.now().strftime('%Y-%m-%d'),
        prerequisites=', '.join(f'"{n}"' for n in related_notes[:2]),
        related=', '.join(f'"{n}"' for n in related_notes[:3]),
        physical_image=physical_image,
        concept_definition=f"本次讨论主要涉及: {', '.join(topics)}",
        core_principles=f"讨论涵盖了{topics[0]}相关的核心原理和应用。",
        knowledge_graph=knowledge_graph,
        key_points=key_points_str,
        follow_up_questions=follow_ups_str,
        related_notes=related_str,
        generated_date=datetime.now().strftime('%Y-%m-%d %H:%M')
    )

    note_path = VAULT_PATH / "0️⃣ Inbox" / f"{generate_note_filename(title)}.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)

    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(note_content)

    print(f"[Session Hook] Created beautiful note: {note_path}")

    # 清理讨论日志
    DISCUSSION_LOG.unlink(missing_ok=True)


def check_handoff():
    """Check if HANDOFF.md was filled — warn if not."""
    HANDOFF = PROJECT_ROOT / "HANDOFF.md"

    if not HANDOFF.exists():
        print("\n[HANDOFF] ⚠ HANDOFF.md does not exist. Next session will have no task continuity.")
        print("[HANDOFF] Consider: writing current task state before /clear.")
        return

    content = HANDOFF.read_text(encoding='utf-8', errors='ignore')

    # Check if any real content was filled into the template
    sections_filled = 0
    for section in ['## Last Task', '## Key Decisions', '## Current Blockers', '## Next Steps']:
        idx = content.find(section)
        if idx >= 0:
            next_line_start = content.find('\n', idx) + 1
            if next_line_start < len(content):
                next_line = content[next_line_start:content.find('\n', next_line_start)].strip()
                if next_line and not next_line.startswith('<!--'):
                    sections_filled += 1

    if sections_filled == 0:
        print("\n" + "=" * 60)
        print("[HANDOFF] ⚠ HANDOFF.md STILL EMPTY — NO TASK STATE SAVED")
        print("[HANDOFF] Next session will lose all task context.")
        print("[HANDOFF] Fill HANDOFF.md before /clear or session end.")
        print("=" * 60)
    elif sections_filled < 3:
        print(f"\n[HANDOFF] ⚡ Only {sections_filled}/4 sections filled — partial context saved.")
    else:
        print(f"\n[HANDOFF] ✓ HANDOFF.md populated ({sections_filled}/4 sections). Next session will resume cleanly.")


def main():
    """入口点"""
    try:
        check_handoff()
        create_session_summary()
    except Exception as e:
        print(f"[Session Hook] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
