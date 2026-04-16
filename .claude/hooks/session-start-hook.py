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


def main():
    try:
        init_discussion_log()
    except Exception as e:
        print(f"[Session Start] Error: {e}")


if __name__ == "__main__":
    main()