# QECTOR Decoder Workbench v1.0.0 — Production Release Report

**Date:** 2026-08-06
**Version:** 1.0.0 (`WORKBENCH_VERSION`)
**Backend:** `qector_decoder_v3` 1.0.0 (minimum supported 1.0.0)
**Platforms shipped:** Windows x64, Linux x64

> The Workbench version line (1.0.x) is independent of the decoder backend line
> (1.0.x); they release on separate cadences. This is the first production-grade
> release with fully offline backend bundling.

---

## 1. Verification results

Every row was run on 2026-08-06 against this tree. Nothing is carried forward
from a previous report.

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `pytest tests/` | **403 passed, 4 skipped, 0 failed** |
| MCP server | `python test_mcp_all.py` | **ALL SECTIONS PASS** — 82 tools, in-process + stdio round-trip |
| Frozen MCP | `python verify_frozen_mcp.py` | **PASS** — 82 tools over the wire, `serverInfo.version` = 1.0.0, clean EOF exit 0 |
| Frozen decoder | `QectorWorkbench-Portable.exe --decoder-selftest` | **OK 1.0.0** |
| Document generation | 8 formats on `rotated_surface d=3` | **8/8 written**, 0 typographic dashes in any rendered artifact |
| Official docs export | `docs_exporter.export_public_docs` | **15/15 artifacts**, DOCX valid (ZIP magic), 2.0 s |
| Debian package | `dpkg-deb --build` | **built** — `qector-workbench_1.0.0_amd64.deb`, Version 1.0.0, Maintainer admin@qector.store |
| Offline provisioning | Bundled wheel extraction | **PASS** — decoder activates from bundled wheel without network |

---

## 2. What ships

| Artifact | Size | SHA-256 |
|----------|------|---------|
| `QectorWorkbench-v1.0.0-Windows-x64-Public.zip` | 57.5 MB | `4b0e7fe6717bcfede43fa7f626dcd0bd03d3ab297c59cc8fc3b098fc84d4a738` |
| `QectorWorkbench-v1.0.0-Linux-x64-Public.zip` | 6.3 MB | `736fb317b3b29db2102d244ab94d80c7fd554184a03f6fd894805ea12b4788ec` |
| `QectorWorkbench-Portable.exe` | 54.2 MB | `0a398f78e065dde0c7c8e4a8e51e093f7b8503f63d0a943c36329ed18fe1900c` |
| `qector-workbench_1.0.0_amd64.deb` | 2.4 MB | `027e55c73a41bf61f4ddf1e1ab2f81cdcb700521d418af1389a03e634b064398` |

The Windows bundle carries the portable executable **and** the
`qector_decoder_v3` 1.0.0 wheel. The executable embeds the wheel and provisions
it into a per-user managed site on first launch, so a lab machine with no
network runs the full workbench. The Linux bundle carries the `.deb` package
and the manylinux wheel for offline provisioning.

**Bundled wheels:**
- Windows: `qector_decoder_v3-1.0.0-cp311-cp311-win_amd64.whl` (SHA-256: `7f198c7d9ca8f28c461f907d2ec4f41464198446abc2239c894b550bce7d4f98`)
- Linux: `qector_decoder_v3-1.0.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` (SHA-256: `9ee1da96e08e6e841e6d8768a830e253c229380e41454f26971d8bd4cc385575`)

**Deliberately not shipped:** a Windows installer, a Linux AppImage, a macOS
`.app`. macOS requires a build on Apple hardware; see
`.github/workflows/build-macos.yml`.

---

## 3. Capability inventory

| Dimension | Count | Source of truth |
|-----------|-------|-----------------|
| MCP tools | **82** | live `_ToolRegistry`, matches `version.MCP_TOOLS` |
| Decoders | **16** | `backend.DECODER_KINDS` |
| Code families | **10** | `backend.CODE_FAMILIES` |
| GUI tabs | **8** plus a live Console | `app._TAB_SPECS` |
| Document formats | **8** | Markdown, JSON, HTML, LaTeX, PDF, SVG, `.zenodo.json`, `CITATION.cff` |
| Root modules | 35 | `*.py` at repo root |
| Test modules | 11 | `tests/test_*.py` |

**Decoders:** `union_find`, `fast_union_find`, `blossom`, `sparse_blossom`,
`bp_osd`, `auto`, `hybrid`, `lookup_table`, `predecoded`, `auto_router`,
`hybrid_cascade`, `gnn_belief_matching`, `belief_matching`, `two_stage`,
`ambiguity_cluster`, `colour_code`.

**Code families:** `repetition`, `ring`, `rotated_surface`, `unrotated_surface`,
`toric`, `heavy_hex`, `bicycle`, `bivariate_bicycle`, `hypergraph_product`,
`color_code`.

**GUI tabs:** Code Explorer, Decoder Lab, Benchmark, Batch & Streaming, Hardware,
Diagnostics, Documentation, Lab & Personal Info, plus the Console.

---

## 4. Changes in this release

Full detail in `CHANGELOG.md`. Summary:

**Added** — Fully offline backend bundling. The `qector-decoder-v3` v1.0.0 wheel
is now bundled inside the application. `decoder_provisioner.py` extracts and
activates it from the bundled wheel on first launch. No PyPI access required.
The app is fully offline-capable on both Windows and Linux.

**Fixed** — Critical `decoder_provisioner.py` indentation bug (lines 456-462)
that could brick upgrades by always returning `False` when import verification
failed, even when the destination was the active site. Fixed legacy `pyproject.toml`
version (previously 0.5.2 → 1.0.0) and status (Beta → Production/Stable). Added missing
modules to `py-modules`. Removed duplicate `_options_desc` in `mcp_server.py`.

**Changed** — All version strings unified to 1.0.0 across root, `Linux/`, and
`Mac/` trees. Backend version previously 0.7.0, unified to 1.0.0. EULA updated to
v1.0.0. Distribution format unchanged (Windows zip + Linux zip).

**Housekeeping** — Removed 60+ stale build log files and scratch files from
repository root. All changes mirrored across platform trees.

---

## 5. Known limitations

- **macOS is not built.** 1.0.0 is Windows and Linux. macOS requires Apple
  hardware or a GitHub Actions macOS runner.
- **GPU decoding is Enterprise-tier gated.** On a Community licence
  `cuda_is_available()` can report a usable device while the backend still
  refuses the batch. The tier readout in the Lab & Personal Info tab shows the
  real entitlement.
- **OpenCL is unavailable in the shipped decoder build**, which carries no
  OpenCL kernels. The Hardware tab distinguishes "this build ships no OpenCL"
  from "this machine has no OpenCL device" rather than reporting a bare failure.
- **Logical failure fractions in generated reports are screening estimates.**
  25 trials per decoder resolves to 1/25 = 0.04; the figures state this limit
  on the plot so a zero bar is not read as "never fails".

---

**Status: release-ready. All local quality gates green on Windows; the Linux
package builds and validates.**

*Workbench v1.0.0 · Backend `qector_decoder_v3` 1.0.0 · 82 MCP tools ·
17 decoders · 10 code families · Fully offline-capable.*
