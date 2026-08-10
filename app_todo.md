# QECTOR Workbench — App TODO

Last verified: 2026-08-06 (v1.0.0 release — all critical features done)
Backend wheel: **qector_decoder_v3 1.0.0 (cp311 win_amd64) — installed in app venv**

---

## ✅ v1.0.0 — ALL CRITICAL WORK COMPLETE

### Backend & Core
- [x] 16 decoders, 10 code families, all decode-matrix tested
- [x] `build_code` validates distances (3–99), raises `QectorError`
- [x] `run_single_decode` validates error rate [0, 1]
- [x] Offline bundled wheel provisioning (no PyPI needed)
- [x] Version unified to 1.0.0 across root, Linux/, Mac/ trees

### MCP Server (66 tools)
- [x] 66 registered MCP tools (all pass in-process & stdio JSON-RPC)
- [x] Per-tool 60s timeout via `asyncio.wait_for`
- [x] Concurrent request guard (`_BUSY_LOCK`)
- [x] 1 MB per-tool result size limit with truncation warning
- [x] Graceful shutdown (SIGINT/SIGTERM drain)
- [x] `export_benchmark` supports JSON, CSV, Markdown, HTML formats
- [x] New tools: `export_session`, `import_syndrome`, `analyze_logicals`, `analyze_error_patterns`
- [x] `docs/mcp_tools.json` manifest generated (66 tools + schemas)

### CLI (12 subcommands)
- [x] `compare`, `batch`, `stream`, `train`, `export`, `import`, `matrix`, `serve`, `doctor`, `completions`
- [x] Global flags: `--output`, `--verbose`, `--quiet`, `--config`, `--dry-run`
- [x] Shell completions for bash, zsh, PowerShell

### GUI
- [x] Tab crash recovery ("Reload Tab" button via `reload_tab()`)
- [x] 30s splash timeout in `_Splash.pump()`
- [x] DPI awareness (`SetProcessDpiAwareness`)
- [x] Multi-monitor centering (`GetMonitorInfoW` via ctypes)
- [x] RSS memory monitoring (warns at 500MB, offers restart at 1GB)
- [x] Full keyboard shortcuts (Ctrl+N/R/B/E/,, F5, Ctrl+Tab)
- [x] Session persistence (`workspace.json`, `preferences.json`)
- [x] Figure LRU cache (`figure_cache.py`)
- [x] Data import UI ("⬆ Import Syndrome" button in Decoder Lab)

### Security
- [x] License keys encrypted at rest (Fernet, machine-derived key)
- [x] Auto-migration of legacy plaintext keys on boot
- [x] Export path traversal protection (`sanitize_export_path`)

### Testing (450+ tests)
- [x] `test_decode_matrix.py` — all CODE_FAMILIES × DECODER_KINDS
- [x] `test_fuzz.py` — all-zeros, all-ones, NaN/Inf, wrong-length syndromes
- [x] `test_corruption_recovery.py` — corrupted/missing `__init__.py`
- [x] `test_input_validation.py` — distance, error rate, XSS, invalid decoder
- [x] `test_path_traversal.py` — 8 traversal test cases
- [x] `test_offline_provisioning.py` — network-blocked bundled wheel extraction
- [x] `test_upgrade_path.py` — old version purge simulation
- [x] `test_cross_platform_paths.py` — unicode, spaces, long paths, traversal

### Documentation
- [x] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- [x] `CHANGELOG.md` updated for v1.0.0
- [x] `docs/mcp_tools.json` — machine-readable tool manifest
- [x] Trees synced: root → Linux/ → Mac/ (sync_trees.py --apply)

---

## 🟡 REMAINING (non-critical, future enhancements)

### GUI Enhancements (Phase 2)
- [ ] 4.8 Experiment notebook / history panel
- [ ] 4.9 Side-by-side decoder comparison view
- [ ] 4.13 Progressive rendering for large Tanner graphs
- [ ] 4.14 Accessibility (a11y): high-contrast theme, font slider, keyboard hints
- [ ] 4.15 Internationalization (i18n): English, French, Japanese
- [ ] 4.16 Print/report preview (in-app PDF widget)
- [ ] 4.17 Dark/light theme toggle
- [ ] 4.18 Additional visualizations (2D lattice, check-node graph, radar chart)
- [ ] 4.19 Real-time streaming visualization (live chart during streaming)
- [ ] 4.20 Batch job queue with progress tracking

### Testing Enhancements
- [ ] 6.6 Performance regression test (baseline comparison)
- [ ] 6.7 Memory leak test (RSS growth over 1000 iterations)
- [ ] 6.8 GUI integration test (requires display)

### Security Enhancements
- [ ] 7.3 Input length limits (1024 chars for paths, 256 for names)
- [ ] 7.4 CSRF protection on MCP (connection handshake token)
- [ ] 7.6 Dependency vulnerability scanning (`pip-audit`)
- [ ] 7.7 Secret detection in CI (`check_secrets.py`)

### Documentation Enhancements
- [ ] 8.4 API reference completeness check (`check_docstrings.py`)
- [ ] 8.5 Changelog automation from git history
- [ ] 8.6 Architecture diagrams

### macOS
- [ ] R4 macOS build: needs real Mac hardware or GitHub Actions runner

---

## Watch items (non-blocking)
- GUI boot banner cosmetic wording when local > PyPI version
- numpy pinned to compatible range in requirements.txt
