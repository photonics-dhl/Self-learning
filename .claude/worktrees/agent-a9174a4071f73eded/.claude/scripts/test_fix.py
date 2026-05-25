"""Test fix_figure_paths functions via subprocess to avoid stdout issues."""
import sys, io, json, re, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

BASE = Path(__file__).parent.parent

# Run fix_figure_paths as subprocess with debug enabled
result = subprocess.run(
    [sys.executable, str(BASE / ".claude" / "fix_figure_paths.py")],
    capture_output=True, text=True, cwd=str(BASE)
)
print("STDOUT:")
print(result.stdout)
if result.stderr:
    print("STDERR:")
    print(result.stderr[:2000])
