"""Tests for the Diagnostics tab: button re-enable, OpenCL env-var escape hatch.

These cover the two regressions fixed in this session:
  * _done() must re-enable the action buttons that _busy(True) disabled,
    or the deferred boot-time self-test locks the tab permanently.
  * QECTOR_DISABLE_OPENCL=1 must actually skip OpenCL probing (the docs
    advertised it but the code never checked it).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_disable_opencl_skips_host_probe(monkeypatch):
    """QECTOR_DISABLE_OPENCL=1 must short-circuit every OpenCL probe."""
    monkeypatch.setenv("QECTOR_DISABLE_OPENCL", "1")
    import hardware_routing as hr
    hw = hr.detect_hardware()
    assert hw.opencl is False
    assert hw.opencl_host_devices == 0
    assert hw.opencl_host_platform is None
    assert "QECTOR_DISABLE_OPENCL" in hw.opencl_reason


def test_opencl_probe_runs_when_not_disabled(monkeypatch):
    """Without the env var, the host probe runs (and returns a real count)."""
    monkeypatch.delenv("QECTOR_DISABLE_OPENCL", raising=False)
    import hardware_routing as hr
    hw = hr.detect_hardware()
    # The host probe must have executed: reason is never empty when not disabled.
    assert hw.opencl_reason
    assert hw.opencl_reason != ""


def test_diagnostics_done_reenables_buttons():
    """_done() must call _busy(False) so buttons come back after a run.

    This is a headless test of the re-enable logic: it stubs the Tk widgets
    with callables that record their state, so it runs without a display.
    """
    import diagnostics_tab as dt

    class _FakeButton:
        def __init__(self):
            self.state = "normal"
        def configure(self, **kw):
            if "state" in kw:
                self.state = kw["state"]

    class _FakeLabel:
        def __init__(self):
            self.text = ""
        def configure(self, **kw):
            if "text" in kw:
                self.text = kw["text"]

    class _FakeText:
        def __init__(self):
            self.content = ""
        def configure(self, **kw): pass
        def delete(self, *a): pass
        def insert(self, *a): self.content = a[-1] if a else ""

    # Build a minimal stub that has the attributes _done/_busy touch.
    class _FakeTab:
        diag_btn = _FakeButton()
        probe_btn = _FakeButton()
        resilient_btn = _FakeButton()
        doctor_btn = _FakeButton()
        reset_btn = _FakeButton()
        status_label = _FakeLabel()
        result_text = _FakeText()
        _seq = 0

        # Bind the real methods from DiagnosticsTab
        _busy = dt.DiagnosticsTab._busy
        _done = dt.DiagnosticsTab._done

    tab = _FakeTab()
    # Simulate a run: busy(True) disables, then _done must re-enable.
    tab._busy(True, "Running…")
    assert all(b.state == "disabled" for b in
               (tab.diag_btn, tab.probe_btn, tab.resilient_btn, tab.doctor_btn, tab.reset_btn))
    tab._seq = 1
    tab._done(1, "result text", "ok")
    assert all(b.state == "normal" for b in
               (tab.diag_btn, tab.probe_btn, tab.resilient_btn, tab.doctor_btn, tab.reset_btn))
