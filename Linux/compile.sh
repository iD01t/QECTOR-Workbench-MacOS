#!/usr/bin/env bash
#
# compile.sh — all-in-one Linux build for QECTOR Decoder Workbench.
#
# Produces a single portable AppImage:
#     dist/QectorWorkbench-<VERSION>-x86_64.AppImage
#
# Pipeline: virtualenv -> pip install (manylinux wheels) -> generate icon ->
# optional pytest -> PyInstaller onedir -> AppDir assembly -> AppImage.
#
# Usage:
#     ./compile.sh                 native build on this host
#     ./compile.sh --docker        reproducible build inside python:3.11-slim-bullseye (glibc 2.31)
#     ./compile.sh --test          run the pytest suite before packaging
#     ./compile.sh --with-deps     apt-get install system prerequisites (needs sudo)
#     ./compile.sh --clean         wipe .venv/ build/ dist/ before building
#     ./compile.sh --no-appimage   stop after the PyInstaller onedir (no AppImage)
#     ./compile.sh -h | --help
#
# Flags combine, e.g.  ./compile.sh --clean --with-deps --test
#
set -euo pipefail

# ---------------------------------------------------------------------------
# Locate ourselves and move into the Linux/ tree so every path is relative.
# ---------------------------------------------------------------------------
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VERSION="$(tr -d ' \t\r\n' < VERSION 2>/dev/null || echo 0.5.2)"
BACKEND_VERSION="$(python3 -c 'from version import BACKEND_VERSION; print(BACKEND_VERSION)' 2>/dev/null || echo 1.0.0)"
APP_NAME="QectorWorkbench"
VENV="$ROOT/.venv"
BUILD="$ROOT/build"
DIST="$ROOT/dist"
CACHE="$ROOT/.cache"
APPDIR="$BUILD/AppDir"
ARCH="x86_64"
APPIMAGETOOL_URL="${APPIMAGETOOL_URL:-https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage}"

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
DO_DOCKER=0; DO_TEST=0; DO_DEPS=0; DO_CLEAN=0; MAKE_APPIMAGE=1
for arg in "$@"; do
    case "$arg" in
        --docker)       DO_DOCKER=1 ;;
        --test)         DO_TEST=1 ;;
        --with-deps)    DO_DEPS=1 ;;
        --clean)        DO_CLEAN=1 ;;
        --no-appimage)  MAKE_APPIMAGE=0 ;;
        --in-container) : ;;  # internal marker; behaves like a native build
        -h|--help)
            sed -n '3,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) echo "Unknown option: $arg (use --help)"; exit 2 ;;
    esac
