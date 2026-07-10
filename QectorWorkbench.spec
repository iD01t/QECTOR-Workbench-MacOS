# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = [
    # QECTOR app modules (all 22)
    'app', 'backend', 'state', 'theme', 'utils', 'logger', 'console', 'version',
    'doc_generator', 'auto_updater', 'threading_utils', 'results_tracker',
    'hardware_routing', 'mcp_server', 'mcp_resources', 'dialogs',
    'code_explorer_tab', 'decoder_lab_tab', 'benchmark_tab',
    'batch_streaming_tab', 'hardware_tab', 'documentation_tab',
]

datas = [('icon.jpg', '.'), ('EULA.txt', '.'), ('README_v3.md', '.')]
binaries = []

app_version = '3.4.0'

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
        'pythoncom', 'win32api', 'win32con', 'pywintypes',
        'tkinter.test', 'unittest', 'pdb', 'email',
        'http.server', 'xmlrpc',
        'torch', 'tensorflow', 'jax', 'pandas', 'notebook',
        'matplotlib.tests', 'matplotlib.testing',
        'scipy.tests', 'scipy.testing',
        'PIL.ImageShow', 'PIL.ImageGrab',
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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QectorWorkbench',
)
