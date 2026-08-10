# QECTOR Decoder Workbench — macOS build

A macOS port of QECTOR Decoder Workbench v3.5.1. Builds a
signed (ad-hoc) `QectorWorkbench.app` and a distributable `.dmg` for **Apple
Silicon (arm64)** and **Intel (x86_64)**.

> The Workbench bundle deliberately excludes `qector-decoder-v3`. On first
> launch it provisions the wheel into the user's managed QECTOR data directory
> using a compatible system CPython + pip. See `../PACKAGING.md`.

> Must be built **on a Mac** — PyInstaller cannot cross-compile, and
> `iconutil`/`hdiutil`/`sips` are macOS-only. Use an Apple-Silicon Mac for the
> arm64 build and an Intel Mac (or Rosetta) for the x86_64 build, or the GitHub
> Actions `macos-14` (arm64) + `macos-13` (Intel) runners.

---

## Quick start

```bash
cd Mac

# Apple Silicon (arm64) — backend wheel comes from PyPI automatically
./build_macos.sh --test

# Intel (x86_64) — first drop the x86_64 backend wheel into wheels/ (see wheels/README.md)
./build_macos.sh --arch x86_64 --test
```

Output:

```
dist/QectorWorkbench.app
dist/QectorWorkbench-3.5.1-arm64.dmg     (or -x86_64.dmg)
```

Run it:

```bash
open dist/QectorWorkbench.app
# MCP (47-tool stdio server):
dist/QectorWorkbench.app/Contents/MacOS/QectorWorkbench --mcp
```

---

## The Intel wheel (important)

`qector-decoder-v3` v0.6.6 ships an **arm64** macOS wheel on PyPI but **no Intel
wheel**. `build_macos.sh` installs with `--find-links wheels/ --prefer-binary`,
so for the Intel build you place the x86_64 backend wheel in **`wheels/`** and it
is bundled/installed automatically. See **`wheels/README.md`** for how to obtain
or build that wheel from the published sdist (needs the Rust toolchain).

The arm64 build needs nothing in `wheels/`.

---

## `build_macos.sh` flags

| Flag             | Effect                                                        |
|------------------|---------------------------------------------------------------|
| `--arch arm64`   | Build the Apple-Silicon slice (default on Apple Silicon).     |
| `--arch x86_64`  | Build the Intel slice (needs an x86_64 Python + `wheels/`).   |
| `--test`         | Run the pytest suite before packaging.                        |
| `--clean`        | Remove `.venv/ build/ dist/` first.                           |
| `--no-dmg`       | Stop after the `.app`.                                        |
| `-h`, `--help`   | Usage.                                                        |

## What the build does

1. venv + `pip install --find-links wheels/ --prefer-binary -r requirements.txt`.
2. Generates the professional icon set from the SVG master: `icon.png` (window) and multi-resolution `icon.icns` (bundle, via `sips`+`iconutil`).
3. PyInstaller (`packaging/QectorWorkbench-macos.spec`) → `dist/QectorWorkbench.app`
   embedding Python 3.11+, Tcl/Tk, and Workbench dependencies, but no decoder.
4. **Ad-hoc code-signs** the bundle so it launches locally.
5. Packages a compressed `.dmg` with an `/Applications` drop link via `hdiutil`.

## macOS-native behaviour (shared, cross-platform source)

- **Window icon** via `iconphoto` + PNG; the `.app` icon is the generated `.icns`.
- **Fonts**: Menlo / Helvetica Neue on macOS (`theme.get_fonts()`).
- **"Open export folder"** uses `open` (`documentation_tab`).
- **Data dir**: `~/Library/Application Support/QectorWorkbench` (override with
  `QECTOR_DATA_DIR`).

## Feature parity

Same as the Linux/Windows builds: **13 decoders** (incl. `auto_router`, `hybrid_cascade`, `gnn_belief_matching`, `belief_matching`), **9 code
families** (incl. the qLDPC `bicycle` / `bivariate_bicycle` and the
`hypergraph_product` CSS family), a resilient self/auto-debug backend, a
**Diagnostics** tab, a **47-tool** MCP server, dynamic live versioning
(`version_service.py`), push-update support (`auto_updater`), ecosystem compatibility
reporting, high-DPI matplotlib figures, and the professional icon set (`.icns`
generated from the SVG master). Verify:

```bash
MPLBACKEND=Agg .venv/bin/python -m pytest -q      # unit + GUI + decoders + autodebug
MPLBACKEND=Agg .venv/bin/python test_mcp_all.py   # 47-tool MCP verification
```

## Gatekeeper / distribution

The ad-hoc signature lets the app run on the build machine. To distribute to
other Macs without the "unidentified developer" prompt, sign with a **Developer
ID Application** certificate (hardened runtime + `assets/QectorWorkbench.entitlements`)
and **notarize**:

```bash
codesign --force --deep --options runtime \
  --entitlements assets/QectorWorkbench.entitlements \
  --sign "Developer ID Application: <you>" dist/QectorWorkbench.app
xcrun notarytool submit dist/QectorWorkbench-3.5.1-arm64.dmg --keychain-profile <profile> --wait
xcrun stapler staple dist/QectorWorkbench-3.5.1-arm64.dmg
```

Recipients of an ad-hoc build can clear the quarantine flag with:
`xattr -dr com.apple.quarantine /Applications/QectorWorkbench.app`.

## Troubleshooting

- **`tkinter` missing** — use the python.org universal2 installer (bundles Tk) or
  `brew install python-tk`.
- **Intel build can't find the backend** — the x86_64 wheel isn't in `wheels/`;
  see `wheels/README.md`.
- **"cannot be opened because the developer cannot be verified"** — right-click →
  Open once, or `xattr -dr com.apple.quarantine <app>`, or notarize.
