

1\. Full local verification — pytest, ruff, mypy, bandit, test\_mcp\_all.py — with real counts.

2\. Launch the actual app to confirm the tabs render and the graphs draw (not just that tests pass).

3\. Rebuild the EXE via PyInstaller so the shipped binary is the real multi-tab app, not the empty-window build.

4\. Fix git so the repo finally contains the product: remove \*.py from ignore, untrack the 40 MB binary, and commit the source locally

