# QECTOR Decoder Workbench v1.0.0 — Professional QEC Analysis Suite

## Overview

Professional quantum error-correction analysis platform built on `qector_decoder_v3`
(compiled Rust core + public Python layer, **v1.0.0**). Features **16 decoders**,
**10 code families** (including qLDPC and color codes), batch/streaming decode,
hardware detection, a resilient self/auto-debug backend, a **56-tool MCP server**,
and multi-format documentation export.

The Windows portable build bundles its own Python runtime, the scientific stack,
**and** the `qector_decoder_v3` wheel. It runs with no external Python, pip, or
internet connection: on first launch the bundled decoder wheel is activated into a
per-user managed site automatically. No online update checks are performed — the
app runs entirely from what ships in the box.

> **Honest posture (from the upstream QECTOR Decoder v3 manual):** every
> LER/throughput/latency figure is hardware-, driver-, seed-, and
> workload-dependent simulation — regenerate before quoting. PyMatching is the
> speed leader on standard surface-code MWPM; QECTOR's exact `BlossomDecoder`
> reaches its logical error rate but is not faster. Every decoder always
> satisfies `H·c == s (mod 2)`. This is a research/evaluation platform, not a
> real-time or fault-tolerant hardware decoder.

## Using the application

Launch **QECTOR Decoder Workbench** (double-click `QectorWorkbench-Portable.exe`).
For the headless MCP server:

```
QectorWorkbench-Portable.exe --mcp     # 56-tool stdio MCP server (no display needed)
```

Runtime data (logs, exported documents) is written to your per-user data
directory (`%LOCALAPPDATA%\QectorWorkbench`; override with `QECTOR_DATA_DIR`).

## Features

### Code Explorer
Build codes from **10 families** with configurable distance/parameter. Live
properties display including qubits, checks, and code rate, plus a clean
bipartite Tanner-graph view.

- **Graphlike / topological:** repetition, ring, rotated_surface,
  unrotated_surface, toric, heavy_hex, and `hypergraph_product` (a CSS code built
  from a repetition-code seed — graphlike, so all matching decoders apply).
- **qLDPC:** `bicycle` (parameter = circulant size) and `bivariate_bicycle`
  (the IBM BB code family — e.g. the [[72,12,6]] "gross" code — selected from
  verified presets). qLDPC codes are non-graphlike: use `bp_osd`, `blossom`,
  `hybrid`, or `auto_router` (the Diagnostics tab's resilient decode
  auto-falls-back to a compatible decoder).
- **Color codes:** `color_code` (triangular & 2D), decoded with the native
  colour-code decoder.

### Decoder Lab
Test any of **16 decoders** with configurable error rate and seed. View error,
syndrome, and correction arrays. Every decoder is verified to satisfy
`H·c == s (mod 2)`. A **Clear Decoder Cache** button frees cached decoder
instances between experiments.

- **union_find / fast_union_find** — fast approximate decode; higher LER than exact MWPM (throughput lever).
- **blossom** — weight-optimal exact MWPM; matches PyMatching's LER but is not faster.
- **sparse_blossom** — region-growing, near-optimal (experimental); **not exact**.
- **sparse_blossom_radix_neighbors** — radix-neighbor variant of the region-growing decoder.
- **bp_osd** — belief propagation + ordered statistics for LDPC / quantum-LDPC codes; tunable via `bp_method` (exact|min_sum) and `osd_order` (0|1|2).
- **auto** — self-selecting decoder: picks the best available backend per problem size.
- **hybrid** — combines a fast heuristic pass with exact matching; trainable weights.
- **lookup_table** — precomputed syndrome→correction table with O(1) lookup (refused above 20 checks).
- **predecoded** — resolves easy/low-weight syndromes in a fast pre-decoding pass before matching.
- **auto_router** — policy decoder: inspects the code and dispatches the best concrete decoder — matching for graphlike codes, bp_osd for qLDPC. Universally compatible, including on `bivariate_bicycle`.
- **hybrid_cascade** — Union-Find pre-filter with Blossom/BP-OSD escalation; exposes live cascade statistics. Graphlike codes only.
- **gnn_belief_matching** — GNN-predicted per-qubit weights guide a weighted matching decode, with a faithfulness fallback to plain MWPM. Graphlike codes.
- **belief_matching** — sum-product BP posteriors reweight an exact Blossom matching step; faithfulness-checked with MWPM fallback.
- **two_stage** — two-stage decode pipeline (fast stage + exact escalation).
- **ambiguity_cluster** — ambiguity-clustering decoder for degenerate syndrome structure.
- **colour_code** — native color-code decoder (restricted to true color-code topologies).

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
**56-tool** Model Context Protocol server (stdio JSON-RPC 2.0) for programmatic
access — including `self_diagnostics`, `probe_decoders`, `resilient_decode`,
`version_info`, `diagnostic_decode`, `native_recommend`, `native_streaming`,
`list_codes`, `compat_report`, hybrid-cascade stats, neural pre-decoder training,
and decoder-option-aware decode tools. All tools are wired to the real backend
with bulletproof error handling.

### Offline Versioning
- The window title and status bar show the workbench version (**v1.0.0**) and the
  installed decoder backend version (**qector-decoder-v3 v1.0.0**).
- No PyPI queries, no auto-updater: the shipped bundle is the single source of truth.

## License

**Workbench:** source-available — see EULA (free use including commercial, with
QECTOR watermark retention per EULA §2).

**Backend `qector-decoder-v3`:** separately licensed by Guillaume Lessard /
iD01t Productions — free for personal/academic/non-commercial research;
commercial use requires a paid commercial license (www.qector.store,
admin@qector.store). Honor the backend license for any commercial deployment.

Author: Guillaume Lessard / iD01t Productions · ORCID 0009-0000-3465-3753 · www.qector.store
