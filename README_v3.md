# QECTOR Decoder Workbench v3.5.0 — Professional QEC Analysis Suite

## Overview

Professional quantum error correction analysis platform built on `qector_decoder_v3`. Features 5 decoders, 6 code families, batch/streaming decode, hardware detection, MCP server, auto-updater, and multi-format documentation export.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Features

### Code Explorer
Build codes from 6 families (repetition, ring, rotated_surface, unrotated_surface, toric, heavy_hex) with configurable distance. Live properties display including qubits, checks, and code rate.

### Decoder Lab
Test any of 5 decoders (union_find, fast_union_find, blossom, sparse_blossom, bp_osd) with configurable error rate and seed. View error, syndrome, and correction arrays.

### Benchmark Suite
Run configurable benchmarks with throughput/latency metrics. Export results to JSON.

### Batch & Streaming
Batch decode multiple error samples with success rate. Streaming session controls (requires backend v0.6.2+).

### Hardware Dashboard
Auto-detect CUDA, OpenCL, and CPU backends. System info with CPU/RAM utilization. Hardware-optimized decoder recommendations.

### Documentation Studio
Export professional documentation in Markdown, HTML, JSON, and LaTeX formats with full provenance metadata.

### MCP Server
29-tool Model Context Protocol server for programmatic access. All tools wired to real backend with bulletproof error handling.

### Auto-Updater
On each boot, checks PyPI for newer `qector_decoder_v3`. Install v0.6.2+ for streaming session support.

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

Proprietary — see EULA.txt

