#!/usr/bin/env bash
#
# build_macos.sh — all-in-one macOS build for QECTOR Decoder Workbench.
#
# Produces a signed (ad-hoc) app bundle and a distributable disk image:
#     dist/QectorWorkbench.app
#     dist/QectorWorkbench-<VERSION>-<arch>.dmg
#
# Pipeline: virtualenv -> pip install (wheels/ first, then PyPI) -> icon.icns ->
# optional pytest -> PyInstaller .app -> ad-hoc codesign -> .dmg.
#
# MUST be run on macOS (PyInstaller cannot cross-compile; iconutil/hdiutil/sips
# are macOS-only).  Build arm64 on Apple Silicon and x86_64 on an Intel Mac.
#
# Backend wheel: qector-decoder-v3 ships an arm64 macOS wheel on PyPI but NO
# Intel (x86_64) wheel.  For an Intel build, drop the x86_64 wheel into wheels/
# (see wheels/README.md); this script installs from wheels/ first.
#
# Usage:
#   ./build_macos.sh                 native-arch build + .dmg
#   ./build_macos.sh --arch x86_64   force Intel slice (needs x86_64 Python + wheel)
#   ./build_macos.sh --arch arm64    force Apple-Silicon slice
#   ./build_macos.sh --test          run pytest before packaging
#   ./build_macos.sh --clean         wipe .venv/ build/ dist/ first
#   ./build_macos.sh --no-dmg        stop at the .app
#   ./build_macos.sh -h | --help
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VERSION="$(tr -d ' \t\r\n' < VERSION 2>/dev/null || echo 3.5.0)"
APP="QectorWorkbench.app"
VENV="$ROOT/.venv"
BUILD="$ROOT/build"
DIST="$ROOT/dist"
WHEELS="$ROOT/wheels"
NATIVE_ARCH="$(uname -m)"        # arm64 | x86_64
TARGET_ARCH="$NATIVE_ARCH"

DO_TEST=0; DO_CLEAN=0; MAKE_DMG=1
while [ $# -gt 0 ]; do
    case "$1" in
        --arch)   TARGET_ARCH="${2:-}"; shift 2 ;;
        --test)   DO_TEST=1; shift ;;
        --clean)  DO_CLEAN=1; shift ;;
        --no-dmg) MAKE_DMG=0; shift ;;
        -h|--help) sed -n '3,33p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Unknown option: $1 (use --help)"; exit 2 ;;
    esac
done

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m OK\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  !\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERR\033[0m %s\n' "$*" >&2; exit 1; }

# --- 0. Platform / arch guards ---------------------------------------------
[ "$(uname -s)" = "Darwin" ] || die "build_macos.sh must run on macOS (uname=$(uname -s)). PyInstaller cannot cross-compile a .app."
case "$TARGET_ARCH" in arm64|x86_64) ;; *) die "invalid --arch '$TARGET_ARCH' (use arm64 or x86_64)";; esac

# Prefix used to force the target architecture (Rosetta) when it differs from
# the host — requires a matching-arch Python to exist.
ARCHPREFIX=""
if [ "$TARGET_ARCH" != "$NATIVE_ARCH" ]; then
    ARCHPREFIX="arch -$TARGET_ARCH"
    warn "Cross-arch build: $NATIVE_ARCH host -> $TARGET_ARCH target (needs an $TARGET_ARCH-capable Python and matching wheels in wheels/)."
fi

if [ "$DO_CLEAN" = "1" ]; then log "Cleaning .venv/ build/ dist/…"; rm -rf "$VENV" "$BUILD" "$DIST"; fi
mkdir -p "$BUILD" "$DIST" "$WHEELS"

# --- 1. Python >= 3.11 ------------------------------------------------------
PY=""
for cand in python3.12 python3.11 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
        if $ARCHPREFIX "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3,11) else 1)' 2>/dev/null; then
            PY="$cand"; break
        fi
    fi
done
[ -n "$PY" ] || die "Python >= 3.11 for $TARGET_ARCH not found. Install python.org universal2 build or a matching Homebrew Python."
log "Interpreter: $($ARCHPREFIX "$PY" -c 'import platform,sys; print(sys.executable, platform.machine(), "py"+".".join(map(str,sys.version_info[:3])))')"

# --- 2. venv + dependencies -------------------------------------------------
if [ ! -x "$VENV/bin/python" ]; then
    log "Creating virtualenv ($TARGET_ARCH)…"
    $ARCHPREFIX "$PY" -m venv "$VENV"
fi
VPY="$VENV/bin/python"
"$VPY" -c 'import tkinter' 2>/dev/null || die "tkinter missing from this Python. Use the python.org installer (bundles Tk) or 'brew install python-tk'."

