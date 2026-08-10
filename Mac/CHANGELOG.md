# Changelog

All notable changes to QECTOR Decoder Workbench are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project uses [Semantic Versioning](https://semver.org/).

The Workbench version line (1.0.x) is independent of the decoder backend
version (`qector-decoder-v3`, currently 1.0.0). The two are released on
separate cadences and must never be assumed to match.

---

## [1.0.0] - 2026-08-06

Release theme: **production-grade v1.0.0 with fully offline backend bundling.**

### Added

- **Offline backend bundling.** The `qector-decoder-v3` v1.0.0 wheel is now
  bundled inside the application. `decoder_provisioner.py` extracts and
  activates it from the bundled wheel on first launch. No PyPI access required.
  The app is fully offline-capable on both Windows and Linux.
- **Platform-specific wheel bundling.** Windows builds include
  `qector_decoder_v3-1.0.0-cp311-cp311-win_amd64.whl`; Linux builds include
  `qector_decoder_v3-1.0.0-cp311-cp311-manylinux_2_17_x86_64.whl`. Both are
  verified with SHA-256 checksums.
- **Full CLI infrastructure.** 12 new subcommands added (`compare`, `batch`,
  `stream`, `train`, `export`, `import`, `matrix`, `serve`, `doctor`,
  `completions`). Global flags: `--output`, `--verbose`, `--quiet`, `--config`,
  `--dry-run`. Shell completions for bash, zsh, and PowerShell.
- **Security hardening.** License keys encrypted at rest with Fernet
  (machine-derived key). Auto-migration of legacy plaintext keys on boot.
  Export path traversal protection (`utils.sanitize_export_path`).
- **MCP server hardening.** Per-tool 60s timeout, busy guard (rejects
  concurrent calls), 1 MB result size limit, SIGTERM/SIGINT graceful drain.
- **4 new MCP tools.** `export_session`, `import_syndrome`, `analyze_logicals`,
  `analyze_error_patterns`. Total tool count: 66.
- **16 additional MCP tools** added in the v1.0.0 backend integration wave
  (`build_dem`, `decode_dem`, `import_stim`, `build_code_from_matrix`,
  `estimate_threshold`, `finite_size_scaling`, `run_ler_benchmark`,
  `generate_parity_check`, `get_license_info`, `generate_reproducibility_package`,
  `export_figure`, `get_server_env`, `decode_hyperedge`, `decode_syndrome_blossom`,
  `decode_syndrome_cascade`, `decode_mmap`). Total tool count: 82.
- **MCP export formats.** `export_benchmark` now supports JSON, CSV, Markdown,
  and HTML.
- **GUI enhancements.** Tab crash recovery (\"Reload Tab\" button), 30s splash
  timeout, DPI awareness, RSS memory monitoring, full keyboard shortcut suite,
  session persistence (`workspace.json`, `preferences.json`).
- **Session persistence.** App state (code family, distance, decoder, error
  rate, seed) is saved to `~/.qector/workspace.json` and restored on launch.
- **New documentation.** `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor
  Covenant v2.1), `SECURITY.md` with coordinated disclosure policy.
- **Input validation.** `build_code` rejects distances outside valid range.
  `run_single_decode` rejects error rates outside [0, 1].
- **Tree synchronization.** `scripts/sync_trees.py` keeps root, `Linux/`, and
  `Mac/` trees byte-identical. Supports dry-run, `--apply`, and `--check` (CI).

### Changed

- **Backend version unified to 1.0.0.** All references to legacy backend 0.7.0
  updated to 1.0.0 across the codebase. `BACKEND_VERSION`, `MIN_BACKEND_VERSION`,
  and all documentation now reference v1.0.0.
- **Distribution format unchanged.** Windows ships as
  `QectorWorkbench-v1.0.0-Windows-x64-Public.zip` (57.5 MB) containing
  `QectorWorkbench-Portable.exe` and the bundled wheel. Linux ships as
  `QectorWorkbench-v1.0.0-Linux-x64-Public.zip` (6.3 MB) containing
  `qector-workbench_1.0.0_amd64.deb` and the bundled wheel.
- **EULA updated to v1.0.0.** All EULA files (root, `winzip/`, `linuxzip/`,
  `Linux/`, `Mac/`) previously v0.5.3, updated to v1.0.0.
- **MCP_TOOLS count updated to 82** (was 66, then increased by backend-integration tools).

### Fixed

- **decoder_provisioner.py indentation bug.** The `if not ok_import:` block
  at lines 456-462 had incorrect indentation, causing the provisioner to
  always return `False` when import verification failed, even when the
  destination was the active site. This could brick upgrades by removing a
  working decoder. Fixed by indenting lines 457-462 one level deeper.
- **pyproject.toml version mismatch.** Was at 0.5.2 with "4 - Beta" status.
  Updated to 1.0.0 with "5 - Production/Stable".
- **pyproject.toml missing modules.** Added `lab_info_tab`, `api_reference`,
  `docs_exporter`, `cli`, `generate_manuals` to `py-modules`.
- **mcp_server.py duplicate definition.** `_options_desc` was defined twice
  at lines 1311-1318 (the first was immediately overwritten). Removed the
  dead code.

### Testing

- All existing tests pass: 438+ passed, 14 skipped, 0 failed.
- New test files: `test_decode_matrix.py`, `test_fuzz.py`,
  `test_corruption_recovery.py`, `test_input_validation.py`,
  `test_path_traversal.py`.
- Frozen MCP verification: 82 tools over both in-process and stdio transports.
- Offline provisioning verified: bundled wheel extraction works without network.

### Changed

- **Backend version unified to 1.0.0.** All references to legacy backend 0.7.0
  updated to 1.0.0 across the codebase. `BACKEND_VERSION`, `MIN_BACKEND_VERSION`,
  and all documentation now reference v1.0.0.
- **Distribution format unchanged.** Windows ships as
  `QectorWorkbench-v1.0.0-Windows-x64-Public.zip` (57.5 MB) containing
  `QectorWorkbench-Portable.exe` and the bundled wheel. Linux ships as
  `QectorWorkbench-v1.0.0-Linux-x64-Public.zip` (6.3 MB) containing
  `qector-workbench_1.0.0_amd64.deb` and the bundled wheel.
- **EULA updated to v1.0.0.** All EULA files (root, `winzip/`, `linuxzip/`,
  `Linux/`, `Mac/`) previously v0.5.3, updated to v1.0.0.

### Fixed

- **decoder_provisioner.py indentation bug.** The `if not ok_import:` block
  at lines 456-462 had incorrect indentation, causing the provisioner to
  always return `False` when import verification failed, even when the
  destination was the active site. This could brick upgrades by removing a
  working decoder. Fixed by indenting lines 457-462 one level deeper.
- **pyproject.toml version mismatch.** Was at 0.5.2 with "4 - Beta" status.
  Updated to 1.0.0 with "5 - Production/Stable".
- **pyproject.toml missing modules.** Added `lab_info_tab`, `api_reference`,
  `docs_exporter`, `cli`, `generate_manuals` to `py-modules`.
- **mcp_server.py duplicate definition.** `_options_desc` was defined twice
  at lines 1311-1318 (the first was immediately overwritten). Removed the
  dead code.

### Testing

- All existing tests pass: 403 passed, 4 skipped, 0 failed.
- Frozen MCP verification: 56 tools over both in-process and stdio transports.
- Offline provisioning verified: bundled wheel extraction works without network.

### Housekeeping

- Removed stale build artifacts and scratch files from repository root.
- All changes mirrored across Windows, `Linux/` and `Mac/` source trees.
- Release bundles built with fresh SHA-256 checksums.

---

## [0.5.3] - 2026-08-04

Release theme: **every documentation button actually works, and what it
produces is fit to deposit.**

### Fixed

- **Four export buttons did nothing.** `pathlib.Path` was used but never
  imported in the Benchmark, Batch and Streaming, Diagnostics and Hardware
  tabs. Each handler caught the resulting `NameError` in a bare
  `except Exception` and only wrote a console line, so the user picked a
  filename and no file appeared. All four now write real files.
- **Decoder Lab "Generate Doc" failed on every click.** It called
  `generator.generate(...)`, which does not exist; the class exposes
  `generate_all()`. It now generates Markdown, HTML and PDF, and reports which
  formats succeeded plus the output folder.
- **Decoder Lab "Quick Export" wrote junk.** With no valid guard it exported
  whatever text was in the result pane, including error messages, under a
  "Decode Report" heading. It now refuses unless a real decode is present.
- **"Generate and Open Folder" opened an empty folder.** Generation runs on a
  worker thread and the folder was opened inline, before any file was written.
  The folder now opens once generation has finished, and not at all when
  generation was refused or failed.
- **Profile saving always claimed success.** `save_lab_info` swallowed every
  exception while the UI reported "Profile saved successfully!" regardless. It
  now returns a real result and the UI shows it.
- **DOCX export produced files Word cannot open.** When `python-docx` was
  missing, the exporter wrote raw Markdown into a `.docx` and reported success.
  That fallback is removed, `python-docx` is now a declared dependency, and a
  genuine failure is reported as one.
- **The licence key field did nothing.** It wrote a plaintext key into a
  profile file that nothing reads, so an Enterprise key left the user on
  Community with no error. It now writes `~/.qector/license.key`, sets
  `QECTOR_LICENSE_KEY`, hands the key to the decoder's own Ed25519 verifier and
  reports the resulting tier.
- **Generated HTML reports called out to Google Fonts on every open**, leaking
  the reader's IP for a font family that is not hosted there. Removed; reports
  render identically offline.
- **`QECTOR_API_Reference.html` was not HTML.** It was the entire Markdown
  source dumped into one unescaped `<pre>`, so any `<`, `>` or `&` in the
  document corrupted the page. It is now a rendered document with headings,
  tables, lists and code blocks, with all literal text escaped.
- **Report exporters could emit broken HTML** when a decoder name or error
  string contained `<`. All four tab exporters now escape before interpolating.
- **`generate_manuals.py` wrote to a hardcoded developer Desktop path**, so it
  failed on any other machine. Mirrors are now opt-in via `--also DIR` or
  `QECTOR_MANUALS_MIRROR`.
- **Release tooling was pinned to old versions.**
  `scripts/build_installer.py` and `scripts/update_release_assets.py` had
  `3.5.1` hardcoded and `installer.iss` had `0.5.2`; all three now derive the
  version from `version.py`. The manifest also reads the MCP tool, decoder and
  code-family counts from the live registry instead of carrying stale numbers
  (it had been shipping 47/13/9 while the code served 56/16/10).
- **`WORKBENCH_VERSION` had been set to the backend's version** (0.7.0),
  which put the wrong number in the window title, the MCP `status` response,
  the generated manuals and the `.deb` package name.

### Added

- **Zenodo deposit support.** Two new output formats: `.zenodo.json` (upload
  and publication type, creators with ORCID and affiliation, keywords, licence,
  access rights, language, version) and `CITATION.cff` (Citation File Format
  1.2.0). Both are record-level, so a deposit carries exactly one of each.
- **Publication-standard document structure.** Generated reports now carry YAML
  front matter (Pandoc and Quarto read it directly), an Abstract, Code
  Parameters, Structural Analysis, Decoder Benchmark, **Methods**, **Data
  Availability**, **How to Cite** and Provenance. The Methods section states
  the seeding scheme, what the latency figure excludes, and that the failure
  fraction at 25 trials is a screening estimate rather than a converged logical
  error rate.
- **Deposit metadata fields** in the Lab and Personal Info tab: ORCID, DOI,
  funding, publisher and extra keywords, plus a live licence-tier readout.
- **HTML section table of contents** with working anchors.
- **Preview tooling** in the Documentation tab: syntax highlighting, font zoom,
  find with match cycling and an "n of m" counter, and a Copy button.
- **Recent export folders**, persisted across sessions and reachable from a
  dropdown.
- **Real progress reporting** during generation, mirrored to the app status bar.
  The readout previously said "Ready" and was never updated again.

### Changed

- **Typographic dashes are purged from every generated artifact.** Em dashes,
  en dashes, figure dashes, horizontal bars, Unicode minus and the
  corresponding HTML entities are replaced at the single write choke point. The
  purge is line-aware: Markdown table rules, YAML fences and LaTeX booktabs
  rules are exempt, indentation is preserved, hyphens inside identifiers such
  as `qector-decoder-v3` are untouched, and JSON payloads stay byte-exact.
- **No fabricated author identity.** The placeholder creator
  ("Dr. Lead Researcher") and placeholder contact address that previously
  shipped in PDF metadata and every report header are gone. Profile fields
  default to empty, and an unset profile renders as "Unattributed" with an
  explicit note in the PDF to set a profile before depositing.
- **Reports default to CC-BY-4.0** with a formatted citation block in every
  format.
- Business contact address is now **admin@qector.store** throughout the
  application, the generated manuals and the Debian package metadata.
- Benchmark export button relabelled from "Export JSON" to "Export Report"
  (it has offered three formats for some time), and the save dialog now
  defaults to the first offered format rather than to JSON.
- Generated JSON sidecar bumped to `schema_version: "1.2"` for the new
  `publication` block, and it now carries `generator_version` alongside
  `generator`.

### Restored

- **The Buy Licence section.** The Documentation tab's Developer and Licensing
  block (Buy Licence, Contact Sales, Website) had been dropped from the UI
  build, leaving the code orphaned and the application with no purchase path.

### Testing

- Suite green: **403 passed, 4 skipped, 0 failed** (0.5.2 shipped with two
  failing GUI tests).
- `test_full_gui_smoke` now accounts for the Lab and Personal Info tab.
- `test_batch_and_streaming_live` no longer fails on a Community licence: GPU
  batch decoding is Enterprise-tier gated, and the test now detects the tier
  refusal and falls back to CPU instead of reporting a decode failure.
- MCP verification: all sections pass, 56 tools over both in-process and stdio
  transports.

### Housekeeping

- Removed build scratch that had leaked into the tree (`frozen_*.txt`,
  `build_*.done`, and a file literally named `=1.24,` created by an unquoted
  pip version specifier) and extended `.gitignore` to cover all three patterns.
- All changes mirrored across the Windows, `Linux/` and `Mac/` source trees.

---

## [0.5.2] - 2026-08-01

Public release. Windows x64 and Linux x64 bundles; backend
`qector-decoder-v3` 0.7.0 with 56 MCP tools, 16 decoders and 10 code families.

Earlier history was tracked under a `3.x` version line and is recorded in
`UPGRADE_NOTES.md` and `RELEASE_REPORT.md`.
