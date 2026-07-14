# QECTOR Decoder Workbench v3.5.0 — Professional QEC Analysis Suite

## Overview

Professional quantum error correction analysis platform built on `qector_decoder_v3` (compiled Rust core + public Python layer; developed and verified against the installed **v0.6.6** wheel). Features 5 decoders, 6 code families, batch/streaming decode, hardware detection, MCP server, auto-updater, and multi-format documentation export.

> **Honest posture (from the upstream QECTOR Decoder v3 manual):** every LER/throughput/latency figure is hardware-, driver-, seed-, and workload-dependent simulation — regenerate before quoting. PyMatching is the speed leader on standard surface-code MWPM; QECTOR's exact `BlossomDecoder` reaches its logical error rate but is not faster. Every decoder always satisfies `H·c == s (mod 2)`. This is a research/evaluation platform, not a real-time or fault-tolerant hardware decoder.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Features

### Code Explorer
Build codes from 6 families (repetition, ring, rotated_surface, unrotated_surface, toric, heavy_hex) with configurable distance. Live properties display including qubits, checks, and code rate.

### Decoder Lab
Test any of 5 decoders with configurable error rate and seed. View error, syndrome, and correction arrays.

- **union_find / fast_union_find** — fast approximate decode; higher LER than exact MWPM (throughput lever).
- **blossom** — weight-optimal exact MWPM; matches PyMatching's LER but is not faster.
- **sparse_blossom** — region-growing, near-optimal (experimental); **not exact** — use blossom for exact matching.
- **bp_osd** — belief propagation + ordered statistics for LDPC / quantum-LDPC codes matching cannot decode.

### Benchmark Suite
Run configurable benchmarks with throughput/latency metrics. Export results to JSON.

### Batch & Streaming
Batch decode multiple error samples with success rate. Streaming session controls (requires backend v0.6.2+).

### Hardware Dashboard
Auto-detect CUDA, OpenCL, and CPU backends. System info with CPU/RAM utilization. Hardware-optimized decoder recommendations. Note: the standard `qector-decoder-v3` wheel ships a CUDA path but no OpenCL kernels, so `opencl_is_available()` reports `False` unless the backend was built from source with the `opencl` feature.

### Documentation Studio
Export professional documentation in Markdown, HTML, JSON, and LaTeX formats with full provenance metadata.

### MCP Server
29-tool Model Context Protocol server for programmatic access. All tools wired to real backend with bulletproof error handling.

### Auto-Updater
On each boot, checks PyPI for newer `qector_decoder_v3` (verified against v0.6.6; minimum 0.6.2).

## Requirements

- Python 3.11+
- qector-decoder-v3 >=0.6.2
- customtkinter >=5.2.0
- numpy, scipy, Pillow, matplotlib, psutil

## Build Production Executable

```bash
pyinstaller QectorWorkbench.spec
```

Output: `dist/QectorWorkbench/QectorWorkbench.exe`

## License

**Workbench:** source-available — see EULA.txt (free use including commercial, with QECTOR watermark retention per EULA §2).

**Backend `qector-decoder-v3`:** separately licensed by Guillaume Lessard / iD01t Productions — free for personal/academic/non-commercial research; commercial use requires a paid commercial license (www.qector.store, admin@qector.store). Honor the backend license for any commercial deployment.

Author: Guillaume Lessard / iD01t Productions · ORCID 0009-0000-3465-3753 · www.qector.store

