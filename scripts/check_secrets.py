"""scripts/check_secrets.py — Secret detection script for CI.

Scans the repository for hardcoded secrets, private keys, or API tokens.

Tuning notes
------------
The generic secret pattern is anchored on a word boundary (``\\b``) so that
.NET-mangled identifiers such as ``publicKeyToken="..."`` in PyInstaller's
``.toc`` files do not trip it. Build artifacts (PyInstaller ``.toc``, frozen
``work/`` trees, ``release_build/``) are excluded by directory and by
extension; if a future build type is added, extend the relevant set rather
than weakening the regex.
"""
import os
import re
import sys
from pathlib import Path

# Common patterns for secrets. The generic pattern requires a word boundary
# on both ends so that words like ``publicKeyToken`` (a .NET runtime token,
# not a secret) do not match.
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN (?:RSA |OPENSSH |DSA |EC |PGP )?PRIVATE KEY-----"), "Private Key"),
    (re.compile(r"\bsk_test_[0-9a-zA-Z]{24}\b"), "Stripe Test Key"),
    (re.compile(r"\bsk_live_[0-9a-zA-Z]{24}\b"), "Stripe Live Key"),
    (re.compile(r"\bghp_[0-9a-zA-Z]{36}\b"), "GitHub Personal Access Token"),
    (re.compile(r"\bxoxb-[0-9]{11}-[0-9]{11}-[0-9a-zA-Z]{24}\b"), "Slack Bot Token"),
    # Word boundary on the keyword prevents ``publicKeyToken``, ``tokenType``
    # and similar non-secret identifiers from triggering a false positive.
    (re.compile(
        r"\b(?:api[_-]?key|apikey|secret|token|password|passwd|pwd)\b"
        r"[\s:='\"]+"
        r"['\"][A-Za-z0-9_\-./+]{16,}['\"]"
    ), "Generic Secret Assignment"),
]

# Excluded directories (build artefacts, vendored wheels, docs, venvs).
EXCLUDE_DIRS = {
    ".git", ".venv", "__pycache__", "node_modules",
    "dist", "build", "wheels", "release_assets", "docs", "manuals",
    # PyInstaller intermediate trees: build artefacts from build_production.py
    # and verify_frozen_mcp.py. They contain .toc files with .NET runtime
    # token strings that the generic pattern must not flag.
    "release_build", "work", "work-final",
}
# Excluded extensions (binary artefacts and pre-built wheels).
EXCLUDE_EXTS = {
    ".pdf", ".exe", ".zip", ".whl", ".png", ".jpg", ".svg", ".ico",
    ".dmg", ".pkg", ".deb", ".app", ".msi", ".appimage",
    # PyInstaller table-of-contents: every frozen .toc contains string
    # references that match a naive "token=" regex.
    ".toc",
}


def scan_file(path: Path) -> list[str]:
    violations = []
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return violations
    for idx, line in enumerate(content.splitlines(), 1):
        # Skip test files when evaluating generic secrets: tests often
        # include literal strings (e.g. a fake API key) that are not real
        # credentials.
        is_test = "test" in path.name
        for pattern, name in SECRET_PATTERNS:
            if name == "Generic Secret Assignment" and is_test:
                continue
            if pattern.search(line):
                violations.append(f"{path}:{idx} -> Possible {name}")
    return violations


def main() -> int:
    root = Path(__file__).parent.parent
    all_violations: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            p = Path(dirpath) / f
            if p.suffix.lower() in EXCLUDE_EXTS:
                continue
            all_violations.extend(scan_file(p))

    if all_violations:
        print("SECRET DETECTION FAILED! Found potential secrets:", file=sys.stderr)
        for v in all_violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("Secret detection passed. No secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
