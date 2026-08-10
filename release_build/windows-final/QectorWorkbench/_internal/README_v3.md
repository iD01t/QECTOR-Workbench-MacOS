# QECTOR Decoder Workbench v3.5.1 — Professional QEC Analysis Suite

## Overview

Professional quantum error-correction analysis platform built on `qector_decoder_v3`
(compiled Rust core + public Python layer; developed and verified against **v0.6.6**).
Features **10 decoders**, **9 code families** (including two qLDPC families),
batch/streaming decode, hardware detection, a resilient self/auto-debug backend,
a 39-tool MCP server, dynamic live versioning, and multi-format documentation export.

This is a **self-contained** application: it bundles its own Python 3.11 runtime,
Tcl/Tk and scientific stack, so nothing else needs to be installed to run it.

> **Honest posture (from the upstream QECTOR Decoder v3 manual):** every
> LER/throughput/latency figure is hardware-, driver-, seed-, and
> workload-dependent simulation — regenerate before quoting. PyMatching is the
> speed leader on standard surface-code MWPM; QECTOR's exact `BlossomDecoder`
> reaches its logical error rate but is not faster. Every decoder always
> satisfies `H·c == s (mod 2)`. This is a research/evaluation platform, not a
> real-time or fault-tolerant hardware decoder.

## Using the application

Launch **QECTOR Decoder Workbench** from the Start menu (or run
`QectorWorkbench.exe` from the portable folder). For the headless MCP server:

```
QectorWorkbench.exe --mcp     # 39-tool stdio MCP server (no display needed)
```

Runtime data (logs, exported documents) is written to your per-user data
directory (`%LOCALAPPDATA%\QectorWorkbench`; override with `QECTOR_DATA_DIR`).

## Features

### Code Explorer
Build codes from **9 families** with configurable distance/parameter. Live
properties display including qubits, checks, and code rate, plus a clean
bipartite Tanner-graph view.

- **Graphlike / topological:** repetition, ring, rotated_surface, unrotated_surface, toric, heavy_hex, and `hypergraph_product` (a CSS code built from a repetition-code seed via `codes.hypergraph_product` — graphlike, so all matching decoders apply; not in QLDPC_FAMILIES).
- **qLDPC (v0.6.6):** `bicycle` (parameter = circulant size) and `bivariate_bicycle`
  (the IBM BB code family — e.g. the [[72,12,6]] "gross" code — selected from
  verified presets). qLDPC codes are non-graphlike: use `bp_osd`, `blossom`,
  `hybrid`, or `auto_router` (the union-find decoders don't apply; the Diagnostics
  tab's resilient decode auto-falls-back to a compatible decoder).

### Decoder Lab
Test any of **10 decoders** with configurable error rate and seed. View error,
syndrome, and correction arrays. Every decoder is verified to satisfy
`H·c == s (mod 2)`.

- **union_find / fast_union_find** — fast approximate decode; higher LER than exact MWPM (throughput lever).
- **blossom** — weight-optimal exact MWPM; matches PyMatching's LER but is not faster.
- **sparse_blossom** — region-growing, near-optimal (experimental); **not exact**.
- **bp_osd** — belief propagation + ordered statistics for LDPC / quantum-LDPC codes.
- **auto** — self-selecting decoder (v0.6.6 `AutoDecoder`): picks the best available backend per problem size.
- **hybrid** — combines a fast heuristic pass with exact matching; trainable weights.
- **lookup_table** — precomputed syndrome→correction table with O(1) lookup (refused above 20 checks).
- **predecoded** — resolves easy/low-weight syndromes in a fast pre-decoding pass before matching.
- **auto_router** — policy decoder (wraps v0.6.6 `AutoRouter`): inspects the code and dispatches the best concrete decoder — matching for graphlike codes, bp_osd for qLDPC. Universally compatible, including on `bivariate_bicycle`.

### Benchmark Suite
Run configurable benchmarks with throughput/latency metrics. Export results to JSON.

### Batch & Streaming
Batch decode multiple error samples with success rate. Sliding-window streaming
session controls.

### Hardware Dashboard
Auto-detect CUDA, OpenCL, and CPU backends. System info with CPU/RAM utilization
and hardware-optimized decoder recommendations. Note: the standard backend ships
a CUDA path but no OpenCL kernels, so OpenCL reports unavailable unless the
backend was built from source with the `opencl` feature.

### Diagnostics (Self / Auto-Debug)
- **Run Self-Diagnostics** — environment/decoder/hardware self-test with per-check pass/warn/fail status.
- **Probe Decoders** — reports which decoders produce a valid (syndrome-verified) correction for the current code.
- **Resilient Decode** — decodes with an automatic multi-decoder fallback chain (verifying `H·c == s` at each step) and shows the full attempt trace.

### Documentation Studio
Export professional documentation in Markdown, HTML, JSON, LaTeX, **PDF**
(matplotlib multi-page) and **SVG** (standalone Tanner graph) with full
provenance metadata.

### MCP Server
**39-tool** Model Context Protocol server for programmatic access — including
`self_diagnostics`, `probe_decoders`, `resilient_decode`, `version_info`,
`check_updates`, `diagnostic_decode`, `native_recommend`, `native_streaming`,
`list_codes`, and `compat_report`. All tools are wired to the real backend with
bulletproof error handling.

### Dynamic Live Versioning & Push-Update
- `version_service.py` queries PyPI at boot for both `qector-decoder-v3` and
  `qector-workbench` (override via `QECTOR_APP_PACKAGE`). Results are cached in-memory
  and on-disk (6h TTL); static baselines from `version.py` serve as an offline fallback.
- The window title and status bar show a **live-resolved** version banner, updated on a
  background thread via the UI pump.
- `auto_updater.boot_update_summary()` prints combined app+backend update availability
  in the console at boot. `auto_updater.perform_backend_update()` performs a background
  pip upgrade on source installs; frozen builds receive release-update guidance instead.

## License

**Workbench:** source-available — see EULA (free use including commercial, with
QECTOR watermark retention per EULA §2).

**Backend `qector-decoder-v3`:** separately licensed by Guillaume Lessard /
iD01t Productions — free for personal/academic/non-commercial research;
commercial use requires a paid commercial license (www.qector.store,
admin@qector.store). Honor the backend license for any commercial deployment.

Author: Guillaume Lessard / iD01t Productions · ORCID 0009-0000-3465-3753 · www.qector.store
