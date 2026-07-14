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
- **Decoder Lab** — Interactive single-syndrome decoding with 5 decoders (union_find, fast_union_find, blossom, sparse_blossom, bp_osd). Configurable error rate and seed. `blossom` is weight-optimal exact MWPM; `sparse_blossom` is near-optimal (not exact); the union-find family is fast/approximate with a higher logical error rate.
- **Benchmark Suite** — Configurable decode benchmarks with throughput and latency stats (mean/p50/p99/min/max). Export results to JSON.
- **Batch & Streaming** — Batch decode with explicit CPU/CUDA/OpenCL routing (no silent fallback — unavailable backends fail loudly). Streaming decode with sliding-window commit semantics.
- **Hardware & System** — Auto-detect CUDA, OpenCL, and CPU backends via `qector_decoder_v3` APIs (`cuda_is_available`, `opencl_is_available`). Note: the standard `qector-decoder-v3` wheel ships a CUDA path but **no OpenCL kernels**, so `opencl_is_available()` is `False` unless the backend was built from source with the `opencl` feature. System info and hardware-aware decoder recommendations via `hardware_routing.detect_hardware()` and `hardware_routing.recommend()`.
- **Documentation Studio** — Multi-format doc export: Markdown, JSON, HTML, LaTeX, PDF (matplotlib PdfPages), SVG (matplotlib). Full provenance metadata and decoder recommendation tables.

#### 29-Tool MCP Server
- Real stdio JSON-RPC 2.0 transport (protocol version 2024-11-05)
- stdin/stdout newline-delimited JSON-RPC — **no HTTP bridge, no port 8765**
- Implements `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call`
- All 29 tools wired to the real `backend.py` API

#### Backend
- Thin Python wrapper over `qector_decoder_v3` (compiled Rust core + public Python layer), developed and verified against the installed **v0.6.6** wheel (minimum supported 0.6.2)
- 6 code families × 5 decoders, all cross-compatible
- Batch decode: CPU/CUDA/OpenCL via `CPUBatchDecoder`/`CUDABatchDecoder`/`OpenCLBatchDecoder` (CUDA is shipped in the wheel; OpenCL requires a source build)
- Streaming decode: sliding-window FIFO with configurable window size, committed corrections, logical error rate tracking
- Spring-layout Tanner graph computation for all families

#### Honest performance posture
Following the upstream QECTOR Decoder v3 manual: all logical-error-rate, throughput, and latency figures are hardware-, driver-, seed-, and workload-dependent simulation results — **regenerate them on your own target before quoting.** PyMatching remains the speed leader on standard surface-code MWPM; QECTOR's exact `BlossomDecoder` reaches PyMatching's logical error rate but is not faster. The real strengths are batch throughput via approximate Union-Find (higher LER), qLDPC coverage via BP-OSD, and correctness that always satisfies the GF(2) syndrome equation `H·c == s (mod 2)`. This is a research/evaluation platform, not a real-time or fault-tolerant hardware decoding stack.

#### Other
- Auto-updater checking PyPI for newer `qector_decoder_v3` on boot
- PyInstaller EXE packaging with Inno Setup installer
- Fonts: Consolas (mono), Segoe UI (body/heading)

### Requirements

- Python >=3.11
- qector-decoder-v3 >=0.6.2 (verified against 0.6.6)
- customtkinter >=5.2.0
- numpy, scipy, Pillow, matplotlib, psutil

### Build Production Executable

```bash
pyinstaller --clean -y QectorWorkbench.spec
```

Output: `dist/QectorWorkbench/QectorWorkbench.exe`

### License

**Workbench (this app):** source-available under EULA.txt. The EULA grants a royalty-free,
worldwide license to use, execute, copy, and distribute the software for any purpose —
including commercial, academic, and personal use — provided the embedded "QECTOR" notices
and watermarks are retained (EULA §2).

**Backend (`qector-decoder-v3`):** a separately licensed, source-available Rust/Python
platform by the same author. Its own license is free for personal, academic, educational, and
non-commercial research, but **commercial use of `qector-decoder-v3` (company R&D, SaaS,
hosted API, OEM, redistribution) requires a paid commercial license** — see www.qector.store.
This workbench depends on it at runtime; honor the backend's license for any commercial deployment.

Author: Guillaume Lessard / iD01t Productions © 2026 · ORCID 0009-0000-3465-3753 ·
www.qector.store · admin@qector.store

Built on qector_decoder_v3 (v0.6.6).