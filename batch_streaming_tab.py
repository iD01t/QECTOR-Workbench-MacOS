"""batch_streaming_tab.py — Batch & Streaming tab for QECTOR Workbench.

Batch decode (CPU backend) and streaming session controls for
real-time decode visualization.
"""

from __future__ import annotations

import time
from typing import Any, Optional

try:
    import customtkinter as ctk
    _HAS_GUI = True
except Exception:
    _HAS_GUI = False

import backend as be


if _HAS_GUI:

    class BatchStreamingTab(ctk.CTkFrame):
        """Batch & streaming decode panel."""

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
                scroll, text="Batch & Streaming",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(16, 4))
            ctk.CTkLabel(
                scroll, text="Batch decode multiple error samples and run streaming sessions.",
                font=ctk.CTkFont(size=11), text_color="gray",
            ).pack(anchor="w", padx=16, pady=(0, 12))

            # --- Batch section ---
            ctk.CTkLabel(
                scroll, text="Batch Decode",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(8, 4))

            row0 = ctk.CTkFrame(scroll, fg_color="transparent")
            row0.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row0, text="Samples:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.batch_samples_var = ctk.IntVar(value=50)
            ctk.CTkEntry(row0, textvariable=self.batch_samples_var, width=80).pack(side="left", padx=(12, 20))
            ctk.CTkLabel(row0, text="Error Rate:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.batch_rate_var = ctk.DoubleVar(value=0.05)
            ctk.CTkEntry(row0, textvariable=self.batch_rate_var, width=80).pack(side="left", padx=(12, 20))
            ctk.CTkLabel(row0, text="Seed:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.batch_seed_var = ctk.IntVar(value=1)
            ctk.CTkEntry(row0, textvariable=self.batch_seed_var, width=80).pack(side="left", padx=(12, 0))

            # Backend selector
            row_be = ctk.CTkFrame(scroll, fg_color="transparent")
            row_be.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row_be, text="Backend:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.backend_var = ctk.StringVar(value="cpu")
            ctk.CTkOptionMenu(
                row_be, values=["cpu", "cuda", "opencl"],
                variable=self.backend_var, width=140,
            ).pack(side="left", padx=(12, 0))

            btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
            btn_row.pack(fill="x", padx=16, pady=8)
            self.batch_btn = ctk.CTkButton(
                btn_row, text="Run Batch Decode", command=self._on_batch,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.batch_btn.pack(side="left")

            # --- Streaming section ---
            ctk.CTkLabel(
                scroll, text="Streaming Session",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(12, 4))

            row1 = ctk.CTkFrame(scroll, fg_color="transparent")
            row1.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row1, text="Window:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.stream_window_var = ctk.IntVar(value=5)
            ctk.CTkEntry(row1, textvariable=self.stream_window_var, width=80).pack(side="left", padx=(12, 20))
            ctk.CTkLabel(row1, text="Rounds:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.stream_rounds_var = ctk.IntVar(value=10)
            ctk.CTkEntry(row1, textvariable=self.stream_rounds_var, width=80).pack(side="left", padx=(12, 20))
            ctk.CTkLabel(row1, text="Error Rate:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.stream_rate_var = ctk.DoubleVar(value=0.03)
            ctk.CTkEntry(row1, textvariable=self.stream_rate_var, width=80).pack(side="left", padx=(12, 0))

            stream_btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
            stream_btn_row.pack(fill="x", padx=16, pady=8)
            self.stream_btn = ctk.CTkButton(
                stream_btn_row, text="Run Streaming Session", command=self._on_stream,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.stream_btn.pack(side="left")

            # Results display
            self.result_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.result_frame.pack(fill="x", padx=16, pady=(4, 16))
            self.result_text = ctk.CTkTextbox(
                self.result_frame, height=200, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.result_text.pack(fill="both", expand=True)
            self.result_text.insert("1.0", "Run batch or streaming decode to see results.")
            self.result_text.configure(state="disabled")

        def _on_batch(self) -> None:
            code = self.state.current_code if self.state else None
            if code is None:
                self._set_result_text("No active code. Build a code in Code Explorer first.")
                return
            n = max(self.batch_samples_var.get(), 1)
            rate = self.batch_rate_var.get()
            seed = self.batch_seed_var.get()
            try:
                t0 = time.perf_counter()
                out = be.run_batch_decode(code, self.backend_var.get(), n_samples=n, error_rate=rate, seed=seed)
                elapsed = time.perf_counter() - t0
                corr = out.get("corrections", [])
                ler = out.get("logical_error_rate")
                ler_str = f"{ler:.4f}" if ler is not None else "N/A"
                mhw = out.get("mean_hamming_weight", 0)
                text = (
                    f"Batch decode: {n} samples  (backend: {out.get('backend_used', 'cpu')})\n"
                    f"Syndrome match rate: {out.get('success_rate', 0)*100:.1f}%\n"
                    f"Logical error rate:  {ler_str}\n"
                    f"Mean Hamming weight: {mhw:.2f}\n"
                    f"Corrections:  {len(corr)} total\n"
                    f"Time:         {elapsed*1000:.1f} ms\n"
                    f"Throughput:   {n/max(elapsed, 1e-9):.0f} decodes/s\n"
                )
                self._set_result_text(text)
                if self.console:
                    self.console.log(f"Batch {n} samples: {out.get('success_rate', 0)*100:.0f}% syndrome match", "SUCCESS")
            except be.QectorError as e:
                self._set_result_text(f"Batch error: {e}")

        def _on_stream(self) -> None:
            code = self.state.current_code if self.state else None
            if code is None:
                self._set_result_text("No active code. Build a code in Code Explorer first.")
                return
            try:
                result = be.run_streaming_session(
                    code,
                    window_size=self.stream_window_var.get(),
                    n_rounds=self.stream_rounds_var.get(),
                    error_rate=self.stream_rate_var.get(),
                    seed=1,
                )
                ler = result.get("logical_error_rate")
                ler_str = f"{ler:.4f}" if ler is not None else "N/A"
                text = (
                    f"Streaming Session Complete\n"
                    f"{'─' * 34}\n"
                    f"Committed count: {result.get('committed_count', 0)}\n"
                    f"Logical error rate: {ler_str}\n"
                    f"Session time:    {result.get('session_seconds', 0)*1000:.1f} ms\n"
                    f"Window size:     {result.get('window_size', 0)}\n"
                    f"Rounds:          {result.get('rounds', 0)}\n"
                )
                self._set_result_text(text)
                if self.console:
                    self.console.log(
                        f"Streaming done: {result.get('committed_count', 0)} committed, LER={ler_str}",
                        "SUCCESS",
                    )
            except be.QectorError as e:
                self._set_result_text(f"Streaming: {e}")

        def _set_result_text(self, text: str) -> None:
            try:
                self.result_text.configure(state="normal")
                self.result_text.delete("1.0", "end")
                self.result_text.insert("1.0", text)
                self.result_text.configure(state="disabled")
            except Exception:
                pass

else:
    class BatchStreamingTab:
        def __init__(self, master=None, state=None, console=None, **kwargs):
            pass
