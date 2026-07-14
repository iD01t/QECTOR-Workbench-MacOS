# QECTOR Decoder Workbench v3.5.0 — Upgrade Notes

## What Changed (v3.4.0 → v3.5.0)

v3.4.0 shipped a bare application window with none of its tabs wired in, a
package that could not be installed or built, an "MCP server" with no transport,
and documentation describing features that did not exist. v3.5.0 makes the
product real. Every claim below is backed by the test suite (`pytest` — 84
passed) and the MCP conformance script (`python test_mcp_all.py`).

### Application (`app.py`)
- Builds a real 7-tab `CTkTabview`: Code Explorer, Decoder Lab, Benchmark,
  Batch & Streaming, Hardware, Documentation, and a live Console tab — all
  sharing one `AppState` and one `Console`.
- Global crash handling: the Tk callback exception hook, `sys.excepthook`, and
  the `mainloop` wrapper all log the traceback and keep the app alive. A failure
  building any single tab is isolated to that tab; the rest still work.
- Every decode/benchmark/build runs on a background thread and marshals results
  back to the UI with `after`, so the window never freezes.
- No import-time side effects: importing `app` starts no threads and makes no
  network calls. The PyPI update check is scheduled ~1.5s after launch instead.
- A status bar shows the app version and the active code summary.

### Embedded graphs (matplotlib via `FigureCanvasTkAgg`)
- Code Explorer renders a live Tanner graph (qubit/check nodes, edges, legend)
  with a toggle to a parity-check-matrix (`imshow`) view.
- Benchmark renders latency and throughput charts across runs.
- Batch & Streaming renders per-round streaming and batch hamming-weight charts.
- All figures are drawn on the Tk main thread, reuse one figure per tab, and are
  dark-themed to match the palette.

### Backend engine (`backend.py`)
- `run_streaming_session` is a real sliding-window decoder (commit-on-eviction,
  end-of-session flush, reproducible per seed) — no longer a stub that raised.
- `run_benchmark` honors the chosen decoder and error rate and reports latency
  mean/p50/p99/min/max (µs), syndrome-match rate, and logical error rate.
- `run_batch_decode` genuinely routes `cuda`/`opencl` to the GPU batch decoders
  and raises a clear error when the backend is unavailable — no silent CPU
  fallback.
- `run_single_decode` results expose `syndrome_valid` and `logical_failure`
  (computed against `logicals_matrix`).

### MCP server (`mcp_server.py`)
- A real MCP server over newline-delimited JSON-RPC 2.0 on stdin/stdout
  (`initialize`, `tools/list`, `tools/call`, protocol version 2024-11-05). There
  is no HTTP transport.
- 29 tools, all wired to the real backend, with JSON-safe results. Fabricated
  handlers (benchmark that ignored its arguments, stub comparisons) were
  replaced with honest implementations, including `decode_single`,
  `batch_decode`, `stream_decode`, and `recommend_decoder`.

### Documentation generator (`doc_generator.py`)
- Real multi-page PDF and standalone SVG output (Tanner graph rendered with
  matplotlib), decoder recommendations computed for the documented code, and
  HTML/LaTeX escaping. Output goes to the per-user export directory.

### Robustness & packaging
- `utils.get_data_dir()` / `get_export_dir()` give a per-user writable location;
  `logger` writes there by default, fixing crashes when installed read-only
  under Program Files.
- `pyproject.toml` uses the correct `setuptools.build_meta` backend, an
  installable `py-modules` layout, and realistic dependency pins; the package
  now builds a wheel that actually contains the code.
- `.gitignore` no longer excludes `*.py` (the reason the repository had shipped
  with no source). A real multi-resolution `icon.ico` is generated and wired
  into the PyInstaller spec and Inno Setup installer.
- `main.py` launches only under a `__main__` guard with `freeze_support()`.

### Quality gates (all green locally)
- `pytest` — 84 passed
- `python test_mcp_all.py` — all in-process tools plus the stdio round-trip pass
- `ruff check .` — clean
- `mypy .` — no issues in 35 source files
- `bandit -ll` — no medium or high findings

### Version
- Workbench: 3.5.0
- Minimum backend: `qector-decoder-v3` 0.6.2 (developed and verified against 0.6.6)
