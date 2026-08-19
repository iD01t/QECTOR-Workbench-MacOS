"""generate_api_manual.py — CLI wrapper for the API reference generator.

The generator itself lives in the app tree (``api_reference.py``) so it can be
imported by the frozen builds and driven by the in-app "Export Official Docs"
button without hard-coded machine paths.  This wrapper preserves the historical
CLI contract (defaults: manuals/ + Desktop/manuals).
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api_reference import build_api_reference, main  # noqa: E402

__all__ = ["build_api_reference", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
