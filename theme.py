"""theme.py — Theme, palette and font definitions for QECTOR Workbench."""

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
    # Status bar / toast / severity palette
    "bg_status": "#1f1f1f",
    "bg_toast": "#3a2a2a",
    "border_toast": "#ff5555",
    "error": "#ff5555",
    "warning": "#e5a53a",
    "success": "#4caf7d",
    "text_muted": "#8a8a8a",
    # Matplotlib dark-figure palette
    "fig_bg": "#242424",
    "axes_bg": "#2b2b2b",
    "grid": "#404040",
    "qubit_node": "#4a9eff",
    "check_node": "#ff9f43",
    "edge": "#6a6a6a",
    "bar": "#4a9eff",
    "bar_dim": "#3a5f8f",
    "bar_hot": "#ff9f43",
    "marker_p50": "#4caf7d",
    "marker_p99": "#ff9f43",
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


# ---------------------------------------------------------------------------
# Matplotlib dark styling helpers (figures are only ever touched on the Tk
# main thread; these helpers contain no matplotlib imports of their own so
# importing theme stays cheap).
# ---------------------------------------------------------------------------

def style_dark_figure(fig) -> None:
    """Apply the workbench dark palette to a matplotlib Figure."""
    try:
        fig.set_facecolor(COLORS["fig_bg"])
    except Exception:
        pass


def style_dark_axes(ax, title: str = "", xlabel: str = "", ylabel: str = "", grid: bool = True) -> None:
    """Apply the workbench dark palette to a matplotlib Axes.

    Sets facecolor, spine/tick colors, optional title and axis labels, and a
    subtle grid drawn below the data.
    """
    ax.set_facecolor(COLORS["axes_bg"])
    for spine in ax.spines.values():
        spine.set_color(COLORS["grid"])
    ax.tick_params(colors=COLORS["text_secondary"], labelsize=8)
    if title:
        ax.set_title(title, color=COLORS["text_primary"], fontsize=10)
    if xlabel:
        ax.set_xlabel(xlabel, color=COLORS["text_secondary"], fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=COLORS["text_secondary"], fontsize=9)
    if grid:
        ax.grid(True, color=COLORS["grid"], alpha=0.5, linewidth=0.5)
        ax.set_axisbelow(True)
    else:
        ax.grid(False)


def style_dark_legend(legend) -> None:
    """Style a matplotlib legend to match the dark palette."""
    if legend is None:
        return
    try:
        frame = legend.get_frame()
        frame.set_facecolor(COLORS["bg_panel"])
        frame.set_edgecolor(COLORS["grid"])
        for text in legend.get_texts():
            text.set_color(COLORS["text_primary"])
    except Exception:
        pass
