#!/usr/bin/env python3
"""
可视化同步脚本
================
将 Claude Code 生成的可视化结果自动同步到 Obsidian Vault

使用方式:
    python sync_viz.py <image_path> <topic> [note_title]

示例:
    python sync_viz.py gaussian_beam.png "高斯光束" "光学基础"
    python sync_viz.py diffraction.png "衍射图样" "波动光学"
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
VAULT_PATH = PROJECT_ROOT / "Obsidian-Vault"
VIZ_DIR = VAULT_PATH / "6️⃣ 工具" / "visualizations"
METADATA_FILE = VAULT_PATH / "6️⃣ 工具" / "viz_metadata.json"


def load_metadata() -> dict:
    """加载已同步可视化元数据"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_metadata(metadata: dict) -> None:
    """保存可视化元数据"""
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def check_image_exists(topic: str) -> Optional[str]:
    """检查某主题是否已有可视化，避免重复"""
    metadata = load_metadata()
    topic_lower = topic.lower()
    for img_path, info in metadata.items():
        if topic_lower in info.get('topic', '').lower():
            return img_path
    return None


def sync_visualization(
    image_path: str,
    topic: str,
    note_title: str = "",
    description: str = ""
) -> str:
    """
    同步可视化到 Obsidian

    Returns:
        Obsidian 中可引用的语法，如 ![[path/to/image.png]]
    """
    src_path = Path(image_path)

    if not src_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # 确保目标目录存在
    VIZ_DIR.mkdir(parents=True, exist_ok=True)

    # 生成目标文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_topic = safe_topic.replace(' ', '_')[:30]
    dest_filename = f"{safe_topic}_{timestamp}{src_path.suffix}"
    dest_path = VIZ_DIR / dest_filename

    # 复制图片
    shutil.copy2(src_path, dest_path)

    # 更新元数据
    metadata = load_metadata()
    metadata[str(dest_path)] = {
        'topic': topic,
        'note_title': note_title,
        'description': description,
        'synced_at': datetime.now().isoformat(),
        'original_path': str(src_path)
    }
    save_metadata(metadata)

    # 返回 Obsidian 引用语法
    relative_path = dest_path.relative_to(VAULT_PATH)
    return f"![[{relative_path}]]"


def link_to_note(
    image_path: str,
    note_title: str,
    section: str = ""
) -> str:
    """
    生成指向特定笔记中特定章节的链接

    Args:
        image_path: 图片路径
        note_title: 目标笔记标题
        section: 章节标题（可选）

    Returns:
        完整的引用链接
    """
    # 查找对应笔记
    note_path = None
    for md_file in VAULT_PATH.rglob("*.md"):
        if note_title.lower() in md_file.stem.lower():
            note_path = md_file
            break

    if note_path and section:
        # 锚点链接
        anchor = section.lower().replace(' ', '-')
        return f"![[{note_path.relative_to(VAULT_PATH)}#{anchor}]]"

    return f"![[{note_path.relative_to(VAULT_PATH)}]]" if note_path else ""


def list_visualizations(topic: str = "") -> list:
    """列出已同步的可视化"""
    metadata = load_metadata()
    results = []

    if topic:
        topic_lower = topic.lower()
        for path, info in metadata.items():
            if topic_lower in info.get('topic', '').lower():
                results.append({
                    'path': path,
                    'topic': info.get('topic'),
                    'synced_at': info.get('synced_at')
                })
    else:
        results = [
            {'path': p, 'topic': i.get('topic'), 'synced_at': i.get('synced_at')}
            for p, i in metadata.items()
        ]

    return results


def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print("Usage: python sync_viz.py <image_path> <topic> [note_title]")
        print("       python sync_viz.py --list [topic]")
        print("       python sync_viz.py --check <topic>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == '--list':
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        viz_list = list_visualizations(topic)
        print(f"\nFound {len(viz_list)} visualization(s):")
        for v in viz_list:
            print(f"  - {v['topic']}: {v['path']}")
        return

    if cmd == '--check':
        topic = sys.argv[2] if len(sys.argv) > 2 else ""
        existing = check_image_exists(topic)
        if existing:
            print(f"[OK] Found existing visualization for '{topic}':")
            print(f"     ![[{existing}]]")
        else:
            print(f"[NEW] No existing visualization for '{topic}'")
        return

    # 同步新可视化
    image_path = sys.argv[1]
    topic = sys.argv[2]
    note_title = sys.argv[3] if len(sys.argv) > 3 else ""

    try:
        obsidian_ref = sync_visualization(image_path, topic, note_title)
        print(f"[OK] Visualization synced to Obsidian:")
        print(f"     {obsidian_ref}")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
