# QECTOR Decoder Workbench — Upgrade Notes

## Release v0.5.3 (Current) — publication-grade documentation & release plumbing

Upgrading from v0.5.2 needs no migration: the profile, export and licence paths
are unchanged. What changes for users:

- **Version reporting is correct again.** v0.5.2 shipped with
  `WORKBENCH_VERSION` set to the *backend's* number (0.7.0), so the window title,
  the MCP `status` response, the generated manuals and the `.deb` package name
  all claimed the wrong release. The product line is 0.5.x and the backend line
  is 0.7.x; they are independent and now stay that way.
- **Seven export buttons that did nothing now work.** Benchmark, Batch &
  Streaming, Diagnostics and Hardware all raised a swallowed `NameError` on
  export, and Decoder Lab's "Generate Doc" called a method that does not exist.
- **Documents are deposit ready.** Reports gain `.zenodo.json` and
  `CITATION.cff`, a five-figure publication suite, Methods and Data Availability
  sections, a citation block and a CC-BY-4.0 licence line. Typographic dashes are
  purged from every generated artifact.
- **No fabricated attribution.** The placeholder author that previously landed in
  PDF metadata and every report header is gone; an unset profile renders as
  "Unattributed" with a note to fill in the profile before depositing.
- **The licence key field is real.** It writes `~/.qector/license.key`, hands the
  key to the decoder's own verifier, and reports the resulting tier. Previously
  it wrote to a file nothing read, so an Enterprise key silently did nothing.
- **The Buy Licence section is back** in the Documentation tab; it had been
  dropped from the UI build.
- **Contact address is now `admin@qector.store`** throughout the app, the
  manuals and the Debian package metadata.

**If you keep a `~/.qector/lab_info.json` from v0.5.2**, its `license_key` entry
is ignored and dropped on load: put a real key in the Lab & Personal Info tab so
it reaches `~/.qector/license.key` where the decoder looks for it.

See `CHANGELOG.md` for the complete list.

---

## Release v0.5.2 — Workbench rebranding & offline hardening

This release establishes the **workbench's own version line (v0.5.2)**, decoupled
from the decoder backend version, and removes all online update machinery:

- **Versioning:** the app now identifies as **QECTOR Decoder Workbench v0.5.2**
  with backend **qector-decoder-v3 v0.7.0**. The status bar banner reads
  `QECTOR Decoder Workbench v0.5.2 | qector-decoder-v3 0.7.0 (latest)`.
- **Auto-updater removed:** `auto_updater.py` deleted; no PyPI queries at boot,
  no background pip upgrades. The shipped bundle is the single source of truth.
- **Offline provisioning with purge:** `decoder_provisioner.purge_outdated_managed_sites()`
  deletes any managed decoder site older than v0.7.0 (e.g. cached 0.6.6/0.6.8/0.6.9
  on machines that ran older builds) before activating the bundled wheel — no
  manual cleanup needed when upgrading from older releases.
- **Stale-cache guard:** `version_service` overwrites any stale on-disk version
  cache so the app can never display a downgraded version.
- **Fixes:** `decoder_lab_tab` Clear-Decoder-Cache button no longer raises
  `AttributeError` (`_set_result_text` → `_set_text`); bivariate-bicycle
  compatibility list no longer offers `two_stage` / `ambiguity_cluster`
  (hypergraph checks exceed their 2-body assumptions); colour-code adapter
  falls back to BP-OSD/Blossom on graph-like topologies.

## Release v0.7.0 / Workbench v3.7.0

This release upgrades the core backend to **`qector_decoder_v3` v0.7.0**, adding 3 new decoders (bringing total decoders to 16), 1 new code family (bringing total code families to 10), 9 new MCP tools (bringing total registered tools to 56), native system diagnostics (`qd.doctor`), Ed25519 license verification, Stripe metered billing metrics flush (`flush_usage`), SparseBlossom RadixHeap $k$-NN candidate edge discovery, and native decoder cache management.

