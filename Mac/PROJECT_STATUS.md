# QECTOR Decoder Workbench v1.0.0 — Project Status Report

## Executive Summary
**Status: PRODUCTION READY — ALL TESTS PASSING (backend v1.0.0 Core + Enterprise Unlock)**

Complete professional-grade quantum error correction analysis suite with stdio
JSON-RPC 2.0 MCP server (82 tools, 10MB frame limit), 8 fully wired GUI feature tabs + live
Console, a resilient self/auto-debug backend, a multi-format doc generator, and
cross-platform production builds (Windows `.exe`, Linux `.deb`,
ready-to-build macOS tree). Fully offline: no auto-updater, no PyPI queries —
the bundled v1.0.0 decoder wheel is provisioned locally with automatic purge of
outdated managed sites.

---

## Test Results
```
pytest tests/            — 403 passed, 4 skipped, 0 failed (.venv, qector_decoder_v3 1.0.0)
MCP comprehensive test   — 82 / 82 tools passed (in-process + stdio round-trip JSON-RPC 2.0)
All 35 root modules import cleanly (headless), GUI smoke tests pass under Tk
Enterprise/GPU unlock   — tier reports max_distance=63, gpu_enabled=True (Ed25519 token verification); GUI distance slider now supports d3–d63
```

---

## Module Inventory (key modules)

| Module | Status | Purpose |
|--------|--------|---------|
| `backend.py` | Upgraded | QEC wrapper — **17 decoders, 10 code families** (incl. color_code, qLDPC bicycle / bivariate_bicycle / hypergraph_product), layout, validation, decoder-compatibility probe; new: `two_stage`, `ambiguity_cluster`, `colour_code`, `sparse_blossom_radix_neighbors`, `clear_decoder_cache`, `run_doctor_checks`, `flush_usage`, `verify_license_token`, `set_license_key_file` |
| `autodebug.py` | Upgraded | Resilient self/auto-debug backend: multi-decoder fallback, batch cuda→opencl→cpu fallback, decoder probe, full self-diagnostics |
| `version_service.py` | Upgraded | Offline versioning: workbench version from `version.py` (v1.0.0), backend version as imported; stale disk-cache guard; no PyPI queries |
| `decoder_provisioner.py` | Upgraded | Runtime decoder provisioning — bundles the decoder package and a matching wheel into frozen apps; extracts the bundled wheel or installs/upgrades the ABI-correct wheel into an **ABI-partitioned** per-user managed site (import-verified, atomic pointer, inter-process lock). The portable Windows exe runs with no external Python; system Python is only a network-fallback |
| `app.py` | Upgraded | Main CTk window with 9 wired tabs (8 feature + Console) + live-resolved version banner in status bar |
| `state.py` | Hardened | AppState with listeners |
| `theme.py` | Cross-platform | Per-OS fonts (Consolas/Segoe · DejaVu · Menlo) |
| `utils.py` | Cross-platform | Data dir per-OS (Win/macOS/XDG), validation, safe write |
| `logger.py` | Hardened | File + stdout logging, all ops wrapped |
| `console.py` | Hardened | Console buffer with callbacks for live tab output |
| `version.py` | Updated | **Workbench v1.0.0, backend v1.0.0, MCP_TOOLS=82**; static version baselines |
| `doc_generator.py` | Upgraded | 8 formats (Markdown/JSON/HTML/LaTeX/PDF/SVG + `.zenodo.json`/`CITATION.cff`) — full provenance, deposit metadata, five-figure publication suite, no typographic dashes |
| ~~`auto_updater.py`~~ | **REMOVED** | Deleted in v0.5.2 — no PyPI auto-updates; bundled wheel is the single source of truth |
| `threading_utils.py` | Stable | UiPump, run_in_background |
| `results_tracker.py` | Stable | In-memory result tracking |
| `hardware_routing.py` | Upgraded | detect_hardware, recommend (qLDPC-aware: never recommends an unusable decoder) |
| `mcp_server.py` | Upgraded | **82 MCP tools**, stdio JSON-RPC 2.0 transport |
| `mcp_resources.py` | Stable | Thread-safe resource manager |
| `dialogs.py` | Stable | Dialog helpers |
| `code_explorer_tab.py` | Upgraded | Family selector (10 families), distance slider, properties, analysis, doc export |
| `decoder_lab_tab.py` | Upgraded | Decoder selector (17), **resilient fallback** on incompatible decoder/code, doc + quick export |
| `benchmark_tab.py` | Stable | Configurable benchmark, throughput, export |
| `batch_streaming_tab.py` | Stable | Batch decode (backend selector) + streaming controls |
| `hardware_tab.py` | Stable | CUDA/OpenCL/CPU detection, system info, recs |
| `diagnostics_tab.py` | **NEW** | Self-Diagnostics / Probe Decoders / Resilient Decode UI |
| `documentation_tab.py` | Upgraded | 8-format export, preview with search/zoom/highlighting, recent folders, live progress, Buy Licence section |
| `lab_info_tab.py` | **NEW** | Deposit profile (author, ORCID, DOI, funding, keywords) + decoder licence-key install with live tier readout |
| `docs_exporter.py` | Upgraded | Official docs export incl. DOCX; honest failure reporting |

