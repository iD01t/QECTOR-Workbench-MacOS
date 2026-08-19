# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — macOS .app bundle for QECTOR Decoder Workbench.
#
# Produces dist/QectorWorkbench.app (a windowed bundle embedding the Python
# runtime, Tcl/Tk, and the workbench dependencies.  The decoder is deliberately
# external and provisioned at run time.  build_macos.sh wraps the .app into a
# .dmg.  Run from the Mac/ dir:
#
#     pyinstaller --clean -y packaging/QectorWorkbench-macos.spec
#
# Architecture: set QECTOR_TARGET_ARCH=arm64 or x86_64 to thin the build to one
# slice (matching the installed wheels); unset builds for the running Python's
# native architecture.  There is no universal2 build because the backend ships
# no universal2 / x86_64 wheel — build arm64 on Apple Silicon and x86_64 on an
# Intel Mac (or under Rosetta with an x86_64 Python + the bundled Intel wheel).
import os
import importlib.util as _ilu
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs, collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))
TARGET_ARCH = os.environ.get("QECTOR_TARGET_ARCH") or None  # 'arm64' | 'x86_64' | None

# Bundle the compiled decoder INTO the .app so it runs on any Mac with no
# Python/pip/network.  Must be importable in the build interpreter
# (pip install qector-decoder-v3) and match the target arch's wheel — fail loudly
# otherwise.
assert _ilu.find_spec('qector_decoder_v3') is not None, (
    "qector_decoder_v3 is not installed in the build interpreter; run "
    "`pip install qector-decoder-v3` before building so it can be bundled."
)
_dec_datas, _dec_binaries, _dec_hidden = collect_all('qector_decoder_v3')

# Single source of truth for the version — read the VERSION file so the bundle
# metadata never drifts from the rest of the app.
try:
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as _vf:
        APP_VERSION = _vf.read().strip() or "3.5.1"
except Exception:
    APP_VERSION = "3.5.1"

app_modules = [
    'app', 'backend', 'state', 'theme', 'utils', 'logger', 'console', 'version',
    'version_service', 'decoder_provisioner', 'doc_generator', 'auto_updater', 'threading_utils', 'results_tracker',
    'hardware_routing', 'mcp_server', 'mcp_resources', 'dialogs', 'autodebug', 'cli', 'errors',
    'code_explorer_tab', 'decoder_lab_tab', 'benchmark_tab',
    'batch_streaming_tab', 'hardware_tab', 'diagnostics_tab', 'documentation_tab',
    'lab_info_tab', 'history_tab', 'compliance', 'entra_auth', 'i18n',
    'generate_manuals', 'api_reference', 'docs_exporter',
    # Runtime dependency of the externally provisioned decoder: qector-decoder-v3
    # >= 0.6.8 imports `cryptography` (via cffi) at package import time.  The
    # decoder is installed --no-deps and never imported at build time, so it must
    # be bundled explicitly or `import qector_decoder_v3` fails at launch.
    'cffi', '_cffi_backend',
]

hiddenimports = (
    app_modules
    + collect_submodules('customtkinter')
    + collect_submodules('cryptography')
    + _dec_hidden
)

datas = [
    (os.path.join(ROOT, 'icon.png'), '.'),
    (os.path.join(ROOT, 'assets', 'icon.jpg'), '.'),
    (os.path.join(ROOT, 'EULA.txt'), '.'),
    (os.path.join(ROOT, 'README.md'), '.'),
]
datas += collect_data_files('customtkinter') + _dec_datas

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    # cryptography's rust bindings and the cffi backend are compiled extensions;
    # pull their dylibs in explicitly so bundled cryptography loads at runtime.
    # _dec_binaries carries the decoder's own compiled .so.
    binaries=collect_dynamic_libs('cryptography') + collect_dynamic_libs('cffi') + _dec_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Decoder is bundled (collect_all above); provisioner is upgrade-only.
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
app = BUNDLE(
    coll,
    name='QectorWorkbench.app',
    icon=os.path.join(ROOT, 'icon.icns'),
    bundle_identifier='store.qector.workbench',
    version=APP_VERSION,
    info_plist={
        'CFBundleName': 'QECTOR Workbench',
        'CFBundleDisplayName': 'QECTOR Decoder Workbench',
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,   # allow dark mode
        'LSMinimumSystemVersion': '11.0',          # matches macosx_11_0 wheels
        'LSApplicationCategoryType': 'public.app-category.education',
        'NSHumanReadableCopyright':
            'Guillaume Lessard / iD01t Productions — see EULA.txt',
    },
)
