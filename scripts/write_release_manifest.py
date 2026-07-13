"""Write release checksums and a factual release manifest for a built zip.

Usage:
    python scripts/write_release_manifest.py --version 3.5.0 --zip dist/QectorWorkbench.zip

Computes the SHA-256 digest and byte size of the given zip, then writes
``checksums.txt`` and ``RELEASE_MANIFEST.txt`` next to it. Every value in the
output is measured from the actual file at run time; nothing is hardcoded.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

_CHUNK_SIZE = 1024 * 1024


def sha256_of_file(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*, streamed in chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="write_release_manifest",
        description=(
            "Compute SHA-256 and size of a release zip, then write "
            "checksums.txt and RELEASE_MANIFEST.txt next to it."
        ),
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Release version string recorded in the manifest (e.g. 3.5.0).",
    )
    parser.add_argument(
        "--zip",
        dest="zip_path",
        required=True,
        type=Path,
        metavar="PATH",
        help="Path to the built release zip archive.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    zip_path: Path = args.zip_path

    if not zip_path.is_file():
        print(f"error: release zip not found: {zip_path}", file=sys.stderr)
        return 2

    try:
        sha256 = sha256_of_file(zip_path)
        size_bytes = zip_path.stat().st_size
    except OSError as exc:
        print(f"error: could not read {zip_path}: {exc}", file=sys.stderr)
        return 2

    out_dir = zip_path.resolve().parent
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    checksums_path = out_dir / "checksums.txt"
    manifest_path = out_dir / "RELEASE_MANIFEST.txt"

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        checksums_path.write_text(f"{sha256}  {zip_path.name}\n", encoding="utf-8")
        manifest_path.write_text(
            "\n".join(
                [
                    "# QECTOR Workbench release manifest",
                    f"version: {args.version}",
                    f"package: {zip_path.name}",
                    f"generated_utc: {generated_at}",
                    f"sha256: {sha256}",
                    f"size_bytes: {size_bytes}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"error: could not write manifest files in {out_dir}: {exc}", file=sys.stderr)
        return 2

    print(f"wrote {checksums_path}")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
