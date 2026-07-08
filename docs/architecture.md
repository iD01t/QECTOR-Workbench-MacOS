# QECTOR Workbench — Architecture (v3.4.0)

The MCP server (`mcp_server.py` + `mcp_resources.py`) sits on top of the backend and exposes 25 tools for external control (tested exhaustively).

**Repo Hygiene**: Strict .gitignore keeps source clean. Production artifacts live only in GitHub Releases.

## Topology

```
┌────────────────────────────────────────────┐
│                QECTOR App                  │
│ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│ │  app.py  │ │ dialogs  │ │   theme    │  │
│ └────┬─────┘ └──────────┘ └────────────┘  │
│      │                                     │
│      ├─ state.py (AppState)                │
│      ├─ console.py (ConsoleLog)            │
│      └─ threading_utils                    │
│        └─ run_in_background()              │
├────────────────────────────────────────────┤
│              Tab Layer                     │
│  code_explorer_tab                         │
│  decoder_lab_tab                           │
│  benchmark_tab                             │
│  batch_streaming_tab                       │
│  hardware_tab                              │
│  documentation_tab                         │
├────────────────────────────────────────────┤
│              backend.py                    │
│  Thin wrapper over qector_decoder_v3       │
│  - build_code()                            │
│  - run_single_decode()                     │
│  - run_benchmark()                         │
│  - run_batch_decode()                      │
│  - run_streaming_session()                 │
│  - get_hardware_profile()                  │
│  - get_recommendation()                    │
│  - get_tanner_graph_layout()               │
│  - validate_parameter()                    │
│  - code_summary()                          │
├────────────────────────────────────────────┤
│          qector_decoder_v3                 │
│  Rust core + Python bindings               │
│  - codes (repetition, surface, toric...)   │
│  - decoders (union_find, blossom, bp_osd)  │
│  - BatchDecoder / StreamingDecoder         │
│  - BenchmarkSuite                          │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│              MCP Server                     │
│  mcp_server.py                             │
│  - stdio/HTTP bridge                        │
│  - tool registry                             │
│  - XML-RPC/dispatch layer                    │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│         Persistence & Output                │
│  config.py  → .qector_config.json           │
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
5. `_on_decode` calls `run_in_background` → `backend.run_single_decode(code, p, kind, seed)`
6. Backend calls `decode_with_diagnostics(code, syndrome, kind=kind)`
7. Result dict displayed in Decoder Lab UI
8. Optional doc export via `ProfessionalDocGenerator`

## Data Flow: Benchmark

1. User sets `n_samples`, `seed` in `benchmark_tab.py`
2. `run_in_background` → `backend.run_benchmark(code, n_samples, seed)`
3. Backend creates `BenchmarkSuite(check_to_qubits, n_qubits, n_samples, seed)`
4. `.run()` returns real latency stats
5. UI displays latency bars and throughput metadata