done

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m OK\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  !\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERR\033[0m %s\n' "$*" >&2; exit 1; }

# ===========================================================================
# Docker path — rebuild inside a controlled OLD-glibc image so the AppImage
# runs "everywhere".  The image is Debian 11 / glibc 2.31 (python:3.11-slim-
# bullseye), giving a binary that requires only glibc >= 2.30 — it runs on
# antiX 21+/MX 21+, Ubuntu 20.04+, Debian 11+, Mint 20+, Fedora 32+,
# openSUSE 15.3+, Arch, and everything newer.
#
# The build runs in the container's own filesystem (not the bind mount) to
# avoid slow drvfs I/O and venv symlink issues; only the finished AppImage is
# copied back to ./dist.
# ===========================================================================
if [ "$DO_DOCKER" = "1" ]; then
    command -v docker >/dev/null 2>&1 || die "docker not found on PATH"
    log "Building reproducible image (python:3.11-slim-bullseye, glibc 2.31)…"
    docker build -t qector-workbench-linux-build -f packaging/Dockerfile.build packaging
    log "Running the build inside the container…"
    FORWARD=""
    [ "$DO_TEST" = "1" ]       && FORWARD="$FORWARD --test"
    [ "$MAKE_APPIMAGE" = "0" ] && FORWARD="$FORWARD --no-appimage"
    docker run --rm -v "$ROOT":/mnt/out qector-workbench-linux-build bash -c '
        set -e
        cp -a /mnt/out /tmp/qbuild
        cd /tmp/qbuild
        rm -rf .venv build dist .cache icon.png
        bash compile.sh '"$FORWARD"'
        mkdir -p /mnt/out/dist
        cp -f /tmp/qbuild/dist/*.AppImage /mnt/out/dist/ 2>/dev/null || true
    '
    ok "Docker build finished. Artifacts in $DIST/"
    ls -lh "$DIST"/*.AppImage 2>/dev/null || true
    exit 0
fi

# ===========================================================================
# Native build
# ===========================================================================
if [ "$DO_CLEAN" = "1" ]; then
    log "Cleaning .venv/ build/ dist/…"
    rm -rf "$VENV" "$BUILD" "$DIST"
fi
mkdir -p "$BUILD" "$DIST" "$CACHE"

# --- 1. System prerequisites -----------------------------------------------
if [ "$DO_DEPS" = "1" ]; then
    if command -v apt-get >/dev/null 2>&1; then
        log "Installing system prerequisites via apt-get…"
        SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
        $SUDO apt-get update
        $SUDO apt-get install -y --no-install-recommends \
            python3 python3-venv python3-dev python3-tk \
            build-essential libgl1 libglib2.0-0 fonts-dejavu-core \
            wget file desktop-file-utils libfuse2
    else
        warn "--with-deps given but apt-get not found; skipping (install prereqs manually)."
    fi
fi

# --- 2. Pick a Python >= 3.11 ----------------------------------------------
PY=""
for cand in python3.12 python3.11 python3; do
    if command -v "$cand" >/dev/null 2>&1; then
        if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3,11) else 1)'; then
            PY="$(command -v "$cand")"; break
        fi
    fi
done
[ -n "$PY" ] || die "Python >= 3.11 not found. Install it (or run ./compile.sh --with-deps), or use ./compile.sh --docker."
log "Using interpreter: $PY ($("$PY" --version 2>&1))"

# Tkinter must be importable (python3-tk).  PyInstaller bundles Tcl/Tk from here.
"$PY" -c 'import tkinter' 2>/dev/null || die "tkinter missing. Install python3-tk (or run ./compile.sh --with-deps / --docker)."

# --- 3. Virtualenv + dependencies ------------------------------------------
if [ ! -x "$VENV/bin/python" ]; then
    log "Creating virtualenv…"
    "$PY" -m venv "$VENV"
fi
VPY="$VENV/bin/python"
log "Installing Python dependencies (manylinux wheels)…"
"$VPY" -m pip install --upgrade pip wheel >/dev/null
"$VPY" -m pip install -r requirements.txt pyinstaller
# The decoder is NOT installed into the build venv: the production spec bundles
# the manylinux wheel as a data file and decoder_provisioner extracts it into
# the managed user site on first launch (fully offline), exactly like Windows.
ok "Dependencies installed."

# --- 4. Generate the 256x256 PNG icon from the JPEG ------------------------
log "Generating icon.png from assets/icon.jpg…"
"$VPY" - <<'PY'
from PIL import Image
img = Image.open("assets/icon.jpg").convert("RGBA")
w, h = img.size
s = min(w, h)
left, top = (w - s) // 2, (h - s) // 2
img = img.crop((left, top, left + s, top + s)).resize((256, 256), Image.LANCZOS)
img.save("icon.png")
print("  icon.png", img.size)
PY
ok "icon.png ready."

# --- 5. Optional test gate --------------------------------------------------
if [ "$DO_TEST" = "1" ]; then
    log "Running pytest…"
    # Tests run against the exact bundled manylinux wheel for this release.
    # Derive the cpXY tag from the active interpreter so the gate works on
    # Python 3.11, 3.12, and 3.13 alike (wheels are shipped for each).
    CP_TAG="cp$("$VPY" -c 'import sys; print(f"{sys.version_info[0]}{sys.version_info[1]}")')"
    WHEEL_NAME="qector_decoder_v3-${BACKEND_VERSION}-${CP_TAG}-${CP_TAG}-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
    [ -f "wheels/$WHEEL_NAME" ] || die "bundled Linux decoder wheel missing for $CP_TAG: wheels/$WHEEL_NAME"
    MPLBACKEND=Agg "$VPY" -m pip install pytest pytest-asyncio "wheels/$WHEEL_NAME" >/dev/null
    MPLBACKEND=Agg "$VPY" -m pytest -q
    MPLBACKEND=Agg "$VPY" test_mcp_all.py
    ok "Tests passed."
fi

# --- 6. PyInstaller onedir --------------------------------------------------
log "Building PyInstaller onedir…"
"$VENV/bin/pyinstaller" --clean -y \
    --distpath "$DIST" --workpath "$BUILD/pyi" \
    packaging/QectorWorkbench-linux.spec
[ -x "$DIST/$APP_NAME/$APP_NAME" ] || die "PyInstaller did not produce $DIST/$APP_NAME/$APP_NAME"
ok "onedir at $DIST/$APP_NAME/"

if [ "$MAKE_APPIMAGE" = "0" ]; then
    ok "Stopping before AppImage (--no-appimage). Run the app with: $DIST/$APP_NAME/$APP_NAME"
    exit 0
fi

# --- 7. Assemble the AppDir -------------------------------------------------
log "Assembling AppDir…"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" \
         "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$APPDIR/usr/share/fonts/truetype/dejavu"

cp -a "$DIST/$APP_NAME/." "$APPDIR/usr/bin/"
install -m 0755 packaging/AppRun "$APPDIR/AppRun"
cp assets/qector-workbench.desktop "$APPDIR/qector-workbench.desktop"
cp assets/qector-workbench.desktop "$APPDIR/usr/share/applications/qector-workbench.desktop"
cp icon.png "$APPDIR/qector-workbench.png"
cp icon.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/qector-workbench.png"

# Bundle DejaVu fonts when present on the build host (nice-to-have; Tk falls
# back gracefully if a target somehow lacks them).
for f in DejaVuSans.ttf DejaVuSans-Bold.ttf DejaVuSansMono.ttf DejaVuSansMono-Bold.ttf; do
    src="/usr/share/fonts/truetype/dejavu/$f"
    [ -f "$src" ] && cp "$src" "$APPDIR/usr/share/fonts/truetype/dejavu/" || true
done

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$APPDIR/qector-workbench.desktop" \
        && ok "desktop entry valid" || warn "desktop-file-validate reported warnings"
fi

# --- 8. Fetch appimagetool (cached) and build the AppImage ------------------
AIT="$CACHE/appimagetool-x86_64.AppImage"
if [ ! -x "$AIT" ]; then
    log "Downloading appimagetool…"
    command -v wget >/dev/null 2>&1 || die "wget not found (needed to fetch appimagetool)."
    wget -q -O "$AIT" "$APPIMAGETOOL_URL" || die "Failed to download appimagetool from $APPIMAGETOOL_URL"
    chmod +x "$AIT"
fi

OUT="$DIST/${APP_NAME}-${VERSION}-${ARCH}.AppImage"
rm -f "$OUT"
log "Packaging AppImage…"
# APPIMAGE_EXTRACT_AND_RUN lets appimagetool (itself an AppImage) run without
# FUSE — essential inside Docker/WSL and on FUSE-less hosts.
ARCH="$ARCH" APPIMAGE_EXTRACT_AND_RUN=1 "$AIT" "$APPDIR" "$OUT"
[ -f "$OUT" ] || die "appimagetool did not produce $OUT"
chmod +x "$OUT"

# --- 9. Report --------------------------------------------------------------
echo
ok "Build complete."
echo "  Artifact : $OUT"
echo "  Size     : $(du -h "$OUT" | cut -f1)"
echo "  SHA256   : $(sha256sum "$OUT" | cut -d' ' -f1)"
echo
echo "Run it:  $OUT"
echo "MCP mode: $OUT --mcp"
