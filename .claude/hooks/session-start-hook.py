#!/usr/bin/env python3
"""
会话开始钩子 - 初始化讨论日志
============================

触发时机: Claude Code 会话开始时自动调用
工作内容:
  1. 初始化新的讨论日志文件
  2. 记录会话开始时间
  3. 清理旧日志（保留最近一次）

依赖:
  - Python 标准库 (无需额外安装)
"""

import json
from pathlib import Path
from datetime import datetime


def init_discussion_log():
    """初始化讨论日志"""
    PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
    DISCUSSION_LOG = PROJECT_ROOT / ".claude" / "discussion_log.json"

    # 初始化空日志
    initial_log = [{
        "session_start": datetime.now().isoformat(),
        "entries": []
    }]

    DISCUSSION_LOG.parent.mkdir(parents=True, exist_ok=True)

    with open(DISCUSSION_LOG, 'w', encoding='utf-8') as f:
        json.dump(initial_log, f, ensure_ascii=False, indent=2)

    print(f"[Session Start] Discussion log initialized: {DISCUSSION_LOG}")


def print_handoff():
    """Print HANDOFF.md content for session continuity."""
    PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
    HANDOFF = PROJECT_ROOT / "HANDOFF.md"

    if not HANDOFF.exists():
        print("\n[HANDOFF] No HANDOFF.md found. New session with no prior context.")
        return

    content = HANDOFF.read_text(encoding='utf-8', errors='ignore')

    # Check if HANDOFF is empty template (no actual content filled)
    sections_filled = False
    for section in ['## Last Task', '## Key Decisions', '## Current Blockers', '## Next Steps']:
        # Find section and check if next line has non-empty content
        idx = content.find(section)
        if idx >= 0:
            next_line_start = content.find('\n', idx) + 1
            if next_line_start < len(content):
                next_line = content[next_line_start:content.find('\n', next_line_start)].strip()
                if next_line and not next_line.startswith('<!--'):
                    sections_filled = True
                    break

    if not sections_filled:
        print("\n[HANDOFF] HANDOFF.md exists but is empty — no prior task state recorded.")
        return

    # Print HANDOFF summary (first 2000 chars, key sections only)
    summary = content[:2000]
    print("\n" + "=" * 60)
    print("[HANDOFF] Prior session state:")
    print("=" * 60)
    print(summary)
    if len(content) > 2000:
        print(f"... (truncated, {len(content)} total chars)")
    print("=" * 60)


def main():
    try:
        init_discussion_log()
        print_handoff()
    except Exception as e:
        print(f"[Session Start] Error: {e}")


if __name__ == "__main__":
    main()