#!/usr/bin/env python
"""
学术论文 RAG 系统 - 主程序入口

Usage:
    python run_rag.py index <pdf_path> [--domain] [--subfield]
    python run_rag.py search <query> [--domain] [--subfield]
    python run_rag.py find-figure <concept> [--domain] [--subfield]
    python run_rag.py list
    python run_rag.py stats
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from academic_rag.cli.rag_cli import main

if __name__ == "__main__":
    sys.exit(main())
