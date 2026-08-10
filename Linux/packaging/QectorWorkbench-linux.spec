# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir spec — Linux x86_64 build of QECTOR Decoder Workbench.
#
# Produces dist/QectorWorkbench/ (an ELF launcher + _internal/ holding the
# Python 3.11 runtime, Tcl/Tk, and every dependency).  compile.sh wraps this
# output into a portable AppImage.  Run from the Linux/ directory:
#
#     pyinstaller --clean -y packaging/QectorWorkbench-linux.spec
#
# UPX is disabled and binaries are stripped: this maximises loader robustness
# inside the AppImage while keeping the payload lean.
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

# This spec lives in Linux/packaging/; PyInstaller resolves relative script and
# data paths against the spec's own directory, so anchor everything to the app
# tree (the parent of packaging/) via the injected SPECPATH.  This makes the
# build work regardless of the current working directory.
ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))

# The decoder (qector-decoder-v3) ships as a bundled manylinux .whl data file.
# On first launch decoder_provisioner.py purges any outdated managed decoder
# site (< MIN_BACKEND_VERSION), extracts the bundled wheel into the ABI-scoped
# managed user site, and activates it — fully offline, no PyPI access needed.
# This is the exact same model as the Windows production build.
WHEEL = os.path.join(ROOT, 'qector_decoder_v3-0.7.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl')

app_modules = [
    'app', 'backend', 'state', 'theme', 'utils', 'logger', 'console', 'version',
    'version_service', 'decoder_provisioner', 'doc_generator', 'threading_utils', 'results_tracker',
    'hardware_routing', 'mcp_server', 'mcp_resources', 'dialogs', 'autodebug', 'cli',
    'code_explorer_tab', 'decoder_lab_tab', 'benchmark_tab',
    'batch_streaming_tab', 'hardware_tab', 'diagnostics_tab', 'documentation_tab',
    'generate_manuals', 'api_reference', 'docs_exporter',
    'cffi', '_cffi_backend',
    # In-app official docs export (reportlab is imported lazily by the
    # generators, so it must be listed explicitly to be bundled).
    'reportlab', 'reportlab.platypus', 'reportlab.lib', 'reportlab.lib.pagesizes',
    'reportlab.lib.units', 'reportlab.lib.colors', 'reportlab.lib.styles',
    'reportlab.lib.enums', 'reportlab.platypus.tableofcontents',
]

hiddenimports = (
    app_modules
    + collect_submodules('customtkinter')
    + collect_submodules('cryptography')
)

datas = [
    (WHEEL, '.'), (os.path.join(ROOT, 'wheels', 'qector_decoder_v3-0.7.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl'), 'wheels'),
    (os.path.join(ROOT, 'icon.png'), '.'),
    (os.path.join(ROOT, 'assets', 'icon.jpg'), '.'),
    (os.path.join(ROOT, 'assets', 'EULA.txt'), '.'),
    (os.path.join(ROOT, 'assets', 'README_v3.md'), '.'),
]
datas += collect_data_files('customtkinter')

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    # The cryptography rust bindings and cffi backend are compiled extensions;
    # pull their shared objects in explicitly so bundled cryptography loads.
    binaries=collect_dynamic_libs('cryptography') + collect_dynamic_libs('cffi'),
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # The decoder package is NOT importable from the bundle — it is
        # provisioned from the bundled manylinux wheel by decoder_provisioner.
        'qector_decoder_v3',
        'torch', 'tensorflow', 'jax', 'pandas', 'notebook',
        'matplotlib.tests', 'matplotlib.testing',
        'scipy.tests', 'scipy.testing',
        # GPU acceleration is optional; excluding cupy + its bundled CUDA
        # runtime keeps the AppImage lean.  CPU decode works fully and the GPU
        # batch backend reports "unavailable" through the graceful error path.
        'cupy', 'cupy_backends', 'cupyx', 'fastrlock',
        # Interactive/notebook tooling pulled in transitively; unused at runtime.
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
    os.path.join(ROOT, 'assets', 'splash.png'),
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
    strip=False,  # never strip: old-glibc build hosts' binutils can corrupt
    upx=False,    # large-alignment .so files (e.g. numpy's OpenBLAS)
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    splash.binaries,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='QectorWorkbench',
)
