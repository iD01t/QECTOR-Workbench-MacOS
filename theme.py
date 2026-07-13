"""theme.py — Theme and font definitions for QECTOR Workbench."""

from __future__ import annotations

from types import SimpleNamespace

COLORS = {
    "bg_panel": "#2b2b2b",
    "bg_panel_alt": "#333333",
    "bg_widget": "#3a3a3a",
    "text_primary": "#dcdcdc",
    "text_secondary": "#a0a0a0",
    "accent": "#4a9eff",
    "accent_dim": "#3a7bd5",
}

Fonts = SimpleNamespace


def get_fonts() -> SimpleNamespace:
    """Return a namespace with font definitions."""
    return SimpleNamespace(
        mono="Consolas",
        ui="Segoe UI",
        heading="Segoe UI",
        mono_size=10,
        ui_size=10,
        heading_size=14,
    )
