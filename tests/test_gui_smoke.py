"""
tests/test_gui_smoke.py — Live end-to-end GUI smoke test for QECTOR Workbench.

Instantiates the real QectorApp, drives the Code Explorer / Decoder Lab /
Benchmark handlers, and asserts that background work completes and the
embedded matplotlib figures actually draw.  Skipped (like test_app_gui.py)
when Tk/Tcl or the GUI dependencies are not usable on this host.
"""

from __future__ import annotations

import time

import pytest


# ---------------------------------------------------------------------------
# Guard: only run GUI tests when Tk works on this host
# ---------------------------------------------------------------------------
def _tk_works() -> bool:
    try:
        import tkinter as tk
        root = tk.Tk()
        root.destroy()
        return True
    except Exception:
        return False


_HAS_TK = _tk_works()


def _gui_deps_installed() -> bool:
    if not _HAS_TK:
        return False
    try:
        import customtkinter  # noqa: F401
        import matplotlib  # noqa: F401
        import numpy  # noqa: F401
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _gui_deps_installed(), reason="GUI deps/tk not available"
)

EXPECTED_TABS = [
    "Code Explorer",
    "Decoder Lab",
    "Benchmark",
    "Batch & Streaming",
    "Hardware",
    "Documentation",
    "Console",
]


def _pump(app, condition, timeout: float = 45.0, interval: float = 0.02) -> bool:
    """Pump Tk events until condition() is true or the timeout expires.

    Background worker threads post their completions to per-tab UI pumps,
    so the event loop must be serviced while polling.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app._app.update()
        try:
            if condition():
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def test_full_gui_smoke():
    from app import QectorApp

    app = QectorApp()
    try:
        app._app.update_idletasks()

        # -- exactly the 7 named tabs, in order --------------------------
        assert list(app.tabview._name_list) == EXPECTED_TABS
        print("PASS: tabview has exactly the 7 named tabs")

        # -- Code Explorer: build rotated_surface d=5 --------------------
        explorer = app.tabs["Code Explorer"]
        explorer.family_var.set("rotated_surface")
        explorer.distance_var.set(5)
        explorer._on_build()
        assert _pump(app, lambda: app.state.current_code is not None), \
            "code build did not complete"
        assert app.state.current_code.n_qubits == 25
        print("PASS: code explorer built rotated_surface d=5 (25 qubits)")

        # -- Tanner graph drew real artists ------------------------------
        assert _pump(
            app,
            lambda: explorer._graph_data is not None
            and any(len(ax.collections) >= 2 for ax in explorer._figure.axes),
        ), "Tanner graph did not draw"
        print("PASS: Tanner graph axes contain scatter/edge artists")

        # -- toggle to matrix view and back -------------------------------
        explorer.view_toggle.set("Parity-check matrix")
        explorer._on_view_change("Parity-check matrix")
        app._app.update()
        assert any(len(ax.images) > 0 for ax in explorer._figure.axes), \
            "matrix view did not render an image"
        explorer.view_toggle.set("Tanner graph")
        explorer._on_view_change("Tanner graph")
        app._app.update()
        assert any(len(ax.collections) >= 2 for ax in explorer._figure.axes), \
            "toggling back to Tanner graph did not redraw"
        print("PASS: matrix view and Tanner view toggle both render")

        # -- Decoder Lab: run a decode ------------------------------------
        lab = app.tabs["Decoder Lab"]
        lab._on_decode()
        assert _pump(
            app, lambda: "Hamming" in lab.result_text.get("1.0", "end")
        ), "decoder lab result never showed 'Hamming'"
        print("PASS: decoder lab rendered a decode result with Hamming weight")

        # -- Benchmark: small run, chart must draw ------------------------
        bench = app.tabs["Benchmark"]
        bench.samples_entry.delete(0, "end")
        bench.samples_entry.insert(0, "50")
        bench.distance_var.set(3)
        bench._on_run()
        assert _pump(
            app,
            lambda: len(bench._results) == 1
            and any(len(ax.patches) > 0 for ax in bench._figure.axes),
            timeout=90.0,
        ), "benchmark did not complete or chart did not draw"
        print("PASS: benchmark ran and its figure axes contain bar artists")

        # -- Console tab received log lines --------------------------------
        assert _pump(
            app,
            lambda: "Tab loaded" in app._console_text.get("1.0", "end"),
        ), "console tab textbox never received log lines"
        print("PASS: console tab textbox received log lines")
    finally:
        app.destroy()


def test_batch_and_streaming_live():
    """Drive the Batch & Streaming tab end to end (CUDA when available)."""
    import qector_decoder_v3 as qd
    from app import QectorApp

    app = QectorApp()
    try:
        app._app.update_idletasks()

        explorer = app.tabs["Code Explorer"]
        explorer.family_var.set("rotated_surface")
        explorer.distance_var.set(3)
        explorer._on_build()
        assert _pump(app, lambda: app.state.current_code is not None), \
            "code build did not complete"

        tab = app.tabs["Batch & Streaming"]

        # -- batch decode on the best available backend -------------------
        backend = "cuda" if qd.cuda_is_available() else "cpu"
        tab.backend_var.set(backend)
        tab.batch_samples_entry.delete(0, "end")
        tab.batch_samples_entry.insert(0, "64")
        tab._on_batch()
        assert _pump(
            app,
            lambda: f"Backend used:        {backend}" in tab.result_text.get("1.0", "end"),
        ), f"batch decode on {backend} did not complete"
        assert any(len(ax.patches) > 0 for ax in tab._figure.axes), \
            "batch hamming-weight histogram did not draw"
        print(f"PASS: batch decode ran on {backend} and drew a histogram")

        # -- streaming session with a chosen decoder ----------------------
        tab.stream_decoder_var.set("fast_union_find")
        tab._on_stream()
        assert _pump(
            app,
            lambda: "Streaming Session Complete" in tab.result_text.get("1.0", "end"),
        ), "streaming session did not complete"
        text = tab.result_text.get("1.0", "end")
        assert "Committed count:    20" in text
        assert "fast_union_find" in text
        assert any(ax.has_data() for ax in tab._figure.axes), \
            "streaming per-round chart did not draw"
        print("PASS: streaming session ran and drew the per-round chart")

        # -- invalid input never crashes ----------------------------------
        tab.batch_rate_entry.delete(0, "end")
        tab.batch_rate_entry.insert(0, "not-a-number")
        tab._on_batch()
        app._app.update()
        assert "Invalid error rate" in tab.result_text.get("1.0", "end")
        print("PASS: invalid entry text surfaced a friendly message")
    finally:
        app.destroy()
