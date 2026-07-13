"""utils.py — Shared utility functions for QECTOR Workbench."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def get_data_dir() -> Path:
    """Return the per-user writable data directory for the workbench.

    Resolution order: the QECTOR_DATA_DIR environment variable when set, else
    %LOCALAPPDATA%/QectorWorkbench on Windows, else ~/.qector_workbench.  The
    directory is created on demand; any candidate that cannot be created is
    skipped and the fallback chain ends at the current working directory.
    Never raises.
    """
    candidates: list[Path] = []
    try:
        override = os.environ.get("QECTOR_DATA_DIR", "").strip()
        if override:
            candidates.append(Path(override))
    except Exception:
        pass
    try:
        if os.name == "nt":
            local_appdata = os.environ.get("LOCALAPPDATA", "").strip()
            if local_appdata:
                candidates.append(Path(local_appdata) / "QectorWorkbench")
            else:
                candidates.append(Path.home() / "AppData" / "Local" / "QectorWorkbench")
        else:
            candidates.append(Path.home() / ".qector_workbench")
    except Exception:
        pass
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            if candidate.is_dir():
                return candidate
        except Exception:
            continue
    try:
        return Path.cwd()
    except Exception:
        return Path(".")


def get_export_dir() -> Path:
    """Return the per-user export directory (get_data_dir()/"exports").

    Created on demand; if creation fails the (existing) data directory itself
    is returned.  Never raises.
    """
    data_dir = get_data_dir()
    export_dir = data_dir / "exports"
    try:
        export_dir.mkdir(parents=True, exist_ok=True)
        return export_dir
    except Exception:
        return data_dir


def validate_int(val: str, min_val: int = 0, max_val: int = 100) -> tuple[bool, str]:
    """Validate that a string represents an integer in [min_val, max_val]."""
    try:
        n = int(val)
        if n < min_val or n > max_val:
            return False, f"value {n} out of range [{min_val}, {max_val}]"
        return True, ""
    except (ValueError, TypeError):
        return False, f"invalid integer: {val!r}"


def format_number(num: float, precision: int = 2) -> str:
    """Format a number to a given precision."""
    return f"{num:.{precision}f}"


def safe_write_file(path: Any, content: str) -> tuple[bool, str]:
    """Atomically write content to a file, creating parent directories."""
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(p)
        return True, ""
    except Exception as e:
        return False, str(e)
