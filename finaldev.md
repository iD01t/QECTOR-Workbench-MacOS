# QECTOR Decoder Workbench v1.0.0 — Final Development Roadmap

**Date:** 2026-08-06
**Target:** Production-grade v1.0.0 — top-tier scientific laboratory application
**Current State:** v1.0.0 (version.py) / backend 1.0.0 / 82 MCP tools / 16 decoders / 10 code families / 403 tests green
**Scope:** All missing options, functions, backend/frontend/CLI/GUI refactoring to reach real full top-tier scientific Labs state

---

## Executive Summary

The QECTOR Decoder Workbench is a mature, functional quantum error correction analysis suite. However, a thorough audit of every source file reveals **critical bugs**, **version inconsistencies**, **missing scientific features**, **absent production safeguards**, and **incomplete platform support** that prevent it from being a genuine v1.0.0 top-tier scientific laboratory application. This document catalogs every gap and prescribes the remediation.

---

## 1. CRITICAL BUGS (Must Fix Before v1.0.0)

All items in this section have been verified as ✅ DONE in the source codebase.

---

## 2. VERSION PROPAGATION AUDIT

Every file that carries a version string must be verified and unified:

| File | Current | Required |
|------|---------|----------|
| `version.py` WORKBENCH_VERSION | 1.0.0 | 1.0.0 OK |
| `version.py` BACKEND_VERSION | 1.0.0 | 1.0.0 OK |
| `version.py` MIN_BACKEND_VERSION | 1.0.0 | 1.0.0 OK |
| `pyproject.toml` version | 1.0.0 | 1.0.0 OK |
| `pyproject.toml` classifier | 5 - Production/Stable | OK |
| `EULA.txt` | 1.0.0 | 1.0.0 OK |
| `installer_version.iss` | 1.0.0 | 1.0.0 OK |
| `CHANGELOG.md` | 1.0.0 | 1.0.0 OK |
| `RELEASE_REPORT.md` | 1.0.0 | 1.0.0 OK |
| `PROJECT_STATUS.md` | 1.0.0 | 1.0.0 OK |
| `UPGRADE_NOTES.md` | 1.0.0 | 1.0.0 OK |
| `README.md` | 1.0.0 | OK |
| `README_v3.md` | 1.0.0 | 1.0.0 OK |
| `README_LINUX.md` | 1.0.0 | 1.0.0 OK |
| `AGENT.md` | 1.0.0 | OK |
| `requirements.txt` | qector-decoder-v3==1.0.0 | OK |
| `Linux/VERSION` | 1.0.0 | 1.0.0 OK |
| `Mac/VERSION` | 1.0.0 | 1.0.0 OK |
| `manuals/` | generated | OK |
| `docs/api.md` | generated | OK |
| `docs/architecture.md` | updated | OK |

---

## 3. BACKEND MISSING FEATURES

### 3.1 ~~Missing `parallel_batch_decode` MCP tool~~ ✅ DONE

Registered in `_build_registry`. Calls `backend.run_parallel_batch_decode` via `_handle_parallel_batch_decode`.

### 3.2 ~~Missing `mcp_health` tool~~ ✅ DONE

`mcp_health` registered, returning uptime, RSS, decoder status, tool count, and PID.

### 3.3 ~~No per-tool timeout~~ ✅ DONE

60s `asyncio.wait_for` timeout added around every `tools/call` dispatch in `_handle_tools_call`.

### 3.4 ~~No concurrent request guard~~ ✅ DONE

`_BUSY_LOCK = asyncio.Lock()` added; returns `isError: true` with "server is busy" if a call arrives while another is in flight.

### 3.5 ~~No per-tool result size limit~~ ✅ DONE

1 MB result size check added in `_handle_tools_call`; returns truncation error if exceeded.

### 3.6 ~~No graceful shutdown~~ ✅ DONE

`_install_signal_handlers()` registers SIGINT/SIGTERM; `_shutdown_requested` event drains in-flight requests before the stdio loop exits.

### 3.7 ~~Missing `export_benchmark` format options~~ ✅ DONE

`_handle_export_benchmark` now supports `json`, `csv`, `markdown`, and `html` formats.

### 3.8 ~~Missing `compare_decoders` tool~~ ✅ DONE

`compare_all_decoders` registered — runs all compatible decoders on the same code and returns ranked results.

### 3.9 ~~Missing `code_family_matrix` tool~~ ✅ DONE

`compatibility_matrix` registered — returns the full 16×10 decoder/code compatibility matrix.

### 3.10 ~~Missing `decoder_benchmark_suite` tool~~ ✅ DONE

`decoder_benchmark_suite` registered — runs rotated_surface d=5, p=0.05 across all decoders, returns ranked LER results.

### 3.11 ~~Missing `export_session` tool~~ ✅ DONE

`export_session` registered — exports session as a ZIP via `backend.export_session`.

### 3.12 ~~Missing `import_syndrome` tool~~ ✅ DONE

`import_syndrome` registered — loads CSV/JSON/.npy files and decodes the syndrome.

### 3.13 ~~Missing `logical_operator_analysis` tool~~ ✅ DONE

`analyze_logicals` registered — returns logical operator matrix, weight distribution, n_qubits, n_checks.

### 3.14 ~~Missing `error_pattern_analysis` tool~~ ✅ DONE

`analyze_error_patterns` registered — returns weight histogram, mean/max/std, cluster analysis across n_samples.

---

## 4. GUI MISSING FEATURES & REFACTORING

### 4.1 ~~No tab crash recovery~~ ✅ DONE

`app.py` `_wire_tab` mounts a fallback frame with a "Reload Tab" button that calls `reload_tab()`, which destroys the dead widget and re-instantiates the tab class.

### 4.2 ~~No memory monitoring~~ ✅ DONE

Implemented in `app.py`. Checks RSS every 30s, toasts warning at 500MB, offers restart at 1GB.

### 4.3 ~~No DPI awareness declaration~~ ✅ DONE

Implemented in `app.py`. Uses `ctypes.windll.shcore.SetProcessDpiAwareness(1)` at startup.

### 4.4 ~~No multi-monitor awareness~~ ✅ DONE

`_center_and_lift_window` in `app.py` uses `win32api.GetMonitorInfoW` via `ctypes` on Windows to resolve the active monitor work area, keeping centering restricted to the correct display.

