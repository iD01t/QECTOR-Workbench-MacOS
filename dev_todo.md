# QECTOR Decoder Workbench - Implementation TODO

## Phase 0: Backend Integration
- [x] Wire `SpaceTimeDecoder` into `backend.py` and GUI
- [x] Wire `CUDABpOsdDecoder` as batch backend option (add `cuda_bposd` to `_BATCH_BACKENDS`)
- [x] Add `bp_method="relay"` to BP-OSD options (backend.py:618-620)
- [x] Add `damping` and `osd_lambda` to BP-OSD options (backend.py:630-633)
- [x] Add `edge_weights` support to GPU batch decode
- [x] Add `CUDABatchDecoder(precision="f64")` option (backend.py:pass-through)
- [x] Wire `get_license_info()` to Lab & Personal Info tab
- [x] Add all 6 tuning environment variables to Hardware tab (`QECTOR_BLOSSOM_K_MULT`, etc.)
- [x] Wire `DemModel` import to Code Explorer
- [x] Add `stim_compat` import to Code Explorer
- [x] Register missing 6 MCP tools (`decode_hyperedge`, `decode_syndrome_blossom`, `decode_syndrome_cascade`, `run_ler_benchmark`, `get_backend_health`, `get_server_env`)
- [x] Add `LERBenchmark` to Benchmark tab
- [x] Add `decode_mmap` MCP tool (mcp_server.py) and CLI command
- [x] Add `ColourCodeDecoder(method="cluster_bposd")` option
- [x] Wire `AutoDecoder._diag` to Diagnostics tab
- [x] Add `reset_backend_health()` button to Diagnostics tab
- [x] Add Wilson CI display to Benchmark results
- [x] Add `n_unfaithful` / `unfaithful_rate` to Benchmark
- [x] Add `qector serve` CLI subcommand (cli.py)
- [x] Add `qector-doctor` CLI subcommand (cli.py)
- [x] Wire `generate_parity_check_matrix()` to Code Explorer
- [x] Add `qiskit_plugin` export option (backend.py:export_to_qiskit_plugin)
- [x] Add `sinter_compat` export (backend.py:export_to_sinter_compat)
- [x] Add `pymatching` shim (backend.py:export_to_pymatching_shim)
- [x] Add `QECTOR_SILENT` toggle
- [x] Add `QECTOR_ENFORCE` toggle
- [x] Handle v2 license token expiry display (backend.py:get_license_info_with_expiry)
- [x] Test invalid license key raises ValueError (backend.py:test_invalid_license_key)

## Phase 2: Scientific Features
- [x] Add threshold estimation (MCP tool: estimate_threshold)
- [x] Add finite-size scaling analysis (MCP tool: finite_size_scaling)
- [x] Add user-defined parity check matrix support (MCP tool: build_code_from_matrix)
- [x] Add noise model configuration (MCP tool: build_dem noise_model param)
- [x] Add statistical analysis tools (MCP tools: analyze_error_patterns, analyze_logicals)
- [x] Add publication-ready figure export (MCP tool: export_figure)
- [x] Add reproducibility package generation (MCP tool: generate_reproducibility_package)

## Phase 3: Platform & Distribution
- [ ] Build macOS `.dmg` (requires Apple hardware)
- [ ] Build Linux AppImage (recipe exists, not built for 1.0.0)
- [ ] Build Windows installer (Inno Setup)
- [x] Add build reproducibility (SHA-256 checksum manifest in build_production.py)
- [x] Add artifact signing (GPG signing infrastructure in build_production.py)
- [ ] Add Docker MCP image
- [ ] Add conda recipe

## Phase 4: Quality of Life
- [ ] Add experiment notebook / history
- [ ] Add side-by-side decoder comparison (MCP tool: compare_all_decoders exists; GUI not wired)
- [x] Add configuration persistence (workspace.json, preferences.json)
- [ ] Add progressive rendering
- [ ] Add dark/light theme toggle (theme.py exists, no toggle in GUI)
- [ ] Add accessibility features
- [x] Add internationalization (i18n.py exists with EN/FR/ZH)
- [ ] Add job queue for batch operations

## Verification Checklist
- [x] All Python files compile cleanly (syntax check passed)
- [x] version.py MCP_TOOLS matches actual registration count (82)
- [x] docs/api.md tool count matches (updated to 82)
- [x] docs/architecture.md tool count matches (updated to 82)
- [x] README.md tool count matches (updated to 82)
- [x] AGENT.md tool count matches (updated to 82)
- [x] PROJECT_STATUS.md tool count matches (updated to 82)
- [x] RELEASE_REPORT.md tool count matches (updated to 82)
- [x] README_LINUX.md tool count matches (updated to 82)
- [x] README_v3.md tool count matches (updated to 82)
- [x] CHANGELOG.md updated with correct tool count
- [x] build_production.py: SHA-256 checksum manifest generation
- [x] build_production.py: GPG artifact signing infrastructure
- [x] build_production.py: Dynamic wheel version in spec files
- [x] build_production.py: Syntax error fixed (lines 63-68)
- [x] decoder_provisioner.py: PyPI install with retry + checksum verification
- [x] All changes synced to Linux/ and Mac/ trees
