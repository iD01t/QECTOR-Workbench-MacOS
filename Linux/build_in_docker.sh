#!/usr/bin/env bash
# This script runs inside the Docker container (mounted at /mnt/out).
set -euo pipefail

echo "==> Copying source to container-local filesystem (avoid slow bind-mount I/O)..."
cp -a /mnt/out /tmp/qbuild
cd /tmp/qbuild

echo "==> Cleaning previous build artifacts..."
rm -rf .venv build dist .cache icon.png

echo "==> Running compile.sh (PyInstaller onedir)..."
bash compile.sh --no-appimage --clean 2>&1 | tail -20

echo "==> Building .deb installers..."
bash packaging/build_deb.sh 2>&1 | tail -10

echo "==> Copying back to host bind mount..."
mkdir -p /mnt/out/dist
cp -f /tmp/qbuild/dist/*.deb /mnt/out/dist/ 2>/dev/null || true
cp -f /tmp/qbuild/dist/QectorWorkbench-*.AppImage /mnt/out/dist/ 2>/dev/null || true

echo "==> Build finished. Artifacts in /mnt/out/dist/"
ls -lh /mnt/out/dist/
