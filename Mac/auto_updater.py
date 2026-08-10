"""auto_updater.py — Automatic PyPI version check and upgrade for qector_decoder_v3.

On each boot, checks PyPI for the latest version. If newer, prompts for upgrade.
Never crashes the app — all failures are silently caught.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import urllib.request
import urllib.error
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
        import importlib
        qd = importlib.import_module("qector_decoder_v3")
        return getattr(qd, "__version__", None)
    except Exception:
        return None


def _fetch_latest_pypi_version(timeout: int = 5) -> Optional[str]:
    # Only ever contact the fixed https PyPI endpoint; reject any other scheme
    # (file:/ftp:/custom) defensively before opening the connection.
    if not _PYPI_JSON.lower().startswith("https://"):
        return None
    try:
        req = urllib.request.Request(_PYPI_JSON, headers={"User-Agent": "QECTOR-Workbench/3.4"})
        if req.type != "https":
            return None
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - scheme pinned to https above
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


def _is_frozen() -> bool:
    """True when running from a packaged build (PyInstaller / AppImage / .deb)."""
    return bool(getattr(sys, "frozen", False))


def upgrade_instructions(latest: str) -> str:
    """Return upgrade guidance appropriate to how the app was installed.

    Decoder wheels are managed independently from the workbench bundle.  A
    packaged app uses an ABI-compatible system CPython discovered at launch;
    source runs use their own interpreter.
    """
    return (
        f"qector_decoder_v3 {latest} is available on PyPI. QECTOR will install "
        "it into its managed per-user decoder site; restart after completion."
    )


def _do_upgrade(target_version: str) -> tuple[bool, str]:
    """Upgrade through the managed-site provisioner, never the app bundle."""
    try:
        import decoder_provisioner
        result = decoder_provisioner.ensure(
            prefer_latest=True, target_version=target_version,
        )
        return bool(result.get("ok")), str(result.get("message", "unknown provisioning result"))
    except Exception as exc:
        return False, str(exc)


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


# ---------------------------------------------------------------------------
# Unified push-update surface (app + backend)
#
# Live version resolution is delegated to :mod:`version_service` (cached, both
# the backend *and* the workbench app package), while the actual upgrade action
# stays here.  Used by the GUI "Check for updates / Update now" flow and the MCP
# check_updates / version_info tools.  Everything here is bulletproof: no call
# raises for control flow.
# ---------------------------------------------------------------------------

def check_app_update() -> Optional[str]:
    """Latest workbench app version on PyPI if newer than the local build, else None."""
    try:
        import version_service
        info = version_service.get_app_version_info()
        return info.get("latest") if info.get("update_available") else None
    except Exception:
        return None


def boot_update_summary(refresh: bool = False) -> dict:
    """Combined app + backend update summary for boot / on-demand checks.

    Returns a plain, JSON-serialisable dict describing both components, whether
    each has an update available and the managed installer availability on this host.
    Never raises.
    """
    frozen = _is_frozen()
    pip_upgrade_supported = False
    try:
        import decoder_provisioner
        pip_upgrade_supported = bool(decoder_provisioner.self_check().get("pip_available"))
    except Exception:
        pass
    backend: dict = {"package": _PACKAGE, "installed": _get_installed_version(),
                     "latest": None, "update_available": False}
    app: dict = {"latest": None, "update_available": False}
    try:
        import version_service
        report = version_service.get_version_report(refresh=refresh)
        backend.update({
            "installed": report["backend"].get("installed"),
            "latest": report["backend"].get("latest"),
            "update_available": report["backend"].get("update_available", False),
        })
        app.update({
            "package": report["app"].get("package"),
            "local": report["app"].get("local"),
            "latest": report["app"].get("latest"),
            "update_available": report["app"].get("update_available", False),
        })
    except Exception:
        # Fall back to the local backend-only check if version_service is broken.
        latest = check_for_update()
        if latest:
            backend["latest"] = latest
            backend["update_available"] = True

    instructions = None
    if backend["update_available"] and backend.get("latest"):
        instructions = upgrade_instructions(backend["latest"])
    return {
        "frozen_build": frozen,
        "pip_upgrade_supported": pip_upgrade_supported,
        "backend": backend,
        "app": app,
        "any_update": bool(backend["update_available"] or app["update_available"]),
        "instructions": instructions,
    }


def perform_backend_update(callback=None, target_version: Optional[str] = None) -> dict:
    """Push (install) the latest decoder backend from PyPI in the background.

    On a source install this runs ``pip install --upgrade`` to ``target_version``
    (or the current PyPI latest) on a daemon thread and reports via ``callback``.
    On a frozen build an in-place upgrade is impossible, so it returns a status
    dict with release-update instructions and never touches pip.
    """
    target = target_version or check_for_update()
    if not target:
        return {"started": False, "frozen": False,
                "message": "already up to date (no newer backend on PyPI)"}
    try_upgrade(target, callback=callback)
    return {"started": True, "frozen": _is_frozen(), "target_version": target,
            "message": f"upgrading {_PACKAGE} to {target} in the background"}


def _auto_upgrade_enabled() -> bool:
    """Whether boot-time auto-upgrade is enabled (default on; env opt-out)."""
    return os.environ.get("QECTOR_AUTO_UPGRADE", "1").strip().lower() in ("1", "true", "yes", "on")


def auto_upgrade_on_boot(callback=None) -> dict:
    """Keep the app on the latest live PyPI decoder backend, automatically.

    On boot, if a newer ``qector-decoder-v3`` is published, upgrade to it in the
    background so the app always runs — and re-versions itself to — the latest
    live release (e.g. adopting 0.6.7 the first boot after it ships).  The new
    wheel loads on the next launch, at which point the app reports the new
    version everywhere.  No-op on frozen builds (the backend is bundled) and when
    already current.  Disable with ``QECTOR_AUTO_UPGRADE=0``.  Never raises.
    """
    if not _auto_upgrade_enabled():
        return {"attempted": False, "reason": "disabled via QECTOR_AUTO_UPGRADE"}
    try:
        latest = check_for_update()
    except Exception as e:
        return {"attempted": False, "reason": f"update check failed: {e}"}
    if not latest:
        return {"attempted": False, "reason": "already on the latest live PyPI decoder version"}
    try_upgrade(latest, callback=callback)
    return {"attempted": True, "target_version": latest,
            "message": f"auto-upgrading {_PACKAGE} to {latest} in the background; "
                       "restart to load the new version"}