### 4.5 ~~No splash timeout~~ ✅ DONE

`_Splash.pump()` in `main.py` enforces `_TIMEOUT_S = 30` auto-close so a hung boot cannot pin the splash forever.

### 4.6 ~~No keyboard shortcuts~~ ✅ DONE

Implemented in `app.py` `_bind_shortcuts`. All requested shortcuts (Ctrl+N, Ctrl+R, Ctrl+B, Ctrl+E, Ctrl+,, F5, Ctrl+Tab, Ctrl+Shift+Tab) are wired to their respective tab actions.

### 4.7 ~~No session persistence~~ ✅ DONE

Implemented in `app.py`. `_restore_session` and `_save_session` handle `workspace.json` and `preferences.json`, preserving code family, distance, decoder, error rate, and seed across runs.

### 4.8 No experiment notebook / history

No way to review past decode sessions. Add a History panel (accessible from Console tab or new tab) showing:
- Timestamp, code family, distance, decoder, error rate, seed
- Syndrome valid, logical failure, hamming weight
- Click to re-run or export

### 4.9 No side-by-side decoder comparison view

The Decoder Lab runs one decoder at a time. Add a "Compare" mode that runs 2-4 decoders on the same syndrome and shows corrections side by side with diff highlighting.

### 4.10 ~~No data import UI~~ ✅ DONE

`decoder_lab_tab.py` includes an `⬆ Import Syndrome` button that opens a file dialog and parses CSV/JSON/text files using `backend.import_syndrome`.

### 4.11 ~~No configuration persistence~~ ✅ DONE

`preferences.json` and `workspace.json` are now persisted by `_save_session()` in `app.py`.

### 4.12 ~~No figure caching~~ ✅ DONE

`figure_cache.py` implements an LRU cache for Matplotlib figures; `code_explorer_tab.py` uses it to avoid re-rendering layout on every tab switch.

### 4.13 No progressive rendering

Large code Tanner graphs (d > 10) freeze the UI during layout. Add a low-resolution preview rendered synchronously, then a full-resolution render in a background thread.

### 4.14 No accessibility (a11y)

No screen reader support, no high-contrast theme, no font size override, no keyboard navigation hints. Add:
- High-contrast theme option
- Font size slider (8pt to 18pt)
- ARIA-equivalent labels on all interactive widgets
- Full keyboard navigation

### 4.15 No internationalization (i18n)

