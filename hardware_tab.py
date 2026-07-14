"""hardware_tab.py — Hardware tab for QECTOR Workbench.

Detects available decode backends (CUDA, OpenCL, CPU), system resources
(psutil) and decoder recommendations.  All probes run on a background
thread — the refresh button never blocks the UI.
"""

from __future__ import annotations

import platform
import sys
import tkinter
import traceback
from typing import Any, Optional

try:
    import customtkinter as ctk
    _HAS_GUI = True
except Exception:
    _HAS_GUI = False

import backend as be
import theme
import threading_utils


def _probe_hardware_text() -> str:
    """Backend availability probe (safe to call off the UI thread)."""
    try:
        from hardware_routing import detect_hardware
        hw = detect_hardware()
        return (
            f"CUDA:          {'available' if hw.cuda_rust else 'not available'}\n"
            f"GPU:           {hw.gpu or 'N/A'}\n"
            f"OpenCL:        {'available' if hw.opencl else 'not available'}\n"
            f"OpenCL device: {hw.opencl_device or 'N/A'}\n"
            f"CPU:           always available\n"
        )
    except Exception as e:
        return f"Hardware detection unavailable: {e}"


def _probe_recommendation_text(family: Optional[str], d: Optional[int], n_qubits: Optional[int]) -> str:
    """Decoder recommendation probe (safe to call off the UI thread)."""
    try:
        from hardware_routing import recommend
        rec = recommend(family, d, n_qubits, "balanced")
        return (
            f"Recommended:    {rec.decoder}\n"
            f"Priority:       {rec.priority}\n"
            f"Hardware:       {rec.hardware}\n"
            f"Batch size:     {rec.batch_size}\n"
            f"GPU batched BP: {rec.gpu_batched_bp}\n"
            f"Reason:         {rec.reason}\n"
        )
    except Exception:
        return "Build a code to get decoder recommendations."


