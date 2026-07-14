"""auto_updater.py — Automatic PyPI version check and upgrade for qector_decoder_v3.

On each boot, checks PyPI for the latest version. If newer, prompts for upgrade.
Never crashes the app — all failures are silently caught.
"""

from __future__ import annotations

import json
import sys
import threading
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

_PYPI_JSON = "https://pypi.org/pypi/qector-decoder-v3/json"
_PACKAGE = "qector-decoder-v3"


def _parse_version(v: str) -> tuple:
    """Parse a version string into a tuple of ints for comparison.

    The leading digits of each dot-separated segment are extracted, so PEP 440
    style suffixes are tolerated: "0.6.2rc1" -> (0, 6, 2).  Parsing stops at
    the first segment without leading digits ("1.2.dev3" -> (1, 2)); anything
    completely unparseable yields (0, 0, 0).
    """
    import re
    nums: list = []
    try:
        for segment in str(v).split("."):
            m = re.match(r"\s*(\d+)", segment)
            if not m:
                break
            nums.append(int(m.group(1)))
    except Exception:
        return (0, 0, 0)
    return tuple(nums) if nums else (0, 0, 0)


def _get_installed_version() -> Optional[str]:
    try:
        import qector_decoder_v3 as qd
        return getattr(qd, "__version__", None)
    except Exception:
        return None


def _fetch_latest_pypi_version(timeout: int = 5) -> Optional[str]:
    try:
        req = urllib.request.Request(_PYPI_JSON, headers={"User-Agent": "QECTOR-Workbench/3.4"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("info", {}).get("version")
    except Exception:
        return None


def check_for_update() -> Optional[str]:
    """Check PyPI for a newer version. Returns version string if update available, else None."""
    installed = _get_installed_version()
    if not installed:
        return None
    latest = _fetch_latest_pypi_version()
    if not latest:
        return None
    if _parse_version(latest) > _parse_version(installed):
        return latest
    return None


def _do_upgrade(target_version: str) -> tuple[bool, str]:
    """Attempt to upgrade the package in the background."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", f"{_PACKAGE}=={target_version}"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            return True, f"upgraded to {target_version}"
        return False, result.stderr.strip() or result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def try_upgrade(target_version: str, callback=None) -> None:
    """Upgrade in a background thread, optionally calling callback(success, msg)."""
    def _run():
        ok, msg = _do_upgrade(target_version)
        if callback:
            try:
                callback(ok, msg)
            except Exception:
                pass
    threading.Thread(target=_run, daemon=True).start()