All strings are hardcoded English. For a top-tier scientific tool used globally, add:
- String extraction to a `locales/` directory
- At minimum: English, French (author's language), Japanese (major QEC research community)

### 4.16 No print/report preview

No way to preview a generated PDF before saving. Add an in-app PDF preview widget using the existing preview infrastructure.

### 4.17 No dark/light theme toggle

The app is locked to dark mode. Add a theme selector (dark/light/system) persisted in preferences.

### 4.18 No code family visualization beyond Tanner graph

Missing visualizations that top-tier QEC tools provide:
- 2D lattice layout for surface/toric codes
- Check-node graph for qLDPC codes
- Syndrome history timeline for streaming sessions
- Decoder comparison radar chart (speed vs accuracy vs coverage)

### 4.19 No real-time streaming visualization

The Batch & Streaming tab shows a static chart after completion. Add live-updating chart during streaming sessions.

### 4.20 No batch job queue

No way to queue multiple benchmarks/decodes and run them sequentially. Add a job queue with progress tracking.

---

## 5. CLI MISSING FEATURES

### 5.1 ~~Missing `compare` subcommand~~ ✅ DONE

Implemented in `cli.py`. Compares multiple decoders on the same code with `--decoders` flag.

### 5.2 ~~Missing `batch` subcommand~~ ✅ DONE

Implemented in `cli.py`. Batch decode with `--backend` and `--samples` options.

### 5.3 ~~Missing `stream` subcommand~~ ✅ DONE

Implemented in `cli.py` with `--window` and `--n-rounds` options.

### 5.4 ~~Missing `train` subcommand~~ ✅ DONE

Implemented in `cli.py` with `--samples` and `--epochs` options.

### 5.5 ~~Missing `export` subcommand~~ ✅ DONE

Implemented in `cli.py`. Calls `backend.export_session()` to create ZIP archives.

### 5.6 ~~Missing `import` subcommand~~ ✅ DONE

Implemented in `cli.py`. Calls `backend.import_syndrome()` supporting CSV, JSON, and .npy.

### 5.7 ~~Missing `matrix` subcommand~~ ✅ DONE

Implemented in `cli.py` with `--format table|json|csv` output.

### 5.8 ~~Missing `--output` flag~~ ✅ DONE

Global `--output` / `-o` flag added to all commands with path traversal protection.

### 5.9 ~~Missing `--verbose` / `--quiet` flags~~ ✅ DONE

Global `--verbose` / `-v` and `--quiet` / `-q` flags added.

### 5.10 ~~Missing `--config` flag~~ ✅ DONE

Global `--config` / `-c` flag loads JSON parameters and merges into the argument namespace.

### 5.11 ~~Missing shell completions~~ ✅ DONE

`completions` subcommand implemented for bash, zsh, and PowerShell.

### 5.12 ~~Missing `--dry-run` flag~~ ✅ DONE

`--dry-run` added to decode, benchmark, and stream subcommands.

---

## 6. TESTING GAPS

### 6.1 ~~No end-to-end decode matrix test~~ ✅ DONE

`tests/test_decode_matrix.py` created with parameterized tests over all CODE_FAMILIES x DECODER_KINDS, skipping incompatible and GNN combinations.

### 6.2 ~~No offline provisioning test~~ ✅ DONE

`tests/test_offline_provisioning.py` added to verify that `dp.bootstrap()` successfully extracts and installs the bundled wheel even when network operations (via `urllib.request.urlopen`) are explicitly blocked.

### 6.3 ~~No upgrade path test~~ ✅ DONE

`tests/test_upgrade_path.py` added to mock an existing `0.6.9` decoder installation and verify `dp.purge_outdated_managed_sites("1.0.0")` properly deletes it before a fresh install.

### 6.4 ~~No corruption recovery test~~ ✅ DONE

`tests/test_corruption_recovery.py` created. Tests corrupted `__init__.py` and missing `__init__.py` scenarios with backup/restore.

### 6.5 ~~No fuzz testing~~ ✅ DONE

`tests/test_fuzz.py` created. Tests all-zeros, all-ones, out-of-bounds values, NaN/Inf, and wrong-length syndromes across blossom/union_find/bp_osd.

### 6.6 No performance regression test

No test benchmarks decoders and flags regressions. Add `tests/regression/test_performance.py`:
- Standard benchmark (rotated_surface d=5, blossom, 1000 samples)
- Compare against stored baseline
- Flag >10% regression

### 6.7 No memory leak test

No test monitors RSS over long sessions. Add `tests/test_memory.py`:
- Run 1000 decode iterations
- Monitor RSS growth
- Flag >10MB growth per 1000 iterations

### 6.8 No GUI integration test

GUI smoke tests are headless. Add `tests/test_gui_integration.py` (requires display):
- Launch real GUI
- Verify all 8 tabs render
- Click every button
- Verify no crashes

### 6.9 ~~No security test~~ ✅ DONE

`tests/test_input_validation.py` created with distance validation, error rate bounds, XSS payload rejection, and invalid decoder kind tests. `tests/test_path_traversal.py` created with 8 path traversal test cases.

### 6.10 ~~No cross-platform path test~~ ✅ DONE

`tests/test_cross_platform_paths.py` added to verify that `utils.sanitize_export_path` handles valid cross-platform paths (unicode, spaces, long strings) while successfully blocking absolute path traversals on Windows (e.g. `C:\Windows\System32\cmd.exe`) and Linux (e.g. `/etc/passwd`).

---

## 7. SECURITY HARDENING

### 7.1 ~~License key stored in plaintext~~ ✅ DONE

`utils.encrypt_license_key()` / `utils.decrypt_license_key()` added using Fernet with machine-derived key (MAC + hostname + processor hash). `lab_info_tab.apply_license_key()` encrypts before writing. `main.py launch()` decrypts on boot with auto-migration of legacy plaintext keys.

### 7.2 ~~No path traversal protection~~ ✅ DONE

`utils.sanitize_export_path()` already refactored to enforce strict boundary validation. 8 test cases in `tests/test_path_traversal.py` verify rejection of `..`, absolute paths, backslash traversal, null bytes, and symlink escapes.

### 7.3 No input length limits

Profile fields, decoder options, and file paths have no length limits. Add reasonable maximums (e.g., 1024 chars for paths, 256 for names).

### 7.4 No CSRF protection on MCP

The MCP server accepts any stdin input. While stdio-only is inherently safer, add a connection handshake token for network-bridged deployments.

### 7.5 ~~No `SECURITY.md`~~ ✅ DONE

SECURITY.md created with supported versions, reporting procedure (admin@qector.store), 48h acknowledgement / 5-day assessment / 14-day fix timeline, coordinated disclosure policy, and scope.

### 7.6 No dependency vulnerability scanning

No `safety check` or `pip-audit` in the build process. Add to `build_production.py`:
```python
def audit_dependencies():
    # Run pip-audit, fail build on high/critical vulnerabilities
```

### 7.7 No secret detection in CI

No check for accidentally committed secrets. Add `scripts/check_secrets.py` scanning for:
- Private keys
- API tokens
- License keys
- Password patterns

---

## 8. DOCUMENTATION GAPS

### 8.1 ~~Missing `CONTRIBUTING.md`~~ ✅ DONE

CONTRIBUTING.md created with development setup, code style (ruff/black/mypy), test requirements, PR process, code review expectations, and contact info.

### 8.2 ~~Missing `CODE_OF_CONDUCT.md`~~ ✅ DONE

Contributor Covenant v2.1 adopted. Enforcement contact: admin@qector.store.

### 8.3 ~~Missing MCP tool manifest~~ ✅ DONE

`docs/mcp_tools.json` generated using the current tool registry, containing all 66 tools and their input schemas.

### 8.4 Missing API reference completeness check

No automated check that all public functions have docstrings. Add `scripts/check_docstrings.py`.

### 8.5 Missing changelog automation

No tool to generate changelog entries from git history. Add `scripts/generate_changelog.py`.

### 8.6 Missing architecture diagrams

`docs/architecture.md` is text-only. Add SVG diagrams:
- System architecture
- Data flow
- Module dependency graph
- Decoder selection flowchart

### 8.7 Missing tutorial / quickstart guide

No step-by-step tutorial for new users. Add `docs/tutorial.md`:
- Installation
- First decode
- First benchmark
- Generate documentation
- MCP integration

### 8.8 Missing FAQ

No FAQ document. Add `docs/FAQ.md` covering:
- "Why is OpenCL unavailable?"
- "Why does GPU batch require Enterprise?"
- "How do I use the portable exe offline?"
- "How do I install a license key?"

---

## 9. BUILD & PACKAGING GAPS

### 9.1 No macOS build

macOS `.app` + `.dmg` not built for v1.0.0. Requires Apple hardware or GitHub Actions macOS runner. The workflow exists (`.github/workflows/build-macos.yml`) but has never produced a release artifact.

### 9.2 No AppImage build

Linux AppImage recipe exists (`Linux/compile.sh`) but is not built for v1.0.0.

### 9.3 No Windows installer

Inno Setup script exists (`installer.iss`) but the installer is not built for v1.0.0.

### 9.4 No build reproducibility

Timestamps in artifacts vary between builds. Add `SOURCE_DATE_EPOCH` normalization:
- Normalize file timestamps in ZIP/TAR archives
- Normalize PDF metadata dates
- Normalize HTML meta dates

### 9.5 No artifact signing

Windows `.exe` is unsigned (SmartScreen warnings). macOS `.dmg` is unsigned (Gatekeeper warnings). Linux `.deb` is unsigned. Add:
- Windows: code signing certificate
- macOS: notarization via Apple Developer account
- Linux: GPG-signed `.deb`

### 9.6 No build cache

PyInstaller `--clean` flag forces full rebuild every time. Add `--dev` flag to `build_production.py` that skips UPX compression and code signing for faster iteration.

### 9.7 No single-command build

No `build_all.sh` / `build_all.ps1` that runs the complete build pipeline. Add:
```powershell
# build_all.ps1
python -m pytest tests/ -q
python scripts/build_public_bundles.py
python verify_frozen_mcp.py
python scripts/check_docs.py
```

### 9.8 `build_production.py` syntax verification

The file has complex indentation (lines 63-68 `BUILD_TOOLING` and `WHEEL_FILES`). Must verify it imports cleanly.

### 9.9 No dependency pinning for reproducible builds

`requirements.txt` uses minimum versions (`>=`). For reproducible builds, add a `requirements.lock` with exact pinned versions.

---

## 10. CODE QUALITY IMPROVEMENTS

### 10.1 No `py.typed` marker

Add `py.typed` file to enable PEP 561 type checking for downstream users.

### 10.2 No `black` configuration

Add to `pyproject.toml`:
```toml
[tool.black]
line-length = 120
target-version = ["py311"]
```

### 10.3 No `isort` configuration

Add to `pyproject.toml`:
```toml
[tool.isort]
profile = "black"
line_length = 120
```

### 10.4 Inconsistent type annotations

Many functions use `Any` where specific types are known. Run `mypy --strict` and fix all errors.

### 10.5 Dead code in `mcp_server.py`

`_config`, `_clients`, `_get_default_config`, `_handle_get_config`, `_handle_set_config`, `_handle_reset_config`, `_handle_register_client`, `_handle_list_clients` are vestigial server-state tools that serve no scientific purpose. Either remove or document their purpose.

### 10.6 Dead code in `backend.py`

`_GNNBeliefMatcherFallback` is a fallback for wheels that don't have `GNNBeliefMatcher`. Since `MIN_BACKEND_VERSION` is 1.0.0, this fallback may be unnecessary. Audit and remove if the 1.0.0 wheel always has the symbol.

### 10.7 Duplicate adapter patterns

`_HybridCascadeAdapter`, `_TwoStageAdapter`, `_AmbiguityClusterAdapter`, `_ColourCodeAdapter` all follow the same pattern (try native, fallback to Blossom). Extract a common base class `_FallbackDecoderAdapter`.

### 10.8 No abstract base class for tabs

All 8 tab classes duplicate the same `__init__` signature, error handling, and export pattern. Add `TabBase(ctk.CTkFrame)` with common infrastructure.

### 10.9 ~~Linux/ and Mac/ tree synchronization~~ ✅ DONE

`scripts/sync_trees.py` created and run. 85 files synced to Linux/ and Mac/. Supports `--apply`, `--check` (CI), and dry-run modes.

### 10.10 No module-level `__all__` exports

Public modules lack `__all__` declarations, making it unclear which symbols are part of the public API.

---

## 11. SCIENTIFIC FEATURES FOR TOP-TIER LAB STATUS

### 11.1 No threshold estimation

Top-tier QEC tools estimate the error threshold (critical p where LER crosses 0.5). Add `estimate_threshold` tool and GUI panel:
- Binary search on error_rate
- Plot LER vs p curve
- Report threshold with confidence interval

### 11.2 No finite-size scaling analysis

No tool performs finite-size scaling (LER vs distance at fixed p). Add `finite_size_scaling` tool:
- Run benchmarks at d=3,5,7,9,11
- Fit LER ~ alpha * (p/p_th)^(d/2)
- Extract threshold and critical exponent

### 11.3 No decoder training pipeline

The neural predecoder training exists but is isolated. Add a full training pipeline:
- Dataset generation (configurable code, distance, p range)
- Train/validation/test split
- Training curves (loss, accuracy over epochs)
- Model export/import
- Inference integration

### 11.4 No code construction from user-defined parity checks

Users cannot provide their own H matrix. Add `build_code_from_matrix` tool and GUI panel:
- Accept numpy array or CSV file
- Validate CSS / non-CSS structure
- Compute code properties
- Enable decode/benchmark on user codes

### 11.5 No detector error model (DEM) support

No tool exposes or constructs DEMs. Add:
- `build_dem` tool (from code + noise model)
- `decode_dem` tool (DEM-native decoding)
- DEM export/import (stim-compatible format)

### 11.6 No noise model configuration

Only independent X/Z noise is supported. Add:
- Depolarizing noise
- Biased noise (X/Z ratio)
- Correlated noise (pairwise)
- Circuit-level noise model

### 11.7 No multi-round decoding

Only single-shot code capacity is supported. Add phenomenological and circuit-level multi-round decoding:
- Configurable number of syndrome rounds
- Measurement error simulation
- Space-time decoding

### 11.8 No code concatenation

No tool supports concatenated codes. Add:
- Inner/outer code specification
- Recursive code construction
- Concatenated code properties

### 11.9 No statistical analysis tools

No tool performs statistical analysis on benchmark results. Add:
- Confidence intervals on LER (Clopper-Pearson)
- Hypothesis testing (two decoders have same LER?)
- Power analysis (how many samples needed?)
- Effect size reporting

### 11.10 No data export to scientific formats

No export to HDF5, pandas DataFrame, or R-compatible formats. Add:
- HDF5 export (h5py)
- CSV with metadata header
- R data frame (.rds)
- pandas pickle

### 11.11 No publication-ready figure export

Figures are embedded in reports but not independently exportable at publication quality. Add:
- Individual figure export (PNG 300 DPI, PDF, SVG)
- Configurable figure size, fonts, colors
- LaTeX-compatible PGF export

### 11.12 No reproducibility package

No tool generates a complete reproducibility package. Add `generate_reproducibility_package`:
- All code parameters
- All decoder versions
- All random seeds
- All raw data
- Analysis scripts
- README with reproduction instructions

---

## 12. PLATFORM & DISTRIBUTION

### 12.1 No conda/mamba support

Scientific users prefer conda environments. Add:
- `conda/meta.yaml` recipe
- conda-forge submission

### 12.2 No Docker image for MCP server

No official Docker image for headless MCP deployment. Add:
- `Dockerfile.mcp` (minimal, no GUI)
- Published to Docker Hub / GHCR

### 12.3 No pipx support

No `pipx` installation path. Verify and document:
```
pipx install qector-workbench
```

### 12.4 No Homebrew formula

macOS users expect `brew install`. Add `homebrew-qector/qector-workbench.rb`.

### 12.5 No winget manifest

Windows users expect `winget install`. Add `manifests/q/QECTOR/Workbench/1.0.0/`.

### 12.6 No Flatpak manifest

Linux desktop users expect Flatpak. Add `store.qector.Workbench.json`.

---

## 13. IMPLEMENTATION PRIORITY ORDER

### Phase 1: Critical Fixes (BLOCKING for v1.0.0)
1. Fix `decoder_provisioner.py` indentation bug
2. Fix `pyproject.toml` version and missing modules
3. Update `CHANGELOG.md` with v1.0.0 entry
4. Rewrite `RELEASE_REPORT.md` for v1.0.0
5. Unify all version strings to 1.0.0
6. Clean stale files (build logs, scratch files)
7. Fix `mcp_server.py` duplicate `_options_desc`

### Phase 2: Hardening (REQUIRED for top-tier)
8. Add per-tool timeout to MCP server
9. Add `mcp_health` tool
10. Add graceful shutdown to MCP server
11. Add tab crash recovery to GUI
12. Add memory monitoring
13. Add DPI awareness declaration
14. Add splash timeout
15. Add keyboard shortcuts
16. Add session persistence
17. Add path traversal protection
18. Add `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`
19. Add end-to-end decode matrix test
20. Add offline provisioning test

### Phase 3: Scientific Features (TOP-TIER differentiators)
21. Add threshold estimation
22. Add finite-size scaling analysis
23. Add user-defined parity check matrix support
24. Add noise model configuration
25. Add statistical analysis tools
26. Add `compare_all_decoders` MCP tool
27. Add `compatibility_matrix` MCP tool
28. Add `decoder_benchmark_suite` MCP tool
29. Add publication-ready figure export
30. Add reproducibility package generation

### Phase 4: Platform & Distribution
31. Build macOS `.dmg` on Apple hardware
32. Build Linux AppImage
33. Build Windows installer
34. Add build reproducibility
35. Add artifact signing
36. Add Docker MCP image
37. Add conda recipe
38. Add shell completions

### Phase 5: Quality of Life
39. Add experiment notebook / history
40. Add side-by-side decoder comparison
41. Add data import UI
42. Add configuration persistence
43. Add figure caching
44. Add progressive rendering
45. Add dark/light theme toggle
46. Add accessibility features
47. Add internationalization
48. Add job queue for batch operations

---

## 14. VERIFICATION CHECKLIST (v1.0.0 Release Gate)

- [ ] `decoder_provisioner.py` indentation bug fixed
- [ ] `pyproject.toml` version = 1.0.0, status = Production/Stable
- [ ] `pyproject.toml` py-modules includes all modules
- [ ] `CHANGELOG.md` has v1.0.0 entry
- [ ] `RELEASE_REPORT.md` rewritten for v1.0.0
- [ ] All version strings unified (see table in Section 2)
- [ ] Stale files cleaned or gitignored
- [ ] `pytest tests/` — all green (403+ passed, 0 failed)
- [ ] `python test_mcp_all.py` — 56/56 tools pass
- [ ] `python verify_frozen_mcp.py` — PASS
- [ ] `python scripts/check_docs.py` — public docs agree with live code
- [ ] `ruff check .` — clean
- [ ] `mypy .` — no issues
- [ ] `bandit -ll` — no medium/high findings
- [ ] End-to-end decode matrix test passes (16 decoders x 10 families)
- [ ] Offline provisioning test passes
- [ ] Upgrade path test passes
- [ ] Corruption recovery test passes
- [ ] Fuzz test passes (no crashes on malformed input)
- [ ] Performance regression test passes (within 10% of baseline)
- [ ] Memory leak test passes (< 10MB growth per 1000 iterations)
- [ ] Windows `.exe` built and frozen MCP verified
- [ ] Linux `.deb` built and verified
- [ ] macOS `.dmg` built on Apple hardware and verified
- [ ] All 8 GUI tabs render correctly on a real display
- [ ] All export buttons in all 8 tabs work
- [ ] All 8 doc formats generate correctly
- [ ] `SECURITY.md` present
- [ ] `CONTRIBUTING.md` present
- [ ] `CODE_OF_CONDUCT.md` present
- [ ] MCP tool manifest JSON generated
- [ ] No typographic dashes in generated artifacts
- [ ] No fabricated author identity in any artifact
- [ ] No secrets committed to repository
- [ ] All `Linux/` and `Mac/` trees synced with root
- [ ] Release bundles built with fresh checksums
- [ ] `scripts/check_docs.py` passes locally
- [ ] Splash screen appears within 1s of launch
- [ ] Real window appears within 5s (source) or 15s (frozen)
- [ ] Window is centered on the primary monitor
- [ ] All keyboard shortcuts work
- [ ] Session persistence works (close/reopen preserves state)
- [ ] Memory monitoring works (warning at 500MB)
- [ ] DPI awareness declared (Windows)
- [ ] Tab crash recovery works
- [ ] Path traversal protection works
- [ ] License key encrypted at rest
- [ ] `parallel_batch_decode` MCP tool registered
- [ ] `mcp_health` tool registered
- [ ] Per-tool timeout enforced
- [ ] Graceful shutdown works
- [ ] `compare_all_decoders` tool registered
- [ ] `compatibility_matrix` tool registered
- [ ] `decoder_benchmark_suite` tool registered
- [ ] Threshold estimation tool works
- [ ] Finite-size scaling tool works
- [ ] User-defined parity matrix support works
- [ ] Statistical analysis tools work
- [ ] Publication-ready figure export works
- [ ] Reproducibility package generation works
- [ ] Docker MCP image builds and runs
- [ ] Conda recipe builds
- [ ] Shell completions work (bash, zsh, PowerShell)
- [ ] All CLI subcommands work (decode, benchmark, probe, diagnostics, hardware, list-codes, list-decoders, docgen, version, compare, batch, stream, train, export, import, matrix)
- [ ] All CLI flags work (--json, --no-color, --no-banner, --output, --verbose, --quiet, --config, --dry-run)

---

## 15. ESTIMATED EFFORT

| Phase | Items | Estimated Hours |
|-------|-------|----------------|
| Phase 1: Critical Fixes | 7 | 4-6 |
| Phase 2: Hardening | 13 | 20-30 |
| Phase 3: Scientific Features | 10 | 30-40 |
| Phase 4: Platform & Distribution | 8 | 15-20 |
| Phase 5: Quality of Life | 10 | 20-30 |
| **Total** | **48** | **89-126** |

---

## 16. QECTOR-DECODER V1.0.0 BACKEND INTEGRATION GAPS

The upstream `qector-decoder` v1.0.0 (https://github.com/GuillaumeLessard/qector-decoder) ships numerous features the workbench does not yet expose. Every gap below is a missing integration that prevents the workbench from being a complete front-end to the v1.0.0 decoder.

### 16.1 Missing Decoder Classes (not wired in `backend.py`)

| Decoder Class | Status in v1.0.0 | Workbench Status | Action Required |
|---|---|---|---|
| `SpaceTimeDecoder` | Experimental, reachable from Python | **NOT WIRED** | Add to `backend.py` `_decoder_class()` mapping; add to `DECODER_KINDS` as `"space_time"`; add GUI option in Decoder Lab |
| `CUDABpOsdDecoder` | Build/runtime dependent | **NOT WIRED** | Add as batch backend option in Batch & Streaming tab; add `cuda_bposd` to `_BATCH_BACKENDS` |
| `SlidingWindowDecoder` | Experimental | **NOT WIRED** (workbench has its own Python streaming) | Expose native sliding-window as alternative to `run_streaming_session`; add `native_sliding_window` batch backend |
| `StreamingDecoder` | Experimental | **NOT WIRED** | Same as above |
| `decode_mmap` | Stable, out-of-core memmap decoding | **NOT WIRED** | Add MCP tool `decode_mmap` for large-scale out-of-core decoding; add CLI subcommand |
| `LERBenchmark` | Experimental | **NOT WIRED** | Add to Benchmark tab as "LER Benchmark" mode with Wilson CI; add MCP tool `run_ler_benchmark` |
| `GNNTrainer` | Research, training harness | **NOT WIRED** | Add to Decoder Lab as "Train GNN" button; add MCP tool `gnn_train` |
| `BatchDecoder.parallel_batch_decode()` | Stable | **NOT WIRED** as MCP tool | Already in `backend.run_parallel_batch_decode` but no MCP tool; register `parallel_batch_decode` |

### 16.2 Missing BP-OSD Options (v1.0.0 `BpOsdDecoder` kwargs)

| Option | Description | Workbench Status | Action Required |
|---|---|---|---|
| `bp_method="relay"` | Layered serial BP schedule (Relay-BP) | **NOT EXPOSED** | Add "Relay" to BP-OSD method dropdown in Decoder Lab; add to `_BP_METHODS` dict; add to MCP `_DECODER_OPTION_KEYS` |
| `damping` | LLR message damping `(1-d)*m_new + d*m_old` | **NOT EXPOSED** | Add damping slider (0.0-1.0) to Decoder Lab BP-OSD options; add to MCP options |
| `osd_lambda` | CS-OSD free-bit count (default 24) | **NOT EXPOSED** | Add `osd_lambda` integer field to Decoder Lab BP-OSD options; add to MCP options |

### 16.3 Missing GPU Features

| Feature | Description | Workbench Status | Action Required |
|---|---|---|---|
| `edge_weights` on GPU | `CUDABatchDecoder`/`OpenCLBatchDecoder` accept DEM weights | **NOT EXPOSED** | Add "Weighted GPU" checkbox to Batch & Streaming tab; pass `edge_weights` from DEM when enabled |
| `CUDABatchDecoder(precision="f64")` | Double-precision weighted growth kernel | **NOT EXPOSED** | Add precision dropdown (f32/f64) to Batch & Streaming tab GPU options |
| `QECTOR_CUDA_DEVICE_ID` | Select CUDA device | **NOT EXPOSED** | Add CUDA device selector to Hardware tab; set env var before decoder init |
| `QECTOR_OPENCL_DEVICE_ALLOW` | Filter OpenCL devices by name | **NOT EXPOSED** | Add OpenCL device filter to Hardware tab |

### 16.4 Missing DEM / Stim Integration

| Feature | Description | Workbench Status | Action Required |
|---|---|---|---|
| `DemModel` | Full detector error model support | **NOT EXPOSED** | Add "DEM Import" to Code Explorer; accept `.dem` files and Stim circuits |
| `DemModel.make_decoder` | Build any of 9 decoder families from DEM | **NOT EXPOSED** | Wire to Decoder Lab; allow DEM-native decoding |
| `DemModel.collapse_to_graph` | Convert hypergraph DEM to graphlike | **NOT EXPOSED** | Use for compatibility checking |
| `stim_compat` | `from_stim_detector_error_model` | **NOT EXPOSED** | Add Stim circuit import to Code Explorer (requires `[stim]` extra) |
| `sinter_compat` | `qector_sinter_decoders()` | **NOT EXPOSED** | Add Sinter integration tab or section; allow exporting tasks for `sinter.collect` |
| `qiskit_plugin` | qiskit-qec integration | **NOT EXPOSED** | Document in API reference; add optional integration panel |
| `pymatching` shim | `from qector_decoder_v3.pymatching import Matching` | **NOT EXPOSED** | Add PyMatching compatibility mode to Decoder Lab |

### 16.5 Missing Tuning Environment Variables

| Variable | Default | Effect | Workbench Status | Action Required |
|---|---|---|---|---|
| `QECTOR_BLOSSOM_K_MULT` | `2.0` | Candidate-neighbour multiplier for sparse MWPM. **Affects accuracy.** | **NOT EXPOSED** | Add to Hardware tab "Tuning" section with warning that it affects LER |
| `QECTOR_BLOSSOM_INTRA_PAR` | auto | Force intra-decode parallelism | **NOT EXPOSED** | Add toggle to Hardware tab |
| `QECTOR_BLOSSOM_INTRA_THREADS` | unset | Dedicated Rayon pool size | **NOT EXPOSED** | Add integer field to Hardware tab |
| `QECTOR_CUDA_DEVICE_ID` | `0` | CUDA device selection | **NOT EXPOSED** | Add dropdown to Hardware tab |
| `QECTOR_OPENCL_DEVICE_ALLOW` | unset | Device name filter | **NOT EXPOSED** | Add text field to Hardware tab |
| `QECTOR_SILENT` | unset | Suppress licensing notice | **NOT EXPOSED** | Add toggle to Lab & Personal Info tab |
| `QECTOR_ENFORCE` | unset | Hard license gate | **NOT EXPOSED** | Add toggle to Lab & Personal Info tab |

### 16.6 Missing License Features (v1.0.0)

| Feature | Description | Workbench Status | Action Required |
|---|---|---|---|
| `get_license_info()` | Query tier, key_status, expiry | **NOT WIRED** | Add to Lab & Personal Info tab; show live tier + key status + expiry |
| v2 tokens with `tier` + `exp` | Tokens carry tier and expiry in signature | **NOT EXPOSED** | Display expiry date in Lab & Personal Info; warn when expiring |
| `license_claims()` | Return verified, unexpired claims | **NOT WIRED** | Use for tier display |
| Offline CRL | `~/.qector/revoked.txt` | **NOT EXPOSED** | Document in diagnostics; add to self-check |
| `QECTOR_LICENSE_FILE` resolution | Env var -> file path -> `~/.qector/license.key` | **PARTIALLY WIRED** | Verify workbench follows same resolution order; display which source was used |
| Invalid key raises `ValueError` | `set_license_key()` rejects bad keys | **NOT VERIFIED** | Test that workbench surfaces the ValueError; don't silently accept |

### 16.7 Missing CLI Commands (from upstream `qector` CLI)

| Command | Description | Workbench CLI Status | Action Required |
|---|---|---|---|
| `qector serve` | Launch REST API server | **NOT EXPOSED** | Add `serve` subcommand to `cli.py`; launch `qector_decoder_v3.rest_api` |
| `qector-doctor` | 15-check environment diagnostic | **PARTIALLY** (workbench has `diagnostics`) | Add `doctor` subcommand that wraps `qector-doctor` output; show all 15 checks |
| `qector bench --verify` | Verified benchmark with Wilson CI | **NOT EXPOSED** | Add `--verify` flag to `benchmark` subcommand |

### 16.8 Missing MCP Tools (from upstream decoder's 13-tool MCP server)

The decoder wheel itself ships an MCP server with 13 tools. The workbench should expose or bridge these:

| Tool | Description | Workbench MCP Status | Action Required |
|---|---|---|---|
| `decode_hyperedge` | Hyperedge / qLDPC decoding | **NOT REGISTERED** | Add to workbench MCP registry |
| `decode_syndrome_blossom` / `batch_decode_blossom` | Exact Blossom single/batch | **PARTIALLY** (via `decode_single` with decoder=blossom) | Add dedicated convenience tools |
| `decode_syndrome_cascade` | Hybrid cascading decoder | **PARTIALLY** (via `decode_single` with decoder=hybrid_cascade) | Add dedicated convenience tool |
| `run_ler_benchmark` | LER benchmark across distances | **NOT REGISTERED** | Add to workbench MCP registry |
| `get_backend_health` | 7-tier backend health status | **NOT REGISTERED** | Add to workbench MCP registry |
| `get_server_env` | Effective QECTOR environment variables | **NOT REGISTERED** | Add to workbench MCP registry; show all tuning vars |

### 16.9 Missing `ColourCodeDecoder` Options

| Option | Description | Workbench Status | Action Required |
|---|---|---|---|
| `method="cluster_bposd"` | Weighted UF growth + BP-OSD residual | **NOT EXPOSED** | Add method dropdown to Decoder Lab when colour_code is selected |
| `method="bposd"` | Plain BP-OSD (default) | Current behavior | Keep as default |

### 16.10 Missing `AutoDecoder` Diagnostics

| Feature | Description | Workbench Status | Action Required |
|---|---|---|---|
| `AutoDecoder._diag.backend_health` | Per-tier health status | **NOT EXPOSED** | Add to Diagnostics tab; show 7-tier health |
| `AutoDecoder._diag.active_backend` | Currently active backend | **NOT EXPOSED** | Display in Diagnostics tab |
| `reset_backend_health()` | Restore suspended tiers | **NOT EXPOSED** | Add "Reset Backend Health" button to Diagnostics tab |

### 16.11 Missing Batch Decode Features

| Feature | Description | Workbench Status | Action Required |
|---|---|---|---|
| `BatchDecoder.parallel_batch_decode()` | Parallel batch (distinct from `DecoderPool`) | **NOT WIRED** | Add to `backend.py`; expose in Batch & Streaming tab |
| `CUDABpOsdDecoder.decode` single-shot | One-row convenience | **NOT WIRED** | Add as batch backend option |
| Out-of-core `decode_mmap` | Memmap-based decoding for huge batches | **NOT WIRED** | Add MCP tool and CLI command |

### 16.12 Missing Benchmark Features

| Feature | Description | Workbench Status | Action Required |
|---|---|---|---|
| Wilson 95% CI on LER | `BenchmarkResult` includes `ler_ci95_low/high` | **NOT EXPOSED** | Add CI display to Benchmark tab results |
| `n_unfaithful` / `unfaithful_rate` | Syndrome faithfulness tracking | **NOT EXPOSED** | Add faithfulness metrics to Benchmark tab |
| `ler.assert_comparable` | Refuse cross-noise-model comparisons | **NOT EXPOSED** | Add validation to benchmark comparisons |
| Noise model tagging | Each run tagged with noise model | **NOT EXPOSED** | Add noise model selector to Benchmark tab (code-capacity / circuit-level) |
| Per-cell time budget | Trim shots instead of stalling | **NOT EXPOSED** | Add time budget option to Benchmark tab |

### 16.13 Missing REST API Integration

| Feature | Description | Workbench Status | Action Required |
|---|---|---|---|
| `qector_decoder_v3.rest_api` | Local FastAPI decoding service | **NOT EXPOSED** | Add "Start REST Server" button to Hardware tab or new Services tab |
| REST security (127.0.0.1 bind, rate limit) | Built-in security | Document when exposing REST |

### 16.14 Missing Crash Safety Awareness

The v1.0.0 Rust core had 6 panic-to-abort paths removed. The workbench should:

| Item | Action Required |
|---|---|
| Document crash safety improvements | Add to RELEASE_NOTES and AGENT.md |
| Handle `Result` returns from Rust | Verify all Rust `Result` returns are caught as Python exceptions, not crashes |
| Test with NaN/Inf inputs | Add fuzz tests for NaN error_rate, Inf weights |

### 16.15 Missing Wheel / Platform Awareness

| Fact | Workbench Impact | Action Required |
|---|---|---|
| 15 binary wheels (CPython 3.9-3.13 × 3 platforms) | Workbench requires 3.11+ | Document supported wheel matrix; verify provisioner handles all ABIs |
| No sdist published | Provisioner must use wheels only | Verify `--only-binary=:all:` in pip install |
| No aarch64/musllinux/macOS x86_64 wheels | Document unsupported platforms | Add platform check to diagnostics |
| macOS arm64 wheel exists | Workbench can now target macOS | Enable macOS build path |

### 16.16 Missing `generate_parity_check_matrix()` Binding

The v1.0.0 decoder now exposes `generate_parity_check_matrix()` at module level. The workbench should:

- Add to `backend.py` as a public function
- Expose in Code Explorer for custom code construction
- Add MCP tool `generate_parity_check`

### 16.17 Missing `qiskit_plugin` Integration

The v1.0.0 decoder ships a qiskit-qec plugin entry point. The workbench should:

- Document the integration in API reference
- Add optional "Export to Qiskit" button in Code Explorer
- Add MCP tool `export_qiskit`

### 16.18 Missing `rest_api` Integration

The v1.0.0 decoder ships a local REST API. The workbench should:

- Add "Start REST Server" option to CLI (`qector serve`)
- Add GUI toggle in Hardware tab
- Document the security model (127.0.0.1 bind, rate limit)

---

## 17. UPDATED IMPLEMENTATION PRIORITY (with v1.0.0 backend gaps)

### Phase 0: Backend Integration (NEW — BLOCKING for v1.0.0 parity)
1. Wire `SpaceTimeDecoder` into `backend.py` and GUI
2. Wire `CUDABpOsdDecoder` as batch backend option
3. Add `bp_method="relay"` to BP-OSD options
4. Add `damping` and `osd_lambda` to BP-OSD options
5. Add `edge_weights` support to GPU batch decode
6. Add `CUDABatchDecoder(precision="f64")` option
7. Wire `get_license_info()` to Lab & Personal Info tab
8. Add all 6 tuning environment variables to Hardware tab
9. Wire `DemModel` import to Code Explorer
10. Add `stim_compat` import to Code Explorer
11. Register missing 6 MCP tools from decoder's own server
12. Add `LERBenchmark` to Benchmark tab
13. Add `decode_mmap` MCP tool and CLI command
14. Add `ColourCodeDecoder(method="cluster_bposd")` option
15. Wire `AutoDecoder._diag` to Diagnostics tab
16. Add Wilson CI display to Benchmark results
17. Add `qector serve` CLI subcommand
18. Add `qector-doctor` CLI subcommand
19. Wire `generate_parity_check_matrix()` to Code Explorer
20. Add `qiskit_plugin` export option

### Phase 1: Critical Fixes (unchanged from original)
21. Fix `decoder_provisioner.py` indentation bug
22. Fix `pyproject.toml` version and missing modules
23. Update `CHANGELOG.md` with v1.0.0 entry
24. Rewrite `RELEASE_REPORT.md` for v1.0.0
25. Unify all version strings to 1.0.0
26. Clean stale files
27. Fix `mcp_server.py` duplicate `_options_desc`

### Phase 2-5: (unchanged from original, renumbered)

---

## 18. UPDATED VERIFICATION CHECKLIST (v1.0.0 backend integration)

- [ ] `SpaceTimeDecoder` constructs and decodes in workbench
- [ ] `CUDABpOsdDecoder` available as batch backend
- [ ] `bp_method="relay"` works in Decoder Lab
- [ ] `damping` and `osd_lambda` options work in Decoder Lab
- [ ] GPU batch decode accepts `edge_weights` from DEM
- [ ] `CUDABatchDecoder(precision="f64")` works
- [ ] `get_license_info()` displays tier + key_status + expiry
- [ ] All 6 tuning env vars configurable from Hardware tab
- [ ] `DemModel` import works from Code Explorer
- [ ] Stim circuit import works from Code Explorer
- [ ] All 6 missing MCP tools registered and tested
- [ ] `LERBenchmark` runs with Wilson CI
- [ ] `decode_mmap` works for large out-of-core batches
- [ ] `ColourCodeDecoder(method="cluster_bposd")` selectable
- [ ] `AutoDecoder._diag` shows 7-tier health
- [ ] `reset_backend_health()` button works
- [ ] Wilson 95% CI displayed in Benchmark results
- [ ] `n_unfaithful` / `unfaithful_rate` displayed
- [ ] `qector serve` launches REST API
- [ ] `qector-doctor` runs 15-check diagnostic
- [ ] `generate_parity_check_matrix()` accessible
- [ ] `qiskit_plugin` export works
- [ ] `sinter_compat` export works
- [ ] `pymatching` shim accessible from Decoder Lab
- [ ] `QECTOR_SILENT` toggle works
- [ ] `QECTOR_ENFORCE` toggle works
- [ ] v2 license token expiry displayed and warned
- [ ] Invalid license key raises ValueError (not silently accepted)
- [ ] All 15 wheel ABIs handled by provisioner
- [ ] Platform check in diagnostics (no aarch64/musllinux)

---

## 19. UPDATED EFFORT ESTIMATE

| Phase | Items | Estimated Hours |
|-------|-------|----------------|
| Phase 0: Backend Integration | 20 | 30-40 |
| Phase 1: Critical Fixes | 7 | 4-6 |
| Phase 2: Hardening | 13 | 20-30 |
| Phase 3: Scientific Features | 10 | 30-40 |
| Phase 4: Platform & Distribution | 8 | 15-20 |
| Phase 5: Quality of Life | 10 | 20-30 |
| **Total** | **68** | **119-166** |

---

*End of finaldev.md — QECTOR Decoder Workbench v1.0.0 final development roadmap.*
*Generated: 2026-08-06 from full codebase audit of all source files + upstream qector-decoder v1.0.0 analysis.*
