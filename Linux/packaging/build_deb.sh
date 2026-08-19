#!/usr/bin/env bash
#
# build_deb.sh — wrap the PyInstaller onedir into per-distro .deb installers.
#
# Produces two Debian packages from the SAME self-contained onedir bundle
# (dist/QectorWorkbench/, built by `compile.sh --no-appimage` on the glibc-2.31
# base so it runs on Ubuntu 20.04+ and antiX 21+):
#
#     dist/qector-workbench_<VERSION>_amd64_ubuntu.deb
#     dist/qector-workbench_<VERSION>_amd64_antix.deb
#
# Both install the bundle to /opt/qector-workbench, add a /usr/bin/qector-workbench
# launcher, a desktop menu entry, and the official 256x256 icon in the hicolor
# theme.  The variants differ only in their tuned Depends: (GL library naming).
#
# Run from anywhere; paths are anchored to the Linux/ tree.  Requires dpkg-deb
# (present on every Debian/Ubuntu host and in packaging/Dockerfile.build).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="$(tr -d ' \t\r\n' < VERSION 2>/dev/null || echo 0.5.2)"
ARCH="amd64"
PKG="qector-workbench"
ONEDIR="$ROOT/dist/QectorWorkbench"
ICON="$ROOT/icon.png"
OUTDIR="$ROOT/dist"
MAINTAINER="${QECTOR_DEB_MAINTAINER:-QECTOR Workbench <admin@qector.store>}"
HOMEPAGE="https://www.qector.store"

