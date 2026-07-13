"""decoder_lab_tab.py — Decoder Lab tab for QECTOR Workbench.

Interactive decoder testing: select decoder, set error rate, run single decode,
inspect error, syndrome, and correction results.
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

    class DecoderLabTab(ctk.CTkFrame):
        """Interactive decoder laboratory panel."""

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
                scroll, text="Decoder Laboratory",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(16, 4))
            ctk.CTkLabel(
                scroll, text="Test decoders interactively on the current code.",
                font=ctk.CTkFont(size=11), text_color="gray",
            ).pack(anchor="w", padx=16, pady=(0, 12))

            # Decoder selector
            row0 = ctk.CTkFrame(scroll, fg_color="transparent")
            row0.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row0, text="Decoder:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.decoder_var = ctk.StringVar(value="union_find")
            self.decoder_menu = ctk.CTkOptionMenu(
                row0, values=list(be.DECODER_KINDS),
                variable=self.decoder_var, width=180,
            )
            self.decoder_menu.pack(side="left", padx=(12, 0))

            # Error rate
            row1 = ctk.CTkFrame(scroll, fg_color="transparent")
            row1.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row1, text="Error Rate:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.rate_var = ctk.DoubleVar(value=0.05)
            self.rate_slider = ctk.CTkSlider(
                row1, from_=0.01, to=0.5, number_of_steps=49,
                variable=self.rate_var, command=self._update_rate_label,
                width=250,
            )
            self.rate_slider.pack(side="left", padx=(12, 8))
            self.rate_label = ctk.CTkLabel(row1, text="0.05", font=ctk.CTkFont(size=12))
            self.rate_label.pack(side="left")

            # Seed
            row2 = ctk.CTkFrame(scroll, fg_color="transparent")
            row2.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row2, text="Seed:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.seed_var = ctk.IntVar(value=42)
            self.seed_entry = ctk.CTkEntry(row2, textvariable=self.seed_var, width=100)
            self.seed_entry.pack(side="left", padx=(12, 0))

            # Decode button
            btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
            btn_row.pack(fill="x", padx=16, pady=8)
            self.decode_btn = ctk.CTkButton(
                btn_row, text="Run Decode", command=self._on_decode,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.decode_btn.pack(side="left")

            # Decoder info
            self.info_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.info_frame.pack(fill="x", padx=16, pady=4)
            self.info_text = ctk.CTkTextbox(
                self.info_frame, height=60, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.info_text.pack(fill="both", expand=True)
            self.info_text.insert("1.0", "Select a decoder and run decode to see results.")
            self.info_text.configure(state="disabled")

            # Results display
            self.result_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.result_frame.pack(fill="x", padx=16, pady=(4, 16))
            self.result_text = ctk.CTkTextbox(
                self.result_frame, height=160, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.result_text.pack(fill="both", expand=True)
            self.result_text.insert("1.0", "Results will appear here.")
            self.result_text.configure(state="disabled")

            # Show decoder info on load
            self._update_decoder_info()

        def _update_rate_label(self, *args) -> None:
            self.rate_label.configure(text=f"{self.rate_var.get():.2f}")

        def _update_decoder_info(self) -> None:
            try:
                kind = self.decoder_var.get()
                info = be.get_decoder_info(kind)
                self._set_info_text(f"{info['name']}: {info['description']}")
            except Exception:
                pass

        def _on_decode(self) -> None:
            code = self.state.current_code if self.state else None
            if code is None:
                self._set_result_text("No active code. Build a code in Code Explorer first.")
                if self.console:
                    self.console.log("No active code for decode", "WARN")
                return
            kind = self.decoder_var.get()
            rate = self.rate_var.get()
            seed = self.seed_var.get()
            try:
                result = be.run_single_decode(code, rate, kind, seed)
                hw = result["result"].hamming_weight
                error_str = str(result["error"][:20])
                synd_str = str(result["syndrome"][:20])
                corr_str = str(result["result"].correction[:20])
                text = (
                    f"Decoder:        {kind}\n"
                    f"Error rate:     {rate:.2f}\n"
                    f"Seed:           {seed}\n"
                    f"Hamming weight: {hw}\n\n"
                    f"Error:     {error_str}\n"
                    f"Syndrome:  {synd_str}\n"
                    f"Correction:{corr_str}\n"
                )
                self._set_result_text(text)
                if self.console:
                    self.console.log(f"Decode {kind}: hw={hw}", "SUCCESS")
            except be.QectorError as e:
                self._set_result_text(f"Decode error: {e}")
                if self.console:
                    self.console.log(f"Decode failed: {e}", "ERROR")

        def _set_info_text(self, text: str) -> None:
            try:
                self.info_text.configure(state="normal")
                self.info_text.delete("1.0", "end")
                self.info_text.insert("1.0", text)
                self.info_text.configure(state="disabled")
            except Exception:
                pass

        def _set_result_text(self, text: str) -> None:
            try:
                self.result_text.configure(state="normal")
                self.result_text.delete("1.0", "end")
                self.result_text.insert("1.0", text)
                self.result_text.configure(state="disabled")
            except Exception:
                pass

else:
    class DecoderLabTab:
        def __init__(self, master=None, state=None, console=None, **kwargs):
            pass
