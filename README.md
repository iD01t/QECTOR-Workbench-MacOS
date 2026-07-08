# QECTOR Decoder Workbench v3.4 — Scientific QEC Analysis Suite (Production Ready)

**Professional Quantum Error Correction Analysis Suite**

[![CI](https://github.com/qectorlab/qector-decoder-workbench/actions/workflows/ci.yml/badge.svg)](https://github.com/qectorlab/qector-decoder-workbench/actions/workflows/ci.yml) [![License](https://img.shields.io/badge/License-Source_Available-blue)](LICENSE)

> Next-generation professional-grade platform for exploring, decoding, benchmarking, and analyzing quantum error correction codes. Features a polished 10/10 CustomTkinter GUI, full MCP server (25 tools), publication-quality documentation export, and production-ready packaging.

## What's New in v3.4.0 (Production)

- **Upgraded Installer**: Inno Setup 64-bit (x64compatible), lzma2 compression, full version metadata, modern min Windows requirements.
- **Production Package**: Clean standalone bundle + full installer with checksums, manifests, and included premium docs.
- **All Wiring Fully Verified**: Library ↔ backend ↔ MCP ↔ doc generator ↔ GUI tabs. 25/25 MCP tools passing, end-to-end flows tested.
- **Version Bumps**: Workbench 3.4.0, aligned with qector_decoder_v3 0.6.2.

## Core Highlights (from v3.3 10/10 Polish)

- **10/10 GUI Polish**: Refined quantum dark theme (expanded palette, modern fonts like Inter/Cascadia/JetBrains), consistent card layouts, premium buttons/controls, accent bars, better spacing/typography.
- **MCP Server**: Complete stdio + HTTP MCP server exposing **25 tools** (code analysis, decoders, benchmarks, results, config, hardware, resources, clients, `generate_documentation`). All exhaustively tested and working.
- **Premium Documentation Generator**: Self-contained modern HTML (stats grids, matrix previews, copy buttons, provenance), improved Markdown (TOC), LaTeX, JSON + high-quality SVG/PDF figures with watermark. Full repro snippets and certification in every export.
- **Docs Studio Tab**: One-click multi-format exports (HTML/MD/LaTeX/JSON) with real provenance.

## Installation

```bash
# From source (recommended for dev)
python -m pip install --upgrade pip
pip install -e .[dev]
python -m pytest -q
python app.py

# Or use the production installer / standalone exe from the v3.4.0 release
```

On first launch:
- Creates `.qector_config.json`
- `logs/` with rotation
- Exports and cache dirs

## Quick Start

1. Launch `python app.py` (or the installed exe).
2. **Code Explorer**: Select family (e.g. rotated_surface), set distance, Build. View matrix + summary.
3. Export professional docs (HTML/MD/LaTeX/JSON) via the Documentation tab or buttons.
4. Use **Decoder Lab** for single-syndrome decode with diagnostics.
5. **Benchmark** for real latency/throughput.
6. **Batch & Streaming**, **Hardware & Routing** for advanced workflows.
7. Full MCP integration for agents/automation (tools include list_code_families, generate_documentation, run_benchmark, etc.).

## Features by Tab

### Code Explorer
- Real qector_decoder_v3 code families (Repetition, Ring, Rotated/Unrotated Surface, Toric, Heavy-hex, etc.)
- Parameter validation
- Sparsity matrix, Tanner graph, circuit views
- Premium export buttons

### Decoder Lab
- Multiple decoders (union_find, fast_union_find, blossom, sparse_blossom, bp_osd)
- Error sampling + decode with seed
- Visual results + explain

### Benchmark
- Real Rust backend measurements
- Configurable samples
- Results tracking + export

### Batch & Streaming + Hardware
- CPU / CUDA / OpenCL batch
- Streaming sessions
- Hardware profile + routing recommendations

## MCP Server (25 Tools, Fully Tested)

stdio + HTTP (default 8765). All functions verified in test_mcp_all.py.

Key tools:
- analyze_code_family, list_code_families, get_code_properties
- list_decoders, get_decoder_info, benchmark_decoder
- run_benchmark, compare_benchmarks, export_benchmark
- get_results, get_statistics, clear_results
- get_config, set_config, reset_config
- get_system_info, get_hardware_info, list_tools
- generate_documentation (premium multi-format)
- get_resources, get_resource, delete_resource
- register_client, list_clients, mcp_status

Example (Python):
```python
import asyncio
from mcp_server import call_mcp_tool

res = asyncio.run(call_mcp_tool("generate_documentation", {
    "family_key": "rotated_surface", "param": 5,
    "formats": ["html", "markdown", "json", "latex"]
}))
```

## Documentation Export (10/10 Quality)

`ProfessionalDocGenerator` produces:
- Modern self-contained HTML (Inter + JetBrains Mono, responsive stats, matrix preview, JS copy, provenance)
- Clean Markdown with TOC + repro
- Publication LaTeX + figures
- Rich JSON
- SVG/PDF matrix + Tanner graphs

All include generator/backend versions, timestamp, author/ORCID, watermark.

## Packaging & Release

- PyInstaller spec (updated for v3.4)
- Inno Setup installer (64-bit, lzma2, version info)
- Production bundles include exe, setup, docs samples, manifests, SHA256 checksums

See release assets for `QectorWorkbench-v3.4.0-production.zip` and `QectorWorkbenchSetup.exe`.

Build locally:
```bash
pyinstaller -y QectorWorkbench.spec
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /Q installer.iss
```

## Reproducibility & Verification

- All 25 MCP tools passing
- End-to-end: build → decode/benchmark → MCP → doc gen verified
- Self-tests pass (`python main.py --self-test`)
- Seeded RNGs, full provenance in exports

## System Requirements

- Python 3.11+
- Windows 10+ / Linux (recommended)
- 4 GB+ RAM
- Optional: CUDA/OpenCL for batch acceleration

## Version History

- v3.4.0 (2026-07): Production release — upgraded installer, production packaging, full verification of wiring/MCP/docs/GUI
- v3.3.0: 10/10 GUI polish, premium doc generator, MCP server completion + 25-tool exhaustive tests
- v3.1 / earlier: Initial professional infrastructure (config, logging, results, docs, dialogs)

## License

Source-available under EULA.txt. Free for personal/academic/non-commercial research. Commercial licensing available.

Developer: Guillaume Lessard © 2026

## Acknowledgments

Built on qector_decoder_v3 (Rust + Python, v0.6.2).

QECTOR Decoder Workbench v3.4 — Production Ready
