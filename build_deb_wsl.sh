#!/bin/bash
set -e

# build_deb_wsl.sh -- Build a flawless .deb package using WSL
# Run from repo root in WSL:
#   bash build_deb_wsl.sh
#
# This script builds the .deb package tree on the Windows mount,
# then copies it to WSL's native filesystem so dpkg-deb can record
# correct Unix ownership/permissions (root:root, 644/755).

WIN_DIST="/mnt/d/QECTOR APP/dist"
TMP_TREE="/tmp/qector_deb_tree"

echo "[1/4] Building .deb package tree on Windows mount..."
cd "/mnt/d/QECTOR APP"
python3 build_production.py --deb
# The package name is derived from version.py: a literal here went stale at
# 3.5.1 and would silently archive the wrong package after every version bump.
DEB_NAME="qector-workbench_$(python3 -c 'import version; print(version.WORKBENCH_VERSION)')_amd64"

echo "[2/4] Copying package tree to WSL native filesystem for permission fixing..."
rm -rf "$TMP_TREE"
cp -r "$WIN_DIST/$DEB_NAME" "$TMP_TREE"

echo "[3/4] Fixing Debian permissions..."
cd "$TMP_TREE"
find . -type d -exec chmod 755 {} \;
find opt -type f -exec chmod 644 {} \;
chmod 755 usr/local/bin/qector-workbench
chmod 755 DEBIAN/postinst
chmod 644 DEBIAN/control

echo "[4/4] Building .deb with dpkg-deb..."
cd /tmp
fakeroot dpkg-deb --build --root-owner-group "$TMP_TREE" "${DEB_NAME}.deb"

mkdir -p "$WIN_DIST"
cp "/tmp/${DEB_NAME}.deb" "$WIN_DIST/"

echo ""
echo "===================================="
echo "  .deb built successfully"
echo "===================================="
ls -lh "$WIN_DIST/${DEB_NAME}.deb"
echo ""
echo "Package info:"
dpkg-deb -I "$WIN_DIST/${DEB_NAME}.deb"
echo ""
echo "Install with:"
echo "  sudo dpkg -i $WIN_DIST/${DEB_NAME}.deb"
echo "  sudo apt-get install -f   # if dependencies are missing"
