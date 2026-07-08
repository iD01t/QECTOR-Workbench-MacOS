"""
tests/test_app.py — Application-layer tests: config, state, logging, docs, exports, GUI tabs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

import state
import theme
import utils
from logger import get_logger
from doc_generator import ProfessionalDocGenerator


# ---------------------------------------------------------------------------
# config/state/logging
# ---------------------------------------------------------------------------

def test_fonts_contains_required_families():
    fonts = theme.get_fonts()
    assert fonts.mono
    assert fonts.ui
    assert fonts.heading
    assert fonts.mono_size > 0
    assert fonts.ui_size > 0
    assert fonts.heading_size > 0


def test_app_state_listeners():
    s = state.AppState()
    fired = []

    def cb():
        fired.append(True)

    s.on_code_changed(cb)
    s.set_code(object(), "repetition", 5)
    assert fired == [True]


def test_validate_int():
    valid, _ = utils.validate_int("42", min_val=0, max_val=100)
    assert valid is True
    valid, _ = utils.validate_int("-1", min_val=0, max_val=100)
    assert valid is False


def test_format_number():
    formatted = utils.format_number(3.14159, precision=2)
    assert formatted == "3.14"


def test_logger_writes_file(tmp_path, monkeypatch):
    # stub log file path so we don't pollute repo logs/
    monkeypatch.setenv("QECTOR_LOG_DIR", str(tmp_path))
    logger = get_logger()
    logger.info("hello from pytest")
    logger.warning("warn from pytest")
    assert logger.log_file.exists()
    text = logger.log_file.read_text(encoding="utf-8", errors="ignore")
    assert "hello from pytest" in text
    assert "warn from pytest" in text


# ---------------------------------------------------------------------------
# doc_generator
# ---------------------------------------------------------------------------

def test_doc_generator_initializes():
    ProfessionalDocGenerator()


def test_doc_generator_export_watermarks(tmp_path, monkeypatch):
    import backend as be
    try:
        code = be.build_code("repetition", 5)
    except be.QectorError:
        pytest.skip("backend unavailable for code build")

    gen = ProfessionalDocGenerator()
    monkeypatch.chdir(tmp_path)
    paths_map = gen.generate_all(code, formats=["markdown", "json", "html"])
    assert len(paths_map) == 3
    for fmt, (ok, path) in paths_map.items():
        assert ok is True, fmt
        assert path.exists()
        assert path.stat().st_size > 0
    # watermark or attribution marker exists somewhere across generated docs
    md_text = Path(paths_map["markdown"][1]).read_text(encoding="utf-8", errors="ignore")
    assert any(marker in md_text for marker in ["QECTOR", "Qector", "Watermark", "Generated", "CERTIFIED"])


# ---------------------------------------------------------------------------
# exports atomicity/locking — sanity on file system
# ---------------------------------------------------------------------------

def test_utils_safe_write_and_read(tmp_path):
    target = tmp_path / "sub" / "result.json"
    success, msg = utils.safe_write_file(target, '{"ok": true}')
    assert success is True, msg
    assert target.exists()
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["ok"] is True


# ---------------------------------------------------------------------------
# GUI tab no-init tests
# ---------------------------------------------------------------------------

def _installed_gui_deps():
    try:
        import customtkinter  # noqa: F401
        import matplotlib  # noqa: F401
        import numpy  # noqa: F401
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _installed_gui_deps(), reason="GUI deps not installed in this interpreter")
def test_gui_tabs_import_without_mainloop():
    import app  # noqa: F401
    import code_explorer_tab  # noqa: F401
    import decoder_lab_tab  # noqa: F401
    import benchmark_tab  # noqa: F401
    import batch_streaming_tab  # noqa: F401
    import hardware_tab  # noqa: F401
    import mcp_server  # noqa: F401
    import dialogs  # noqa: F401
    import documentation_tab  # noqa: F401