log "Installing dependencies (wheels/ first, then PyPI)…"
"$VPY" -m pip install --upgrade pip wheel >/dev/null
# --find-links wheels/ + --prefer-binary makes a bundled Intel/arm wheel win.
if ! "$VPY" -m pip install --find-links "$WHEELS" --prefer-binary -r requirements.txt pyinstaller; then
    die "dependency install failed. For an Intel build, place the qector_decoder_v3 x86_64 macOS wheel in wheels/ (see wheels/README.md)."
fi
# Verify the compiled backend matches the target architecture.
BACK_ARCH="$("$VPY" -c 'import qector_decoder_v3,platform; print(platform.machine())' 2>/dev/null || echo unknown)"
ok "Dependencies installed (backend arch reports: $BACK_ARCH)."

# --- 3. Icons: icon.png (window) + icon.icns (bundle) -----------------------
log "Generating icon.png (256) and icon.icns…"
"$VPY" - <<'PY'
from PIL import Image
img = Image.open("assets/icon.jpg").convert("RGBA")
w, h = img.size; s = min(w, h); l, t = (w-s)//2, (h-s)//2
img.crop((l, t, l+s, t+s)).resize((256, 256), Image.LANCZOS).save("icon.png")
print("  icon.png 256x256")
PY
ICONSET="$BUILD/icon.iconset"
rm -rf "$ICONSET"; mkdir -p "$ICONSET"
if command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
    for sz in 16 32 128 256 512; do
        sips -z $sz $sz assets/icon.jpg --out "$ICONSET/icon_${sz}x${sz}.png" >/dev/null
        dbl=$((sz*2))
        sips -z $dbl $dbl assets/icon.jpg --out "$ICONSET/icon_${sz}x${sz}@2x.png" >/dev/null
    done
    iconutil -c icns "$ICONSET" -o "$ROOT/icon.icns"
    ok "icon.icns generated."
else
    warn "sips/iconutil not found — building without a bundle icon."
    : > "$ROOT/icon.icns" || true
fi

# --- 4. Optional test gate --------------------------------------------------
if [ "$DO_TEST" = "1" ]; then
    log "Running pytest…"
    # Test only: the production spec deliberately excludes this wheel.
    MPLBACKEND=Agg "$VPY" -m pip install pytest pytest-asyncio qector-decoder-v3 >/dev/null
    MPLBACKEND=Agg "$VPY" -m pytest -q
    ok "Tests passed."
fi

# --- 5. PyInstaller .app ----------------------------------------------------
log "Building QectorWorkbench.app (target arch: $TARGET_ARCH)…"
export QECTOR_TARGET_ARCH="$TARGET_ARCH"
"$VENV/bin/pyinstaller" --clean -y \
    --distpath "$DIST" --workpath "$BUILD/pyi" \
    packaging/QectorWorkbench-macos.spec
[ -d "$DIST/$APP" ] || die "PyInstaller did not produce $DIST/$APP"
ok "Bundle: $DIST/$APP"

# --- 6. Ad-hoc codesign (so Gatekeeper lets it launch locally) --------------
if command -v codesign >/dev/null 2>&1; then
    log "Ad-hoc code-signing the bundle…"
    codesign --force --deep --sign - "$DIST/$APP" 2>/dev/null \
        && ok "ad-hoc signed (for Developer ID distribution, re-sign + notarize)" \
        || warn "ad-hoc codesign failed (bundle still runs after: xattr -dr com.apple.quarantine)"
fi

if [ "$MAKE_DMG" = "0" ]; then
    ok "Stopping before .dmg (--no-dmg). Launch: open '$DIST/$APP'"
    exit 0
fi

# --- 7. .dmg ----------------------------------------------------------------
DMG="$DIST/QectorWorkbench-${VERSION}-${TARGET_ARCH}.dmg"
rm -f "$DMG"
log "Building disk image…"
STAGE="$BUILD/dmg"; rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R "$DIST/$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications" 2>/dev/null || true
cp EULA.txt "$STAGE/" 2>/dev/null || true
hdiutil create -volname "QECTOR Workbench $VERSION" -srcfolder "$STAGE" \
    -ov -format UDZO "$DMG" >/dev/null
[ -f "$DMG" ] || die "hdiutil did not produce $DMG"

# --- 8. Report --------------------------------------------------------------
echo
ok "Build complete."
echo "  App     : $DIST/$APP"
echo "  Disk img: $DMG"
echo "  Arch    : $TARGET_ARCH"
echo "  Size    : $(du -h "$DMG" | cut -f1)"
echo "  SHA256  : $(shasum -a 256 "$DMG" | cut -d' ' -f1)"
echo
echo "Run it:  open '$DIST/$APP'"
echo "MCP mode: '$DIST/$APP/Contents/MacOS/QectorWorkbench' --mcp"
