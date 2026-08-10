
================================================================================

                      QECTOR DECODER WORKBENCH  v3.5.1
                 Quantum Error Correction Analysis Suite

              Built on qector-decoder-v3 v0.6.9 (Rust/PyO3)
          (c) 2026 Guillaume Lessard / iD01t Productions
                         www.qector.store

================================================================================


  CONTENTS
  --------
  1.  About
  2.  Quick Start
  3.  What's Inside
  4.  Features at a Glance
  5.  Code Families (9)
  6.  Decoder Algorithms (13)
  7.  Command-Line Usage
  8.  MCP Server (AI/LLM Integration)
  9.  System Requirements
  10. Runtime & Self-Healing
  11. Documentation
  12. Performance Notes
  13. License
  14. Contact & Support


================================================================================
  1.  ABOUT
================================================================================

  QECTOR Decoder Workbench is a professional-grade, portable desktop
  application for quantum error correction (QEC) research, evaluation,
  and documentation.

  It wraps the high-performance qector-decoder-v3 compiled Rust engine
  and provides:

    *  Interactive single-syndrome decoding with 13 algorithms
    *  9 topological and quantum LDPC code families
    *  Batch and streaming decode with GPU acceleration
    *  47-tool Model Context Protocol (MCP) server for AI agents
    *  Publication-grade benchmark charts and documentation export
    *  Full command-line interface for scripted workflows

  No installation required. No Python needed. No internet on first run.
  Just launch the .exe.


================================================================================
  2.  QUICK START
================================================================================

  PORTABLE .EXE (this package)
  ----------------------------

    1. Extract this archive (if zipped) to any folder
    2. Double-click  QectorWorkbench-Portable.exe
    3. The decoder engine activates automatically on first launch

  That's it. No admin rights, no registry entries, no install wizard.
  Runs from a USB drive, network share, or any local folder.

  COMMAND LINE
  ------------

    QectorWorkbench-Portable.exe decode --code rotated_surface -d 5
    QectorWorkbench-Portable.exe benchmark --code toric -d 7 -n 10000
    QectorWorkbench-Portable.exe diagnostics
    QectorWorkbench-Portable.exe --mcp

  FROM SOURCE (developers)
  ------------------------

    pip install -r requirements.txt
    python main.py


================================================================================
  3.  WHAT'S INSIDE
================================================================================

  File / Folder               Description
  --------------------------  -----------------------------------------------
  QectorWorkbench-Portable.exe   Main application (portable, self-contained)
  README.txt                     This file
  EULA.txt                       End User License Agreement
  docs/                          User manuals, API reference, guides (PDF/MD)


================================================================================
  4.  FEATURES AT A GLANCE
================================================================================

  GRAPHICAL INTERFACE (7 tabs + live console)
  -------------------------------------------

    Code Explorer        Build and inspect 9 code families. View qubit
                         and check counts, distance, rate, and interactive
                         Tanner graph visualizations.

    Decoder Lab          Interactive single-syndrome decoding with 13
                         algorithms. Tunable BP-OSD parameters, resilient
                         fallback mode, and detailed correction analysis.

    Benchmark Suite      Configurable benchmarks with throughput and latency
                         statistics (mean, p50, p99, min, max). Multi-panel
                         high-DPI charts. JSON export.

    Batch & Streaming    Batch decode with explicit CPU / CUDA / OpenCL
                         routing. Streaming decode with sliding-window
                         commit semantics and live logical error rate.

    Hardware & System    Auto-detect CUDA, OpenCL, and CPU backends.
                         Hardware-aware decoder recommendations.

    Diagnostics          Full environment, decoder, and hardware self-
                         diagnostics. Auto-debug with multi-decoder
                         fallback and complete attempt trace analysis.

    Documentation        Multi-format export: Markdown, JSON, HTML, LaTeX,
      Studio             PDF, and SVG. Provenance metadata and decoder
                         recommendation tables included.

    Console (Live)       Real-time log output and interactive terminal.


  COMMAND-LINE INTERFACE
  ----------------------

    Full-featured terminal UI with colored output, supporting all backend
    operations: decode, benchmark, probe, diagnostics, hardware detection,
    code listing, and document generation.


  MCP SERVER
  ----------

    47-tool Model Context Protocol server over stdio JSON-RPC 2.0.
    Plug directly into Claude, GPT, Copilot, or any MCP-compatible
    AI agent for headless quantum error correction workflows.


