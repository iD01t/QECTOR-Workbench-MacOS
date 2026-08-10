#!/usr/bin/env bash
#
# build_installers.sh — build the separated Ubuntu and antiX .deb installers.
#
# Runs the whole pipeline inside the reproducible python:3.11-slim-bullseye
# image (glibc 2.31) so the resulting packages install and run on Ubuntu 20.04+
# and antiX 21+ (and every newer Debian-family distro):
#
#     virtualenv -> pip install (manylinux wheels) -> generate official icon ->
#     optional pytest -> PyInstaller onedir -> two tuned .deb packages.
#
# Output:
#     dist/qector-workbench-<VERSION>_amd64_ubuntu.deb
#     dist/qector-workbench-<VERSION>_amd64_antix.deb
#
# Usage:
#     ./build_installers.sh            build both installers
#     ./build_installers.sh --test     run the pytest suite before packaging
#     ./build_installers.sh --native   build on THIS host instead of Docker
#                                       (packages then require the host's glibc)
#     ./build_installers.sh -h | --help
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
DIST="$ROOT/dist"

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m OK\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mERR\033[0m %s\n' "$*" >&2; exit 1; }

DO_TEST=0; DO_NATIVE=0
for arg in "$@"; do
    case "$arg" in
        --test)   DO_TEST=1 ;;
        --native) DO_NATIVE=1 ;;
        -h|--help)
            sed -n '3,27p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) echo "Unknown option: $arg (use --help)"; exit 2 ;;
    esac
done

# --- Native path: build directly on this host (glibc = host's) --------------
if [ "$DO_NATIVE" = "1" ]; then
    log "Native build on this host…"
    EXTRA=""; [ "$DO_TEST" = "1" ] && EXTRA="--test"
    bash compile.sh --no-appimage $EXTRA
    bash packaging/build_deb.sh
    ok "Native build finished. Installers in $DIST/"
    ls -lh "$DIST"/*.deb 2>/dev/null || true
    exit 0
fi

# --- Docker path (default): reproducible glibc-2.31 build -------------------
command -v docker >/dev/null 2>&1 || die "docker not found on PATH (or use --native)."

log "Building reproducible image (python:3.11-slim-bullseye, glibc 2.31)…"
docker build -t qector-workbench-linux-build -f packaging/Dockerfile.build packaging

FORWARD=""; [ "$DO_TEST" = "1" ] && FORWARD="--test"

log "Building onedir + .deb installers inside the container…"
docker run --rm -v "$ROOT":/mnt/out qector-workbench-linux-build bash -c '
    set -e
    cp -a /mnt/out /tmp/qbuild
    cd /tmp/qbuild
    rm -rf .venv build dist .cache icon.png
    bash compile.sh --no-appimage '"$FORWARD"'
    bash packaging/build_deb.sh
    mkdir -p /mnt/out/dist
    cp -f /tmp/qbuild/dist/*.deb /mnt/out/dist/ 2>/dev/null || true
'

ok "Build complete. Installers in $DIST/"
ls -lh "$DIST"/*.deb 2>/dev/null || true
echo
echo "Install (Ubuntu):  sudo apt install ./dist/qector-workbench_*_amd64_ubuntu.deb"
echo "Install (antiX) :  sudo dpkg -i ./dist/qector-workbench_*_amd64_antix.deb && sudo apt-get -f install"
