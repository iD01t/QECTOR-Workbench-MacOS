## QECTOR Decoder Workbench v3.4.0

**Production Release**

[![Release](https://img.shields.io/github/v/release/qectorlab/qector-decoder-workbench?label=v3.4.0)](https://github.com/qectorlab/qector-decoder-workbench/releases/tag/v3.4.0)

> Professional Quantum Error Correction Analysis Suite with polished 10/10 CustomTkinter GUI, full MCP server (25 tools), and publication-quality documentation export.

**Official Release Page:** https://github.com/qectorlab/qector-decoder-workbench/releases/tag/v3.4.0

### Download v3.4.0 (Recommended)

**Direct from the release:**

- `QectorWorkbenchSetup.exe` — Full Windows installer (64-bit Inno Setup with modern settings)
- `QectorWorkbench-v3.4.0-production.zip` — Complete production bundle including:
  - Standalone `QectorWorkbench.exe` + `_internal`
  - `QectorWorkbenchSetup.exe`
  - Updated docs (README, UPGRADE_NOTES, PROJECT_STATUS)
  - Sample premium documentation exports
  - `RELEASE_MANIFEST.txt` with SHA256 checksums

**Checksums (SHA256) are included in the production zip and manifest.**

### Quick Install from Release

1. Go to https://github.com/qectorlab/qector-decoder-workbench/releases/tag/v3.4.0
2. Download `QectorWorkbenchSetup.exe`
3. Run the installer (requires admin for system-wide install, or use the portable exe from the zip)
4. Launch QectorWorkbench.exe

The app will create config, logs, and exports folders on first run.

### v3.4.0 Release-Specific Notes

This is the first full **production** release after extensive verification and cleanup:

- **Upgraded Installer**:
  - Switched to 64-bit only (`x64compatible`)
  - lzma2 compression for smaller/faster packages
  - Full VersionInfo metadata (company, description, product version)
  - Modern minimum Windows version (10.0.17763+)
  - Clean output directory and desktop shortcut options

- **Production Packaging**:
  - Built with `pyinstaller --clean -y QectorWorkbench.spec`
  - Inno Setup built with `/Q` for reproducible output
  - All large build artifacts (dist/, build/, old production folders) removed from source control
  - Bundles now include only what users need + verification files

- **Repository Cleanup**:
  - Added comprehensive `.gitignore` covering build artifacts, venvs, caches, logs, old zips, and production folders
  - Removed >1.5 GB of bloat (previous QectorWorkbench_v* folders, release zips, .venv, dist/, build/)
  - Source repo is now lean and focused on code + docs

- **Full Verification Completed**:
  - All 25 MCP tools tested and passing (via `test_mcp_all.py`)
  - End-to-end wiring verified: qector_decoder_v3 0.6.2 ↔ backend ↔ MCP server ↔ doc generator ↔ GUI tabs
  - Self-tests pass (`python main.py --self-test`)
  - Production builds confirmed functional

- **10/10 GUI & Tooling Polish** (carried forward and stabilized):
  - Modern quantum dark theme with expanded palette and professional fonts (Inter, Cascadia, JetBrains Mono)
  - Consistent card-based layouts, premium controls, and high-quality matplotlib integration
  - Complete MCP server (stdio + HTTP on port 8765) exposing 25 tools for automation/LLM integration
  - ProfessionalDocGenerator producing premium self-contained HTML, Markdown (with TOC), LaTeX, and JSON with provenance, repro snippets, and figures

- **Documentation Refresh**:
  - All docs (README_v3.md, UPGRADE_NOTES.md, PROJECT_STATUS.md, api.md, architecture.md) updated for v3.4.0
  - Clear notes on production packaging and repo hygiene

### Key Features (v3.4.0)

- **Code Explorer**: Real qector_decoder_v3 code families with matrix/tanner/circuit views and one-click premium exports
- **Decoder Lab**: Interactive single-syndrome decoding with multiple algorithms (union_find, blossom, bp_osd, etc.)
- **Benchmark**: Real Rust-backed latency and throughput measurements
- **Batch & Streaming**: High-volume and sliding-window workflows with CPU/CUDA/OpenCL support
- **Hardware & Routing**: Auto-detection and intelligent decoder recommendations
- **MCP Server**: Full control surface for external tools and agents
- **Docs Studio**: Publication-grade multi-format exports

### Documentation & Source

For the complete feature guide, architecture, and building from source, see the files inside the `QectorWorkbench-v3.4.0-production.zip` or browse the repository.

**Source (for developers):** https://github.com/qectorlab/qector-decoder-workbench

### License

Source-available under EULA.txt. Free for personal, academic, and non-commercial research.

Commercial licensing available.

Developer: Guillaume Lessard © 2026

Built on qector_decoder_v3 (v0.6.2).

---

**Latest Release:** [v3.4.0](https://github.com/qectorlab/qector-decoder-workbench/releases/tag/v3.4.0)