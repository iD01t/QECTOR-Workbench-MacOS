## QECTOR Decoder Workbench v3.5.0

**Production Release**

> Quantum Error Correction Analysis Suite with CustomTkinter GUI, 29-tool MCP server, and multi-format documentation export.

### Quick Start (from source)

```bash
pip install -r requirements.txt
python main.py
```

### Download v3.5.0

- `QectorWorkbenchSetup.exe` — Windows installer (64-bit, Inno Setup)
- `QectorWorkbench-v3.5.0-production.zip` — Complete production bundle including standalone EXE, docs, and SHA256 manifest

### Key Features

#### 6 GUI Tabs
- **Code Explorer** — Build codes from 6 families (repetition, ring, rotated_surface, unrotated_surface, toric, heavy_hex) with configurable distance. View code properties (qubits, checks, distance, rate).
- **Decoder Lab** — Interactive single-syndrome decoding with 5 decoders (union_find, fast_union_find, blossom, sparse_blossom, bp_osd). Configurable error rate and seed.
- **Benchmark Suite** — Configurable decode benchmarks with throughput and latency stats (mean/p50/p99/min/max). Export results to JSON.
- **Batch & Streaming** — Batch decode with explicit CPU/CUDA/OpenCL routing (no silent fallback — unavailable backends fail loudly). Streaming decode with sliding-window commit semantics.
- **Hardware & System** — Auto-detect CUDA, OpenCL, and CPU backends via `qector_decoder_v3` APIs (`cuda_is_available`, `opencl_is_available`). System info and hardware-aware decoder recommendations via `hardware_routing.detect_hardware()` and `hardware_routing.recommend()`.
- **Documentation Studio** — Multi-format doc export: Markdown, JSON, HTML, LaTeX, PDF (matplotlib PdfPages), SVG (matplotlib). Full provenance metadata and decoder recommendation tables.

#### 29-Tool MCP Server
- Real stdio JSON-RPC 2.0 transport (protocol version 2024-11-05)
- stdin/stdout newline-delimited JSON-RPC — **no HTTP bridge, no port 8765**
- Implements `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call`
- All 29 tools wired to the real `backend.py` API

#### Backend
- Thin Python wrapper over `qector_decoder_v3` (Rust core + Python bindings)
- 6 code families × 5 decoders, all cross-compatible
- Batch decode: CPU/CUDA/OpenCL via `CPUBatchDecoder`/`CUDABatchDecoder`/`OpenCLBatchDecoder`
- Streaming decode: sliding-window FIFO with configurable window size, committed corrections, logical error rate tracking
- Spring-layout Tanner graph computation for all families

#### Other
- Auto-updater checking PyPI for newer `qector_decoder_v3` on boot
- PyInstaller EXE packaging with Inno Setup installer
- Fonts: Consolas (mono), Segoe UI (body/heading)

### Requirements

- Python >=3.11
- qector-decoder-v3 >=0.6.2
- customtkinter >=5.2.0
- numpy, scipy, Pillow, matplotlib, psutil

### Build Production Executable

```bash
pyinstaller --clean -y QectorWorkbench.spec
```

Output: `dist/QectorWorkbench/QectorWorkbench.exe`

### License

Source-available under EULA.txt. The EULA grants a royalty-free, worldwide license to
use, execute, copy, and distribute the software for any purpose — including commercial,
academic, and personal use — provided the embedded "QECTOR" notices and watermarks are
retained (EULA §2).

Developer: Guillaume Lessard © 2026

Built on qector_decoder_v3 (v0.6.2).