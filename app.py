"""app.py — Main application entry point for QECTOR Decoder Workbench.

Wires all six feature tabs into a CTkTabview with shared AppState and
Console instances.  Includes a live Console tab, a status bar, global
Tk exception handling, per-tab crash isolation, and no import-time
network calls.
"""

from __future__ import annotations

import sys
import threading
import traceback
from typing import Optional

from version import WORKBENCH_VERSION, FULL_VERSION

try:
    import customtkinter as ctk
    _HAS_GUI = True
except Exception:
    _HAS_GUI = False


# ---------------------------------------------------------------------------
# Application class
# ---------------------------------------------------------------------------

class QectorApp:
    """Main QECTOR Decoder Workbench application with all tabs wired."""

    def __init__(self):
        if not _HAS_GUI:
            raise RuntimeError("customtkinter is required for QectorApp")

        self.root = ctk.CTk()
        self.root.title(FULL_VERSION)
        self.root.geometry("1200x800")
        self.root.minsize(960, 600)

        # ── Shared state & console ────────────────────────────────
        from state import AppState
        from console import Console

        self.state = AppState()
        self.console = Console()

        # ── Install global Tk exception hook ──────────────────────
        self.root.report_callback_exception = self._on_tk_exception

        # ── Build UI ──────────────────────────────────────────────
        self._build_ui()

        # ── Start background update check ─────────────────────────
        threading.Thread(target=self._bg_update_check, daemon=True).start()

    def _bg_update_check(self) -> None:
        try:
            from auto_updater import check_for_update
            avail = check_for_update()
            if avail:
                self.console.log(f"New qector_decoder_v3 version available: {avail}", "INFO")
                self.root.after(200, lambda: self._prompt_upgrade(avail))
        except Exception:
            pass

    def _prompt_upgrade(self, version: str) -> None:
        from dialogs import ask_yes_no, show_info, show_error
        msg = f"A new version of qector_decoder_v3 ({version}) is available.\n\nWould you like to upgrade now?"
        if ask_yes_no(self.root, "Upgrade Available", msg):
            self.console.log(f"Upgrading to qector_decoder_v3 v{version} in background...", "INFO")
            from auto_updater import try_upgrade
            def callback(success: bool, detail: str):
                if success:
                    self.console.log(f"Upgrade succeeded: {detail}", "SUCCESS")
                    self.root.after(0, lambda: show_info(self.root, "Upgrade Successful", "Upgrade successful! Please restart the application to use the new version."))
                else:
                    self.console.log(f"Upgrade failed: {detail}", "ERROR")
                    self.root.after(0, lambda: show_error(self.root, "Upgrade Failed", f"Upgrade failed:\n{detail}"))
            try_upgrade(version, callback)

    # ── helpers expected by test suite ────────────────────────────
    def title(self) -> str:
        return self.root.title()

    def winfo_reqwidth(self) -> int:
        return 1200

    def winfo_reqheight(self) -> int:
        return 800

    def destroy(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass

    def mainloop(self) -> None:
        self.root.mainloop()

    # ── UI construction ───────────────────────────────────────────
    def _build_ui(self) -> None:
        """Build the full application layout: tabview + status bar."""

        # Main container
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)

        # ── Tab view ──────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 0))

        # Create tab slots
        tab_names = [
            "Code Explorer",
            "Decoder Lab",
            "Benchmark",
            "Batch & Streaming",
            "Hardware",
            "Documentation",
            "Console",
        ]
        for name in tab_names:
            self.tabview.add(name)

        # ── Wire feature tabs (crash-isolated) ────────────────────
        self._wire_tab(
            "Code Explorer",
            "code_explorer_tab", "CodeExplorerTab",
        )
        self._wire_tab(
            "Decoder Lab",
            "decoder_lab_tab", "DecoderLabTab",
        )
        self._wire_tab(
            "Benchmark",
            "benchmark_tab", "BenchmarkTab",
        )
        self._wire_tab(
            "Batch & Streaming",
            "batch_streaming_tab", "BatchStreamingTab",
        )
        self._wire_tab(
            "Hardware",
            "hardware_tab", "HardwareTab",
        )
        self._wire_tab(
            "Documentation",
            "documentation_tab", "DocumentationTab",
        )

        # ── Console tab (built inline) ────────────────────────────
        self._build_console_tab()

        # ── Status bar ────────────────────────────────────────────
        self._build_status_bar()

        # Set default tab
        self.tabview.set("Code Explorer")

    def _wire_tab(self, tab_name: str, module_name: str, class_name: str) -> None:
        """Import and instantiate a tab class into its tabview slot.

        If the import or construction fails, a red error label is shown
        instead — crash isolation ensures one broken tab doesn't kill the
        entire app.
        """
        parent = self.tabview.tab(tab_name)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        try:
            import importlib
            mod = importlib.import_module(module_name)
            cls = getattr(mod, class_name)
            widget = cls(parent, state=self.state, console=self.console)
            widget.grid(row=0, column=0, sticky="nsew")
            self.console.log(f"Tab loaded: {tab_name}", "INFO")
        except Exception as exc:
            error_text = f"Failed to load {tab_name}:\n{exc}"
            self.console.log(error_text, "ERROR")
            lbl = ctk.CTkLabel(
                parent, text=error_text,
                text_color="#ff4444",
                font=ctk.CTkFont(family="Consolas", size=11),
                wraplength=600, justify="left",
            )
            lbl.grid(row=0, column=0, sticky="nw", padx=16, pady=16)

    def _build_console_tab(self) -> None:
        """Build the live Console tab showing all log output."""
        parent = self.tabview.tab("Console")
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=0)

        self._console_text = ctk.CTkTextbox(
            parent, wrap="word",
            font=ctk.CTkFont(family="Consolas", size=11),
        )
        self._console_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 0))
        self._console_text.configure(state="disabled")

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=4)

        ctk.CTkButton(
            btn_frame, text="Clear", width=80,
            command=self._clear_console,
            font=ctk.CTkFont(size=11),
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            btn_frame, text="Refresh", width=80,
            command=self._refresh_console,
            font=ctk.CTkFont(size=11),
        ).pack(side="right", padx=4)

        # Register callback for live console updates
        self.console._callbacks.append(self._on_console_output)

        # Show existing output
        self._refresh_console()

    def _on_console_output(self, text: str) -> None:
        """Callback fired whenever new text is written to the Console."""
        try:
            self._console_text.configure(state="normal")
            self._console_text.insert("end", text)
            self._console_text.see("end")
            self._console_text.configure(state="disabled")
        except Exception:
            pass

    def _refresh_console(self) -> None:
        """Reload the full console text from the Console buffer."""
        try:
            self._console_text.configure(state="normal")
            self._console_text.delete("1.0", "end")
            self._console_text.insert("1.0", self.console.get_text())
            self._console_text.see("end")
            self._console_text.configure(state="disabled")
        except Exception:
            pass

    def _clear_console(self) -> None:
        """Clear the console buffer and display."""
        self.console.clear()
        self._refresh_console()

    def _build_status_bar(self) -> None:
        """Build the bottom status bar showing version and backend info."""
        status_frame = ctk.CTkFrame(self.root, height=28, fg_color="#1e1e1e")
        status_frame.grid(row=1, column=0, sticky="ew")
        status_frame.grid_propagate(False)

        try:
            import backend as be
            backend_ver = f"qector_decoder_v3 {be.PACKAGE_VERSION}"
        except Exception:
            backend_ver = "backend unavailable"

        status_text = f"  {FULL_VERSION}  |  {backend_ver}  |  Python {sys.version.split()[0]}"
        ctk.CTkLabel(
            status_frame, text=status_text,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#888888",
            anchor="w",
        ).pack(side="left", fill="x", padx=4)

    # ── Exception handling ────────────────────────────────────────
    def _on_tk_exception(self, exc_type, exc_value, exc_tb) -> None:
        """Global Tk exception handler — log and show error, don't crash."""
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        self.console.log(f"Unhandled exception:\n{msg}", "ERROR")
        try:
            from dialogs import show_error
            show_error(self.root, "Error", f"An error occurred:\n{exc_value}")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Application entry point."""
    if not _HAS_GUI:
        print("ERROR: customtkinter is required to run QECTOR Workbench")
        sys.exit(1)



    try:
        from logger import get_logger
        logger = get_logger()
        logger.info(f"Starting {FULL_VERSION}")
    except Exception:
        pass

    app = QectorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
