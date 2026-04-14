#!/usr/bin/env python3
"""
会话总结钩子
============
在 Claude Code 会话结束时自动运行，生成学习总结。

使用方式:
    在 .claude/settings.json 中配置 SessionEnd hook
    或手动运行: python .claude/hooks/session-summary.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def get_recent_notes(vault_path: Path, hours: int = 24) -> List[Dict]:
    """
    获取最近修改的笔记

    Args:
        vault_path: Vault 路径
        hours: 过去几小时内的笔记

    Returns:
        笔记列表
    """
    notes = []
    cutoff = datetime.now().timestamp() - hours * 3600

    if not vault_path.exists():
        return notes

    for md_file in vault_path.rglob("*.md"):
        if md_file.stat().st_mtime > cutoff:
            rel_path = md_file.relative_to(vault_path)
            notes.append({
                'path': str(rel_path),
                'name': md_file.stem,
                'modified': datetime.fromtimestamp(md_file.stat().st_mtime).strftime('%H:%M')
            })

    return sorted(notes, key=lambda x: x['modified'], reverse=True)


def generate_summary() -> str:
    """
    生成会话总结

    Returns:
        总结文本
    """
    vault_path = Path(__file__).parent.parent / "Obsidian-Vault"

    recent_notes = get_recent_notes(vault_path)

    summary = f"""
📚 会话学习总结
============
时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📝 今日笔记 ({len(recent_notes)}篇)
"""

    if recent_notes:
        for note in recent_notes[:10]:  # 最多显示10篇
            summary += f"   - {note['name']} ({note['modified']})\n"
    else:
        summary += "   (无新笔记)\n"

    summary += """
💡 下一步建议
   1. 回顾今日所学概念
   2. 更新知识树关联
   3. 整理文献笔记
"""

    return summary


def main():
    summary = generate_summary()
    print(summary)

    # 可选：保存到文件
    summary_file = Path(__file__).parent.parent / "Obsidian-Vault" / "0️⃣ Inbox" / "session_summary.md"
    if summary_file.parent.exists():
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n---\n{summary}\n")
        print(f"\n✓ 总结已追加到: {summary_file}")


if __name__ == "__main__":
    main()
