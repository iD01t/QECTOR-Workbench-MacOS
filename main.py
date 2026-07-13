"""main.py — QECTOR Decoder Workbench entry point for the PyInstaller build.

PyInstaller executes this module as ``__main__`` inside the frozen app, so the
``__main__`` guard below still launches the GUI in the packaged EXE while
keeping ``import main`` side-effect free for tests and tooling.
"""
import multiprocessing
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if "--mcp" in sys.argv:
        from mcp_server import main as mcp_main
        mcp_main()
    else:
        from app import main
        main()