### Decoders & Code Families (`backend.py`)
- **16 decoders** (was 13): added `two_stage` (decoupled X/Z sector decoders), `ambiguity_cluster` (cluster decoding for high-noise/non-graphlike codes), `colour_code` (BP-OSD over undecomposed detector error models). Full list: `union_find`, `fast_union_find`, `blossom`, `sparse_blossom`, `bp_osd`, `auto`, `hybrid`, `lookup_table`, `predecoded`, `auto_router`, `hybrid_cascade`, `gnn_belief_matching`, `belief_matching`, `two_stage`, `ambiguity_cluster`, `colour_code`.
- **10 code families** (was 9): added `color_code` (triangular 4.8.8 color code family). Full list: `repetition`, `ring`, `rotated_surface`, `unrotated_surface`, `toric`, `heavy_hex`, `bicycle`, `bivariate_bicycle`, `hypergraph_product`, `color_code`.

### New Native Capabilities
- `sparse_blossom_radix_neighbors`: RadixHeap candidate edge discovery for defective syndromes.
- `clear_decoder_cache`: Purge native C++/Rust decoder cache.
- `run_doctor_checks`: Health check & diagnostic report via `qector_decoder_v3.doctor`.
- `flush_usage`: Stripe metered billing usage telemetry flush.
- `verify_license_token` & `set_license_key_file`: Offline & online Ed25519 signed license token validation.

### MCP Tools: 56 Registered Tools
Added 9 new tools (`sparse_blossom_radix_neighbors`, `clear_decoder_cache`, `flush_usage`, `doctor_diagnostics`, `verify_license_token`, `set_license_key_file`, `two_stage_decode`, `ambiguity_cluster_decode`, `colour_code_decode`) and enforced a 10 MB frame limit on JSON-RPC transport.

## What Changed (v3.5.1 → v0.6.9)

This release adds a 10th decoder, a 9th code family, 7 new MCP tools (bringing the
total to 39), dynamic live versioning, a push-update mechanism, new backend functions
wrapping the v0.6.6 native API, publication-grade graphs, and a new professional icon
set. There are **no breaking changes**: all existing APIs, tool names, and file paths
are preserved.

### Decoders & code families (`backend.py`)
- **10 decoders** (was 9): added `auto_router` — a policy decoder wrapping v0.6.6
  `AutoRouter`. It inspects the code and dispatches the best concrete decoder (matching
  for graphlike codes, bp_osd for qLDPC). Universally compatible, including on
  `bivariate_bicycle`. Full list: union_find, fast_union_find, blossom, sparse_blossom,
  bp_osd, auto, hybrid, lookup_table, predecoded, auto_router.
- **9 code families** (was 8): added `hypergraph_product` — a CSS code built from a
  repetition-code seed via `codes.hypergraph_product`. It is graphlike (all matching
  decoders construct on it) and is NOT in `QLDPC_FAMILIES` (which remains
  `{"bicycle", "bivariate_bicycle"}`). Full list: repetition, ring, rotated_surface,
  unrotated_surface, toric, heavy_hex, bicycle, bivariate_bicycle, hypergraph_product.

### New backend functions (wrapping v0.6.6 native API)
- `run_diagnostic_decode` — native `decode_with_diagnostics`: returns matched weight,
  backend used, internal fallback flag, and timing.
- `native_recommend` — native `recommend` / `recommend_decoder` with mapped decoder kind.
- `run_native_streaming` — native `sliding_window_decode` with GPU support and telemetry.
- `run_parallel_batch_decode` — multi-process `DecoderPool` for parallel batch decoding.
- `list_available_codes` — list all 9 code families with graphlike/qLDPC flags.
- `compat_report` — detect stim, sinter, pymatching, qiskit, ldpc availability.

### MCP tools: 39 (was 32)
Seven new tools added: `version_info`, `check_updates`, `diagnostic_decode`,
`native_recommend`, `native_streaming`, `list_codes`, `compat_report`. All 32
existing tools are unchanged.

### Dynamic live versioning (`version_service.py`, NEW)
- Queries PyPI at boot for both `qector-decoder-v3` and `qector-workbench`
  (override the app package name via `QECTOR_APP_PACKAGE` env var).
- Results cached in-memory and on-disk with a 6-hour TTL. Static baselines from
  `version.py` serve as an offline fallback when PyPI is unreachable.
- The app's window title and status bar now display the live-resolved version banner,
  updated on a background thread via the UI pump — no longer a hardcoded string.

