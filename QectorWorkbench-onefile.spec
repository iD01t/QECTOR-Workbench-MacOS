# -*- mode: python ; coding: utf-8 -*-
# Single-file (onefile) build of QECTOR Decoder Workbench.
#
# Produces ONE self-contained QectorWorkbench-Portable.exe that bundles the
# Python 3.11 runtime, every dependency, and all data files. At launch it
# unpacks to a private temp directory and runs entirely from there, so it is
# immune to any other Python installed on the target machine (the "python3XX.dll
# conflicts" failure only happens when a onedir launcher is copied WITHOUT its
# _internal folder — a single-file exe cannot be split that way).
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = [
    'app', 'backend', 'state', 'theme', 'utils', 'logger', 'console', 'version',
    'doc_generator', 'auto_updater', 'threading_utils', 'results_tracker',
    'hardware_routing', 'mcp_server', 'mcp_resources', 'dialogs',
    'code_explorer_tab', 'decoder_lab_tab', 'benchmark_tab',
    'batch_streaming_tab', 'hardware_tab', 'documentation_tab',
] + collect_submodules('qector_decoder_v3')

datas = [('icon.jpg', '.'), ('icon.ico', '.'), ('EULA.txt', '.'), ('README_v3.md', '.')] + collect_data_files('qector_decoder_v3')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
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
        'IPython', 'jedi', 'notebook', 'nbconvert', 'nbformat', 'jupyter_client',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='QectorWorkbench-Portable',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # no UPX: maximizes AV/loader compatibility for a standalone exe
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
