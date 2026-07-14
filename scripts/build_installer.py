"""Build the production release package for QECTOR Workbench.

Usage:
    python scripts/build_installer.py

Creates:
  release_assets/QectorWorkbench-v{VERSION}.zip   — portable release ZIP
  release_assets/checksums.txt                     — SHA-256 digest
  release_assets/RELEASE_MANIFEST.txt              — version/metadata

Optional (requires Inno Setup on PATH):
    python scripts/build_installer.py --inno

Compiles installer.iss and includes the resulting Setup .exe in the release.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERSION = "3.5.0"
APP_NAME = "QectorWorkbench"
DIST_DIR = REPO / "dist" / APP_NAME
RELEASE_DIR = REPO / "release_assets"
ZIP_NAME = f"{APP_NAME}-v{VERSION}.zip"
CHUNK_SIZE = 1024 * 1024


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_zip() -> Path:
    """Create the release ZIP from the PyInstaller dist folder."""
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RELEASE_DIR / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()

    extra_files = ["icon.ico", "icon.jpg", "EULA.txt", "README_v3.md"]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add all files from the dist directory
        for root, _dirs, files in os.walk(DIST_DIR):
            for fn in files:
                fpath = Path(root) / fn
                arcname = str(fpath.relative_to(DIST_DIR.parent))
                zf.write(fpath, arcname)

        # Add extra files at the root of the ZIP
        for fn in extra_files:
            fpath = REPO / fn
            if fpath.exists():
                zf.write(fpath, fn)

    print(f"Created {zip_path}  ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return zip_path


def build_inno_installer() -> Path | None:
    """Compile installer.iss with Inno Setup if ISCC is available."""
    iscc = shutil.which("ISCC")
    if not iscc:
        iscc = str(Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"))
        if not os.path.isfile(iscc):
            iscc = str(Path("C:/Program Files/Inno Setup 6/ISCC.exe"))
            if not os.path.isfile(iscc):
                print("Inno Setup (ISCC.exe) not found. Skipping installer compilation.")
                print("Install from: https://jrsoftware.org/isdl.php")
                return None

    iss_path = REPO / "installer.iss"
    result = subprocess.run([iscc, str(iss_path)], capture_output=True, text=True)
    if result.returncode != 0:
        print("Inno Setup compilation failed:")
        print(result.stdout)
        print(result.stderr)
        return None

    # Find the compiled setup exe
    setup_exe = REPO / "dist" / "QectorWorkbenchSetup.exe"
    if setup_exe.exists():
        print(f"Installer compiled: {setup_exe}  ({setup_exe.stat().st_size / 1024 / 1024:.1f} MB)")
        return setup_exe
    print("Warning: compiled setup not found at expected path.")
    return None


def write_checksums(zip_path: Path, installer_path: Path | None) -> None:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # checksums.txt
    lines = []
    lines.append(f"{sha256_of(zip_path)}  {zip_path.name}")
    if installer_path and installer_path.exists():
        lines.append(f"{sha256_of(installer_path)}  {installer_path.name}")
    (RELEASE_DIR / "checksums.txt").write_text("\n".join(lines) + "\n")

    # RELEASE_MANIFEST.txt
    manifest_lines = [
        "# QECTOR Workbench release manifest",
        f"version: {VERSION}",
        f"generated_utc: {timestamp}",
    ]
    for p in [zip_path, installer_path]:
        if p and p.exists():
            manifest_lines.append(f"file: {p.name}")
            manifest_lines.append(f"  sha256: {sha256_of(p)}")
            manifest_lines.append(f"  size_bytes: {p.stat().st_size}")
    (RELEASE_DIR / "RELEASE_MANIFEST.txt").write_text("\n".join(manifest_lines) + "\n")

    print(f"Wrote {RELEASE_DIR / 'checksums.txt'}")
    print(f"Wrote {RELEASE_DIR / 'RELEASE_MANIFEST.txt'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build QECTOR Workbench release package")
    parser.add_argument("--inno", action="store_true", help="Also compile the Inno Setup installer")
    args = parser.parse_args()

    if not DIST_DIR.exists():
        print(f"Error: dist directory not found at {DIST_DIR}")
        print("Run 'pyinstaller QectorWorkbench.spec' first")
        return 1

    print(f"Building release v{VERSION} for {APP_NAME}")
    print(f"Source: {DIST_DIR}")
    print()

    zip_path = build_zip()
    installer_path = build_inno_installer() if args.inno else None
    write_checksums(zip_path, installer_path)

    print()
    print("Release package ready:")
    print(f"  {zip_path}")
    if installer_path:
        print(f"  {installer_path}")
    print(f"  {RELEASE_DIR / 'checksums.txt'}")
    print(f"  {RELEASE_DIR / 'RELEASE_MANIFEST.txt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
