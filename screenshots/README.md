# QECTOR Decoder Workbench — Landing Page Asset Manifest

All screenshots were captured from the **real v1.0.1 release artifacts** (Windows EXE source tree,
Linux AppImage on the Ubuntu VM, plus official PDF manuals). No mockups or edited images.

## gui-windows/ — Desktop GUI (Windows, 1280x820 window, 1366x748 captures)

| File | Tab | Content shown |
|---|---|---|
| 01-code-explorer.png | Code Explorer | rotated_surface d=5 parity-check matrix + Tanner graph built |
| 02-decoder-lab.png | Decoder Lab | sparse_blossom decode run (seed 42) with correction result |
| 03-benchmark.png | Benchmark | repetition d=7 throughput benchmark, 200 samples |
| 04-batch-streaming.png | Batch & Streaming | batch/streaming decode workflow panel |
| 05-history.png | History | decode session history |
| 06-hardware.png | Hardware | CPU / GPU / acceleration detection (OpenCL) |
| 07-diagnostics.png | Diagnostics | full self-diagnostics run |
| 08-documentation.png | Documentation | code-family manual generation (MD/HTML/PDF/JSON) |
| 09-lab-info.png | Lab & Personal Info | license / lab metadata |
| 10-console.png | Console | embedded output console |

## cli-mcp/ — Command-Line & MCP (rendered terminal captures of real output)

| File | Command / Session | Output shown |
|---|---|---|
| cli-01-version.png | `qector version` | workbench + backend versions, update status |
| cli-02-list-codes.png | `qector list-codes` | all supported quantum code families |
| cli-03-list-decoders.png | `qector list-decoders` | all decoder engines (blossom, BP-OSD, union-find, …) |
| cli-04-decode.png | `qector decode --family rotated_surface --distance 5 --decoder blossom` | decode statistics + correction verification |
| cli-05-benchmark.png | `qector benchmark --family repetition --distance 7 --samples 100` | throughput, latency, logical error rate |
| cli-06-probe.png | `qector probe --family rotated_surface --distance 3` | per-decoder probe summary |
| cli-07-compare.png | `qector compare --family rotated_surface --distance 5` | cross-decoder comparison table |
| cli-08-diagnostics.png | `qector diagnostics` | system self-diagnostics report |
| cli-09-hardware.png | `qector hardware` | hardware detection & acceleration info |
| cli-10-compliance.png | `qector compliance` | zero-egress / offline compliance attestation |
| cli-11-matrix.png | `qector matrix` | full decoder/code compatibility matrix |
| cli-12-docgen.png | `qector docgen --family rotated_surface --param 5` | manual generation (MD/HTML/PDF/JSON) |
| cli-13-mcp.png | `qector --mcp` | MCP stdio session: initialize, tools/list (85 tools), tools/call decode_single |

## docs/ — Official PDF manuals (rendered at 160% from the shipped PDFs)

| File | Source PDF | Pages |
|---|---|---|
| docs-01-user-manual-windows-p1..3.png | QECTOR_User_Manual_Windows.pdf | cover + TOC + content |
| docs-02-api-reference-p1..3.png | QECTOR_API_Reference.pdf | cover + TOC + content |
| docs-03-mcp-guide-p1..3.png | QECTOR_MCP_Integration_Guide.pdf | cover + content |
| docs-04-quick-start-p1..3.png | QECTOR_Quick_Start_Guide.pdf | cover + content |
| docs-05-code-sheet-p1..3.png | rotated_surface d=5 generated code sheet (docgen) | code stats + parity matrix |

## linux/ — Linux AppImage on Ubuntu (Xvfb, real release artifact, keyboard-driven tabs)

| File | Tab | Notes |
|---|---|---|
| linux-01-code-explorer.png | Code Explorer | default view |
| linux-02-decoder-lab.png | Decoder Lab | decode run (Ctrl+R) |
| linux-03-benchmark.png | Benchmark | benchmark run (Ctrl+B) |
| linux-04-batch-streaming.png | Batch & Streaming | tab view |
| linux-05-history.png | History | tab view |
| linux-06-hardware.png | Hardware | hardware refresh (F5) |
| linux-07-diagnostics.png | Diagnostics | tab view |
| linux-08-documentation.png | Documentation | doc generation (Ctrl+D) |
| linux-09-lab-info.png | Lab & Personal Info | tab view |
| linux-10-console.png | Console | tab view |

## Re-capturing

- Windows GUI: `python test_venv\Scripts\python.exe capture_pages.py`
- CLI/MCP + PDFs: `python test_venv\Scripts\python.exe capture_cli.py`
- Linux AppImage: run `capture_linux.sh` on the Ubuntu VM (needs xvfb, openbox, xdotool, imagemagick)