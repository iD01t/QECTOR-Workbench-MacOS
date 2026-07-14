"""app.py — Main application entry point for QECTOR Decoder Workbench.

Builds the full application window: a CTkTabview with the six feature tabs
plus a live Console tab, a status bar showing the app version and the
current code summary, per-tab crash isolation, a global Tk callback
exception hook with a non-modal error toast, a logging ``sys.excepthook``,
and an auto-update check that is scheduled only after the window exists.

Importing this module has zero side effects: no threads are started and no
network calls are made until a :class:`QectorApp` is constructed and its
event loop begins servicing timers.
"""

from __future__ import annotations

import sys
import tkinter
import traceback
from typing import Any, Optional

from version import FULL_VERSION

try:
    import customtkinter as ctk
    _HAS_GUI = True
except Exception:
    _HAS_GUI = False


_WINDOW_WIDTH = 1280
_WINDOW_HEIGHT = 820
_MIN_WIDTH = 1100
_MIN_HEIGHT = 700

# (tab name, module, class) in display order; the Console tab is built inline.
_TAB_SPECS = [
    ("Code Explorer", "code_explorer_tab", "CodeExplorerTab"),
    ("Decoder Lab", "decoder_lab_tab", "DecoderLabTab"),
    ("Benchmark", "benchmark_tab", "BenchmarkTab"),
    ("Batch & Streaming", "batch_streaming_tab", "BatchStreamingTab"),
    ("Hardware", "hardware_tab", "HardwareTab"),
    ("Documentation", "documentation_tab", "DocumentationTab"),
]

TAB_NAMES = [spec[0] for spec in _TAB_SPECS] + ["Console"]


def _safe_logger():
    """Return the app logger, or None when logging cannot be initialised."""
    try:
        from logger import get_logger
        return get_logger()
    except Exception:
        return None


_EXCEPTHOOK_INSTALLED = False
_PREVIOUS_EXCEPTHOOK: Optional[Any] = None


def _install_sys_excepthook() -> None:
    """Install (once) a ``sys.excepthook`` that logs uncaught exceptions."""
    global _EXCEPTHOOK_INSTALLED, _PREVIOUS_EXCEPTHOOK
    if _EXCEPTHOOK_INSTALLED:
        return
    _PREVIOUS_EXCEPTHOOK = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        try:
            logger = _safe_logger()
            if logger is not None:
                logger.error(
                    "Uncaught exception:\n"
                    + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
                )
        except Exception:
            pass
        try:
            if _PREVIOUS_EXCEPTHOOK is not None:
                _PREVIOUS_EXCEPTHOOK(exc_type, exc_value, exc_tb)
        except Exception:
            pass

    sys.excepthook = _hook
    _EXCEPTHOOK_INSTALLED = True


# ---------------------------------------------------------------------------
# Application class
# ---------------------------------------------------------------------------