### Push-update mechanism (`auto_updater.py`, updated)
- `boot_update_summary()` prints a combined app+backend update notice to the console
  at boot.
- `perform_backend_update()` performs a background pip upgrade on source installs;
  frozen (PyInstaller) builds receive release-update guidance instead.

### New professional icon set
SVG master generated; multi-resolution `.ico` (Windows), `.icns` (macOS), and `.png`
(Linux) produced and wired into the respective build specs and installers across all
three OS trees.

### High-DPI matplotlib figures
All embedded graphs (Tanner graph, benchmark charts, batch/streaming plots) are now
rendered at high-DPI with antialiasing — publication-grade quality.

### Ecosystem compatibility
`compat_report` / the `compat_report` MCP tool detect and report availability of:
stim, sinter, pymatching, qiskit, ldpc.

### Migration notes
None — no breaking changes. Existing tool calls, API signatures, config files, and
export paths all continue to work.

### Version
- Workbench: **3.5.1** (live-resolved) · MCP tools: **39** · Backend: `qector-decoder-v3` 0.6.6 (min 0.6.2)

---

## What Changed (v3.5.0 → v3.5.1)

v3.5.1 completes coverage of the installed `qector_decoder_v3` **v0.6.6** surface,
adds a resilient self/auto-debug layer, and ships cross-platform builds. Backed
by the test suite (Windows + Linux, all passing) and `python test_mcp_all.py`
(32/32 tools).

### Decoders & code families (`backend.py`)
- **9 decoders** now wired (was 5): added `auto` (v0.6.6 `AutoDecoder`), `hybrid`,
  `lookup_table` (guarded against exponential blow-up), and `predecoded` — each
  verified valid + deterministic across the graphlike families.
- **8 code families** now wired (was 6): added the qLDPC families `bicycle` and
  `bivariate_bicycle` (the IBM BB code family, e.g. the [[72,12,6]] "gross" code),
  finally giving `bp_osd` the qLDPC codes it was designed for.
- New `compatible_decoder_kinds(code)` decode-verifies which decoders work on a
  given code (qLDPC codes reject the union-find decoders).

### Self / auto-debug backend (`autodebug.py`, NEW) + Diagnostics tab
- `resilient_single_decode` — tries the requested decoder then an ordered
  fallback chain, verifying `H·c == s` at each step; returns the first valid
  result plus a full attempt trace. Never raises.
- `resilient_batch_decode` — `cuda → opencl → cpu` fallback with a per-backend trace.
- `probe_decoders` and `run_self_diagnostics` (environment/decoder/hardware
  self-test, surfacing the native `AutoDecoder.diagnostics()`).
- Surfaced in a new **Diagnostics** GUI tab and 3 new MCP tools
  (`self_diagnostics`, `probe_decoders`, `resilient_decode`) → **32 MCP tools**.
- The **Decoder Lab** now auto-recovers (with a clear "Recovered with …" report)
  when the chosen decoder can't handle the current code.

### Correctness fixes
- `hardware_routing.recommend()` is **qLDPC-aware**: it never recommends a decoder
  that cannot construct on the code (previously suggested union-find for BB codes).
- `doc_generator` SVG export hardened: metadata rejection falls back to a clean
  SVG instead of failing; figures are always released.

### Cross-platform packaging
- **Windows:** onedir `.exe` rebuilt with the full feature set; portable ZIP.
- **Linux:** `compile.sh --docker` now builds a **universal AppImage** on Debian 11
  (glibc 2.31) — requires only glibc ≥ 2.30, so it runs on antiX 21+, Ubuntu 20.04+,
  Debian 11+, Mint 20+, Fedora 32+, and newer. Fixed a numpy/OpenBLAS
  "not page-aligned" load failure by disabling `strip` (old-binutils incompatibility).
- **macOS:** ready-to-build `Mac/` tree (`build_macos.sh`) for a signed `.app` + `.dmg`
  (arm64 from PyPI; Intel from a wheel dropped into `Mac/wheels/`).

### Version
- Workbench: **3.5.1** · MCP tools: **32** · Backend: `qector-decoder-v3` 0.6.6 (min 0.6.2)

---

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
