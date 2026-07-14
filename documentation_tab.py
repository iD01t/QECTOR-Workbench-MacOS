"""documentation_tab.py — In-app Documentation tab.

Professional documentation viewer and multi-format exporter (Markdown, JSON,
HTML, LaTeX, PDF, SVG) with provenance, code analysis, and decoder
recommendations.  Generation runs in a background thread so the GUI stays
responsive; every failure path is surfaced in the preview pane and console
instead of raising.
"""

from __future__ import annotations

import os

try:
    import customtkinter as ctk
    _HAS_GUI = True
except Exception:
    _HAS_GUI = False

import backend as be
from doc_generator import ProfessionalDocGenerator
from theme import COLORS, get_fonts
from threading_utils import run_in_background


if _HAS_GUI:

    class DocumentationTab(ctk.CTkFrame):
        """Professional documentation viewer and exporter."""

        def __init__(self, master, state=None, console=None, fonts=None, **kwargs):
            super().__init__(master, fg_color="transparent", **kwargs)
            self.state = state
            self.console = console
            self.fonts = fonts if fonts is not None else get_fonts()
            self.generator = ProfessionalDocGenerator()
            self._generating = False

            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)

            self._build_ui()

        # ------------------------------------------------------------------
        # UI construction
        # ------------------------------------------------------------------
        def _build_ui(self) -> None:
            scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_panel"], corner_radius=10)
            scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

            ctk.CTkLabel(
                scroll, text="Documentation Studio",
                font=ctk.CTkFont(family=self.fonts.heading, size=17, weight="bold"),
                text_color=COLORS["text_primary"],
            ).pack(anchor="w", padx=18, pady=(18, 4))

            ctk.CTkLabel(
                scroll,
                text="Premium multi-format export with provenance, code analysis, and decoder recommendations.",
                font=ctk.CTkFont(family=self.fonts.ui, size=11),
                text_color=COLORS["text_secondary"],
            ).pack(anchor="w", padx=18, pady=(0, 14))

            # Format selector
            self._build_format_section(scroll)
            # Preview
            self._build_preview_section(scroll)
            # Actions
            self._build_actions(scroll)

        def _build_format_section(self, scroll) -> None:
            section = ctk.CTkFrame(scroll, fg_color=COLORS["bg_panel_alt"], corner_radius=10)
            section.pack(fill="x", padx=18, pady=(0, 14))

            ctk.CTkLabel(
                section, text="Export Formats",
                font=ctk.CTkFont(family=self.fonts.heading, size=12, weight="bold"),
                text_color=COLORS["accent"],
            ).pack(anchor="w", padx=14, pady=(14, 8))

            row1 = ctk.CTkFrame(section, fg_color="transparent")
            row1.pack(fill="x", padx=14, pady=2)
            row2 = ctk.CTkFrame(section, fg_color="transparent")
            row2.pack(fill="x", padx=14, pady=(2, 14))

            self.fmt_md = ctk.BooleanVar(value=True)
            self.fmt_pdf = ctk.BooleanVar(value=False)
            self.fmt_html = ctk.BooleanVar(value=True)
            self.fmt_json = ctk.BooleanVar(value=True)
            self.fmt_latex = ctk.BooleanVar(value=False)
            self.fmt_svg = ctk.BooleanVar(value=False)

            for row, checks in [
                (row1, [("Markdown", self.fmt_md), ("HTML", self.fmt_html), ("LaTeX", self.fmt_latex)]),
                (row2, [("JSON", self.fmt_json), ("PDF", self.fmt_pdf), ("SVG", self.fmt_svg)]),
            ]:
                for label, var in checks:
                    ctk.CTkCheckBox(
                        row, text=label, variable=var,
                        fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"],
                    ).pack(side="left", padx=(0, 10))

            # Info
            info = ctk.CTkFrame(scroll, fg_color=COLORS["bg_panel_alt"], corner_radius=10)
            info.pack(fill="x", padx=18, pady=(0, 14))
            ctk.CTkLabel(
                info, text="Certified Provenance",
                font=ctk.CTkFont(family=self.fonts.heading, size=12, weight="bold"),
                text_color=COLORS["accent"],
            ).pack(anchor="w", padx=14, pady=(14, 6))
            ctk.CTkLabel(
                info,
                text=(
                    "All exports embed provenance metadata: doc generator version, "
                    "UTC timestamp, and the QECTOR CERTIFIED watermark for traceability."
                ),
                font=ctk.CTkFont(family=self.fonts.ui, size=11),
                text_color=COLORS["text_secondary"],
                wraplength=640, justify="left",
            ).pack(anchor="w", padx=14, pady=(0, 14))

        def _build_preview_section(self, scroll) -> None:
            preview_label = ctk.CTkLabel(
                scroll, text="Documentation Preview",
                font=ctk.CTkFont(family=self.fonts.heading, size=12, weight="bold"),
                text_color=COLORS["text_primary"],
            )
            preview_label.pack(anchor="w", padx=18, pady=(0, 6))

            self.preview = ctk.CTkTextbox(
                scroll, fg_color=COLORS["bg_panel_alt"], text_color=COLORS["text_primary"],
                font=ctk.CTkFont(family=self.fonts.mono, size=11), height=260, wrap="word",
            )
            self.preview.pack(fill="x", padx=18, pady=(0, 14))
            self.preview.configure(state="disabled")

        def _build_actions(self, scroll) -> None:
            actions = ctk.CTkFrame(scroll, fg_color="transparent")
            actions.pack(fill="x", padx=18, pady=(0, 18))

            self.generate_btn = ctk.CTkButton(
                actions, text="Generate Documentation", command=self._on_generate,
                fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"], text_color=COLORS["text_primary"],
                font=ctk.CTkFont(size=12, weight="bold"),
            )
            self.generate_btn.pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                actions, text="Open Export Folder", command=self._on_open_folder,
                fg_color=COLORS["bg_widget"], hover_color=COLORS["accent_dim"], text_color=COLORS["text_secondary"],
                font=ctk.CTkFont(size=11),
            ).pack(side="left", padx=8)

        # ------------------------------------------------------------------
        # Helpers (console/preview access never raises)
        # ------------------------------------------------------------------
        def _log(self, message: str, level: str = "INFO") -> None:
            if self.console is not None:
                try:
                    self.console.log(message, level)
                except Exception:
                    pass

        def _set_preview(self, text: str) -> None:
            try:
                self.preview.configure(state="normal")
                self.preview.delete("1.0", "end")
                self.preview.insert("1.0", text)
                self.preview.configure(state="disabled")
            except Exception:
                pass

        def _set_generate_enabled(self, enabled: bool) -> None:
            try:
                self.generate_btn.configure(state="normal" if enabled else "disabled")
            except Exception:
                pass

        def _marshal(self, fn) -> None:
            """Schedule ``fn`` on the Tk main thread; never raises."""
            try:
                self.after(0, fn)
            except Exception:
                pass

        # ------------------------------------------------------------------
        # Generation (background thread; results marshaled via .after)
        # ------------------------------------------------------------------
        def _on_generate(self) -> None:
            if self._generating:
                return
            code = getattr(self.state, "current_code", None) if self.state else None
            if code is None:
                self._log("Build a code first, then generate documentation.", "WARN")
                self._set_preview("No active code. Build a code in Code Explorer first.")
                return

            formats = []
            for var, fmt in [
                (self.fmt_md, "markdown"), (self.fmt_html, "html"),
                (self.fmt_json, "json"), (self.fmt_latex, "latex"),
                (self.fmt_pdf, "pdf"), (self.fmt_svg, "svg"),
            ]:
                try:
                    selected = bool(var.get())
                except Exception:
                    selected = False
                if selected:
                    formats.append(fmt)

            if not formats:
                self._log("Select at least one export format.", "WARN")
                self._set_preview("Select at least one export format.")
                return

            self._generating = True
            self._set_generate_enabled(False)
            self._set_preview(f"Generating documentation ({', '.join(formats)})...")
            self._log(f"Documentation generation started: {', '.join(formats)}", "INFO")
            try:
                run_in_background(self._generate_worker, args=(code, formats))
            except Exception as exc:
                # Thread could not even start — restore the UI immediately.
                self._generating = False
                self._set_generate_enabled(True)
                self._set_preview(f"Generation failed to start: {exc}")
                self._log(f"Documentation generation failed to start: {exc}", "ERROR")

        def _generate_worker(self, code, formats: list) -> None:
            """Background thread: run the generator, marshal results via .after."""
            try:
                results = self.generator.generate_all(code, formats=formats)
            except Exception as exc:
                self._marshal(lambda exc=exc: self._on_generate_error(exc))
                return
            self._marshal(lambda: self._on_generate_done(code, results))

        def _on_generate_error(self, exc: Exception) -> None:
            try:
                self._set_preview(f"Generation failed: {exc}")
                self._log(f"Documentation generation failed: {exc}", "ERROR")
            finally:
                self._generating = False
                self._set_generate_enabled(True)

        def _on_generate_done(self, code, results: dict) -> None:
            try:
                exported = [f"{fmt.upper()}: {path}\n" for fmt, (ok, path) in results.items() if ok and path]
                failed = [f"{fmt}: failed\n" for fmt, (ok, _) in results.items() if not ok]
                try:
                    summary = be.code_summary(code)
                except Exception:
                    summary = {}
                preview_text = (
                    f"Code: {getattr(code, 'name', summary.get('name', 'N/A'))}\n"
                    f"Qubits: {summary.get('n_qubits', '?')} | Checks: {summary.get('n_checks', '?')}\n\n"
                    "Exported files:\n" + ("".join(exported) if exported else "None\n") +
                    ("\nFailures:\n" + "".join(failed) if failed else "")
                )
                self._set_preview(preview_text)
                for fmt, (ok, path) in results.items():
                    if ok and path:
                        self._log(f"Generated {fmt}: {path}", "SUCCESS")
                    else:
                        self._log(f"Failed to generate {fmt}", "ERROR")
            except Exception as exc:
                self._set_preview(f"Generation finished but the preview failed: {exc}")
                self._log(f"Documentation preview failed: {exc}", "ERROR")
            finally:
                self._generating = False
                self._set_generate_enabled(True)

        # ------------------------------------------------------------------
        # Export folder
        # ------------------------------------------------------------------
        def _on_open_folder(self) -> None:
            try:
                target = str(self.generator.output_dir.resolve())
                os.makedirs(target, exist_ok=True)
                if hasattr(os, "startfile"):
                    os.startfile(target)
                else:
                    self._log(f"Export folder: {target}", "INFO")
            except Exception as exc:
                self._log(f"Could not open export folder: {exc}", "ERROR")

else:

    class DocumentationTab:
        """No-GUI fallback used when customtkinter is unavailable."""

        def __init__(self, master=None, state=None, console=None, fonts=None, **kwargs):
            self.state = state
            self.console = console
            self.fonts = fonts