class QectorApp:
    """Main QECTOR Decoder Workbench application with all tabs wired."""

    def __init__(self):
        if not _HAS_GUI:
            raise RuntimeError("customtkinter is required for QectorApp")

        import theme
        import threading_utils
        from console import Console
        from state import AppState

        self._logger = _safe_logger()
        self._colors = theme.COLORS
        self._fonts = theme.get_fonts()

        ctk.set_appearance_mode("dark")  # default color theme is kept as-is

        self._app = ctk.CTk()
        self.root = self._app  # backward-compatible alias
        self._width = _WINDOW_WIDTH
        self._height = _WINDOW_HEIGHT
        self._app.title(FULL_VERSION)
        self._app.geometry(f"{self._width}x{self._height}")
        self._app.minsize(_MIN_WIDTH, _MIN_HEIGHT)
        self._set_window_icon()

        self.state = AppState()
        self.console = Console()
        self.tabs: dict[str, Any] = {}
        self._toast: Any = None
        self._toast_after_id: Optional[str] = None
        self._update_after_id: Optional[str] = None
        self._destroyed = False

        # UI pump: safe marshalling of console/status updates coming from
        # worker threads onto the Tk main thread.
        self._ui = threading_utils.UiPump(self._app)

        # Global crash handling: Tk callbacks and uncaught thread exceptions
        # are logged and surfaced without ever killing the app.
        self._app.report_callback_exception = self._on_tk_exception
        _install_sys_excepthook()

        self._build_ui()
        self.console.log(f"{FULL_VERSION} ready", "INFO")

        # Auto-update check: scheduled AFTER construction; importing this
        # module starts zero threads and makes zero network calls.
        try:
            self._update_after_id = self._app.after(1500, self._start_update_check)
        except Exception:
            self._update_after_id = None

    # ── public surface used by tests ──────────────────────────────────
    def title(self) -> str:
        return self._app.title()

    def winfo_reqwidth(self) -> int:
        """The configured window width (matches the geometry set in __init__)."""
        return int(self._width)

    def winfo_reqheight(self) -> int:
        """The configured window height (matches the geometry set in __init__)."""
        return int(self._height)

    def destroy(self) -> None:
        self._destroyed = True
        try:
            self.console.unsubscribe(self._on_console_output)
        except Exception:
            pass
        # Close UI pumps first so no stale "after" timers outlive the window.
        try:
            self._ui.close()
        except Exception:
            pass
        for tab in list(self.tabs.values()):
            pump = getattr(tab, "_ui", None)
            if pump is not None:
                try:
                    pump.close()
                except Exception:
                    pass
        for after_id in (self._update_after_id, self._toast_after_id):
            if after_id is not None:
                try:
                    self._app.after_cancel(after_id)
                except Exception:
                    pass
        self._update_after_id = None
        self._toast_after_id = None
        # Cancel every remaining Tk "after" timer — including CustomTkinter's
        # internal DPI/scaling-tracker loop, which reschedules itself and would
        # otherwise fire against the destroyed interpreter (an intermittent
        # _tkinter.TclError when roots are created and torn down repeatedly).
        try:
            for aid in self._app.tk.eval("after info").split():
                try:
                    self._app.after_cancel(aid)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self._app.update_idletasks()
        except Exception:
            pass
        try:
            self._app.destroy()
        except Exception:
            pass

    def mainloop(self) -> None:
        self._app.mainloop()

    # ── window icon (taskbar / title bar) ────────────────────────────
    def _set_window_icon(self) -> None:
        """Set the window icon from the bundled icon.ico.

        The icon file is bundled next to the source and also included in the
        PyInstaller build via ``QectorWorkbench.spec``.  This call gives the
        window title bar, taskbar button and Alt+Tab preview the QECTOR logo
        when running from source.  When frozen the EXE icon embedded by the
        ``.spec`` file already covers the taskbar; this is still called so
        that ``iconbitmap`` is available when feasible.
        """
        try:
            import os
            ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.isfile(ico):
                self._app.iconbitmap(ico)
        except Exception:
            pass

    # ── UI construction ───────────────────────────────────────────────
    def _build_ui(self) -> None:
        """Build the full application layout: tabview + status bar."""
        self._app.grid_columnconfigure(0, weight=1)
        self._app.grid_rowconfigure(0, weight=1)
        self._app.grid_rowconfigure(1, weight=0)

        self.tabview = ctk.CTkTabview(self._app)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 0))
        for name in TAB_NAMES:
            self.tabview.add(name)

        for tab_name, module_name, class_name in _TAB_SPECS:
            self._wire_tab(tab_name, module_name, class_name)

        self._build_console_tab()
        self._build_status_bar()
        self.tabview.set("Code Explorer")

    def _wire_tab(self, tab_name: str, module_name: str, class_name: str) -> None:
        """Import and instantiate a tab class into its tabview slot.

        Crash isolation: if the import or construction fails, a fallback
        frame showing the error is mounted instead and the rest of the app
        keeps working.
        """
        parent = self.tabview.tab(tab_name)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        try:
            import importlib
            mod = importlib.import_module(module_name)
            cls = getattr(mod, class_name)
            widget = cls(parent, state=self.state, console=self.console, fonts=self._fonts)
            widget.grid(row=0, column=0, sticky="nsew")
            self.tabs[tab_name] = widget
            self.console.log(f"Tab loaded: {tab_name}", "INFO")
        except Exception as exc:
            detail = traceback.format_exc()
            if self._logger is not None:
                self._logger.error(f"Failed to load tab {tab_name}:\n{detail}")
            self.console.log(f"Failed to load tab {tab_name}: {exc}", "ERROR")
            try:
                fallback = ctk.CTkFrame(parent, fg_color=self._colors["bg_panel"])
                fallback.grid(row=0, column=0, sticky="nsew")
                ctk.CTkLabel(
                    fallback,
                    text=f"Failed to load {tab_name}:\n\n{exc}",
                    text_color=self._colors["error"],
                    font=ctk.CTkFont(family=self._fonts.mono, size=11),
                    wraplength=760,
                    justify="left",
                ).pack(anchor="nw", padx=20, pady=20)
            except Exception:
                pass

    # ── Console tab ───────────────────────────────────────────────────
    def _build_console_tab(self) -> None:
        """Build the live Console tab: a read-only textbox fed by Console."""
        parent = self.tabview.tab("Console")
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=0)

        self._console_text = ctk.CTkTextbox(
            parent, wrap="word",
            font=ctk.CTkFont(family=self._fonts.mono, size=self._fonts.mono_size + 1),
        )
        self._console_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 0))
        self._console_text.configure(state="disabled")

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=6)
        ctk.CTkButton(
            btn_frame, text="Clear", width=90,
            command=self._clear_console,
            font=ctk.CTkFont(size=11),
        ).pack(side="right", padx=4)

        # Live subscription: Console.write may fire from worker threads, so
        # each chunk is marshalled to the UI thread before touching Tk.
        self.console.subscribe(self._on_console_output)
        self._refresh_console()

    def _on_console_output(self, text: str) -> None:
        """Console subscriber — may run on any thread; marshal to UI."""
        if self._destroyed:
            return
        self._ui.post(self._append_console, text)

    def _append_console(self, text: str) -> None:
        try:
            self._console_text.configure(state="normal")
            self._console_text.insert("end", text)
            self._console_text.see("end")
            self._console_text.configure(state="disabled")
        except tkinter.TclError:
            pass

    def _refresh_console(self) -> None:
        try:
            self._console_text.configure(state="normal")
            self._console_text.delete("1.0", "end")
            self._console_text.insert("1.0", self.console.get_text())
            self._console_text.see("end")
            self._console_text.configure(state="disabled")
        except tkinter.TclError:
            pass

    def _clear_console(self) -> None:
        self.console.clear()
        self._refresh_console()

    # ── Status bar ────────────────────────────────────────────────────
    def _build_status_bar(self) -> None:
        bar = ctk.CTkFrame(
            self._app, height=30, corner_radius=0,
            fg_color=self._colors["bg_status"],
        )
        bar.grid(row=1, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_columnconfigure(1, weight=0)

        self._status_left = ctk.CTkLabel(
            bar, text=FULL_VERSION, anchor="w",
            font=ctk.CTkFont(family=self._fonts.mono, size=10),
            text_color=self._colors["text_secondary"],
        )
        self._status_left.grid(row=0, column=0, sticky="w", padx=(10, 4), pady=2)

        self._status_right = ctk.CTkLabel(
            bar, text="no code built", anchor="e",
            font=ctk.CTkFont(family=self._fonts.mono, size=10),
            text_color=self._colors["text_secondary"],
        )
        self._status_right.grid(row=0, column=1, sticky="e", padx=(4, 10), pady=2)

        self.state.on_code_changed(self._on_state_code_changed)

    def _on_state_code_changed(self) -> None:
        """State listener — may fire from any thread; marshal to UI."""
        if self._destroyed:
            return
        self._ui.post(self._refresh_status_code)

    def _refresh_status_code(self) -> None:
        try:
            code = self.state.current_code
            if code is None:
                text = "no code built"
            else:
                n_qubits = getattr(code, "n_qubits", "?")
                text = (
                    f"{self.state.current_family_key} d={self.state.current_param}"
                    f" - {n_qubits} qubits"
                )
            self._status_right.configure(text=text)
        except tkinter.TclError:
            pass

    # ── Error toast + exception hooks ─────────────────────────────────
    def _show_error_toast(self, message: str) -> None:
        """Show a non-modal, self-dismissing error toast (bottom-right)."""
        try:
            self._dismiss_toast()
            msg = (message or "").strip() or "Unknown error"
            if len(msg) > 400:
                msg = msg[:400] + "…"
            toast = ctk.CTkFrame(
                self._app, corner_radius=8, border_width=1,
                fg_color=self._colors["bg_toast"],
                border_color=self._colors["border_toast"],
            )
            ctk.CTkLabel(
                toast, text=msg, wraplength=460, justify="left",
                text_color=self._colors["text_primary"],
                font=ctk.CTkFont(size=11),
            ).pack(padx=14, pady=(10, 6))
            ctk.CTkButton(
                toast, text="Dismiss", width=76, height=24,
                command=self._dismiss_toast,
                font=ctk.CTkFont(size=11),
            ).pack(padx=14, pady=(0, 10), anchor="e")
            toast.place(relx=1.0, rely=1.0, x=-18, y=-44, anchor="se")
            self._toast = toast
            self._toast_after_id = self._app.after(8000, self._dismiss_toast)
        except Exception:
            pass

    def _dismiss_toast(self) -> None:
        toast, self._toast = self._toast, None
        after_id, self._toast_after_id = self._toast_after_id, None
        if after_id is not None:
            try:
                self._app.after_cancel(after_id)
            except Exception:
                pass
        if toast is not None:
            try:
                toast.destroy()
            except Exception:
                pass

    def _on_tk_exception(self, exc_type, exc_value, exc_tb) -> None:
        """Global Tk callback exception hook — log, surface, never re-raise."""
        try:
            detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        except Exception:
            detail = f"{exc_type}: {exc_value}"
        try:
            if self._logger is not None:
                self._logger.error(f"Unhandled Tk callback exception:\n{detail}")
        except Exception:
            pass
        try:
            self.console.log(f"Unhandled exception:\n{detail}", "ERROR")
        except Exception:
            pass
        try:
            self._show_error_toast(f"{getattr(exc_type, '__name__', exc_type)}: {exc_value}")
        except Exception:
            pass

    # ── Auto-update (deferred; console/log output only) ───────────────
    def _start_update_check(self) -> None:
        self._update_after_id = None
        if self._destroyed:
            return
        try:
            import threading_utils
            threading_utils.run_in_background(self._update_check_worker)
        except Exception as exc:
            self.console.log(f"Update check could not start: {exc}", "WARN")

    def _update_check_worker(self) -> None:
        """Runs on a daemon thread; results go to console/log only."""
        try:
            import auto_updater
            latest = auto_updater.check_for_update()
        except Exception as exc:
            if self._logger is not None:
                self._logger.warning(f"Update check failed: {exc}")
            return
        try:
            if latest:
                msg = f"qector_decoder_v3 {latest} is available on PyPI (pip install --upgrade qector-decoder-v3)"
                self.console.log(msg, "INFO")
                if self._logger is not None:
                    self._logger.info(msg)
            else:
                self.console.log("qector_decoder_v3 is up to date", "INFO")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Application entry point with a readable fatal-error fallback."""
    logger = _safe_logger()
    if not _HAS_GUI:
        msg = "ERROR: customtkinter is required to run QECTOR Workbench"
        print(msg, file=sys.stderr)
        if logger is not None:
            logger.error(msg)
        sys.exit(1)

    exit_code = 0
    try:
        if logger is not None:
            logger.info(f"Starting {FULL_VERSION}")
        app = QectorApp()
        app.mainloop()
    except Exception:
        detail = traceback.format_exc()
        msg = (
            f"{FULL_VERSION} hit a fatal error and must close.\n"
            f"{detail}\n"
            "The full log is in the per-user data directory (logs/qector.log)."
        )
        print(msg, file=sys.stderr)
        if logger is not None:
            logger.error(msg)
        exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
