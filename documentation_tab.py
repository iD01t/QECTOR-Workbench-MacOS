"""
ui/documentation_tab.py — In-app Documentation tab.

Reads the active code from shared AppState and renders structured docs
plus real export buttons wired to ProfessionalDocGenerator.
"""

from __future__ import annotations

import os
from pathlib import Path

import customtkinter as ctk
import backend as be
from doc_generator import ProfessionalDocGenerator
from state import AppState
from theme import COLORS, Fonts
from console import ConsoleLog


class DocumentationTab(ctk.CTkFrame):
    """Premium documentation viewer and exporter."""

    def __init__(self, master, state: AppState, fonts: Fonts, console: ConsoleLog, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.state = state
        self.fonts = fonts
        self.console = console
        self.generator = ProfessionalDocGenerator()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()

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
            text="Premium multi-format export — HTML / MD / LaTeX / JSON — with full provenance.",
            font=ctk.CTkFont(family=self.fonts.ui, size=11),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", padx=18, pady=(0, 14))

        # Format selector section
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
        row2.pack(fill="x", padx=14, pady=2)

        self.fmt_md = ctk.BooleanVar(value=True)
        self.fmt_pdf = ctk.BooleanVar(value=True)
        self.fmt_html = ctk.BooleanVar(value=True)
        self.fmt_json = ctk.BooleanVar(value=True)
        self.fmt_latex = ctk.BooleanVar(value=False)
        self.fmt_svg = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(row1, text="Markdown", variable=self.fmt_md,
                        fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"]).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(row1, text="HTML", variable=self.fmt_html,
                        fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"]).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(row1, text="LaTeX", variable=self.fmt_latex,
                        fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"]).pack(side="left")

        ctk.CTkCheckBox(row2, text="JSON", variable=self.fmt_json,
                        fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"]).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(row2, text="PDF", variable=self.fmt_pdf,
                        fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"]).pack(side="left", padx=(0, 10))
        ctk.CTkCheckBox(row2, text="SVG", variable=self.fmt_svg,
                        fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"]).pack(side="left")

        # Info section
        info = ctk.CTkFrame(scroll, fg_color=COLORS["bg_panel_alt"], corner_radius=10)
        info.pack(fill="x", padx=18, pady=(0, 14))

        ctk.CTkLabel(
            info, text="Certified Provenance",
            font=ctk.CTkFont(family=self.fonts.heading, size=12, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w", padx=14, pady=(14, 6))

        meta = ctk.CTkLabel(
            info,
            text="All exports include embedded provenance metadata: generator version, backend version, timestamp, author, and ORCID.",
            font=ctk.CTkFont(family=self.fonts.ui, size=11),
            text_color=COLORS["text_secondary"],
            wraplength=640,
            justify="left",
        )
        meta.pack(anchor="w", padx=14, pady=(0, 14))

        # Preview pane
        preview_label = ctk.CTkLabel(
            scroll, text="Documentation Preview",
            font=ctk.CTkFont(family=self.fonts.heading, size=12, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        preview_label.pack(anchor="w", padx=18, pady=(0, 6))

        self.preview = ctk.CTkTextbox(
            scroll, fg_color=COLORS["bg_panel_alt"], text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=self.fonts.mono, size=11), height=220, wrap="word",
        )
        self.preview.pack(fill="x", padx=18, pady=(0, 14))
        self.preview.configure(state="disabled")

        # Actions
        actions = ctk.CTkFrame(scroll, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=(0, 18))

        ctk.CTkButton(
            actions, text="Generate Documentation", command=self._on_generate,
            fg_color=COLORS["accent_dim"], hover_color=COLORS["accent"], text_color=COLORS["text_primary"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            actions, text="Open Export Folder", command=self._on_open_folder,
            fg_color=COLORS["bg_widget"], hover_color=COLORS["accent_dim"], text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=8)

    def _set_preview(self, text: str) -> None:
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _on_generate(self) -> None:
        code = self.state.current_code
        if code is None:
            self.console.log("Build a code first, then generate documentation.", "WARN")
            self._set_preview("No active code. Build a code in Code Explorer first.")
            return

        formats = []
        if self.fmt_md.get():
            formats.append("markdown")
        if self.fmt_pdf.get():
            formats.append("pdf")
        if self.fmt_html.get():
            formats.append("html")
        if self.fmt_json.get():
            formats.append("json")
        if self.fmt_latex.get():
            formats.append("latex")
        if self.fmt_svg.get():
            formats.append("svg")

        if not formats:
            self.console.log("Select at least one export format.", "WARN")
            self._set_preview("Select at least one export format.")
            return

        try:
            results = self.generator.generate_all(code, formats=formats)
        except Exception as exc:
            self.console.log(f"Documentation generation failed: {exc}", "ERROR")
            self._set_preview(f"Generation failed: {exc}")
            return

        exported = [f"{fmt.upper()}: {path}\n" for fmt, (ok, path) in results.items() if ok and path]
        failed = [f"{fmt}: failed\n" for fmt, (ok, _) in results.items() if not ok]

        summary = be.code_summary(code)
        preview_text = (
            f"Code: {summary['name']}\n"
            f"Distance: {summary['distance']} | Qubits: {summary['n_qubits']} | Checks: {summary['n_checks']}\n\n"
            "Exported files:\n" + ("".join(exported) if exported else "None\n") +
            ("\nFailures:\n" + "".join(failed) if failed else "")
        )
        self._set_preview(preview_text)

        for fmt, (ok, path) in results.items():
            if ok and path:
                self.console.log(f"Generated {fmt}: {path}", "SUCCESS")
            else:
                self.console.log(f"Failed to generate {fmt}", "ERROR")

    def _on_open_folder(self) -> None:
        target = self.generator.output_dir
        try:
            os.makedirs(target, exist_ok=True)
            if hasattr(os, "startfile"):
                os.startfile(str(target))
            else:
                self.console.log(f"Export folder: {target}", "INFO")
        except Exception as exc:
            self.console.log(f"Could not open export folder: {exc}", "ERROR")
