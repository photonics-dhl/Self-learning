#!/usr/bin/env python
"""
Run extract_researcher_data.py for all professors that have indexed papers.
Skips those with no indexed papers.
"""
import json, sys, io, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

PROFESSOR_KEYS = [
    "baum", "chang", "gedik", "hommelhoff", "huber", "kaertner",
    "keller", "kling", "krausz", "leone", "lhuillier", "miao",
    "murnane", "nisoli", "ropers",
]

script = PROJECT_ROOT / ".claude" / "extract_researcher_data.py"

for prof in PROFESSOR_KEYS:
    out = PROJECT_ROOT / ".claude" / f"{prof}_extracted.json"
    result = subprocess.run(
        [sys.executable, str(script), "--professor", prof, "--output", str(out)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if result.returncode != 0:
        print(f"[ERR] {prof}: {result.stderr[:200]}")
    else:
        paper_count = 0
        try:
            with open(out, encoding='utf-8') as f:
                data = json.load(f)
            paper_count = data.get("paper_count", 0)
        except Exception:
            pass
        print(f"  {prof:15s}: {paper_count} papers -> {out.name} ({out.stat().st_size} bytes)")
