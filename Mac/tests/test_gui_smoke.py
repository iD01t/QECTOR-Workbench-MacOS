"""
tests/test_gui_smoke.py — Live end-to-end GUI smoke test for QECTOR Workbench.

Instantiates the real QectorApp, drives the Code Explorer / Decoder Lab /
Benchmark handlers, and asserts that background work completes and the
embedded matplotlib figures actually draw.  Skipped (like test_app_gui.py)
when Tk/Tcl or the GUI dependencies are not usable on this host.

Window hygiene
--------------
Every QectorApp built by these tests is withdrawn *before* it gets to call
``geometry`` or ``update``.  That is done by monkey-patching
``customtkinter.CTk.__init__`` to call ``withdraw()`` right after the parent
constructor, the same trick ``test_app_gui.py`` uses, so the test run
produces zero visible windows even when the host has a real desktop.
The same pattern also runs for the module-level ``_tk_works`` probe.
"""

from __future__ import annotations

import time

import pytest


# ---------------------------------------------------------------------------
# Guard: only run GUI tests when Tk works on this host.
#
# The probe creates a Tk root, withdraws it, then destroys it -- so the
# availability check never flashes a window on the host.
# ---------------------------------------------------------------------------
def _tk_works() -> bool:
    try:
        import tkinter as tk
        root = tk.Tk()
        try:
            root.withdraw()
        except Exception:
            pass
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
    "History",
    "Hardware",
    "Diagnostics",
    "Documentation",
    "Lab & Personal Info",
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


def _make_hidden_qector_app():
    """Build a QectorApp that never appears on the host desktop.

    Monkey-patches ``CTk.__init__`` to call ``withdraw()`` right after the
    parent constructor, then restores the original on the way out.  The
    splash screen and any Toplevel children constructed inside QectorApp
    inherit the withdrawn state because they are children of the same Tk
    interpreter.
    """
    import customtkinter as ctk
    import app as _app

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    original_init = ctk.CTk.__init__

    def init_then_hide(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        try:
            self.withdraw()
        except Exception:
            pass

    ctk.CTk.__init__ = init_then_hide
    try:
        return _app.QectorApp()
    finally:
        ctk.CTk.__init__ = original_init


def test_full_gui_smoke():
    app = _make_hidden_qector_app()
    try:
        app._app.update_idletasks()

        # -- exactly the named tabs, in order ----------------------------
        assert list(app.tabview._name_list) == EXPECTED_TABS
        print(f"PASS: tabview has exactly the {len(EXPECTED_TABS)} named tabs")

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

        # -- 2D Lattice view: must also render ---------------------------
        explorer.view_toggle.set("2D Lattice")
        explorer._on_view_change("2D Lattice")
        app._app.update()
        assert any(len(ax.collections) >= 1 for ax in explorer._figure.axes), \
            "2D Lattice view did not render"
        print("PASS: 2D Lattice view renders scatter artists")

        # -- Radar Chart view: must also render --------------------------
        explorer.view_toggle.set("Radar Chart")
        explorer._on_view_change("Radar Chart")
        app._app.update()
        assert any(len(ax.lines) > 0 for ax in explorer._figure.axes), \
            "Radar view did not render a polyline"
        print("PASS: Radar Chart view renders a polyline")

        # Reset to Tanner so subsequent tests start from a known state.
        explorer.view_toggle.set("Tanner graph")
        explorer._on_view_change("Tanner graph")

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
        try:
            app.destroy()
        except Exception:
            pass


def test_decoder_lab_resilient_fallback_on_qldpc():
    """Selecting a union-find decoder on a qLDPC code must auto-recover via the
    resilient fallback instead of erroring."""
    app = _make_hidden_qector_app()
    try:
        app._app.update_idletasks()
        explorer = app.tabs["Code Explorer"]
        explorer.family_var.set("bivariate_bicycle")
        explorer.distance_var.set(3)
        explorer._on_build()
        assert _pump(
            app,
            lambda: app.state.current_code is not None
            and app.state.current_family_key == "bivariate_bicycle",
        ), "bivariate_bicycle code build did not complete"

        lab = app.tabs["Decoder Lab"]
        assert lab.resilient_var.get() is True  # on by default
        lab.decoder_var.set("union_find")       # cannot construct on qLDPC
        lab._on_decode()
        assert _pump(
            app,
            lambda: "resilient fallback" in lab.result_text.get("1.0", "end").lower(),
        ), "resilient fallback did not trigger for union_find on a qLDPC code"
        text = lab.result_text.get("1.0", "end")
        assert "Recovered with" in text and "Syndrome valid:    yes" in text
        print("PASS: decoder lab recovered union_find -> compatible decoder on qLDPC")
    finally:
        try:
            app.destroy()
        except Exception:
            pass


def test_batch_and_streaming_live():
    """Drive the Batch & Streaming tab end to end (CUDA when available)."""
    import qector_decoder_v3 as qd
    app = _make_hidden_qector_app()
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
        # Use CUDA when the decoder reports a usable device (real GPU coverage),
        # else CPU. We assert the batch COMPLETES and reports a backend rather
        # than pinning an exact label: the tab surfaces backend errors verbatim
        # (no silent fallback), so a completed "Backend used:" line is the
        # correct end-to-end signal on any host.
        #
        # `cuda_is_available()` reports the *device*, not the entitlement: GPU
        # batch decoding is Enterprise-tier gated, so on a Community licence the
        # backend refuses with "requires Enterprise Tier". That is a licence
        # state, not a decode failure, so fall back to CPU and keep testing the
        # end-to-end path instead of failing the host.
        def _run_batch(backend: str) -> str:
            tab.backend_var.set(backend)
            tab.batch_samples_entry.delete(0, "end")
            tab.batch_samples_entry.insert(0, "64")
            tab._on_batch()
            _pump(
                app,
                lambda: "Backend used:" in tab.result_text.get("1.0", "end")
                or "failed" in tab.result_text.get("1.0", "end").lower(),
            )
            return tab.result_text.get("1.0", "end")

        backend = "cuda" if qd.cuda_is_available() else "cpu"
        out = _run_batch(backend)
        if backend == "cuda" and "Enterprise Tier" in out:
            print("INFO: GPU batch is Enterprise-gated on this host; falling back to CPU")
            backend = "cpu"
            out = _run_batch(backend)
        assert "Backend used:" in out, \
            f"batch decode did not complete (requested {backend}): {out.strip()[:200]}"
        assert any(len(ax.patches) > 0 for ax in tab._figure.axes), \
            "batch hamming-weight histogram did not draw"
        print(f"PASS: batch decode ran (requested {backend}) and drew a histogram")

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
        try:
            app.destroy()
        except Exception:
            pass
