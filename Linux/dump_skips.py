"""Dump every skipped test and the reason it was skipped."""
from __future__ import annotations

import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-rs", "-q", "--tb=no"],
    capture_output=True, text=True, cwd=r"D:\QECTOR APP",
)
out = result.stdout + result.stderr
print("--- Skip lines from test run ---")
for line in out.splitlines():
    if "SKIPPED" in line or "skip" in line.lower():
        print(line)
print()
print("--- Tail ---")
print("\n".join(out.splitlines()[-5:]))
