# QECTOR Decoder Workbench — devv1.md

**Target:** v1.0.0 production-ready (labs top-tier, fully bulletproof)
**Current:** v0.5.3 (workbench) / qector-decoder-v3 0.7.0 (backend)
**Date:** 2026-08-06
**Scope:** Local build and development only — no CI/CD, Docker, or remote deployment.

---

## 1. Version Bump Strategy

### 1.1 Resolve version inconsistency
- `version.py` has `WORKBENCH_VERSION = "0.5.3"` and `BACKEND_VERSION = "1.0.0"` — the backend is already at 1.0.0 but the workbench is at 0.5.3. Bump `WORKBENCH_VERSION` to `"1.0.0"`.
- Update `pyproject.toml` version from `0.5.2` to `1.0.0` and set `Development Status :: 5 - Production/Stable`.
- Update `EULA.txt` version from `v0.5.3` to `v1.0.0`.
- Update `installer_version.iss` from `0.5.3` to `1.0.0`.
- Update all changelog/upgrade notes to reflect the v1.0.0 release.

### 1.2 Version propagation audit
Every hardcoded version string must be derived from `version.py` at build time, never hand-coded:
- `build_production.py` — already uses `version.WORKBENCH_VERSION` (good).
- `scripts/build_installer.py` — already uses `_version.WORKBENCH_VERSION` (good).
- `scripts/build_public_bundles.py` — already uses `_version.WORKBENCH_VERSION` (good).
- `QectorWorkbench.spec` / `QectorWorkbench-onefile.spec` — already import `version` (good).
- `README.md`, `README_v3.md`, `README_LINUX.md` — must be updated to v1.0.0.
- `AGENT.md` — was historically stale (3.5.1 era); must be regenerated from live facts before every release.
- `PROJECT_STATUS.md`, `RELEASE_REPORT.md`, `CHANGELOG.md`, `UPGRADE_NOTES.md` — all must be updated.
- `docs/api.md`, `docs/architecture.md` — must be regenerated from live source.
- `manuals/` — must be regenerated at v1.0.0.

---

## 2. Production-Readiness Upgrades

### 2.1 Bulletproof error handling (follow autodebug.py pattern)
- **Rule:** No `raise` for control flow. Every error path returns a structured `(ok, message)` or equivalent.
- Audit all tab modules (`code_explorer_tab.py`, `decoder_lab_tab.py`, `benchmark_tab.py`, `batch_streaming_tab.py`, `hardware_tab.py`, `diagnostics_tab.py`, `documentation_tab.py`, `lab_info_tab.py`) for bare `except:` clauses that swallow exceptions silently. Replace with specific exception types and honest error reporting.
- Audit `backend.py` for any `raise` that could surface as an unhandled traceback in the GUI. Wrap all backend calls in `try/except` at the tab level, returning user-friendly messages.
- Audit `mcp_server.py` for any unhandled exception in tool handlers. Every tool must return a JSON-RPC error response, never crash the server.
- Audit `decoder_provisioner.py` for any unhandled exception in `bootstrap()` or `ensure()`. The provisioner must never crash the app — it should log and fall back gracefully.

### 2.2 Provisioning reliability (critical path)
- `decoder_provisioner.py` is the single most fragile component — it controls whether the app can start at all. Harden it:
  - Add a **timeout** to every network operation (PyPI fetch, pip install). Default 30s, configurable via `QECTOR_PROVISION_TIMEOUT`.
  - Add **retry logic** with exponential backoff (3 retries, 2s/4s/8s) for transient network failures.
  - Add **disk space check** before attempting wheel extraction or pip install. Fail with a clear message if `< 100MB` free.
  - Add **checksum verification** for downloaded wheels (SHA-256 from PyPI JSON API). Reject wheels with mismatched checksums.
  - Add **atomic pointer swap** — `active.json` must only be updated after a successful import verification in a subprocess, never after a simple file write.
  - Add **rollback** — if the new decoder fails to import after activation, automatically revert to the previous `active.json` pointer.
  - Add **corruption detection** — if `qector_decoder_v3/__init__.py` exists but import fails, purge the managed site and retry from scratch.
  - The bundled wheel path (`qector_decoder_v3-0.7.0-cp311-cp311-win_amd64.whl`) is hardcoded in the spec files. Make this version dynamic — read from `version.BACKEND_VERSION` at build time.