================================================================================
  5.  CODE FAMILIES (9)
================================================================================

  Family                Type         Description
  --------------------  ----------   -----------------------------------------
  repetition            Graphlike    1D repetition code
  ring                  Graphlike    Ring topology
  rotated_surface       Graphlike    Rotated planar surface code
  unrotated_surface     Graphlike    Standard planar surface code
  toric                 Graphlike    Periodic toric code
  heavy_hex             Graphlike    IBM heavy-hexagon lattice
  hypergraph_product    Graphlike    CSS code from repetition-code seed
  bicycle               qLDPC       Quantum LDPC bicycle code
  bivariate_bicycle     qLDPC       IBM bivariate bicycle (BB) code family

  Graphlike families support all 13 decoders.
  qLDPC families use bp_osd, blossom, hybrid, auto_router, and others
  as reported by the built-in compatibility probe.


================================================================================
  6.  DECODER ALGORITHMS (13)
================================================================================

  Decoder               Strategy         Notes
  --------------------  ---------------  -----------------------------------
  union_find            Approximate      Fast cluster-growth matching
  fast_union_find       Approximate      Optimized UF variant
  blossom               Exact MWPM       Weight-optimal, matches PyMatching
  sparse_blossom        Near-optimal     Sparse graph approximation
  bp_osd                Iterative        BP + OSD for qLDPC codes
  auto                  Auto-select      Self-selects best backend
  hybrid                Combined         Multi-strategy hybrid
  lookup_table          Exact            Table-based, small codes (<=20 chk)
  predecoded            Staged           Pre-decoded syndrome correction
  auto_router           Policy           Dispatches best decoder per topology
  hybrid_cascade        Staged           UF pre-filter + Blossom escalation
  gnn_belief_matching   Neural           GNN-weighted belief matching
  belief_matching       Hybrid           BP posteriors + exact Blossom MWPM

  RESILIENT MODE:  When enabled, the workbench automatically falls back
  through compatible decoders if the selected one cannot handle the
  current code, and reports exactly what happened at each step.


================================================================================
  7.  COMMAND-LINE USAGE
================================================================================

  Usage:  QectorWorkbench-Portable.exe <command> [options]

  Commands
  --------
  decode           Decode a single syndrome
  benchmark        Run decoder benchmarks
  probe            Probe compatible decoders for a code
  diagnostics      Full environment and decoder diagnostics
  hardware         Detect and report hardware backends
  list-codes       List all available code families
  list-decoders    List all decoder algorithms
  docgen           Generate documentation (MD, JSON, HTML, LaTeX, PDF, SVG)
  version          Show version information
  --mcp            Launch the 47-tool MCP server

  Examples
  --------

    Decode with exact Blossom MWPM on rotated surface code:

      QectorWorkbench-Portable.exe decode ^
          --code rotated_surface --distance 5 ^
          --decoder blossom --error-rate 0.05

    Benchmark on toric code with 10,000 samples:

      QectorWorkbench-Portable.exe benchmark ^
          --code toric --distance 7 --samples 10000

    Generate LaTeX documentation:

      QectorWorkbench-Portable.exe docgen ^
          --code rotated_surface --distance 5 --format latex


================================================================================
  8.  MCP SERVER (AI/LLM INTEGRATION)
================================================================================

  Launch:   QectorWorkbench-Portable.exe --mcp

  Transport:   stdio JSON-RPC 2.0 (protocol version 2024-11-05)
  Tools:       47 (full backend API)
  Bridge:      None required — pure stdin/stdout newline-delimited JSON-RPC

  Tool categories include:

    Decoding         decode, resilient_decode, diagnostic_decode,
                     probe_decoders

    Batch            batch_decode, parallel_batch_decode, native_streaming

    Benchmarking     benchmark, run_hybrid_cascade_stats

    Code Mgmt        build_code, list_codes, compat_report,
                     compatible_decoder_kinds

    Hardware         detect_hardware, native_recommend,
                     cuda_is_available, opencl_is_available

    Diagnostics      self_diagnostics, version_info, check_updates

    Documentation    generate_doc (all 6 output formats)

    Research         run_neural_predecoder_training


================================================================================
  9.  SYSTEM REQUIREMENTS
