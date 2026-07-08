from pathlib import Path
import hashlib
import datetime

path = Path("release_ready/QECTOR_Workbench_src_v3.2.0.zip")
data = path.read_bytes()
lines = [
    "# QECTOR Workbench source release",
    "version: v3.2.0",
    "package: QECTOR_Workbench_src_v3.2.0.zip",
    "born: " + datetime.datetime.now().isoformat(timespec="seconds"),
    "md5: " + hashlib.md5(data).hexdigest(),
    "sha256: " + hashlib.sha256(data).hexdigest(),
    "size_bytes: " + str(len(data)),
]
Path("release_ready/artifacts/checksums.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

notes = [
    "# QECTOR Workbench v3.2.0",
    "## Release state",
    "- Packaging: source archive only; `.exe` build blocked by PyInstaller analysis isolation around `pythoncom` despite multipass HOOK/exclude repair.",
    "- Verified source checksums: `md5 " + hashlib.md5(data).hexdigest() + "`, `sha256 " + hashlib.sha256(data).hexdigest() + "`",
    "- Built-in validation: `preflight.py` reports all checks passed in `.venv`; preflight note: `hardware profile routing module unavailable` is non-fatal in the installed build.",
    "## Verified code changes",
    "- `code_explorer_tab.py`: added Circuit view mode, polished legends/titles, premium graph styling",
    "- `backend.py`: kept `list_decoder_info` / `AVAILABLE_CODE_FAMILIES` removed; added graceful routing-aware decode fallback; hardened graph layout path",
    "- `mcp_server.py`: replaced nonexistent imports with `DECODER_KINDS` and `CODE_FAMILIES`; added `mcp_status` tool",
    "- `dialogs.py`, `app.py`: refined `AboutDialog` / `SettingsDialog` / logo fallback; PR nodes won't recur; DTO removed",
]
Path("release_ready/artifacts/RELEASE_NOTES.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
print("ARTIFACTS_WRITTEN")
