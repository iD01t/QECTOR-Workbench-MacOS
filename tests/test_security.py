"""
tests/test_security.py — Local security gates for QECTOR Workbench.

These tests are designed to catch accidental introduction of unsafe patterns
before they land in the main branch. They run in the same pytest suite as the
rest of the project, so CI enforces them automatically.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

PY_SOURCE_GLOBS = [
    "*.py",
    "app.py",
    "backend.py",
    "mcp_server.py",
    "doc_generator.py",
    "documentation_tab.py",
    "dialogs.py",
    "config.py",
    "utils.py",
    "state.py",
    "console.py",
    "hardware_tab.py",
    "benchmark_tab.py",
    "batch_streaming_tab.py",
    "code_explorer_tab.py",
    "decoder_lab_tab.py",
    "threading_utils.py",
    "logger.py",
    "results_tracker.py",
    "theme.py",
    "version.py",
    "tests/test_*.py",
]


def _py_files() -> list[Path]:
    files = []
    for pattern in PY_SOURCE_GLOBS:
        for f in ROOT.glob(pattern):
            if f.is_file() and "tests" not in [p.name for p in f.parents]:
                files.append(f)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def test_no_eval_in_source():
    """The codebase must not use eval()."""
    bad = []
    for path in _py_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'\beval\s*\(', line):
                bad.append((path, lineno, line.strip()))
    assert not bad, "eval() found:\n" + "\n".join(f"{p}:{n}: {l}" for p, n, l in bad)


def test_no_exec_in_source():
    """The codebase must not use exec()."""
    bad = []
    for path in _py_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'\bexec\s*\(', line):
                bad.append((path, lineno, line.strip()))
    assert not bad, "exec() found:\n" + "\n".join(f"{p}:{n}: {l}" for p, n, l in bad)


def test_no_pickle_in_source():
    """Pickle deserialization is unsafe for untrusted data."""
    bad = []
    for path in _py_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r'\bpickle\.(load|loads|Unpickler)\s*\(', line):
                bad.append((path, lineno, line.strip()))
    assert not bad, "pickle deserialization found:\n" + "\n".join(f"{p}:{n}: {l}" for p, n, l in bad)


def test_no_hardcoded_api_keys():
    """Source must not contain long strings that look like AWS/GitHub/OpenAI keys."""
    patterns = [
        re.compile(r'AKIA[0-9A-Z]{16}'),  # AWS access key
        re.compile(r'ghp_[0-9A-Za-z]{36}'),  # GitHub personal access token
        re.compile(r'sk-[A-Za-z0-9]{20,}'),  # OpenAI-style key
    ]
    bad = []
    for path in _py_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if any(p.search(line) for p in patterns):
                bad.append((path, lineno, line.strip()))
    assert not bad, "Possible hardcoded secret found:\n" + "\n".join(f"{p}:{n}: {l}" for p, n, l in bad)


def test_no_subprocess_with_shell_true_in_source():
    """subprocess.run(..., shell=True) is dangerous and should be explicit if present."""
    bad = []
    for path in _py_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "shell=True" in line:
                bad.append((path, lineno, line.strip()))
    assert not bad, "subprocess shell=True found:\n" + "\n".join(f"{p}:{n}: {l}" for p, n, l in bad)


def test_no_nested_ast_bodies():
    """Top-level backend/app modules should not contain deeply nested function
    definitions that indicate copy-pasted instead-of-refactored code.
    """
    suspect = []
    for path in _py_files():
        if "tests" in str(path):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            depth = 0
            cur = node
            while isinstance(cur, ast.FunctionDef) or isinstance(cur, ast.AsyncFunctionDef):
                depth += 1
                cur = getattr(cur, "parent", None)
            if depth >= 5:
                suspect.append((path, getattr(node, "lineno", 0), node.name, depth))
    assert not suspect, (
        "Deeply nested function definitions (>4 levels):\n"
        + "\n".join(f"{p}:{n}: {name} depth={d}" for p, n, name, d in suspect)
    )
