"""hardware_tab.py — Hardware tab for QECTOR Workbench.

Detect and display available hardware backends (CUDA, OpenCL, CPU),
system information, and decoder recommendations.
"""

from __future__ import annotations

from typing import Any, Optional

try:
    import customtkinter as ctk
    _HAS_GUI = True
except Exception:
    _HAS_GUI = False

import backend as be


if _HAS_GUI:

    class HardwareTab(ctk.CTkFrame):
        """Hardware and system info panel."""

        def __init__(self, master, state=None, console=None, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.state = state
            self.console = console
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)

            scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
            scroll.grid(row=0, column=0, sticky="nsew")
            scroll.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                scroll, text="Hardware & System",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(16, 4))
            ctk.CTkLabel(
                scroll, text="Detected backends, system resources, and decoder recommendations.",
                font=ctk.CTkFont(size=11), text_color="gray",
            ).pack(anchor="w", padx=16, pady=(0, 12))

            # Refresh button
            self.refresh_btn = ctk.CTkButton(
                scroll, text="Refresh Hardware Info", command=self._on_refresh,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.refresh_btn.pack(anchor="w", padx=16, pady=(0, 8))

            # Hardware info display
            self.hw_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.hw_frame.pack(fill="x", padx=16, pady=4)
            self.hw_text = ctk.CTkTextbox(
                self.hw_frame, height=120, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.hw_text.pack(fill="both", expand=True)
            self.hw_text.configure(state="disabled")

            # Recommendation
            self.rec_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.rec_frame.pack(fill="x", padx=16, pady=(8, 4))
            self.rec_text = ctk.CTkTextbox(
                self.rec_frame, height=100, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.rec_text.pack(fill="both", expand=True)
            self.rec_text.configure(state="disabled")

            # System info
            self.sys_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.sys_frame.pack(fill="x", padx=16, pady=(4, 16))
            self.sys_text = ctk.CTkTextbox(
                self.sys_frame, height=120, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.sys_text.pack(fill="both", expand=True)
            self.sys_text.configure(state="disabled")

            self._on_refresh()

        def _on_refresh(self) -> None:
            self._update_hardware()
            self._update_recommendation()
            self._update_system()

        def _update_hardware(self) -> None:
            try:
                from hardware_routing import detect_hardware
                hw = detect_hardware()
                text = (
                    f"CUDA:      {hw.cuda_rust}\n"
                    f"GPU:       {hw.gpu or 'N/A'}\n"
                    f"OpenCL:    {hw.opencl}\n"
                    f"OpenCL device: {hw.opencl_device or 'N/A'}\n"
                    f"CPU:       Always available\n"
                )
            except Exception:
                text = "Hardware detection unavailable."
            self._set_text(self.hw_text, text)

        def _update_recommendation(self) -> None:
            try:
                from hardware_routing import recommend
                code = self.state.current_code if self.state else None
                nq = code.n_qubits if code else None
                family = self.state.current_family_key if self.state else None
                d = self.state.current_param if self.state else None
                rec = recommend(family, d, nq, "balanced")
                text = (
                    f"Recommended:   {rec.decoder}\n"
                    f"Priority:      {rec.priority}\n"
                    f"Hardware:      {rec.hardware}\n"
                    f"Batch size:    {rec.batch_size}\n"
                    f"GPU batched BP: {rec.gpu_batched_bp}\n"
                    f"Reason:        {rec.reason}\n"
                )
            except Exception:
                text = "Build a code to get decoder recommendations."
            self._set_text(self.rec_text, text)

        def _update_system(self) -> None:
            import platform, sys
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=0.1)
                mem = psutil.virtual_memory().percent
                ps_text = f"CPU: {cpu}% | RAM: {mem}%"
            except Exception:
                ps_text = "psutil not available"
            text = (
                f"Platform:      {platform.platform()}\n"
                f"Python:        {sys.version.split()[0]}\n"
                f"Backend:       qector_decoder_v3 {be.PACKAGE_VERSION}\n"
                f"Resources:     {ps_text}\n"
            )
            self._set_text(self.sys_text, text)

        @staticmethod
        def _set_text(widget, text: str) -> None:
            try:
                widget.configure(state="normal")
                widget.delete("1.0", "end")
                widget.insert("1.0", text)
                widget.configure(state="disabled")
            except Exception:
                pass

else:
    class HardwareTab:
        def __init__(self, master=None, state=None, console=None, **kwargs):
            pass