### 2.3 MCP server stability
- The MCP server (`mcp_server.py`) exposes 56 tools over stdio JSON-RPC 2024-11-05. Hardening:
  - Add **per-tool timeout** (default 60s). Tools that exceed the timeout return a structured error instead of hanging the server.
  - Add **concurrent request guard** — if a second request arrives while one is processing, queue it or return a busy response.
  - Add **memory limit** per tool call (e.g., 50MB for decode results). Large results are truncated with a warning.
  - Add **health check tool** (`mcp_health`) that returns server uptime, memory usage, and decoder import status.
  - Add **graceful shutdown** — on SIGTERM/SIGINT, drain in-flight requests, then exit cleanly.
  - The 10MB frame limit is good. Consider adding a **per-tool result size limit** (e.g., 1MB) to prevent a single tool from flooding the pipe.

### 2.4 GUI robustness
- `app.py` has per-tab crash isolation (good). Strengthen it:
  - Add **automatic tab recovery** — if a tab crashes, show a "Tab crashed — click to reload" placeholder instead of leaving it dead.
  - Add **memory monitoring** — if the app exceeds 500MB RSS, warn the user and offer to restart.
  - Add **unicode-safe console output** — the `Console` class must handle arbitrary UTF-8 output from the decoder without crashing.
  - Add **DPI awareness** — on Windows, declare DPI awareness in the manifest so the GUI scales correctly on 4K displays.
  - Add **multi-monitor support** — the window centering logic (`_center_and_lift_window`) must handle the case where the primary monitor is disconnected or has a different resolution.
  - The splash screen (`assets/splash.png`) must have a timeout — if the real window doesn't appear within 30s, the splash auto-closes and the window appears regardless.

### 2.5 Cross-platform completeness (local builds)
- **Windows:** Fully built and tested locally. The onefile and onedir PyInstaller specs are complete. Inno Setup installer is ready.
- **Linux:** `.deb` package builds locally via `build_production.py --deb`. AppImage recipe exists in `Linux/compile.sh` but is not built for v1.0.0. **Action:** Build the AppImage locally for v1.0.0.
- **macOS:** `Mac/build_macos.sh` exists and is ready to build, but requires Apple hardware. **Action:** Build on a Mac or macOS CI runner for v1.0.0.
- **Action:** Ensure `build_production.py --all` works on all three platforms locally.

### 2.6 Build system hardening (local)
- `build_production.py` already has `kill_running_instances()`, `assert_fresh()`, and `rmtree_safe()`. Add:
  - **Build reproducibility** — all timestamps in artifacts must be normalized to a fixed date (e.g., the git commit date) so that rebuilds of the same source produce byte-identical outputs.
  - **Dependency pinning** — `requirements.txt` pins `numpy>=1.24,<2.3` (good). Pin all other dependencies with minimum versions: `customtkinter>=5.2.0`, `scipy>=1.9`, `matplotlib>=3.8`, `Pillow>=9.0`, `psutil>=5.9`, `cryptography>=41.0`, `reportlab>=4.0`, `python-docx>=1.1.0`.
  - **Build isolation** — the build script should create a fresh venv and install dependencies there, rather than relying on the system Python.
  - **Artifact signing** — Windows `.exe` should be code-signed with a valid certificate. macOS `.dmg` should be notarized. Linux `.deb` should be GPG-signed.
  - **Build cache** — PyInstaller's `--clean` flag is correct for reproducible builds, but consider adding a `--cache` mode for development speed.

---

## 3. Bug Fixes

