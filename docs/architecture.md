# QECTOR Workbench — Architecture (v3.5.0)

The MCP server (`mcp_server.py` + `mcp_resources.py`) sits on top of the backend and exposes 29 tools for external control (tested exhaustively).

**Repo Hygiene**: Strict `.gitignore` keeps source clean. Production artifacts live only in GitHub Releases.

## Topology

```
┌────────────────────────────────────────────┐
│                QECTOR App                  │
│ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│ │  app.py  │ │ dialogs  │ │   theme    │  │
│ └────┬─────┘ └──────────┘ └────────────┘  │
│      │                                     │
│      ├─ state.py (AppState)                │
│      ├─ console.py (Console)               │
│      └─ threading_utils                    │
│        └─ run_in_thread()                  │
├────────────────────────────────────────────┤
│              Tab Layer                     │
│  code_explorer_tab                         │
│  decoder_lab_tab                           │
│  benchmark_tab                             │
│  batch_streaming_tab                       │
│  hardware_tab                              │
│  documentation_tab                         │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│                 backend.py                 │
│  - thin wrapper over Rust core bindings    │
│  - routing to CPU/CUDA/OpenCL decoders     │
│  - layout generation fallback              │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│              qector_decoder_v3             │
│  - public Python module wrapping Rust QEC  │
│  - decoders: MWPM, fast UF, BPOSD, etc.    │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│               MCP Server                   │
│  mcp_server.py                             │
│  - stdio JSON-RPC 2.0 transport            │
│  - in-process 29-tool registry             │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│         Persistence & Output                │
│  logger.py  → logs/qector.log               │
│  doc_generator.py → exports/                │
│  PyInstaller → dist/QectorWorkbench/        │
└────────────────────────────────────────────┘
```

## Data Flow: Single Decode

1. User selects code family + parameter in `code_explorer_tab.py`
2. `backend.build_code(family, param)` calls real `qector_decoder_v3.codes`
3. `AppState.set_code(code, family, param)` notifies listeners
4. User selects decoder + error rate in `decoder_lab_tab.py`
5. `_on_decode` calls `backend.run_single_decode(code, p, kind, seed)`
6. Result displayed in Decoder Lab UI
7. Optional doc export via `ProfessionalDocGenerator`

## Data Flow: Benchmark

1. User sets `n_samples`, `seed` in `benchmark_tab.py`
2. UI calls `backend.run_benchmark(code, n_samples, seed)`
3. Backend runs loops measuring decode time with `time.perf_counter`
4. UI displays throughput and latency statistics
