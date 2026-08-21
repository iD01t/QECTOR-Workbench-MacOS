# -*- mode: python ; coding: utf-8 -*-
# ==============================================================================
# PyInstaller spec for macOS Application Bundle (.app)
#
# Target: macOS Apple Silicon (arm64, macOS 11.0+)
# Usage:
#     pyinstaller packaging/QectorWorkbench-macos.spec
# ==============================================================================

import importlib.util as _ilu
import os
import sys
from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

SPECPATH = os.path.abspath(os.path.dirname(SPEC))
ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))

TARGET_ARCH = os.environ.get('QECTOR_TARGET_ARCH', 'arm64')

_vpath = os.path.join(ROOT, 'VERSION')
APP_VERSION = open(_vpath, 'r').read().strip() if os.path.exists(_vpath) else '1.0.1'

assert _ilu.find_spec('qector_decoder_v3') is not None, (
    "qector_decoder_v3 is not installed in the build interpreter; run "
    "`pip install qector-decoder-v3` before building so it can be bundled."
)
_dec_datas, _dec_binaries, _dec_hidden = collect_all('qector_decoder_v3')

app_modules = [
    'app', 'backend', 'state', 'theme', 'utils', 'logger', 'console', 'version',
    'version_service', 'decoder_provisioner', 'doc_generator', 'threading_utils',
    'results_tracker', 'hardware_routing', 'mcp_server', 'mcp_resources',
    'dialogs', 'autodebug', 'cli', 'errors', 'code_explorer_tab', 'decoder_lab_tab',
    'benchmark_tab', 'batch_streaming_tab', 'hardware_tab', 'diagnostics_tab',
    'documentation_tab', 'lab_info_tab', 'history_tab', 'compliance', 'entra_auth',
    'i18n', 'figure_cache', 'tooltip', 'shortcuts', 'generate_manuals',
    'api_reference', 'docs_exporter', 'cffi', '_cffi_backend',
]

hiddenimports = (
    app_modules
    + collect_submodules('customtkinter')
    + collect_submodules('cryptography')
    + _dec_hidden
)

datas = []
for _src, _dst in [
    (os.path.join(ROOT, 'icon.png'), '.'),
    (os.path.join(ROOT, 'assets', 'icon.jpg'), 'assets'),
    (os.path.join(ROOT, 'assets', 'icon.png'), 'assets'),
    (os.path.join(ROOT, 'assets', 'icon.icns'), 'assets'),
    (os.path.join(ROOT, 'EULA.txt'), '.'),
    (os.path.join(ROOT, 'README.md'), '.'),
]:
    if os.path.exists(_src):
        datas.append((_src, _dst))
datas += collect_data_files('customtkinter') + _dec_datas

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=collect_dynamic_libs('cryptography') + collect_dynamic_libs('cffi') + _dec_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'tensorflow', 'jax', 'pandas', 'notebook',
        'matplotlib.tests', 'matplotlib.testing',
        'scipy.tests', 'scipy.testing',
        'cupy', 'cupy_backends', 'cupyx', 'fastrlock',
        'IPython', 'jedi', 'nbconvert', 'nbformat', 'jupyter_client',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QectorWorkbench',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=TARGET_ARCH,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='QectorWorkbench',
)

_icon_path = os.path.join(ROOT, 'icon.icns')
if not os.path.exists(_icon_path):
    _icon_path = os.path.join(ROOT, 'assets', 'icon.icns')
if not os.path.exists(_icon_path):
    _icon_path = None

app = BUNDLE(
    coll,
    name='QectorWorkbench.app',
    icon=_icon_path,
    bundle_identifier='store.qector.workbench',
    version=APP_VERSION,
    info_plist={
        'CFBundleName': 'QECTOR Workbench',
        'CFBundleDisplayName': 'QECTOR Decoder Workbench',
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '11.0',
        'LSApplicationCategoryType': 'public.app-category.education',
        'NSHumanReadableCopyright': 'Guillaume Lessard / iD01t Productions — see EULA.txt',
    },
)
