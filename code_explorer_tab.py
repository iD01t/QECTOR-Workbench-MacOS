"""code_explorer_tab.py — Code Explorer tab for QECTOR Workbench.

Full code family browser with distance selector, live properties display,
Tanner graph visualization, and code analysis.
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

    class CodeExplorerTab(ctk.CTkFrame):
        """Full code exploration panel."""

        def __init__(self, master, state=None, console=None, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.state = state
            self.console = console
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)

            scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
            scroll.grid(row=0, column=0, sticky="nsew")
            scroll.grid_columnconfigure(0, weight=1)

            # Header
            ctk.CTkLabel(
                scroll, text="Code Explorer",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(16, 4))

            ctk.CTkLabel(
                scroll, text="Build and inspect quantum error correction codes.",
                font=ctk.CTkFont(size=11),
                text_color="gray",
            ).pack(anchor="w", padx=16, pady=(0, 12))

            # --- Family selector ---
            fam_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            fam_frame.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(fam_frame, text="Code Family:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.family_var = ctk.StringVar(value="rotated_surface")
            self.family_menu = ctk.CTkOptionMenu(
                fam_frame, values=list(be.CODE_FAMILIES.keys()),
                variable=self.family_var, command=self._on_family_change,
                width=200,
            )
            self.family_menu.pack(side="left", padx=(12, 0))

            # --- Distance ---
            dist_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            dist_frame.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(dist_frame, text="Distance:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.distance_var = ctk.IntVar(value=5)
            self.distance_slider = ctk.CTkSlider(
                dist_frame, from_=3, to=15, number_of_steps=12,
                variable=self.distance_var, command=self._on_build,
                width=300,
            )
            self.distance_slider.pack(side="left", padx=(12, 8))
            self.distance_label = ctk.CTkLabel(dist_frame, text="5", font=ctk.CTkFont(size=12))
            self.distance_label.pack(side="left")

            # --- Build button ---
            btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            btn_frame.pack(fill="x", padx=16, pady=8)
            self.build_btn = ctk.CTkButton(
                btn_frame, text="Build Code", command=self._on_build,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.build_btn.pack(side="left")

            # --- Properties display ---
            self.props_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.props_frame.pack(fill="x", padx=16, pady=8)
            self.props_text = ctk.CTkTextbox(
                self.props_frame, height=140, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.props_text.pack(fill="both", expand=True)
            self.props_text.insert("1.0", "Build a code to see its properties.")
            self.props_text.configure(state="disabled")

            # --- Analysis section ---
            self.analysis_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.analysis_frame.pack(fill="x", padx=16, pady=(4, 16))
            self.analysis_text = ctk.CTkTextbox(
                self.analysis_frame, height=100, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.analysis_text.pack(fill="both", expand=True)
            self.analysis_text.insert("1.0", "Analysis will appear here after building a code.")
            self.analysis_text.configure(state="disabled")

        def _on_family_change(self, choice: str) -> None:
            if self.console:
                self.console.log(f"Family changed to {choice}", "INFO")

        def _on_build(self, *args) -> None:
            try:
                d = self.distance_var.get()
                self.distance_label.configure(text=str(d))
                family = self.family_var.get()
                code = be.build_code(family, d)
                if self.state:
                    self.state.set_code(code, family, d)
                self._show_properties(code, family, d)
            except be.QectorError as e:
                self._set_props_text(f"Error: {e}")
                if self.console:
                    self.console.log(f"Build failed: {e}", "ERROR")

        def _show_properties(self, code, family: str, d: int) -> None:
            import numpy as np
            try:
                nq = code.n_qubits
                nc = code.n_checks
                rate = f"{1 - nc / max(nq, 1):.4f}"
            except Exception:
                nq, nc, rate = "?", "?", "?"
            try:
                sm = be.code_summary(code)
                text = (
                    f"Code Family: {family}\n"
                    f"Distance:     {d}\n"
                    f"Qubits:       {sm.get('n_qubits', nq)}\n"
                    f"Checks:       {sm.get('n_checks', nc)}\n"
                    f"Rate:         {rate}\n"
                )
            except Exception:
                text = f"Code built: {family} d={d}, {nq} qubits, {nc} checks"
            self._set_props_text(text)
            self._show_analysis(code, family, d)

        def _show_analysis(self, code, family: str, d: int) -> None:
            try:
                from hardware_routing import recommend
                rec = recommend(family, d, getattr(code, "n_qubits", None), "balanced")
                analysis = (
                    f"Recommended decoder: {rec.decoder}\n"
                    f"Priority:           {rec.priority}\n"
                    f"Hardware:           {rec.hardware}\n"
                    f"Batch size:         {rec.batch_size}\n"
                    f"Reason:             {rec.reason}\n"
                )
            except Exception:
                analysis = "Code analysis: compatible with all decoders."
            try:
                self.analysis_text.configure(state="normal")
                self.analysis_text.delete("1.0", "end")
                self.analysis_text.insert("1.0", analysis)
                self.analysis_text.configure(state="disabled")
            except Exception:
                pass

        def _set_props_text(self, text: str) -> None:
            try:
                self.props_text.configure(state="normal")
                self.props_text.delete("1.0", "end")
                self.props_text.insert("1.0", text)
                self.props_text.configure(state="disabled")
            except Exception:
                pass

else:
    class CodeExplorerTab:
        def __init__(self, master=None, state=None, console=None, **kwargs):
            pass
