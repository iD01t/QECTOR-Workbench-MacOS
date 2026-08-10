#!/usr/bin/env python3
"""Generate assets/splash.png -- the boot splash shown by the frozen app.

The cold qector_decoder_v3 (Rust/PyO3) import plus PyInstaller onefile unpack
cost several seconds before the main window can exist.  PyInstaller shows this
image from the bootloader almost immediately, so the app is never invisible.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "splash.png")

W, H = 520, 260
BG = (18, 20, 26)
CARD = (24, 27, 35)
ACCENT = (77, 163, 255)
FG = (232, 236, 244)
DIM = (130, 148, 173)


def _font(size, bold=False):
    for name in (("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def main() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # Card + accent bar
    d.rounded_rectangle([10, 10, W - 10, H - 10], radius=14, fill=CARD)
    d.rounded_rectangle([10, 10, W - 10, 16], radius=3, fill=ACCENT)

    # Logo
    try:
        logo = Image.open(os.path.join(ROOT, "icon.png")).convert("RGBA")
        logo = logo.resize((72, 72), Image.LANCZOS)
        im.paste(logo, (38, 62), logo)
        text_x = 130
    except Exception:
        text_x = 40

    d.text((text_x, 62), "QECTOR", font=_font(38, bold=True), fill=FG)
    d.text((text_x + 3, 108), "Decoder Workbench", font=_font(15), fill=DIM)

    # Separator above the progress-text area that PyInstaller writes into
    d.line([(40, 176), (W - 40, 176)], fill=(46, 52, 66), width=1)

    im.save(OUT, "PNG")
    print(f"[OK] {OUT}  ({W}x{H})")


if __name__ == "__main__":
    main()
