#!/usr/bin/env bash
# ==============================================================================
# build_macos.sh — Standalone macOS app builder for QECTOR Decoder Workbench
#
# Builds a self-contained QectorWorkbench.app bundle and compresses it into a
# distributable .dmg disk image.
#
# Target: Apple Silicon (arm64, macOS 11.0+)
#
# Usage:
#     ./build_macos.sh                 # default arm64 build + DMG
#     ./build_macos.sh --no-dmg        # stop after .app bundle
#     ./build_macos.sh --test          # run pytest before packaging
# ==============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

APP="QectorWorkbench.app"
DIST="$ROOT/dist"
BUILD="$ROOT/build"
WHEELS="$ROOT/wheels"

TARGET_ARCH="arm64"
MAKE_DMG=1
DO_TEST=0

for arg in "$@"; do
    case "$arg" in
        --arch=*)      TARGET_ARCH="${arg#*=}" ;;
        --arch)        shift; TARGET_ARCH="$1" ;;
        --no-dmg)      MAKE_DMG=0 ;;
        --test)        DO_TEST=1 ;;
        -h|--help)
            sed -ne '/^#/!q;s/^# //;p' "$0"
            exit 0
            ;;
    esac
done

log()  { printf "\033[1;34m==>\033[0m %s\n" "$*"; }
ok()   { printf "\033[1;32m==>\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m==>\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m==>\033[0m %s\n" "$*" >&2; exit 1; }

VERSION="$(cat "$ROOT/VERSION" 2>/dev/null || echo "1.0.1")"
log "Building QECTOR Decoder Workbench v$VERSION ($TARGET_ARCH)"

# --- 1. Python environment + dependencies -----------------------------------
if [ -n "${VIRTUAL_ENV:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ]; then
    VPY="$(which python3 || which python)"
    ok "Using existing Python environment: $VPY"
else
    VENV="$ROOT/.venv"
    if [ ! -x "$VENV/bin/python" ]; then
        log "Creating virtualenv ($TARGET_ARCH)…"
        python3 -m venv "$VENV"
    fi
    VPY="$VENV/bin/python"
    log "Installing dependencies (wheels/ first, then PyPI)…"
    "$VPY" -m pip install --upgrade pip wheel >/dev/null
    "$VPY" -m pip install --find-links "$WHEELS" --prefer-binary -r requirements.txt pyinstaller
fi
BACK_ARCH="$("$VPY" -c 'import qector_decoder_v3,platform; print(platform.machine())' 2>/dev/null || echo unknown)"
ok "Backend loaded (arch: $BACK_ARCH)."

# --- 2. Icons: icon.png (window) + icon.icns (bundle) -----------------------
log "Ensuring icon.png and icon.icns…"
"$VPY" - <<'PY'
import os
from PIL import Image
src = "assets/icon.png" if os.path.exists("assets/icon.png") else ("assets/icon.jpg" if os.path.exists("assets/icon.jpg") else None)
if src:
    img = Image.open(src).convert("RGBA")
    w, h = img.size; s = min(w, h); l, t = (w-s)//2, (h-s)//2
    img.crop((l, t, l+s, t+s)).resize((256, 256), Image.LANCZOS).save("icon.png")
    print("  icon.png generated (256x256)")
PY

if [ -f "assets/icon.icns" ]; then
    cp assets/icon.icns "$ROOT/icon.icns"
    ok "icon.icns copied from assets/icon.icns."
elif command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1 && [ -f "icon.png" ]; then
    ICONSET="$BUILD/icon.iconset"
    rm -rf "$ICONSET"; mkdir -p "$ICONSET"
    for sz in 16 32 128 256 512; do
        sips -z $sz $sz icon.png --out "$ICONSET/icon_${sz}x${sz}.png" >/dev/null
        dbl=$((sz*2))
        sips -z $dbl $dbl icon.png --out "$ICONSET/icon_${sz}x${sz}@2x.png" >/dev/null
    done
    iconutil -c icns "$ICONSET" -o "$ROOT/icon.icns"
    ok "icon.icns generated via iconutil."
fi

# --- 3. Optional test gate --------------------------------------------------
if [ "$DO_TEST" = "1" ]; then
    log "Running pytest…"
    MPLBACKEND=Agg "$VPY" -m pytest tests/test_backend.py tests/test_decoders.py -q
    ok "Tests passed."
fi

# --- 4. PyInstaller .app ----------------------------------------------------
log "Building QectorWorkbench.app (target arch: $TARGET_ARCH)…"
export QECTOR_TARGET_ARCH="$TARGET_ARCH"
"$VPY" -m PyInstaller --clean -y \
    --distpath "$DIST" --workpath "$BUILD/pyi" \
    packaging/QectorWorkbench-macos.spec
[ -d "$DIST/$APP" ] || die "PyInstaller did not produce $DIST/$APP"
ok "Bundle: $DIST/$APP"

# --- 5. Ad-hoc codesign (so Gatekeeper lets it launch locally) --------------
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

# --- 6. .dmg ----------------------------------------------------------------
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

# --- 7. Report --------------------------------------------------------------
echo
ok "Build complete."
echo "  App     : $DIST/$APP"
echo "  Disk img: $DMG"
echo "  Arch    : $TARGET_ARCH"
echo "  Size    : $(du -h "$DMG" | cut -f1)"
echo "  SHA256  : $(shasum -a 256 "$DMG" | cut -d' ' -f1)"
echo
echo "Run it:   open '$DIST/$APP'"
echo "MCP mode: '$DIST/$APP/Contents/MacOS/QectorWorkbench' --mcp"