log()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mERR\033[0m %s\n' "$*" >&2; exit 1; }

command -v dpkg-deb >/dev/null 2>&1 || die "dpkg-deb not found (install 'dpkg' / run inside the build container)."
[ -x "$ONEDIR/QectorWorkbench" ] || die "onedir not found at $ONEDIR — run './compile.sh --no-appimage' first."

# --- 256x256 official icon (from assets/icon.jpg) if not already generated ----
if [ ! -f "$ICON" ]; then
    log "Generating icon.png from assets/icon.jpg…"
    PY="$ROOT/.venv/bin/python"; [ -x "$PY" ] || PY="python3"
    "$PY" - <<'PY'
from PIL import Image
img = Image.open("assets/icon.jpg").convert("RGBA")
w, h = img.size
s = min(w, h)
left, top = (w - s) // 2, (h - s) // 2
img.crop((left, top, left + s, top + s)).resize((256, 256), Image.LANCZOS).save("icon.png")
PY
fi

mkdir -p "$OUTDIR"

build_one() {
    local variant="$1"; local depends="$2"
    local stage pkgdir out
    stage="$(mktemp -d)"
    pkgdir="$stage/pkg"

    mkdir -p "$pkgdir/DEBIAN" \
             "$pkgdir/usr/lib/qector-workbench" \
             "$pkgdir/usr/bin" \
             "$pkgdir/usr/share/applications" \
             "$pkgdir/usr/share/icons/hicolor/256x256/apps" \
             "$pkgdir/usr/share/man/man1" \
             "$pkgdir/usr/share/doc/qector-workbench" \
             "$pkgdir/etc/apparmor.d"

    # AppArmor confinement: loopback-only networking for the whole bundle.
    cp "$ROOT/packaging/qector-workbench.apparmor" "$pkgdir/etc/apparmor.d/qector-workbench"
    chmod 0644 "$pkgdir/etc/apparmor.d/qector-workbench"

    # Payload: the self-contained PyInstaller onedir.  Installed under /usr/lib
    # (FHS-compliant for a package-managed app) rather than /opt.
    cp -a "$ONEDIR/." "$pkgdir/usr/lib/qector-workbench/"
    cp "$ICON" "$pkgdir/usr/share/icons/hicolor/256x256/apps/qector-workbench.png"

    # Hygiene the payload: drop junk and fix permission bits the Windows/drvfs
    # build host mangles.
    #  - macOS .DS_Store files ship inside some third-party wheels (customtkinter);
    #  - data files must not be executable; shared libraries are conventionally 0644.
    find "$pkgdir" -name '.DS_Store' -delete 2>/dev/null || true
    find "$pkgdir/usr/lib/qector-workbench/_internal" -type f \
        \( -name '*.txt' -o -name '*.md' -o -name '*.json' -o -name '*.jpg' \
           -o -name '*.png' -o -name '*.ttf' -o -name '*.tcl' -o -name '*.enc' \
           -o -name '*.whl' \) \
        -exec chmod 0644 {} + 2>/dev/null || true
    find "$pkgdir/usr/lib/qector-workbench" -type f -name '*.so*' \
        -exec chmod 0644 {} + 2>/dev/null || true

    # copyright — a real copyright notice followed by the EULA text.
    {
        printf '%s\n' \
            "QECTOR Decoder Workbench" \
            "Copyright (C) 2024-2026 Guillaume Lessard / iD01t Productions and the" \
            "QECTOR Development Team. All rights reserved." \
            "" \
            "Licensed under the QECTOR End User License Agreement (EULA), reproduced" \
            "below. The bundled qector-decoder-v3 backend is separately licensed —" \
            "see https://www.qector.store." \
            "" \
            "----------------------------------------------------------------------" \
            ""
        [ -f EULA.txt ] && cat EULA.txt
    } > "$pkgdir/usr/share/doc/qector-workbench/copyright"

    # End-user README in the standard Debian doc location (NOT the dev/build docs).
    [ -f README.md ] && cp README.md "$pkgdir/usr/share/doc/qector-workbench/README.md" || true

    # Debian changelog (gzip -9n, no timestamp).  The version carries no Debian
    # revision, so dpkg treats this as a native package: the file must be
    # changelog.gz (not changelog.Debian.gz).
    {
        printf '%s\n\n' "qector-workbench (${VERSION}) stable; urgency=low"
        printf '  * QECTOR Decoder Workbench %s — self-contained %s build.\n' "$VERSION" "$variant"
         printf '  * 17 decoders, 10 code families (incl. qLDPC), 85-tool MCP server.\n\n'
        printf ' -- %s  %s\n' "$MAINTAINER" "$(date -R)"
    } | gzip -9n > "$pkgdir/usr/share/doc/qector-workbench/changelog.gz"

    # Minimal man page so the /usr/bin launcher is documented.
    {
        printf '.TH QECTOR-WORKBENCH 1 "%s" "QECTOR Workbench %s" "User Commands"\n' \
            "$(date +%Y-%m-%d)" "$VERSION"
        cat <<'MAN'
.SH NAME
qector-workbench \- QECTOR Decoder Workbench, a quantum error-correction decoder analysis suite
.SH SYNOPSIS
.B qector-workbench
.RB [ --mcp ]
.SH DESCRIPTION
QECTOR Decoder Workbench is a self-contained desktop GUI and stdio MCP server for
constructing quantum error-correcting codes and measuring single-shot and batch
decoders (union-find, blossom, sparse-blossom, BP-OSD and more) from the
qector-decoder-v3 backend.
.SH OPTIONS
.TP
.B --mcp
Start the 85-tool stdio Model Context Protocol server instead of the GUI (headless).
.SH FILES
.TP
.I ~/.local/share/QectorWorkbench
Per-user data directory for logs and exported documents (override with $QECTOR_DATA_DIR).
.SH HOMEPAGE
https://www.qector.store
.SH AUTHOR
Guillaume Lessard / iD01t Productions.
MAN
    } | gzip -9n > "$pkgdir/usr/share/man/man1/qector-workbench.1.gz"

    # Docs/man/icon must be world-readable, non-executable (the build host's
    # drvfs mount otherwise leaves them 0755).
    chmod 0644 "$pkgdir/usr/share/doc/qector-workbench/"* \
               "$pkgdir/usr/share/man/man1/qector-workbench.1.gz" \
               "$pkgdir/usr/share/icons/hicolor/256x256/apps/qector-workbench.png"

    # /usr/bin launcher — keeps argv[0] basename "QectorWorkbench" so Tk's WM
    # class matches the desktop entry's StartupWMClass (correct taskbar icon).
    cat > "$pkgdir/usr/bin/qector-workbench" <<'SH'
#!/bin/sh
# QECTOR Decoder Workbench launcher. Pass --mcp for the stdio MCP server.
export QECTOR_OFFLINE="${QECTOR_OFFLINE:-1}"
exec /usr/lib/qector-workbench/QectorWorkbench "$@"
SH
    chmod 0755 "$pkgdir/usr/bin/qector-workbench"

    # Desktop menu entry (Exec via the /usr/bin launcher on PATH).
    cat > "$pkgdir/usr/share/applications/qector-workbench.desktop" <<'DESK'
[Desktop Entry]
Type=Application
Version=1.0
Name=QECTOR Decoder Workbench
GenericName=Quantum Error Correction Workbench
Comment=Quantum error-correction decoder analysis suite
Exec=qector-workbench
Icon=qector-workbench
Terminal=false
Categories=Science;Physics;
Keywords=quantum;qec;decoder;error-correction;surface-code;
StartupWMClass=QectorWorkbench
DESK

    if command -v desktop-file-validate >/dev/null 2>&1; then
        desktop-file-validate "$pkgdir/usr/share/applications/qector-workbench.desktop" || true
    fi

    # control (Installed-Size is the payload size in KiB, excluding DEBIAN/).
    local installed_kb
    installed_kb="$(du -s -k --exclude=DEBIAN "$pkgdir" | cut -f1)"
    cat > "$pkgdir/DEBIAN/control" <<CTRL
Package: ${PKG}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${installed_kb}
Depends: ${depends}
Section: science
Priority: optional
Homepage: ${HOMEPAGE}
Description: QECTOR Decoder Workbench (${variant}) — quantum error-correction decoder suite
 Self-contained desktop GUI and stdio MCP server for constructing quantum
  error-correcting codes and measuring single-shot and batch decoders
 (union-find, blossom, sparse-blossom, BP-OSD and more) from the
 qector-decoder-v3 backend.
 .
 Bundles its own Python 3.11 runtime, Tcl/Tk and scientific stack (numpy,
 scipy, matplotlib), so no system Python is required.  Built on a glibc 2.31
 baseline for the ${variant} family.  Run "qector-workbench" for the GUI or
  "qector-workbench --mcp" for the 85-tool MCP server.
CTRL

    # postinst: refresh desktop + icon caches AND drop a launcher icon on the
    # Desktop of every existing user and of future users (/etc/skel), so a
    # clickable QECTOR shortcut with the app icon appears on their desktop.
    cat > "$pkgdir/DEBIAN/postinst" <<'POST'
#!/bin/sh
set -e

SRC=/usr/share/applications/qector-workbench.desktop

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
fi

# Copy the menu entry onto a user's Desktop, owned by that user and marked
# executable + trusted so desktop environments render it as a real icon rather
# than an "untrusted" file.  Best effort — never fail the install.
place_shortcut() {
    home="$1"; owner="$2"
    [ -d "$home" ] || return 0
    desk="$home/Desktop"
    mkdir -p "$desk" 2>/dev/null || return 0
    cp -f "$SRC" "$desk/qector-workbench.desktop" 2>/dev/null || return 0
    chmod 0755 "$desk/qector-workbench.desktop" 2>/dev/null || true
    if [ -n "$owner" ]; then
        chown "$owner:$(id -gn "$owner" 2>/dev/null || echo "$owner")" \
              "$desk" "$desk/qector-workbench.desktop" 2>/dev/null || true
        # GNOME/Nautilus: mark the launcher trusted for this user (best effort).
        su - "$owner" -c 'command -v gio >/dev/null 2>&1 && gio set "$HOME/Desktop/qector-workbench.desktop" metadata::trusted true' 2>/dev/null || true
    fi
}

# Future users get it via /etc/skel.
mkdir -p /etc/skel/Desktop 2>/dev/null || true
cp -f "$SRC" /etc/skel/Desktop/qector-workbench.desktop 2>/dev/null || true
chmod 0755 /etc/skel/Desktop/qector-workbench.desktop 2>/dev/null || true

# Existing users under /home plus root.
for home in /home/*; do
    [ -d "$home" ] || continue
    place_shortcut "$home" "$(basename "$home")"
done
place_shortcut /root root

# Best-effort AppArmor confinement: load the shipped loopback-only profile.
# The profile is written to be safe to enforce on every supported host
# (Ubuntu 20.04+ / antiX 21+); if apparmor_parser is absent, nothing changes.
if [ -x /sbin/apparmor_parser ] || [ -x /usr/sbin/apparmor_parser ]; then
    AP="$(command -v apparmor_parser || echo /sbin/apparmor_parser)"
    "$AP" -r /etc/apparmor.d/qector-workbench 2>/dev/null || true
fi

exit 0
POST
    cat > "$pkgdir/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database -q /usr/share/applications 2>/dev/null || true
    fi
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
    fi
    # Remove the Desktop shortcuts we placed.
    rm -f /etc/skel/Desktop/qector-workbench.desktop 2>/dev/null || true
    for home in /home/* /root; do
        rm -f "$home/Desktop/qector-workbench.desktop" 2>/dev/null || true
    done
fi
if [ "$1" = "purge" ]; then
    # Unload + remove the AppArmor profile we installed.
    if command -v apparmor_parser >/dev/null 2>&1; then
        apparmor_parser -R /etc/apparmor.d/qector-workbench 2>/dev/null || true
    fi
    rm -f /etc/apparmor.d/qector-workbench 2>/dev/null || true
fi
exit 0
POSTRM
    chmod 0755 "$pkgdir/DEBIAN/postinst" "$pkgdir/DEBIAN/postrm"

    # md5sums control file over every shipped regular file (excludes DEBIAN/) —
    # enables `dpkg -V` integrity checks and satisfies lintian.
    ( cd "$pkgdir" && find . -mindepth 1 -type f -not -path './DEBIAN/*' -printf '%P\0' \
        | LC_ALL=C sort -z | xargs -0 -r md5sum > DEBIAN/md5sums )
    chmod 0644 "$pkgdir/DEBIAN/md5sums"

    out="$OUTDIR/${PKG}_${VERSION}_${ARCH}_${variant}.deb"
    rm -f "$out"
    log "Building ${variant} package…"
    dpkg-deb -Zxz --root-owner-group --build "$pkgdir" "$out"
    dpkg-deb --info "$out" >/dev/null || die "dpkg-deb produced an invalid archive for ${variant}"
    printf '     %s  (%s)\n' "$out" "$(du -h "$out" | cut -f1)"
    rm -rf "$stage"
}

# Depends tuned per distro family.  The payload is FULLY self-contained — it
# bundles its own Python 3.11 runtime AND the compiled qector-decoder-v3 backend
# — so there is NO system Python/pip dependency.  These are only the
# X11/GL/fontconfig client libs PyInstaller leaves as shared-library deps.
#   Ubuntu 20.04+ :  libgl1 is a real package on every supported release.
#   antiX 21/23   :  Debian 11 ships libgl1-mesa-glx; Debian 12/antiX 23 dropped
#                    it, so fall through to libgl1 (present on both).
UBUNTU_DEPS="libc6 (>= 2.31), libx11-6, libxext6, libxrender1, libxft2, libfontconfig1, libglib2.0-0, libgl1"
ANTIX_DEPS="libc6 (>= 2.31), libx11-6, libxext6, libxrender1, libxft2, libfontconfig1, libglib2.0-0, libgl1-mesa-glx | libgl1"

build_one "ubuntu" "$UBUNTU_DEPS"
build_one "antix"  "$ANTIX_DEPS"

echo
log "Installers ready in $OUTDIR/"
ls -lh "$OUTDIR"/*.deb