def _probe_system_text() -> str:
    """System resource probe (safe to call off the UI thread)."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.15)
        mem = psutil.virtual_memory()
        cores = psutil.cpu_count(logical=True)
        ps_text = (
            f"CPU usage: {cpu:.0f}% ({cores} logical cores) | "
            f"RAM: {mem.percent:.0f}% of {mem.total / (1024 ** 3):.1f} GiB"
        )
    except Exception as e:
        ps_text = f"psutil probe failed: {e}"
    return (
        f"Platform:      {platform.platform()}\n"
        f"Python:        {sys.version.split()[0]}\n"
        f"Backend:       qector_decoder_v3 {be.PACKAGE_VERSION}\n"
        f"Resources:     {ps_text}\n"
    )


if _HAS_GUI:

    class HardwareTab(ctk.CTkFrame):
        """Hardware and system info panel."""

        def __init__(self, master, state=None, console=None, fonts=None, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.state = state
            self.console = console
            self.fonts = fonts if fonts is not None else theme.get_fonts()

            self._ui = threading_utils.UiPump(self)
            self._refresh_seq = 0

            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)

            scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
            scroll.grid(row=0, column=0, sticky="nsew")
            scroll.grid_columnconfigure(0, weight=1)

            mono = ctk.CTkFont(family=self.fonts.mono, size=self.fonts.mono_size + 1)
            bold = ctk.CTkFont(size=12, weight="bold")

            ctk.CTkLabel(
                scroll, text="Hardware & System",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(16, 4))
            ctk.CTkLabel(
                scroll, text="Detected backends, system resources, and decoder recommendations.",
                font=ctk.CTkFont(size=11), text_color=theme.COLORS["text_secondary"],
            ).pack(anchor="w", padx=16, pady=(0, 12))

            self.refresh_btn = ctk.CTkButton(
                scroll, text="Refresh Hardware Info", command=self._on_refresh,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.refresh_btn.pack(anchor="w", padx=16, pady=(0, 8))

            ctk.CTkLabel(scroll, text="Backends", font=bold).pack(anchor="w", padx=16)
            self.hw_text = ctk.CTkTextbox(scroll, height=120, wrap="word", font=mono)
            self.hw_text.pack(fill="x", padx=16, pady=(2, 8))
            self.hw_text.insert("1.0", "Probing hardware ...")
            self.hw_text.configure(state="disabled")

            ctk.CTkLabel(scroll, text="Recommendation", font=bold).pack(anchor="w", padx=16)
            self.rec_text = ctk.CTkTextbox(scroll, height=120, wrap="word", font=mono)
            self.rec_text.pack(fill="x", padx=16, pady=(2, 8))
            self.rec_text.configure(state="disabled")

            ctk.CTkLabel(scroll, text="System", font=bold).pack(anchor="w", padx=16)
            self.sys_text = ctk.CTkTextbox(scroll, height=120, wrap="word", font=mono)
            self.sys_text.pack(fill="x", padx=16, pady=(2, 16))
            self.sys_text.configure(state="disabled")

            # Initial refresh is deferred so construction never blocks on
            # CUDA/OpenCL probes; the probes themselves run on a worker.
            try:
                self.after(150, self._on_refresh)
            except tkinter.TclError:
                pass

        # ── helpers ────────────────────────────────────────────────────
        def _log(self, msg: str, level: str = "INFO") -> None:
            if self.console:
                try:
                    self.console.log(msg, level)
                except Exception:
                    pass

        # ── refresh action ─────────────────────────────────────────────
        def _on_refresh(self) -> None:
            self._refresh_seq += 1
            seq = self._refresh_seq
            try:
                self.refresh_btn.configure(state="disabled")
            except tkinter.TclError:
                return
            # Snapshot state on the UI thread; the worker only reads copies.
            code = self.state.current_code if self.state else None
            family = self.state.current_family_key if self.state else None
            d = self.state.current_param if self.state else None
            n_qubits = getattr(code, "n_qubits", None) if code is not None else None
            threading_utils.run_in_background(
                self._refresh_worker, args=(seq, family, d, n_qubits)
            )

        def _refresh_worker(self, seq: int, family: Optional[str], d: Optional[int],
                            n_qubits: Optional[int]) -> None:
            try:
                payload = {
                    "hw": _probe_hardware_text(),
                    "rec": _probe_recommendation_text(family, d, n_qubits),
                    "sys": _probe_system_text(),
                }
                self._ui.post(self._on_refresh_done, seq, payload)
            except Exception as e:
                self._log(f"Hardware refresh failed: {e}", "ERROR")
                self._log(traceback.format_exc(), "ERROR")
                self._ui.post(self._on_refresh_failed, seq, f"Hardware refresh failed: {e}")

        def _on_refresh_done(self, seq: int, payload: dict[str, Any]) -> None:
            if seq != self._refresh_seq:
                return
            try:
                self._set_text(self.hw_text, payload["hw"])
                self._set_text(self.rec_text, payload["rec"])
                self._set_text(self.sys_text, payload["sys"])
                self._log("Hardware info refreshed", "INFO")
            except tkinter.TclError:
                pass
            finally:
                self._reenable(seq)

        def _on_refresh_failed(self, seq: int, message: str) -> None:
            if seq != self._refresh_seq:
                return
            try:
                self._set_text(self.hw_text, message)
            except tkinter.TclError:
                pass
            finally:
                self._reenable(seq)

        def _reenable(self, seq: int) -> None:
            if seq != self._refresh_seq:
                return
            try:
                self.refresh_btn.configure(state="normal")
            except tkinter.TclError:
                pass

        @staticmethod
        def _set_text(widget, text: str) -> None:
            try:
                widget.configure(state="normal")
                widget.delete("1.0", "end")
                widget.insert("1.0", text)
                widget.configure(state="disabled")
            except tkinter.TclError:
                pass

else:
    class HardwareTab:
        def __init__(self, master=None, state=None, console=None, fonts=None, **kwargs):
            pass
