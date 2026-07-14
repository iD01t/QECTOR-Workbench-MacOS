"""batch_streaming_tab.py — Batch & Streaming tab for QECTOR Workbench.

Batch decode on cpu/cuda/opencl backends (backend errors surfaced verbatim,
no silent fallback) and real sliding-window streaming sessions with decoder
selection.  Both run in background threads; results include an embedded
matplotlib chart (hamming-weight histogram for batch runs, per-round
committed-weight chart for streaming sessions).
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
_MAX_BATCH_SAMPLES = 100_000
_MAX_ROUNDS = 100_000
_MAX_WINDOW = 10_000
_BATCH_BACKENDS = ["cpu", "cuda", "opencl"]


if _HAS_GUI:

    class BatchStreamingTab(ctk.CTkFrame):
        """Batch & streaming decode panel."""

        def __init__(self, master, state=None, console=None, fonts=None, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.state = state
            self.console = console
            self.fonts = fonts if fonts is not None else theme.get_fonts()

            self._ui = threading_utils.UiPump(self)
            self._batch_seq = 0
            self._stream_seq = 0

            self.grid_columnconfigure(0, weight=0)
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(1, weight=1)

            mono = ctk.CTkFont(family=self.fonts.mono, size=self.fonts.mono_size + 1)
            bold = ctk.CTkFont(size=12, weight="bold")

            # ── Controls (row 0, spans both columns) ──────────────────
            controls = ctk.CTkFrame(self, fg_color="transparent")
            controls.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 4))

            ctk.CTkLabel(
                controls, text="Batch & Streaming",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(anchor="w", pady=(0, 2))
            ctk.CTkLabel(
                controls,
                text="Batch decode multiple error samples and run sliding-window streaming sessions.",
                font=ctk.CTkFont(size=11), text_color=theme.COLORS["text_secondary"],
            ).pack(anchor="w", pady=(0, 8))

            # Batch section
            ctk.CTkLabel(controls, text="Batch Decode", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(2, 2))
            brow = ctk.CTkFrame(controls, fg_color="transparent")
            brow.pack(fill="x", pady=2)
            ctk.CTkLabel(brow, text="Samples:", font=bold).pack(side="left")
            self.batch_samples_entry = ctk.CTkEntry(brow, width=70)
            self.batch_samples_entry.insert(0, "100")
            self.batch_samples_entry.pack(side="left", padx=(8, 16))
            ctk.CTkLabel(brow, text="Error Rate:", font=bold).pack(side="left")
            self.batch_rate_entry = ctk.CTkEntry(brow, width=70)
            self.batch_rate_entry.insert(0, "0.05")
            self.batch_rate_entry.pack(side="left", padx=(8, 16))
            ctk.CTkLabel(brow, text="Seed:", font=bold).pack(side="left")
            self.batch_seed_entry = ctk.CTkEntry(brow, width=70)
            self.batch_seed_entry.insert(0, "1")
            self.batch_seed_entry.pack(side="left", padx=(8, 16))
            ctk.CTkLabel(brow, text="Backend:", font=bold).pack(side="left")
            self.backend_var = ctk.StringVar(value="cpu")
            ctk.CTkOptionMenu(
                brow, values=list(_BATCH_BACKENDS),
                variable=self.backend_var, width=110,
            ).pack(side="left", padx=(8, 16))
            self.batch_btn = ctk.CTkButton(
                brow, text="Run Batch Decode", command=self._on_batch,
                font=ctk.CTkFont(size=12, weight="bold"), width=150,
            )
            self.batch_btn.pack(side="left")

            # Streaming section
            ctk.CTkLabel(controls, text="Streaming Session", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 2))
            srow = ctk.CTkFrame(controls, fg_color="transparent")
            srow.pack(fill="x", pady=2)
            ctk.CTkLabel(srow, text="Window:", font=bold).pack(side="left")
            self.stream_window_entry = ctk.CTkEntry(srow, width=60)
            self.stream_window_entry.insert(0, "5")
            self.stream_window_entry.pack(side="left", padx=(8, 16))
            ctk.CTkLabel(srow, text="Rounds:", font=bold).pack(side="left")
            self.stream_rounds_entry = ctk.CTkEntry(srow, width=60)
            self.stream_rounds_entry.insert(0, "20")
            self.stream_rounds_entry.pack(side="left", padx=(8, 16))
            ctk.CTkLabel(srow, text="Error Rate:", font=bold).pack(side="left")
            self.stream_rate_entry = ctk.CTkEntry(srow, width=60)
            self.stream_rate_entry.insert(0, "0.03")
            self.stream_rate_entry.pack(side="left", padx=(8, 16))
            ctk.CTkLabel(srow, text="Seed:", font=bold).pack(side="left")
            self.stream_seed_entry = ctk.CTkEntry(srow, width=60)
            self.stream_seed_entry.insert(0, "1")
            self.stream_seed_entry.pack(side="left", padx=(8, 16))
            ctk.CTkLabel(srow, text="Decoder:", font=bold).pack(side="left")
            self.stream_decoder_var = ctk.StringVar(value="union_find")
            ctk.CTkOptionMenu(
                srow, values=list(be.DECODER_KINDS),
                variable=self.stream_decoder_var, width=150,
            ).pack(side="left", padx=(8, 16))
            self.stream_btn = ctk.CTkButton(
                srow, text="Run Streaming Session", command=self._on_stream,
                font=ctk.CTkFont(size=12, weight="bold"), width=170,
            )
            self.stream_btn.pack(side="left")

            # ── Left column: results text ─────────────────────────────
            left = ctk.CTkFrame(self, fg_color="transparent", width=340)
            left.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(4, 12))
            left.grid_propagate(False)
            left.grid_columnconfigure(0, weight=1)
            left.grid_rowconfigure(0, weight=1)
            self.result_text = ctk.CTkTextbox(left, wrap="word", font=mono)
            self.result_text.grid(row=0, column=0, sticky="nsew")
            self.result_text.insert("1.0", "Run batch or streaming decode to see results.")
            self.result_text.configure(state="disabled")

            # ── Right column: matplotlib canvas (one shared figure) ───
            right = ctk.CTkFrame(self, fg_color=theme.COLORS["bg_panel"])
            right.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(4, 12))
            right.grid_columnconfigure(0, weight=1)
            right.grid_rowconfigure(0, weight=1)

            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            self._figure = Figure(figsize=(6.8, 4.2), dpi=100)
            theme.style_dark_figure(self._figure)
            self._mpl_canvas = FigureCanvasTkAgg(self._figure, master=right)
            self._mpl_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            self._draw_placeholder("Run a batch decode or streaming session to see charts.")

        # ── helpers ────────────────────────────────────────────────────
        def _log(self, msg: str, level: str = "INFO") -> None:
            if self.console:
                try:
                    self.console.log(msg, level)
                except Exception:
                    pass

        def _current_code(self):
            code = self.state.current_code if self.state else None
            if code is None:
                self._set_result_text("No active code. Build a code in Code Explorer first.")
                self._log("No active code for batch/streaming", "WARN")
            return code

        def _read_int(self, entry, label: str, min_val: int, max_val: int) -> Optional[int]:
            text = entry.get().strip()
            valid, msg = utils.validate_int(text, min_val=min_val, max_val=max_val)
            if not valid:
                self._set_result_text(
                    f"Invalid {label}: {msg}\nEnter an integer between {min_val} and {max_val}."
                )
                return None
            return int(text)

        def _read_rate(self, entry, label: str) -> Optional[float]:
            text = entry.get().strip()
            try:
                rate = float(text)
            except ValueError:
                self._set_result_text(f"Invalid {label}: {text!r}\nEnter a number between 0 and 1 (e.g. 0.05).")
                return None
            if not (0.0 < rate < 1.0):
                self._set_result_text(f"{label} {rate} out of range — it must be strictly between 0 and 1.")
                return None
            return rate

        # ── batch action ───────────────────────────────────────────────
        def _on_batch(self) -> None:
            code = self._current_code()
            if code is None:
                return
            n = self._read_int(self.batch_samples_entry, "sample count", 1, _MAX_BATCH_SAMPLES)
            if n is None:
                return
            rate = self._read_rate(self.batch_rate_entry, "error rate")
            if rate is None:
                return
            seed = self._read_int(self.batch_seed_entry, "seed", 0, _MAX_SEED)
            if seed is None:
                return
            backend = self.backend_var.get()

            self._batch_seq += 1
            seq = self._batch_seq
            try:
                self.batch_btn.configure(state="disabled")
            except tkinter.TclError:
                return
            self._set_result_text(f"Running batch decode ({n} samples, backend={backend}) ...")
            threading_utils.run_in_background(
                self._batch_worker, args=(seq, code, backend, n, rate, seed)
            )

        def _batch_worker(self, seq: int, code, backend: str, n: int, rate: float, seed: int) -> None:
            try:
                out = be.run_batch_decode(code, backend, n, rate, seed)
                weights = np.sum(np.asarray(out["corrections"], dtype=np.int64), axis=1)
                payload = {
                    "n_samples": out["n_samples"],
                    "backend_used": out["backend_used"],
                    "success_rate": out["success_rate"],
                    "logical_error_rate": out["logical_error_rate"],
                    "mean_hamming_weight": out["mean_hamming_weight"],
                    "batch_seconds": out["batch_seconds"],
                    "weights": weights.tolist(),
                }
                self._ui.post(self._on_batch_done, seq, payload)
            except be.QectorError as e:
                # Backend errors (e.g. "cuda backend unavailable ...") are
                # surfaced verbatim — no silent fallback.
                self._log(f"Batch decode failed: {e}", "ERROR")
                self._ui.post(self._on_batch_failed, seq, str(e))
            except Exception as e:
                self._log(f"Unexpected batch error: {e}", "ERROR")
                self._log(traceback.format_exc(), "ERROR")
                self._ui.post(self._on_batch_failed, seq, f"Unexpected batch error: {e}")

        def _on_batch_done(self, seq: int, p: dict[str, Any]) -> None:
            if seq != self._batch_seq:
                return
            try:
                ler = p["logical_error_rate"]
                ler_str = f"{ler:.4f}" if ler is not None else "N/A (no logicals matrix)"
                n = p["n_samples"]
                secs = p["batch_seconds"]
                text = (
                    f"Batch Decode Complete\n"
                    f"{'-' * 34}\n"
                    f"Samples:             {n}\n"
                    f"Backend used:        {p['backend_used']}\n"
                    f"Syndrome match rate: {p['success_rate'] * 100:.1f}%\n"
                    f"Logical error rate:  {ler_str}\n"
                    f"Mean Hamming weight: {p['mean_hamming_weight']:.2f}\n"
                    f"Batch time:          {secs * 1000:.2f} ms\n"
                    f"Throughput:          {n / max(secs, 1e-9):.0f} decodes/s\n"
                )
                self._set_result_text(text)
                self._draw_batch_histogram(p)
                self._log(
                    f"Batch {n} samples on {p['backend_used']}: "
                    f"{p['success_rate'] * 100:.0f}% syndrome match, LER={ler_str}",
                    "SUCCESS",
                )
            except tkinter.TclError:
                pass
            except Exception as e:
                self._log(f"Batch chart rendering failed: {e}", "ERROR")
            finally:
                self._reenable_batch(seq)

        def _on_batch_failed(self, seq: int, message: str) -> None:
            if seq != self._batch_seq:
                return
            try:
                self._set_result_text(f"Batch decode failed:\n{message}")
            except tkinter.TclError:
                pass
            finally:
                self._reenable_batch(seq)

        def _reenable_batch(self, seq: int) -> None:
            if seq != self._batch_seq:
                return
            try:
                self.batch_btn.configure(state="normal")
            except tkinter.TclError:
                pass

        # ── streaming action ───────────────────────────────────────────
        def _on_stream(self) -> None:
            code = self._current_code()
            if code is None:
                return
            window = self._read_int(self.stream_window_entry, "window size", 1, _MAX_WINDOW)
            if window is None:
                return
            rounds = self._read_int(self.stream_rounds_entry, "round count", 0, _MAX_ROUNDS)
            if rounds is None:
                return
            rate = self._read_rate(self.stream_rate_entry, "error rate")
            if rate is None:
                return
            seed = self._read_int(self.stream_seed_entry, "seed", 0, _MAX_SEED)
            if seed is None:
                return
            kind = self.stream_decoder_var.get()

            self._stream_seq += 1
            seq = self._stream_seq
            try:
                self.stream_btn.configure(state="disabled")
            except tkinter.TclError:
                return
            self._set_result_text(f"Running streaming session ({rounds} rounds, window={window}, decoder={kind}) ...")
            threading_utils.run_in_background(
                self._stream_worker, args=(seq, code, window, rounds, rate, seed, kind)
            )

        def _stream_worker(self, seq: int, code, window: int, rounds: int,
                           rate: float, seed: int, kind: str) -> None:
            try:
                result = be.run_streaming_session(
                    code, window_size=window, n_rounds=rounds,
                    error_rate=rate, seed=seed, decoder_kind=kind,
                )
                weights = [int(np.sum(c)) for c in result["committed_corrections"]]
                payload = {
                    "committed_count": result["committed_count"],
                    "rounds": result["rounds"],
                    "window_size": result["window_size"],
                    "session_seconds": result["session_seconds"],
                    "logical_error_rate": result["logical_error_rate"],
                    "weights": weights,
                    "decoder": kind,
                }
                self._ui.post(self._on_stream_done, seq, payload)
            except be.QectorError as e:
                self._log(f"Streaming session failed: {e}", "ERROR")
                self._ui.post(self._on_stream_failed, seq, str(e))
            except Exception as e:
                self._log(f"Unexpected streaming error: {e}", "ERROR")
                self._log(traceback.format_exc(), "ERROR")
                self._ui.post(self._on_stream_failed, seq, f"Unexpected streaming error: {e}")

        def _on_stream_done(self, seq: int, p: dict[str, Any]) -> None:
            if seq != self._stream_seq:
                return
            try:
                ler = p["logical_error_rate"]
                ler_str = f"{ler:.4f}" if ler is not None else "N/A (no logicals matrix)"
                text = (
                    f"Streaming Session Complete\n"
                    f"{'-' * 34}\n"
                    f"Decoder:            {p['decoder']}\n"
                    f"Committed count:    {p['committed_count']}\n"
                    f"Rounds:             {p['rounds']}\n"
                    f"Window size:        {p['window_size']}\n"
                    f"Session time:       {p['session_seconds'] * 1000:.2f} ms\n"
                    f"Logical error rate: {ler_str}\n"
                )
                self._set_result_text(text)
                self._draw_stream_chart(p)
                self._log(
                    f"Streaming done ({p['decoder']}): {p['committed_count']} committed, LER={ler_str}",
                    "SUCCESS",
                )
            except tkinter.TclError:
                pass
            except Exception as e:
                self._log(f"Streaming chart rendering failed: {e}", "ERROR")
            finally:
                self._reenable_stream(seq)

        def _on_stream_failed(self, seq: int, message: str) -> None:
            if seq != self._stream_seq:
                return
            try:
                self._set_result_text(f"Streaming session failed:\n{message}")
            except tkinter.TclError:
                pass
            finally:
                self._reenable_stream(seq)

        def _reenable_stream(self, seq: int) -> None:
            if seq != self._stream_seq:
                return
            try:
                self.stream_btn.configure(state="normal")
            except tkinter.TclError:
                pass

        # ── drawing (UI thread only, one shared figure) ────────────────
        def _draw_placeholder(self, message: str) -> None:
            self._figure.clear()
            ax = self._figure.add_subplot(111)
            theme.style_dark_axes(ax, grid=False)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(
                0.5, 0.5, message, ha="center", va="center",
                color=theme.COLORS["text_secondary"], fontsize=10,
                transform=ax.transAxes,
            )
            self._mpl_canvas.draw_idle()

        def _draw_batch_histogram(self, p: dict[str, Any]) -> None:
            weights = np.asarray(p["weights"], dtype=np.int64)
            self._figure.clear()
            ax = self._figure.add_subplot(111)
            theme.style_dark_axes(
                ax,
                title=f"Correction Hamming weights — batch ({p['backend_used']}, n={p['n_samples']})",
                xlabel="hamming weight", ylabel="count",
            )
            if weights.size:
                low, high = int(weights.min()), int(weights.max())
                bins = np.arange(low, high + 2) - 0.5
                ax.hist(
                    weights, bins=bins, color=theme.COLORS["bar"],
                    edgecolor=theme.COLORS["fig_bg"], linewidth=0.5,
                )
            self._figure.tight_layout()
            self._mpl_canvas.draw_idle()

        def _draw_stream_chart(self, p: dict[str, Any]) -> None:
            weights = list(p["weights"])
            self._figure.clear()
            ax = self._figure.add_subplot(111)
            theme.style_dark_axes(
                ax,
                title=f"Committed correction weight per round — {p['decoder']} (window={p['window_size']})",
                xlabel="round", ylabel="hamming weight",
            )
            if weights:
                xs = np.arange(len(weights))
                colors = [
                    theme.COLORS["bar_hot"] if w > 0 else theme.COLORS["bar_dim"]
                    for w in weights
                ]
                ax.bar(xs, weights, color=colors, width=0.8)
                from matplotlib.patches import Patch
                legend = ax.legend(
                    handles=[
                        Patch(color=theme.COLORS["bar_hot"], label="nonzero weight"),
                        Patch(color=theme.COLORS["bar_dim"], label="zero weight"),
                    ],
                    loc="upper right", fontsize=7,
                )
                theme.style_dark_legend(legend)
            self._figure.tight_layout()
            self._mpl_canvas.draw_idle()

        def _set_result_text(self, text: str) -> None:
            try:
                self.result_text.configure(state="normal")
                self.result_text.delete("1.0", "end")
                self.result_text.insert("1.0", text)
                self.result_text.configure(state="disabled")
            except tkinter.TclError:
                pass

else:
    class BatchStreamingTab:
        def __init__(self, master=None, state=None, console=None, fonts=None, **kwargs):
            pass
