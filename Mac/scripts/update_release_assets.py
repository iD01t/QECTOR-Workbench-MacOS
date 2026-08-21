"""Refresh release asset checksums and the manifest after a rebuild.

Everything that can drift is derived at run time rather than hardcoded:

* the version comes from ``version.py``;
* the MCP tool, decoder and code-family counts are read from the live registry
  and backend, not copied from a previous release (they were last committed as
  47/13/9 while the code actually served 56/16/10);
* the artifact list is whatever is present in ``release_assets/``, so a file
  that was not rebuilt cannot silently keep an old checksum.

Usage:
    python scripts/update_release_assets.py
    python scripts/update_release_assets.py --verified "note about frozen verification"
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import version as _version  # noqa: E402

OUT = REPO / "release_assets"

#: Extensions treated as publishable artifacts, mapped to a human label.
KINDS = {
    ".zip": "release bundle zip",
    ".exe": "Windows executable",
    ".deb": "Debian package",
    ".whl": "Python wheel",
    ".AppImage": "Linux AppImage",
    ".dmg": "macOS disk image",
}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe(path: Path) -> str:
    """Best-effort human label for an artifact, from its name and extension."""
    base = KINDS.get(path.suffix, "release artifact")
    name = path.name.lower()
    if "portable" in name:
        return "Windows single-file portable"
    if "setup" in name:
        return "Windows installer"
    if "linux" in name:
        return f"Linux x64 {base}"
    if "windows" in name:
        return f"Windows x64 {base}"
    if "macos" in name or "darwin" in name:
        return f"macOS {base}"
    return base


#: Platform display order; artifacts that do not match any key land in "shared".
_PLATFORMS: list[tuple[str, str]] = [
    ("windows", "Windows x64"),
    ("linux", "Linux x64"),
    ("macos", "macOS"),
]


def platform_of(path: Path) -> str:
    """Classify an artifact into 'windows', 'linux', 'macos', or 'shared'.

    The classifier reads the filename only — no I/O — so the same file
    always lands in the same section regardless of the machine that runs
    the script.  The wheel tags are the authoritative signal for .whl
    files (``win_amd64`` vs ``manylinux``), because ``.whl`` alone is
    platform-agnostic.
    """
    name = path.name.lower()
    if path.suffix == ".exe" or "windows" in name or "win_amd64" in name:
        return "windows"
    if (path.suffix == ".deb" or path.suffix == ".appimage"
            or "linux" in name or "manylinux" in name):
        return "linux"
    if path.suffix == ".dmg" or "macos" in name or "darwin" in name:
        return "macos"
    return "shared"


def live_counts() -> tuple[str, str]:
    """Read the real tool/decoder/family counts, or say plainly that we could not."""
    try:
        import backend as be
        from mcp_server import get_mcp_server

        server = get_mcp_server()
        # MCPServer.tools is a _ToolRegistry, and the registry's own .tools is
        # the name -> spec dict. Walk down until a mapping appears; stopping at
        # the registry object is how this manifest first shipped "mcp_tools: 0"
        # beside a working 56-tool server.
        node = server
        table = None
        for _ in range(4):
            candidate = getattr(node, "tools", None)
            if isinstance(candidate, dict):
                table = candidate
                break
            if candidate is None:
                break
            node = candidate
        if table is None:
            raise RuntimeError(
                f"cannot count tools: no .tools mapping reachable from "
                f"{type(server).__name__}"
            )
        tools = len(table)
        if tools == 0:
            raise RuntimeError("tool registry reported 0 tools; refusing to record that")
        counts = (f"mcp_tools: {tools}   decoders: {len(be.DECODER_KINDS)}   "
                  f"code_families: {len(be.CODE_FAMILIES)}")
        backend_line = f"backend: qector-decoder-v3 {be.PACKAGE_VERSION}"
        return counts, backend_line
    except Exception as exc:
        return (f"mcp_tools: unavailable ({type(exc).__name__})",
                "backend: unavailable")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verified", default="",
                    help="Free-text note recording how this build was verified.")
    args = ap.parse_args(argv)

    if not OUT.exists():
        print(f"error: {OUT} does not exist")
        return 1

    files = sorted(
        (p for p in OUT.iterdir() if p.is_file() and p.suffix in KINDS),
        key=lambda p: p.name.lower(),
    )
    if not files:
        print(f"error: no publishable artifacts found in {OUT}")
        return 1

    counts, backend_line = live_counts()

    # Group artifacts by platform so a lab downloading for one OS sees only
    # its own checksums, not a flat list it must scan through.  A flat list
    # is how a Windows user once pip-installed the manylinux wheel and filed
    # a bug report.
    groups: dict[str, list[Path]] = {key: [] for key, _ in _PLATFORMS}
    groups["shared"] = []
    for path in files:
        groups[platform_of(path)].append(path)

    # Flat list (kept for backward compatibility and the top-level manifest).
    checksums: list[str] = []
    manifest = [
        "# QECTOR Workbench release manifest",
        f"version: {_version.WORKBENCH_VERSION}",
        f"generated_utc: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "decoder_provisioning: live PyPI install (portable and cross-platform)",
        backend_line,
        counts,
    ]
    if args.verified:
        manifest.append(f"frozen_verification: {args.verified}")
    manifest += ["", "artifacts:"]

    for path in files:
        sha = sha256_of(path)
        size = path.stat().st_size
        checksums.append(f"{sha}  {path.name}")
        manifest += [
            f"  - name: {path.name}",
            f"    platform: {platform_of(path)}",
            f"    kind: {describe(path)}",
            f"    sha256: {sha}",
            f"    size_bytes: {size} ({round(size / 1024 / 1024, 1)} MB)",
            f"    modified_utc: {datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec='seconds')}",
        ]

    # Sectioned checksums file: one header, one section per platform that has
    # artifacts, each section introduced by a "## <label>" line.  A platform
    # with no artifacts gets a "(not built for this release)" note so the
    # absence is explicit rather than mysterious.
    sectioned: list[str] = [
        f"# QECTOR Decoder Workbench v{_version.WORKBENCH_VERSION} — SHA-256 checksums",
        f"# Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "# Verify:    sha256sum -c checksums.txt   (or the per-platform file)",
        "",
    ]
    for key, label in _PLATFORMS:
        members = sorted(groups[key], key=lambda p: p.name.lower())
        sectioned.append(f"## {label}")
        if not members:
            sectioned.append("# (not built for this release)")
            sectioned.append("")
            continue
        for path in members:
            sectioned.append(f"{sha256_of(path)}  {path.name}")
        # Per-platform checksum file so a download page can link just one.
        (OUT / f"checksums-{key}.txt").write_text(
            "\n".join(f"{sha256_of(p)}  {p.name}" for p in members) + "\n",
            encoding="utf-8",
        )
        sectioned.append("")
    if groups["shared"]:
        sectioned.append("## Shared (cross-platform)")
        for path in sorted(groups["shared"], key=lambda p: p.name.lower()):
            sectioned.append(f"{sha256_of(path)}  {path.name}")
        sectioned.append("")

    (OUT / "checksums.txt").write_text("\n".join(sectioned) + "\n", encoding="utf-8")
    (OUT / "RELEASE_MANIFEST.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"updated checksums.txt and RELEASE_MANIFEST.txt for "
          f"v{_version.WORKBENCH_VERSION} ({len(files)} artifacts)")
    for line in checksums:
        print("  " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
