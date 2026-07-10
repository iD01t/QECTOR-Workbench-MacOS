# QECTOR Decoder Workbench v3.4.0 — Upgrade Notes

## What Changed

### New Modules
- `auto_updater.py` — PyPI version check on boot, background upgrade
- `mcp_server.py` — Full MCP server with 25 tools wired to backend
- `mcp_resources.py` — Thread-safe resource allocation tracker
- `main.py` — PyInstaller entry point

### Upgraded Modules
- `backend.py` — Added `get_decoder_info()`, `get_compatible_decoders()`
- `app.py` — Auto-update fires in daemon thread on import
- `doc_generator.py` — Pro-tier: full provenance, code analysis, decoder recs, 4 formats
- `code_explorer_tab.py` — Family dropdown, distance slider, properties, analysis
- `decoder_lab_tab.py` — Decoder selector, error rate slider, seed, live results
- `benchmark_tab.py` — Configurable samples/seed, throughput display, JSON export
- `batch_streaming_tab.py` — Batch decode + streaming controls
- `hardware_tab.py` — CUDA/OpenCL/CPU detection, system info, recommendations
- `documentation_tab.py` — 6 export format checkboxes, preview pane, provenance
- `state.py` — Bulletproof restore with try/except
- `logger.py` — All ops wrapped, no crash on log dir failure
- `console.py` — Added `log(text, level)` method
- `theme.py` — Added `COLORS` dict and `Fonts` alias

### PyInstaller Build
- Spec updated: all 22 QECTOR modules as hidden imports
- Extra collections: customtkinter, PIL, matplotlib, scipy, psutil, qector_decoder_v3
- Excludes: pythoncom, win32api, unittest, http.server, xmlrpc

### Version
- Workbench: 3.4.0
- Backend: qector_decoder_v3 0.5.8+ (auto-upgrades to latest PyPI)