---

## Key Features Verified
- **17 decoders** (union_find, fast_union_find, blossom, sparse_blossom, bp_osd, auto, hybrid, lookup_table, predecoded, auto_router, hybrid_cascade, gnn_belief_matching, belief_matching, two_stage, ambiguity_cluster, colour_code, space_time) × **10 code families** (incl. qLDPC, hypergraph_product, color_code)
- `hybrid_cascade` — Union-Find pre-filter + Blossom/BP-OSD escalation with live cascade statistics
- `gnn_belief_matching` — GNN-guided weighted matching with faithfulness fallback (graphlike)
- `belief_matching` — BP posteriors + exact MWPM with faithfulness fallback
- `auto_router` — policy decoder wrapping the backend `AutoRouter`; universally compatible including on `bivariate_bicycle`
- `hypergraph_product` — CSS code from repetition-code seed; graphlike (all matching decoders apply)
- Resilient decode with automatic multi-decoder fallback + full attempt trace
- Full environment/decoder/hardware self-diagnostics (`self_diagnostics`)
- Reproducible seed-based decoding; batch decode with success rate & LER
- Spring-layout Tanner graph for all families; **high-DPI, antialiased matplotlib figures**
- MCP server with **82 tools** (stdio JSON-RPC 2.0, 10 MB frame limit)
- Hardware detection (CUDA/OpenCL/CPU); qLDPC-aware decoder recommendation
- Ecosystem compatibility report: stim, sinter, pymatching, qiskit, ldpc
- Multi-format doc export (MD, JSON, HTML, LaTeX, PDF, SVG, `.zenodo.json`, `CITATION.cff`)
- **Offline versioning**: workbench v1.0.0 + installed backend v1.0.0 banner; stale disk-cache guard; no PyPI queries
- **No auto-updater**: `auto_updater.py` removed in v0.5.2; the shipped bundle is the single source of truth
- **Bundled decoder + offline wheel provisioning with purge**: the frozen app ships the `qector-decoder-v3` v1.0.0 wheel embedded; `decoder_provisioner.py` purges any outdated managed site (< 1.0.0), extracts the bundled wheel into a per-user managed site (**ABI-partitioned by interpreter, import-verified**) on first launch — the portable Windows exe runs with no external Python or network
- **New professional icon set**: SVG master + multi-resolution `.ico` (Windows), `.icns` (macOS), `.png` (Linux)
- Professional dark-themed UI with per-tab crash isolation

---

## Cross-platform builds
The decoder ships as a **bundled wheel** inside every build; it is provisioned
at launch into an ABI-scoped managed site (see `PACKAGING.md`).
- **Windows:** PyInstaller onedir `.exe` (`QectorWorkbench.spec`) **and** a single-file portable `QectorWorkbench-Portable.exe` (`QectorWorkbench-onefile.spec`, ~53 MB). Both bundle the v1.0.0 wheel and were verified provisioning the decoder offline and serving `--mcp` (82 tools) frozen.
- **Linux:** `.deb` built reproducibly in Docker (`Dockerfile.deb`) → `qector-workbench_1.0.0_amd64.deb`. An AppImage recipe exists (`Linux/compile.sh --docker`) but is not built for 1.0.0.
- **macOS:** ready-to-build tree (`Mac/build_macos.sh`) producing a signed `.app` + `.dmg` for arm64 and Intel; must run on Apple hardware. Not built for 1.0.0; see `.github/workflows/build-macos.yml`.

---

**Report generated:** 2026-08-04
**Version:** Workbench v1.0.0 · Backend qector-decoder-v3 v1.0.0
**Status:** READY FOR PRODUCTION DEPLOYMENT — 403 passed / 4 skipped / 0 failed; MCP 82 tools green in-process, over stdio and from the frozen exe (which now reports v1.0.0); Windows and Linux bundles built with refreshed checksums; manuals regenerated at v1.0.0