### 3.1 Known bugs from app_todo.md and lastdev.md
- **`sys.stdout is None` in windowed builds** — FIXED in `main.py` via `_LogStream` and `_ensure_std_streams()`. Verify this fix is present in all three platform trees (root, `Linux/`, `Mac/`).
- **`decoder_provisioner.py` `_verify_import` shortcut** — FIXED in `decoder_provisioner.py` to use subprocess probe instead of in-process import when module is already loaded. Verify the fix is present in all three platform trees.
- **`cli.py hardware` command broken** — FIXED in `cli.py` to read `HardwareProfile` dataclass attributes instead of calling `.get()`. Verify the fix is present in all three platform trees.
- **`version.py` `WORKBENCH_VERSION` carried backend version** — FIXED. `WORKBENCH_VERSION = "0.5.3"` is now independent of `BACKEND_VERSION = "0.7.0"`. Verify no stale copies remain in `Linux/` or `Mac/`.
- **`build_production.py` silent build failure** — FIXED with `kill_running_instances()`, `assert_fresh()`, and return code checking. Verify the fix is present in all three platform trees.
- **4 export buttons that silently did nothing** — FIXED in the doc-gen overhaul (Path import added to 4 tabs, `generate_all` used instead of `generator.generate`, race condition fixed). Verify all 4 tabs export correctly.
- **Decoder Lab "Generate Doc" calling nonexistent method** — FIXED (uses `generate_all` now). Verify.
- **Profile save always reporting success** — FIXED (honest `(ok, message)` returns). Verify.
- **DOCX exporter writing raw Markdown** — FIXED (real DOCX generation with `python-docx`). Verify.
- **Licence key field writing to unread file** — FIXED (writes `~/.qector/license.key`, calls decoder's verifier). Verify.
- **Generated HTML fetching Google font** — FIXED (offline-safe fonts). Verify.
- **API reference "HTML" being unescaped `<pre>` dump** — FIXED. Verify.
- **Decoder selftest crashing while reporting success** — FIXED. Verify.

### 3.2 New bugs to fix in v1.0.0
- **`build_production.py` syntax error** — Lines 63-68 have `BUILD_TOOLING` and `WHEEL_FILES` indented as if inside a function but at module level after a list assignment. This causes a `SyntaxError` and prevents the file from importing. Fix the indentation or move these to module level properly.
- **`build_production.py` `WHEEL_FILES` references `qector_decoder_v3-1.0.0`** but the actual bundled wheel is `qector_decoder_v3-0.7.0`. The version in `WHEEL_FILES` must match `BACKEND_VERSION`.
- **Bundled wheel version hardcoded in spec files** — `QectorWorkbench.spec` and `QectorWorkbench-onefile.spec` reference `qector_decoder_v3-0.7.0-cp311-cp311-win_amd64.whl` directly. This must be derived from `version.BACKEND_VERSION` at build time, not hardcoded.
- **`decoder_provisioner.py` offline wheel extraction fallback** — The provisioner may still have `_bundled_wheel_path`, `_extract_wheel`, `_install_bundled_wheel` logic from the old bundled-wheel era. Since `lastdev.md` Step 2-3 purged all bundled wheel artifacts and refactored to pure live PyPI provisioning, verify that `decoder_provisioner.py` in the root tree does NOT contain any bundled-wheel fallback logic. If it does, it's dead code that adds complexity and must be removed or documented as a legacy fallback.
- **`Linux/` and `Mac/` trees are untracked** — They are full copies of the root tree. Any bug fix in the root must be manually synced to `Linux/` and `Mac/`. Consider using a symlink tree or a sync script to ensure consistency.
- **`build_deb_wsl.sh`** — A leftover from the Docker-based .deb build. If the .deb is now built via `build_production.py --deb` locally, this script may be obsolete. Verify and remove if unused.
- **`qector_v069_benchmark.py`** — A benchmark script from the 0.6.9 era. It may reference APIs that have changed in 0.7.0. Verify it still works or remove it.
- **`generate_manuals_final.py`, `generate_manuals_final2.py`, `generate_manuals_docs.lo`** — These appear to be scratch/partial files from manual generation runs. They are not in the project file listing but may exist as temp files. Clean up any temp files.

---

## 4. Testing Requirements

### 4.1 Current test suite (local)
- `pytest tests/` — 403 passed, 4 skipped, 0 failed. All green.
- `python test_mcp_all.py` — 56/56 tools passed (in-process + stdio round-trip).
- `python verify_frozen_mcp.py` — PASS (56 tools over the wire, clean EOF exit 0).
- `python scripts/check_docs.py` — public docs agree with live code.
- GUI smoke tests — 18 tests green (headless environment; real GUI eyeball check deferred).

### 4.2 Gaps to close for v1.0.0 (local)
- **GUI eyeball check** — The real GUI has been launched once (2026-07-24) and booted clean. A formal GUI test on a real display is needed. Run the GUI locally and verify all 8 tabs render correctly.
- **End-to-end decode test** — A test that runs a full decode cycle (generate code → decode → verify result) for each of the 16 decoders on each of the 10 code families. Currently only a subset is tested. Run this locally.
- **Offline provisioning test** — A test that simulates a machine with no network and verifies the bundled wheel provisioning works end-to-end. Run locally by disconnecting from the network.
- **Upgrade path test** — A test that simulates upgrading from an older decoder version and verifies the managed site is purged and the new version is activated. Run locally.
- **Corruption recovery test** — A test that simulates a corrupted decoder installation and verifies the provisioner self-heals. Run locally.
- **Security audit** — Run `bandit -ll` (already clean), `ruff check .` (already clean), `mypy .` (already clean). Add `safety check` for dependency vulnerabilities and `pip-audit` for the venv. Run locally.
- **Fuzz testing** — Feed random/malformed syndrome data to the decoders and verify they handle it gracefully (no crashes, no hangs, honest error messages). Run locally.
- **Performance regression test** — Benchmark each decoder on a standard code and compare against baseline. Flag any regression > 10%. Run locally.
- **Memory leak test** — Run a long decode session (1000+ iterations) and monitor RSS growth. Flag if growth exceeds 10MB per 1000 iterations. Run locally.

---

## 5. Security Hardening

### 5.1 Dependency security (local)
- Run `safety check` and `pip-audit` on the venv before every release.
- Pin all dependencies with exact versions in `requirements.txt` for reproducible builds (currently only `numpy` is range-pinned).
- Add a `SECURITY.md` file with a vulnerability disclosure policy and contact info.
- Add a `CODE_OF_CONDUCT.md` file for the project community.

### 5.2 Application security (local)
- **Licence key handling** — The licence key is stored in `~/.qector/license.key` as a plain text file. Consider encrypting it with `cryptography` (Fernet) so it's not readable by other users on the same machine.
- **MCP server** — The MCP server communicates over stdio only (no network). This is secure by design. No changes needed.
- **Network isolation** — The app has no network calls at runtime (no auto-updater, no telemetry, no analytics). This is good. Ensure no new network calls are added without a clear security review.
- **Input validation** — All user inputs (code parameters, decoder options, file paths) must be validated before passing to the backend. The `utils.py` validation functions should be extended to cover all input paths.
- **Path traversal** — File export paths must be validated to prevent directory traversal attacks. The `utils.get_export_dir()` function should sanitize paths.
- **Temporary files** — The app creates temporary files during doc generation and decode operations. These must be cleaned up even on crash (use `tempfile.NamedTemporaryFile` with `delete=True`).

---

## 6. Documentation Completeness

### 6.1 Current state
- `README.md` — Updated for v0.5.3. Must be updated for v1.0.0.
- `README_v3.md` — Full README. Must be updated for v1.0.0.
- `README_LINUX.md` — Linux-specific README. Must be updated for v1.0.0.
- `AGENT.md` — Agent instructions. Must be regenerated from live facts before every release.
- `CHANGELOG.md` — Must have a v1.0.0 entry.
- `UPGRADE_NOTES.md` — Must have a v1.0.0 entry.
- `PROJECT_STATUS.md` — Must be updated for v1.0.0.
- `RELEASE_REPORT.md` — Must be updated for v1.0.0.
- `docs/api.md` — Must be regenerated from live source.
- `docs/architecture.md` — Must be updated for v1.0.0.
- `manuals/` — All PDFs and JSON manuals must be regenerated at v1.0.0.
- `EULA.txt` — Must be updated to v1.0.0.
- `PACKAGING.md` — Must be updated for v1.0.0.
- `SHIP_0.6.8_HOTFIX.md` — Historical; no changes needed.

### 6.2 Documentation gaps
- **API reference** — `docs/api.md` is auto-generated from source docstrings. Ensure all public functions have complete docstrings.
- **User manual** — `manuals/` contains PDFs for all platforms. Must be regenerated at v1.0.0 with the new version number and any new features.
- **MCP tool reference** — The MCP server has 56 tools. A machine-readable tool manifest (JSON) should be generated and included in the release bundle so AI agents can discover tools without connecting to the server.
- **Changelog format** — `CHANGELOG.md` should follow Keep a Changelog format (https://keepachangelog.com/) with sections for Added, Changed, Deprecated, Removed, Fixed, Security.
- **Contributing guide** — No `CONTRIBUTING.md` exists. Add one with build instructions, test instructions, and PR guidelines.
- **Code of conduct** — No `CODE_OF_CONDUCT.md` exists. Add one.
- **Security policy** — No `SECURITY.md` exists. Add one with vulnerability disclosure instructions.

---

## 7. Performance Optimizations

### 7.1 Decoder performance
- The 16 decoders have varying performance characteristics. For v1.0.0:
  - Add a **decoder benchmark suite** that runs each decoder on a standard code (e.g., `rotated_surface d=5`) and records latency percentiles (p50, p90, p99).
  - Include benchmark results in the release notes so users can choose the right decoder for their use case.
  - Consider adding a **decoder auto-select** feature that picks the fastest decoder that produces correct results for a given code family.

### 7.2 GUI performance
- The matplotlib figures in each tab are rendered on the Tk main thread. For large codes (d > 10), this can cause UI freezes.
  - Add **figure caching** — don't re-render a figure if the code and decoder parameters haven't changed.
  - Add **progressive rendering** — render a low-resolution preview first, then refine in the background.
  - Add **figure export progress** — the Export Report buttons should show real progress, not just a spinner.

### 7.3 Build performance (local)
- PyInstaller builds take ~60s each. For development:
  - Add a `--dev` flag to `build_production.py` that skips UPX compression and code signing for faster iteration.
  - Consider using PyInstaller's `--diff` mode to only rebuild changed modules.

---

## 8. Local Build Process

### 8.1 Prerequisites (local)
- Python 3.11 (CPython) installed and on PATH
- `py -3.11` on Windows, `python3.11` on Linux/macOS
- pip installed and working
- PyInstaller: `pip install pyinstaller`
- Inno Setup (Windows only): `ISCC` on PATH for `.exe` installer builds
- `dpkg-deb` (Linux only): for `.deb` package builds
- `fakeroot` (Linux only): for `.deb` package builds with correct permissions
- Apple hardware (macOS only): for `.app` + `.dmg` builds

### 8.2 Local build steps

#### Windows (PowerShell)
```powershell
cd "D:\QECTOR APP"

# 1. Activate venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build onedir (for Inno Setup installer)
py -3.11 -m PyInstaller --clean --noconfirm QectorWorkbench.spec

# 4. Build onefile portable
py -3.11 -m PyInstaller --clean --noconfirm QectorWorkbench-onefile.spec

# 5. Build Inno Setup installer (requires ISCC on PATH)
py -3.11 scripts\build_installer.py --inno

# 6. Build release bundles
py -3.11 scripts\build_public_bundles.py

# 7. Verify frozen MCP
py -3.11 verify_frozen_mcp.py

# 8. Run test suite
py -3.11 -m pytest tests/ -q

# 9. Check docs consistency
py -3.11 scripts\check_docs.py
```

#### Linux (bash)
```bash
cd /path/to/QECTOR APP

# 1. Activate venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build .deb package
python3 build_production.py --deb

# 4. Build AppImage (requires Linux host)
cd Linux && ./compile.sh --docker --test

# 5. Build release bundles
python3 scripts/build_public_bundles.py

# 6. Verify frozen MCP
python3 verify_frozen_mcp.py

# 7. Run test suite
python3 -m pytest tests/ -q

# 8. Check docs consistency
python3 scripts/check_docs.py
```

#### macOS (bash, requires Apple hardware)
```bash
cd /path/to/QECTOR APP

# 1. Activate venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build .app + .dmg
cd Mac && ./build_macos.sh --arch arm64 --test

# 4. Build release bundles
python3 scripts/build_public_bundles.py

# 5. Verify frozen MCP
python3 verify_frozen_mcp.py

# 6. Run test suite
python3 -m pytest tests/ -q

# 7. Check docs consistency
python3 scripts/check_docs.py
```

### 8.3 Local build verification
After each local build, verify:
- The `.exe` / `.deb` / `.dmg` exists and has a non-zero size
- The frozen MCP verify passes (`verify_frozen_mcp.py` → PASS)
- The test suite passes (`pytest tests/` → all green)
- The docs check passes (`scripts/check_docs.py` → public docs agree with live code)
- The portable `.exe` runs on a machine with no external Python (Windows only)
- The `.deb` installs and runs on a clean Debian/Ubuntu system (Linux only)
- The `.app` launches and runs on a clean macOS system (macOS only)

---

## 9. Code Quality

### 9.1 Linting and formatting
- `ruff` is already configured and clean. Maintain this.
- `mypy` is already clean. Maintain this.
- `bandit` is already clean. Maintain this.
- Add **`black`** formatting with a `pyproject.toml` config to ensure consistent formatting across all three platform trees.
- Add **`isort`** import sorting to keep imports organized.

### 9.2 Type hints
- The codebase uses `from __future__ import annotations` and type hints in most places. For v1.0.0:
  - Ensure **all** public functions have complete type annotations (no `Any` where a specific type is known).
  - Add a `py.typed` marker file so the package can be used as a type-aware dependency.
  - Run `mypy --strict` locally and fail on any new type errors.

### 9.3 Docstrings
- All public functions should have Google-style docstrings with Args, Returns, and Raises sections.
- All public classes should have docstrings explaining their purpose and key attributes.
- Module-level docstrings should explain the module's role in the architecture.

---

## 10. Known Limitations (v1.0.0)

Document these honestly in `README.md` and `RELEASE_REPORT.md`:

1. **macOS requires Apple hardware** — PyInstaller cannot cross-compile macOS apps. The build must run on a Mac or macOS CI runner.
2. **GPU decoding is Enterprise-tier gated** — Community licences disable GPU batch decode and GNN decoders. The tier readout in the Lab & Personal Info tab shows the real entitlement.
3. **OpenCL is unavailable in the shipped decoder build** — The `qector-decoder-v3` 0.7.0 wheel ships without OpenCL kernels. The Hardware tab distinguishes "this build ships no OpenCL" from "this machine has no OpenCL device."
4. **Logical failure fractions in generated reports are screening estimates** — 25 trials per decoder resolves to 1/25 = 0.04; the figures state this limit.
5. **The app requires a system Python with pip for decoder provisioning** — A machine with no Python and no bundled decoder wheel cannot provision the decoder. This is an architectural decision (bundle the decoder, or bundle a Python) tracked separately.
6. **The `.deb` package requires system Python 3.10+ and pip** — The .deb is a thin application layer; the scientific stack comes from the system package manager.

---

## 11. Implementation Order

### Phase 1: Critical fixes (must-do before v1.0.0)
1. Fix `build_production.py` syntax error (lines 63-68 indentation)
2. Fix `WHEEL_FILES` version mismatch (`1.0.0` vs `0.7.0`)
3. Make bundled wheel version dynamic in spec files
4. Sync all bug fixes from `lastdev.md` and `app_todo.md` to `Linux/` and `Mac/` trees
5. Update all version strings to `1.0.0`

### Phase 2: Hardening (should-do for bulletproof quality)
6. Add provisioning timeout, retry, and checksum verification
7. Add MCP per-tool timeout and concurrent request guard
8. Add GUI tab crash recovery
9. Add input validation and path traversal protection
10. Add build reproducibility and artifact signing

### Phase 3: Completeness (nice-to-have for top-tier)
11. Build macOS `.dmg` on Apple hardware
12. Build Linux AppImage locally
13. Add end-to-end decode test for all 16 decoders × 10 code families
14. Add offline provisioning test
15. Add security audit (`safety check`, `pip-audit`)
16. Add `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
17. Regenerate all docs and manuals at v1.0.0
18. Automate local build process with a single `build_all.sh` / `build_all.ps1` script

---

## 12. Verification Checklist

Before tagging `v1.0.0` locally:

- [ ] `pytest tests/` — all green (403+ passed, 0 failed)
- [ ] `python test_mcp_all.py` — 56/56 tools pass (in-process + stdio)
- [ ] `python verify_frozen_mcp.py` — PASS over the wire
- [ ] `python scripts/check_docs.py` — public docs agree with live code
- [ ] `ruff check .` — clean
- [ ] `mypy .` — no issues
- [ ] `bandit -ll` — no medium/high findings
- [ ] `safety check` — no vulnerabilities
- [ ] `pip-audit` — no vulnerable dependencies
- [ ] Windows `.exe` built and frozen MCP verified locally
- [ ] Linux `.deb` built and verified locally
- [ ] macOS `.dmg` built on Apple hardware and verified locally
- [ ] All 8 GUI tabs render correctly on a real display
- [ ] All 16 decoders decode correctly on all 10 code families
- [ ] Offline provisioning works (no network, bundled wheel)
- [ ] Online provisioning works (PyPI, live install)
- [ ] Upgrade path works (older decoder → newer decoder)
- [ ] Corruption recovery works (broken install → self-heal)
- [ ] Release bundles built with fresh checksums and manifest
- [ ] All docs regenerated at v1.0.0
- [ ] `AGENT.md` reflects live facts (not stale 3.5.x-era content)
- [ ] `CHANGELOG.md` has v1.0.0 entry
- [ ] `UPGRADE_NOTES.md` has v1.0.0 entry
- [ ] `RELEASE_REPORT.md` has v1.0.0 verification results
- [ ] `PROJECT_STATUS.md` updated for v1.0.0
- [ ] `README.md`, `README_v3.md`, `README_LINUX.md` updated for v1.0.0
- [ ] `EULA.txt` updated to v1.0.0
- [ ] `installer_version.iss` updated to `1.0.0`
- [ ] `pyproject.toml` version set to `1.0.0`, `Development Status :: 5 - Production/Stable`
- [ ] `version.py` `WORKBENCH_VERSION = "1.0.0"`
- [ ] All `Linux/` and `Mac/` trees synced with root
- [ ] No stale artifacts from previous releases in `dist/`, `release_assets/`, `winzip/`, `linuxzip/`
- [ ] `build_production.py` syntax verified (importable without errors)
- [ ] `build_public_bundles.py` `--allow-stale` does NOT produce stale bundles
- [ ] All release bundles pass the staleness guard
- [ ] Checksums match the actual files in `release_assets/`
- [ ] `scripts/check_docs.py` passes locally
- [ ] No hardcoded version strings remain anywhere except `version.py`
- [ ] No hardcoded wheel filenames remain anywhere except `build_production.py` WHEEL_FILES (which must match `BACKEND_VERSION`)
- [ ] No hardcoded contact addresses remain (must be `admin@qector.store` everywhere)
- [ ] No fabricated author identity in any generated artifact
- [ ] No typographic dashes in any generated artifact
- [ ] All 8 doc formats work (Markdown, JSON, HTML, LaTeX, PDF, SVG, `.zenodo.json`, `CITATION.cff`)
- [ ] All export buttons in all 8 tabs work (the 4 that were broken in v0.5.2)
- [ ] Licence key field writes to `~/.qector/license.key` and is read by the decoder
- [ ] Buy Licence / Contact Sales / Website links are functional
- [ ] Developer & Licensing section is present in the Documentation tab
- [ ] `lab_info_tab.py` is included in `APP_MODULES` in `build_production.py`
- [ ] Module closure check passes (`_check_module_closure`)
- [ ] `.deb` package installs and runs correctly on a clean Debian/Ubuntu system
- [ ] Windows installer (Inno Setup) builds and installs correctly locally
- [ ] Portable `.exe` runs on a machine with no external Python
- [ ] Frozen MCP verify passes from the portable `.exe`
- [ ] `--mcp` mode works from the frozen `.exe`
- [ ] `--cli` mode works from the frozen `.exe`
- [ ] `--decoder-selftest` works from the frozen `.exe`
- [ ] `--cli version` reports `1.0.0`
- [ ] `--cli diagnostics` passes (11/0/0)
- [ ] Splash screen appears within 1s of launch
- [ ] Real window appears within 5s of launch (source) or 15s (frozen)
- [ ] Window is centered on the primary monitor
- [ ] Window is not obscured by other windows
- [ ] All tabs render correctly on first launch
- [ ] Console tab shows live output from background tasks
- [ ] Crash in any tab does not affect other tabs
- [ ] Crash in the GUI does not lose unsaved work
- [ ] Memory usage is stable over long sessions (no leaks)
- [ ] CPU usage is idle when no decode is running
- [ ] Disk usage does not grow unbounded (temp files are cleaned up)
- [ ] Network usage is zero at runtime (no telemetry, no update checks)
- [ ] No personal data is collected, transmitted, or stored
- [ ] EULA is displayed on first launch or accessible from the Help menu
- [ ] All third-party licenses are included in the distribution
- [ ] `LICENSE` file (if different from `EULA.txt`) is present and correct
- [ ] `NOTICE` file (if any) is included with copyright notices
- [ ] All generated output includes "QECTOR" provenance tags
- [ ] All generated output includes `.zenodo.json` and `CITATION.cff` where applicable
- [ ] All generated output uses typographic quotes, not ASCII straight quotes
- [ ] All generated output uses typographic dashes (—), not ASCII hyphens (--)
- [ ] All generated output has correct metadata (author, date, version)
- [ ] All generated output is valid (PDF opens, HTML renders, JSON parses, etc.)
- [ ] The `manuals/` directory contains all expected deliverables
- [ ] The `docs/` directory contains all expected deliverables
- [ ] The `release_assets/` directory contains all expected artifacts
- [ ] `checksums.txt` and `RELEASE_MANIFEST.txt` are present and correct
- [ ] No secrets or API keys are committed to the repository
- [ ] `.gitignore` excludes all build artifacts, temp files, and IDE files
- [ ] `.dockerignore` excludes all unnecessary files from Docker builds
- [ ] The `Linux/` and `Mac/` trees are either synced or documented as platform-specific overrides
- [ ] No `Linux/` or `Mac/` specific bugs exist (all fixes applied to all three trees)
- [ ] The `build_macos.sh` script is executable and produces a valid `.dmg`
- [ ] The `compile.sh --docker` script produces a valid AppImage
- [ ] The `build_deb_wsl.sh` script is either functional or removed if obsolete
- [ ] All build scripts (`build_production.py`, `build_installer.py`, `build_public_bundles.py`, `check_docs.py`, `update_release_assets.py`) are tested and work locally
- [ ] All test scripts (`test_mcp_all.py`, `verify_frozen_mcp.py`, `qector_v069_benchmark.py`) are tested and work locally
- [ ] The `tests/` directory has comprehensive coverage for all critical paths
- [ ] The `tests/regression/` directory has baseline benchmarks for performance regression detection
- [ ] The `tests/conftest.py` sets up the test environment correctly
- [ ] All test files are importable and runnable without errors
- [ ] The test suite runs in under 5 minutes
- [ ] The test suite is deterministic (no flaky tests)
- [ ] The test suite covers all 16 decoders × 10 code families
- [ ] The test suite covers all 56 MCP tools
- [ ] The test suite covers all 8 GUI tabs
- [ ] The test suite covers provisioning (bootstrap, ensure, activate, verify)
- [ ] The test suite covers version resolution (workbench version, backend version, live PyPI)
- [ ] The test suite covers error paths (network failure, disk full, corrupted wheel, ABI mismatch)
- [ ] The test suite covers security paths (input validation, path traversal, licence key handling)
- [ ] The test suite covers performance paths (decode latency, memory usage, temp file cleanup)
- [ ] The test suite covers cross-platform paths (Windows paths, Linux paths, macOS paths)
- [ ] The test suite covers offline paths (no network, bundled wheel only)
- [ ] The test suite covers upgrade paths (old decoder → new decoder)
- [ ] The test suite covers corruption recovery paths (broken install → self-heal)
- [ ] All documentation is consistent with the code (no stale numbers, no fabricated features)
- [ ] The `docs/api.md` matches the live MCP tool registry
- [ ] The `docs/architecture.md` matches the actual module structure
- [ ] The `README.md` download table only names artifacts that actually exist in `release_assets/`
- [ ] The `README.md` feature list matches the actual implemented features
- [ ] The `PROJECT_STATUS.md` reflects the current state (v1.0.0, 56 tools, 16 decoders, 10 families)
- [ ] The `RELEASE_REPORT.md` has v1.0.0 verification results
- [ ] The `CHANGELOG.md` has a v1.0.0 entry with all changes since v0.5.3
- [ ] The `UPGRADE_NOTES.md` has a v1.0.0 entry with migration notes (if any)
- [ ] All version numbers in all files are consistent (1.0.0 for workbench, 1.0.0 for backend)
- [ ] No file contains a stale version number from a previous release
- [ ] The `LICENSE` file (if separate from `EULA.txt`) is present and correct
- [ ] The `NOTICE` file (if any) is present and correct
- [ ] All copyright notices are correct and up to date
- [ ] The `CONTRIBUTING.md` is present and has build/test instructions
- [ ] The `CODE_OF_CONDUCT.md` is present
- [ ] The `SECURITY.md` is present with vulnerability disclosure instructions
- [ ] All local builds pass before tagging `v1.0.0`
- [ ] The git tag `v1.0.0` is created and pushed
- [ ] The release notes are generated from the changelog since the last tag

---

*End of devv1.md — QECTOR Decoder Workbench v1.0.0 local build production-readiness plan.*