================================================================================

  Component      Minimum
  -------------  -----------------------------------------
  OS             Windows 10 or 11 (x64)
  Runtime        None (portable build is self-contained)
  RAM            4 GB minimum, 8 GB recommended
  Disk           ~130 MB
  GPU            Optional (CUDA for accelerated batch decode)
  Internet       Not required

  The portable .exe bundles the Python runtime, all dependencies,
  and the qector-decoder-v3 wheel. No external software is needed.

  Other platforms:
    Linux    glibc >= 2.30 (Ubuntu 20.04+, Debian 11+, Fedora 32+)
    macOS    12+ (arm64 and Intel)


================================================================================
  10. RUNTIME & SELF-HEALING
================================================================================

  The workbench uses a zero-config decoder provisioner:

    1. BUNDLED       The portable .exe ships with an embedded,
                     ABI-matched decoder wheel.

    2. MANAGED SITE  Falls back to a per-user, ABI-partitioned
                     managed site  (decoder_site/<abi_tag>/).

    3. PYPI          If neither is available, downloads the
                     correct wheel from PyPI automatically.

    4. SELF-HEAL     On corruption, re-extracts the bundled
                     wheel and rebuilds the managed site.

  No manual intervention is needed. No internet is required for
  normal operation with the portable build.


================================================================================
  11. DOCUMENTATION
================================================================================

  Included in the  docs/  folder:

    QECTOR_Quick_Start_Guide.pdf          Getting started
    QECTOR_User_Manual_Windows.pdf        Full Windows user guide
    QECTOR_User_Manual_Linux.pdf          Full Linux user guide
    QECTOR_User_Manual_macOS.pdf          Full macOS user guide
    QECTOR_API_Reference.pdf              Complete API reference
    QECTOR_MCP_Integration_Guide.pdf      MCP server setup and usage
    QECTOR_LLM_Manual.json               Machine-readable LLM reference
    architecture.md                       System architecture overview
    api.md                                API reference (Markdown)

  Online:  https://www.qector.store


================================================================================
  12. PERFORMANCE NOTES
================================================================================

  All logical-error-rate, throughput, and latency figures are hardware-,
  driver-, seed-, and workload-dependent simulation results.

  REGENERATE THEM ON YOUR OWN TARGET HARDWARE BEFORE QUOTING.

    *  PyMatching remains the speed leader on standard surface-code MWPM.
    *  QECTOR's exact blossom decoder matches PyMatching's logical error
       rate but is not faster.
    *  Key strengths: batch throughput via approximate Union-Find (higher
       LER trade-off), qLDPC coverage via BP-OSD, and correctness that
       always satisfies H*c = s (mod 2).

  This is a research and evaluation platform, not a real-time or
  fault-tolerant hardware decoding stack.


================================================================================
  13. LICENSE
================================================================================

  WORKBENCH (this application)
  ----------------------------
  Source-available under EULA.txt (included in this package).

  Grants a royalty-free, worldwide license to use, execute, copy, and
  distribute the software for any purpose -- including commercial,
  academic, and personal use -- provided the embedded "QECTOR" notices
  and watermarks are retained (EULA Section 2).

  BACKEND (qector-decoder-v3)
  ----------------------------
  Separately licensed Rust/Python platform by the same author.

    *  FREE for personal, academic, educational, and non-commercial
       research use.

    *  COMMERCIAL USE (company R&D, SaaS, hosted API, OEM, or
       redistribution) requires a paid license.
       See:  https://qector.store/pricing

    *  60-day commercial evaluation available, creditable against
       a full license purchase.

  The workbench depends on qector-decoder-v3 at runtime.
  Honor the backend's license terms for any commercial deployment.


================================================================================
  14. CONTACT & SUPPORT
================================================================================

  Website             https://www.qector.store
  Commercial Sales    admin@qector.store
  Technical Support   contact@qector.store
  Pricing             https://qector.store/pricing

  Author              Guillaume Lessard / iD01t Productions
  ORCID               0009-0000-3465-3753


================================================================================

  QECTOR Decoder Workbench v3.5.1
  Built on qector-decoder-v3 v0.6.9 (Rust/PyO3 core)
  (c) 2026 Guillaume Lessard / iD01t Productions

  Powered by QECTOR.

================================================================================
