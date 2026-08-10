# -*- mode: python ; coding: utf-8 -*-
# ==========================================================================
# QectorWorkbench.spec  —  PRODUCTION onedir (bundled offline decoder wheel)
# ==========================================================================
# The decoder (qector-decoder-v3) ships as a bundled .whl data file.  On first
# launch the app's decoder_provisioner.py purges any outdated managed decoder
# site (< MIN_BACKEND_VERSION), extracts the bundled wheel into the ABI-scoped
# managed user site, and activates it — fully offline, no PyPI access needed.
# ==========================================================================
from PyInstaller.utils.hooks import (
    collect_submodules, collect_data_files, collect_dynamic_libs,
)

import version as _qector_version  # noqa: E402

app_version = _qector_version.WORKBENCH_VERSION
backend_version = _qector_version.BACKEND_VERSION

hiddenimports = [
    # ---------- QECTOR app modules (keep in sync with APP_MODULES) ----------
    'app', 'backend', 'state', 'theme', 'utils', 'logger', 'console', 'version',
    'version_service', 'decoder_provisioner', 'doc_generator',
    'threading_utils', 'results_tracker', 'hardware_routing',
    'mcp_server', 'mcp_resources', 'dialogs', 'autodebug', 'cli',
    'code_explorer_tab', 'decoder_lab_tab', 'benchmark_tab',
    'batch_streaming_tab', 'hardware_tab', 'diagnostics_tab', 'documentation_tab',
    'lab_info_tab',
    'generate_manuals', 'api_reference', 'docs_exporter',
    # ---------- Runtime deps of the decoder ----------
    'cffi', '_cffi_backend',
    # ---------- In-app official docs export ----------
    'reportlab', 'reportlab.platypus', 'reportlab.lib', 'reportlab.lib.pagesizes',
    'reportlab.lib.units', 'reportlab.lib.colors', 'reportlab.lib.styles',
    'reportlab.lib.enums', 'reportlab.platypus.tableofcontents',
] + collect_submodules('customtkinter') + collect_submodules('cryptography')

datas = [
    ('icon.jpg', '.'), ('icon.ico', '.'), ('EULA.txt', '.'), ('README_v3.md', '.'),
    ('wheels/*', 'wheels'), 
    (f'wheels/qector_decoder_v3-{backend_version}-cp311-cp311-win_amd64.whl', '.'),
] + collect_data_files('customtkinter')

binaries = collect_dynamic_libs('cryptography') + collect_dynamic_libs('cffi')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # The decoder is NOT bundled — it is live-installed from PyPI by decoder_provisioner.
        'qector_decoder_v3',
        # Heavy ML / notebook frameworks: unused at runtime.
        'torch', 'tensorflow', 'jax', 'pandas', 'notebook',
        'matplotlib.tests', 'matplotlib.testing',
        'scipy.tests', 'scipy.testing',
        # GPU acceleration (optional; users who want GPU run from source).
        'cupy', 'cupy_backends', 'cupyx', 'fastrlock',
        # Interactive tooling pulled in transitively.
        'IPython', 'jedi', 'notebook', 'nbconvert', 'nbformat', 'jupyter_client',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Boot splash: painted by the bootloader before Python starts, so the cold
# Rust/PyO3 decoder import is never an invisible wait.  main.py writes progress
# into it via pyi_splash and closes it once the real window is mapped.
splash = Splash(
    'assets/splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(40, 205),
    text_size=9,
    text_color='#8294ad',
    text_default='Starting QECTOR Decoder Workbench...',
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    [],
    exclude_binaries=True,
    name='QectorWorkbench',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
coll = COLLECT(
    exe,
    splash.binaries,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QectorWorkbench',
)
