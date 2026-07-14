"""decoder_lab_tab.py — Decoder Lab tab for QECTOR Workbench.

Interactive decoder testing: select decoder (info updates live), set error
rate and seed, run a single decode in a background thread, and inspect the
error, syndrome, correction, syndrome validity, and logical failure.
"""

from __future__ import annotations

import tkinter
import traceback
from typing import Any, Optional

try:
    import customtkinter as ctk
    _HAS_GUI = True
except Exception:
    _HAS_GUI = False

import numpy as np

import backend as be
import theme
import threading_utils
import utils

_MAX_SEED = 2**31 - 1


if _HAS_GUI:

    class DecoderLabTab(ctk.CTkFrame):
        """Interactive decoder laboratory panel."""

        def __init__(self, master, state=None, console=None, fonts=None, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.state = state
            self.console = console
            self.fonts = fonts if fonts is not None else theme.get_fonts()

            self._ui = threading_utils.UiPump(self)
            self._run_seq = 0

            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)

            scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
            scroll.grid(row=0, column=0, sticky="nsew")
            scroll.grid_columnconfigure(0, weight=1)

            mono = ctk.CTkFont(family=self.fonts.mono, size=self.fonts.mono_size + 1)
            bold = ctk.CTkFont(size=12, weight="bold")

            ctk.CTkLabel(
                scroll, text="Decoder Laboratory",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(16, 4))
            ctk.CTkLabel(
                scroll, text="Test decoders interactively on the current code.",
                font=ctk.CTkFont(size=11), text_color=theme.COLORS["text_secondary"],
            ).pack(anchor="w", padx=16, pady=(0, 12))

            # Decoder selector — info text updates when the choice changes
            row0 = ctk.CTkFrame(scroll, fg_color="transparent")
            row0.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row0, text="Decoder:", font=bold).pack(side="left")
            self.decoder_var = ctk.StringVar(value="union_find")
            self.decoder_menu = ctk.CTkOptionMenu(
                row0, values=list(be.DECODER_KINDS),
                variable=self.decoder_var, width=180,
                command=self._on_decoder_change,
            )
            self.decoder_menu.pack(side="left", padx=(12, 0))

            # Error rate
            row1 = ctk.CTkFrame(scroll, fg_color="transparent")
            row1.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row1, text="Error Rate:", font=bold).pack(side="left")
            self.rate_var = ctk.DoubleVar(value=0.05)
            self.rate_slider = ctk.CTkSlider(
                row1, from_=0.01, to=0.5, number_of_steps=49,
                variable=self.rate_var, command=self._update_rate_label,
                width=250,
            )
            self.rate_slider.pack(side="left", padx=(12, 8))
            self.rate_label = ctk.CTkLabel(row1, text="0.05", font=ctk.CTkFont(size=12))
            self.rate_label.pack(side="left")

            # Seed (plain entry — validated as text, never crashes)
            row2 = ctk.CTkFrame(scroll, fg_color="transparent")
            row2.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row2, text="Seed:", font=bold).pack(side="left")
            self.seed_entry = ctk.CTkEntry(row2, width=100)
            self.seed_entry.insert(0, "42")
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
            self.info_text = ctk.CTkTextbox(scroll, height=60, wrap="word", font=mono)
            self.info_text.pack(fill="x", padx=16, pady=4)
            self.info_text.configure(state="disabled")

            # Results display
            self.result_text = ctk.CTkTextbox(scroll, height=230, wrap="word", font=mono)
            self.result_text.pack(fill="both", expand=True, padx=16, pady=(4, 16))
            self.result_text.insert("1.0", "Results will appear here.")
            self.result_text.configure(state="disabled")

            self._update_decoder_info()

        # ── helpers ────────────────────────────────────────────────────
        def _log(self, msg: str, level: str = "INFO") -> None:
            if self.console:
                try:
                    self.console.log(msg, level)
                except Exception:
                    pass

        def _update_rate_label(self, *_args) -> None:
            try:
                self.rate_label.configure(text=f"{self.rate_var.get():.2f}")
            except (tkinter.TclError, ValueError):
                pass

        def _on_decoder_change(self, _choice: str = "") -> None:
            self._update_decoder_info()

        def _update_decoder_info(self) -> None:
            try:
                kind = self.decoder_var.get()
                info = be.get_decoder_info(kind)
                self._set_text(self.info_text, f"{info['name']}: {info['description']}")
            except Exception:
                pass

        # ── decode action ──────────────────────────────────────────────
        def _on_decode(self) -> None:
            code = self.state.current_code if self.state else None
            if code is None:
                self._set_text(self.result_text, "No active code. Build a code in Code Explorer first.")
                self._log("No active code for decode", "WARN")
                return

            kind = self.decoder_var.get()
            try:
                rate = float(self.rate_var.get())
            except (tkinter.TclError, ValueError):
                self._set_text(self.result_text, "Invalid error rate — use the slider to pick a value.")
                return
            seed_text = self.seed_entry.get().strip()
            valid, msg = utils.validate_int(seed_text, min_val=0, max_val=_MAX_SEED)
            if not valid:
                self._set_text(self.result_text, f"Invalid seed: {msg}\nEnter an integer between 0 and {_MAX_SEED}.")
                return
            seed = int(seed_text)

            self._run_seq += 1
            seq = self._run_seq
            try:
                self.decode_btn.configure(state="disabled")
            except tkinter.TclError:
                return
            threading_utils.run_in_background(
                self._decode_worker, args=(seq, code, rate, kind, seed)
            )

        def _decode_worker(self, seq: int, code, rate: float, kind: str, seed: int) -> None:
            try:
                out = be.run_single_decode(code, rate, kind, seed)
                result = out["result"]
                payload = {
                    "kind": kind,
                    "rate": rate,
                    "seed": seed,
                    "hamming_weight": result.hamming_weight,
                    "syndrome_valid": result.syndrome_valid,
                    "logical_failure": result.logical_failure,
                    "error_str": np.array2string(np.asarray(out["error"])[:24], max_line_width=68),
                    "syndrome_str": np.array2string(np.asarray(out["syndrome"])[:24], max_line_width=68),
                    "correction_str": np.array2string(np.asarray(result.correction)[:24], max_line_width=68),
                }
                self._ui.post(self._on_decode_done, seq, payload)
            except be.QectorError as e:
                self._log(f"Decode failed: {e}", "ERROR")
                self._ui.post(self._on_decode_failed, seq, f"Decode error: {e}")
            except Exception as e:
                self._log(f"Unexpected decode error: {e}", "ERROR")
                self._log(traceback.format_exc(), "ERROR")
                self._ui.post(self._on_decode_failed, seq, f"Unexpected decode error: {e}")

        def _on_decode_done(self, seq: int, p: dict[str, Any]) -> None:
            if seq != self._run_seq:
                return
            try:
                lf = p["logical_failure"]
                lf_str = "N/A (code exposes no logicals matrix)" if lf is None else ("YES" if lf else "no")
                text = (
                    f"Decoder:         {p['kind']}\n"
                    f"Error rate:      {p['rate']:.2f}\n"
                    f"Seed:            {p['seed']}\n"
                    f"Hamming weight:  {p['hamming_weight']}\n"
                    f"Syndrome valid:  {'yes' if p['syndrome_valid'] else 'NO'}\n"
                    f"Logical failure: {lf_str}\n\n"
                    f"Error (first 24):      {p['error_str']}\n"
                    f"Syndrome (first 24):   {p['syndrome_str']}\n"
                    f"Correction (first 24): {p['correction_str']}\n"
                )
                self._set_text(self.result_text, text)
                self._log(
                    f"Decode {p['kind']}: hw={p['hamming_weight']} "
                    f"syndrome_valid={p['syndrome_valid']} logical_failure={lf}",
                    "SUCCESS",
                )
            except tkinter.TclError:
                pass
            finally:
                self._reenable(seq)

        def _on_decode_failed(self, seq: int, message: str) -> None:
            if seq != self._run_seq:
                return
            try:
                self._set_text(self.result_text, message)
            except tkinter.TclError:
                pass
            finally:
                self._reenable(seq)

        def _reenable(self, seq: int) -> None:
            if seq != self._run_seq:
                return
            try:
                self.decode_btn.configure(state="normal")
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
    class DecoderLabTab:
        def __init__(self, master=None, state=None, console=None, fonts=None, **kwargs):
            pass
