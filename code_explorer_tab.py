"""code_explorer_tab.py — Code Explorer tab for QECTOR Workbench.

Code family browser with a debounced distance slider, background code
building, rich property/analysis panels, and an embedded matplotlib view
that toggles between a professional Tanner graph and the parity-check
matrix (dark-styled to match the app theme).
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

_DEBOUNCE_MS = 200
_VIEW_TANNER = "Tanner graph"
_VIEW_MATRIX = "Parity-check matrix"


def _dense_parity_matrix(code) -> Optional[np.ndarray]:
    """Return the code's parity-check matrix as a dense uint8 2-D array.

    ``parity_check_matrix`` may be an attribute or a bound method, dense or
    sparse; returns None when no usable matrix can be extracted.
    """
    matrix = getattr(code, "parity_check_matrix", None)
    if matrix is None:
        matrix = getattr(code, "H", None)
    try:
        if callable(matrix):
            matrix = matrix()
    except Exception:
        return None
    if matrix is None:
        return None
    try:
        if hasattr(matrix, "todense"):
            matrix = matrix.todense()
        arr = np.asarray(matrix)
    except Exception:
        return None
    if arr.ndim != 2 or arr.size == 0:
        return None
    return (arr != 0).astype(np.uint8)


if _HAS_GUI:

    class CodeExplorerTab(ctk.CTkFrame):
        """Full code exploration panel."""

        def __init__(self, master, state=None, console=None, fonts=None, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.state = state
            self.console = console
            self.fonts = fonts if fonts is not None else theme.get_fonts()

            self._ui = threading_utils.UiPump(self)
            self._build_seq = 0
            self._debounce_id: Optional[str] = None
            self._graph_data: Optional[dict[str, Any]] = None

            self.grid_columnconfigure(0, weight=0)
            self.grid_columnconfigure(1, weight=1)
            self.grid_rowconfigure(1, weight=1)

            mono = ctk.CTkFont(family=self.fonts.mono, size=self.fonts.mono_size + 1)
            bold = ctk.CTkFont(size=12, weight="bold")

            # ── Controls (row 0, spans both columns) ──────────────────
            controls = ctk.CTkFrame(self, fg_color="transparent")
            controls.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(10, 4))

            ctk.CTkLabel(
                controls, text="Code Explorer",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(anchor="w", pady=(0, 2))
            ctk.CTkLabel(
                controls,
                text="Build and inspect quantum error correction codes.",
                font=ctk.CTkFont(size=11),
                text_color=theme.COLORS["text_secondary"],
            ).pack(anchor="w", pady=(0, 8))

            row = ctk.CTkFrame(controls, fg_color="transparent")
            row.pack(fill="x")
            ctk.CTkLabel(row, text="Code Family:", font=bold).pack(side="left")
            self.family_var = ctk.StringVar(value="rotated_surface")
            self.family_menu = ctk.CTkOptionMenu(
                row, values=list(be.CODE_FAMILIES.keys()),
                variable=self.family_var, command=self._on_family_change,
                width=190,
            )
            self.family_menu.pack(side="left", padx=(10, 24))

            ctk.CTkLabel(row, text="Distance:", font=bold).pack(side="left")
            self.distance_var = ctk.IntVar(value=5)
            self.distance_slider = ctk.CTkSlider(
                row, from_=3, to=15, number_of_steps=12,
                variable=self.distance_var, command=self._on_slider_change,
                width=240,
            )
            self.distance_slider.pack(side="left", padx=(10, 8))
            self.distance_label = ctk.CTkLabel(row, text="5", width=24, font=ctk.CTkFont(size=12))
            self.distance_label.pack(side="left", padx=(0, 24))

            self.build_btn = ctk.CTkButton(
                row, text="Build Code", command=self._on_build,
                font=ctk.CTkFont(size=12, weight="bold"), width=120,
            )
            self.build_btn.pack(side="left")

            self.status_label = ctk.CTkLabel(
                row, text="", font=ctk.CTkFont(size=11),
                text_color=theme.COLORS["text_secondary"],
            )
            self.status_label.pack(side="left", padx=(14, 0))

            # ── Left column: properties + analysis ────────────────────
            left = ctk.CTkFrame(self, fg_color="transparent", width=340)
            left.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(4, 12))
            left.grid_propagate(False)
            left.grid_columnconfigure(0, weight=1)
            left.grid_rowconfigure(1, weight=3)
            left.grid_rowconfigure(3, weight=2)

            ctk.CTkLabel(left, text="Properties", font=bold).grid(row=0, column=0, sticky="w")
            self.props_text = ctk.CTkTextbox(left, wrap="word", font=mono)
            self.props_text.grid(row=1, column=0, sticky="nsew", pady=(2, 8))
            self.props_text.insert("1.0", "Build a code to see its properties.")
            self.props_text.configure(state="disabled")

            ctk.CTkLabel(left, text="Analysis", font=bold).grid(row=2, column=0, sticky="w")
            self.analysis_text = ctk.CTkTextbox(left, wrap="word", font=mono)
            self.analysis_text.grid(row=3, column=0, sticky="nsew", pady=(2, 0))
            self.analysis_text.insert("1.0", "Analysis will appear here after building a code.")
            self.analysis_text.configure(state="disabled")

            # ── Right column: view toggle + matplotlib canvas ─────────
            right = ctk.CTkFrame(self, fg_color=theme.COLORS["bg_panel"])
            right.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(4, 12))
            right.grid_columnconfigure(0, weight=1)
            right.grid_rowconfigure(1, weight=1)

            self.view_toggle = ctk.CTkSegmentedButton(
                right, values=[_VIEW_TANNER, _VIEW_MATRIX],
                command=self._on_view_change,
                font=ctk.CTkFont(size=11),
            )
            self.view_toggle.set(_VIEW_TANNER)
            self.view_toggle.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))

            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

            self._figure = Figure(figsize=(6.4, 4.8), dpi=100)
            theme.style_dark_figure(self._figure)
            self._mpl_canvas = FigureCanvasTkAgg(self._figure, master=right)
            self._mpl_canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
            self._draw_placeholder("Build a code to see its Tanner graph.")

        # ── logging helper ─────────────────────────────────────────────
        def _log(self, msg: str, level: str = "INFO") -> None:
            if self.console:
                try:
                    self.console.log(msg, level)
                except Exception:
                    pass

        # ── event handlers ─────────────────────────────────────────────
        def _on_family_change(self, choice: str) -> None:
            self._log(f"Family changed to {choice}", "INFO")
            self._schedule_build()

        def _on_slider_change(self, value=None) -> None:
            """Debounce slider drags so we do not spam code builds."""
            try:
                d = int(round(float(value))) if value is not None else int(self.distance_var.get())
            except (TypeError, ValueError, tkinter.TclError):
                return
            try:
                self.distance_label.configure(text=str(d))
            except tkinter.TclError:
                return
            self._schedule_build()

        def _schedule_build(self) -> None:
            if self._debounce_id is not None:
                try:
                    self.after_cancel(self._debounce_id)
                except Exception:
                    pass
            try:
                self._debounce_id = self.after(_DEBOUNCE_MS, self._on_build)
            except tkinter.TclError:
                self._debounce_id = None

        def _on_build(self, *_args) -> None:
            """Validate inputs and build the selected code in the background."""
            self._debounce_id = None
            family = self.family_var.get()
            try:
                d = int(self.distance_var.get())
            except tkinter.TclError:
                self._set_text(self.props_text, "Invalid distance value — use the slider to pick 3-15.")
                return
            if family not in be.CODE_FAMILIES:
                self._set_text(self.props_text, f"Unknown code family: {family!r}")
                return

            self._build_seq += 1
            seq = self._build_seq
            try:
                self.build_btn.configure(state="disabled")
                self.status_label.configure(text=f"Building {family} d={d} ...")
            except tkinter.TclError:
                return
            threading_utils.run_in_background(self._build_worker, args=(seq, family, d))

        # ── worker (background thread) ─────────────────────────────────
        def _build_worker(self, seq: int, family: str, d: int) -> None:
            try:
                code = be.build_code(family, d)
                summary = be.code_summary(code)
                H = _dense_parity_matrix(code)
                q_coords, c_coords = be.get_tanner_graph_layout(code, family, d)
                analysis = self._analysis_text(code, family, d)
                payload = {
                    "code": code, "family": family, "d": d,
                    "summary": summary, "H": H,
                    "q_coords": q_coords, "c_coords": c_coords,
                    "analysis": analysis,
                }
                self._ui.post(self._on_build_done, seq, payload)
            except be.QectorError as e:
                self._log(f"Build failed: {e}", "ERROR")
                self._ui.post(self._on_build_failed, seq, f"Build failed: {e}")
            except Exception as e:
                self._log(f"Unexpected build error: {e}", "ERROR")
                self._log(traceback.format_exc(), "ERROR")
                self._ui.post(self._on_build_failed, seq, f"Unexpected build error: {e}")

        @staticmethod
        def _analysis_text(code, family: str, d: int) -> str:
            """Decoder recommendation for this code (safe to call off-thread)."""
            try:
                from hardware_routing import recommend
                rec = recommend(family, d, getattr(code, "n_qubits", None), "balanced")
                return (
                    f"Recommended decoder: {rec.decoder}\n"
                    f"Priority:            {rec.priority}\n"
                    f"Hardware:            {rec.hardware}\n"
                    f"Batch size:          {rec.batch_size}\n"
                    f"Reason:              {rec.reason}\n"
                )
            except Exception:
                return "Code analysis: compatible with all decoders."

        # ── completion (UI thread via UiPump) ──────────────────────────
        def _on_build_done(self, seq: int, payload: dict[str, Any]) -> None:
            if seq != self._build_seq:
                return  # a newer build superseded this one
            code, family, d = payload["code"], payload["family"], payload["d"]
            summary = payload["summary"]
            try:
                if self.state:
                    self.state.set_code(code, family, d)

                n_qubits = summary.get("n_qubits", "?")
                n_checks = summary.get("n_checks", "?")
                try:
                    rate = f"{(n_qubits - n_checks) / n_qubits:.4f}"
                except Exception:
                    rate = "?"
                lines = [
                    f"Name:             {summary.get('name', family)}",
                    f"Family:           {family}",
                    f"Distance:         {summary.get('distance', d)}",
                    f"Qubits:           {n_qubits}",
                    f"Checks:           {n_checks}",
                    f"Rate (n-m)/n:     {rate}",
                ]
                if "max_qubit_degree" in summary:
                    lines.append(f"Max qubit degree: {summary['max_qubit_degree']}")
                if summary.get("description"):
                    lines.append("")
                    lines.append(str(summary["description"]))
                self._set_text(self.props_text, "\n".join(lines))
                self._set_text(self.analysis_text, payload["analysis"])

                self._graph_data = {
                    "q_coords": payload["q_coords"],
                    "c_coords": payload["c_coords"],
                    "H": payload["H"],
                    "name": str(summary.get("name", f"{family} d={d}")),
                }
                self._redraw()
                self.status_label.configure(text=f"Built {family} d={d}")
                self._log(f"Built {family} d={d}: {n_qubits} qubits, {n_checks} checks", "SUCCESS")
            except tkinter.TclError:
                pass
            finally:
                self._reenable(seq)

        def _on_build_failed(self, seq: int, message: str) -> None:
            if seq != self._build_seq:
                return
            try:
                self._set_text(self.props_text, message)
                self.status_label.configure(text="Build failed")
            except tkinter.TclError:
                pass
            finally:
                self._reenable(seq)

        def _reenable(self, seq: int) -> None:
            if seq != self._build_seq:
                return
            try:
                self.build_btn.configure(state="normal")
            except tkinter.TclError:
                pass

        # ── drawing (UI thread only) ───────────────────────────────────
        def _on_view_change(self, _choice: str = "") -> None:
            self._redraw()

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

        def _redraw(self) -> None:
            """Redraw the current view; figures are reused, never recreated."""
            data = self._graph_data
            if data is None:
                self._draw_placeholder("Build a code to see its Tanner graph.")
                return
            try:
                view = self.view_toggle.get()
            except tkinter.TclError:
                return
            try:
                if view == _VIEW_MATRIX:
                    self._draw_matrix(data)
                else:
                    self._draw_tanner(data)
            except Exception as e:
                self._log(f"Graph rendering failed: {e}", "ERROR")
                self._draw_placeholder(f"Graph rendering failed:\n{e}")

        def _draw_tanner(self, data: dict[str, Any]) -> None:
            from matplotlib.collections import LineCollection

            q_coords = data["q_coords"]
            c_coords = data["c_coords"]
            H = data["H"]

            self._figure.clear()
            ax = self._figure.add_subplot(111)
            theme.style_dark_axes(ax, title=f"Tanner graph — {data['name']}", grid=False)
            ax.set_xticks([])
            ax.set_yticks([])

            if H is not None and len(q_coords) and len(c_coords):
                rows, cols = np.nonzero(H)
                segments = [
                    (q_coords[c_idx], c_coords[r_idx])
                    for r_idx, c_idx in zip(rows, cols)
                    if r_idx < len(c_coords) and c_idx < len(q_coords)
                ]
                if segments:
                    ax.add_collection(LineCollection(
                        segments, colors=theme.COLORS["edge"],
                        linewidths=0.7, alpha=0.75, zorder=1,
                    ))

            n_nodes = len(q_coords) + len(c_coords)
            size = float(np.clip(2600.0 / max(n_nodes, 1), 14.0, 90.0))
            if q_coords:
                qx, qy = zip(*q_coords)
                ax.scatter(
                    qx, qy, s=size, marker="o",
                    c=theme.COLORS["qubit_node"],
                    edgecolors=theme.COLORS["fig_bg"], linewidths=0.5,
                    zorder=2, label="qubit",
                )
            if c_coords:
                cx, cy = zip(*c_coords)
                ax.scatter(
                    cx, cy, s=size, marker="s",
                    c=theme.COLORS["check_node"],
                    edgecolors=theme.COLORS["fig_bg"], linewidths=0.5,
                    zorder=2, label="check",
                )
            legend = ax.legend(loc="upper right", fontsize=8, scatterpoints=1)
            theme.style_dark_legend(legend)
            ax.set_aspect("equal", adjustable="datalim")
            ax.autoscale_view()
            ax.margins(0.08)
            self._mpl_canvas.draw_idle()

        def _draw_matrix(self, data: dict[str, Any]) -> None:
            from matplotlib.colors import ListedColormap

            H = data["H"]
            self._figure.clear()
            ax = self._figure.add_subplot(111)
            if H is None:
                theme.style_dark_axes(ax, grid=False)
                ax.set_xticks([])
                ax.set_yticks([])
                ax.text(
                    0.5, 0.5, "No parity-check matrix available for this code.",
                    ha="center", va="center", color=theme.COLORS["text_secondary"],
                    fontsize=10, transform=ax.transAxes,
                )
            else:
                theme.style_dark_axes(
                    ax, title=f"Parity-check matrix — {data['name']}",
                    xlabel="qubits", ylabel="checks", grid=False,
                )
                cmap = ListedColormap([theme.COLORS["axes_bg"], theme.COLORS["accent"]])
                ax.imshow(H, cmap=cmap, aspect="auto", interpolation="nearest", vmin=0, vmax=1)
            self._mpl_canvas.draw_idle()

        # ── textbox helper ─────────────────────────────────────────────
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
    class CodeExplorerTab:
        def __init__(self, master=None, state=None, console=None, fonts=None, **kwargs):
            pass
