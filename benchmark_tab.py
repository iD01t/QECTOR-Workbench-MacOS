"""benchmark_tab.py — Benchmark tab for QECTOR Workbench.

Run configurable benchmarks across decoders, view throughput/latency,
compare results, and export data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

try:
    import customtkinter as ctk
    _HAS_GUI = True
except Exception:
    _HAS_GUI = False

import backend as be


if _HAS_GUI:

    class BenchmarkTab(ctk.CTkFrame):
        """Professional benchmark runner panel."""

        def __init__(self, master, state=None, console=None, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.state = state
            self.console = console
            self._results: list[dict[str, Any]] = []
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)

            scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
            scroll.grid(row=0, column=0, sticky="nsew")
            scroll.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                scroll, text="Benchmark Suite",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(anchor="w", padx=16, pady=(16, 4))
            ctk.CTkLabel(
                scroll, text="Measure decoder throughput and latency across codes.",
                font=ctk.CTkFont(size=11), text_color="gray",
            ).pack(anchor="w", padx=16, pady=(0, 12))

            # Code family / distance
            row0 = ctk.CTkFrame(scroll, fg_color="transparent")
            row0.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row0, text="Code:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.family_var = ctk.StringVar(value="rotated_surface")
            ctk.CTkOptionMenu(
                row0, values=list(be.CODE_FAMILIES.keys()),
                variable=self.family_var, width=160,
            ).pack(side="left", padx=(12, 12))
            self.distance_var = ctk.IntVar(value=5)
            ctk.CTkSlider(
                row0, from_=3, to=11, number_of_steps=8,
                variable=self.distance_var, width=120,
            ).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row0, text="d=", font=ctk.CTkFont(size=11)).pack(side="left")
            self.dist_label = ctk.CTkLabel(row0, text="5", font=ctk.CTkFont(size=11))
            self.dist_label.pack(side="left")

            # Decoder selector
            row_dec = ctk.CTkFrame(scroll, fg_color="transparent")
            row_dec.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row_dec, text="Decoder:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.decoder_var = ctk.StringVar(value="union_find")
            ctk.CTkOptionMenu(
                row_dec, values=list(be.DECODER_KINDS),
                variable=self.decoder_var, width=180,
            ).pack(side="left", padx=(12, 0))

            # Samples / seed
            row1 = ctk.CTkFrame(scroll, fg_color="transparent")
            row1.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row1, text="Samples:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.samples_var = ctk.IntVar(value=200)
            ctk.CTkEntry(row1, textvariable=self.samples_var, width=80).pack(side="left", padx=(12, 20))
            ctk.CTkLabel(row1, text="Seed:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            self.seed_var = ctk.IntVar(value=42)
            ctk.CTkEntry(row1, textvariable=self.seed_var, width=80).pack(side="left", padx=(12, 0))

            # Run button
            btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
            btn_row.pack(fill="x", padx=16, pady=8)
            self.run_btn = ctk.CTkButton(
                btn_row, text="Run Benchmark", command=self._on_run,
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.run_btn.pack(side="left", padx=(0, 8))
            self.export_btn = ctk.CTkButton(
                btn_row, text="Export JSON", command=self._on_export,
                font=ctk.CTkFont(size=11),
            )
            self.export_btn.pack(side="left")

            # Results display
            self.result_frame = ctk.CTkFrame(scroll, fg_color="transparent")
            self.result_frame.pack(fill="x", padx=16, pady=(4, 16))
            self.result_text = ctk.CTkTextbox(
                self.result_frame, height=220, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=11),
            )
            self.result_text.pack(fill="both", expand=True)
            self.result_text.insert("1.0", "Run a benchmark to see results.")
            self.result_text.configure(state="disabled")

        def _on_run(self) -> None:
            family = self.family_var.get()
            d = self.distance_var.get()
            self.dist_label.configure(text=str(d))
            n = max(self.samples_var.get(), 1)
            seed = self.seed_var.get()
            try:
                code = be.build_code(family, d)
                result = be.run_benchmark(code, n_samples=n, seed=seed, decoder_kind=self.decoder_var.get())
                result["code_family"] = family
                result["distance"] = d
                self._results.append(result)
                self._show_result(result)
                if self.console:
                    self.console.log(
                        f"Benchmark {family} d={d}: {result['throughput_decodes_per_s']:.0f} dec/s",
                        "SUCCESS",
                    )
            except be.QectorError as e:
                self._set_result_text(f"Benchmark error: {e}")
                if self.console:
                    self.console.log(f"Benchmark failed: {e}", "ERROR")

        def _show_result(self, result: dict) -> None:
            ler = result.get('logical_error_rate')
            ler_str = f"{ler:.4f}" if ler is not None else "N/A"
            text = (
                f"Code:              {result.get('code_family', 'N/A')} d={result.get('distance', 'N/A')}\n"
                f"Throughput:        {result['throughput_decodes_per_s']:.0f} decodes/s\n"
                f"Decode time:       {result['decode_seconds']*1000:.2f} ms\n"
                f"Trials:            {result['n_trials']}\n"
                f"Error rate (p):    {result['p']}\n"
                f"Decoder:           {result.get('method', 'N/A')}\n"
                f"Backend:           {result.get('backend', 'N/A')}\n"
                f"Seed:              {result.get('seed', 'N/A')}\n"
                f"\n--- Latency (μs) ---\n"
                f"  p50:             {result.get('latency_p50_us', 0):.1f}\n"
                f"  p99:             {result.get('latency_p99_us', 0):.1f}\n"
                f"  min:             {result.get('latency_min_us', 0):.1f}\n"
                f"  max:             {result.get('latency_max_us', 0):.1f}\n"
                f"\nLogical error rate: {ler_str}\n"
            )
            self._set_result_text(text)

        def _on_export(self) -> None:
            if not self._results:
                self._set_result_text("No results to export.")
                return
            try:
                path = Path("benchmark_export.json")
                data = json.dumps(self._results, indent=2, default=str)
                path.write_text(data, encoding="utf-8")
                self._set_result_text(f"Exported {len(self._results)} results to {path.resolve()}")
                if self.console:
                    self.console.log(f"Benchmark exported to {path}", "SUCCESS")
            except Exception as e:
                if self.console:
                    self.console.log(f"Export failed: {e}", "ERROR")

        def _set_result_text(self, text: str) -> None:
            try:
                self.result_text.configure(state="normal")
                self.result_text.delete("1.0", "end")
                self.result_text.insert("1.0", text)
                self.result_text.configure(state="disabled")
            except Exception:
                pass

else:
    class BenchmarkTab:
        def __init__(self, master=None, state=None, console=None, **kwargs):
            pass
