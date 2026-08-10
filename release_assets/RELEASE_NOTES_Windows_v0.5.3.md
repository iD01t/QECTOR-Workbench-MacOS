# QECTOR Decoder Workbench v0.5.3 — Windows x64

Portable Windows build running the qector-decoder-v3 0.7.0 backend. Single-executable distribution, no installer.

## Assets in this release

- **QectorWorkbench-Portable.exe** — the application; bundles its own Python runtime, scientific stack, and the decoder wheel below
- **qector_decoder_v3-0.7.0-cp311-cp311-win_amd64.whl** — the exact decoder wheel bundled inside the portable exe, included standalone for reference
- **manuals/** — API Reference (MD + HTML + PDF), MCP Integration Guide, Quick Start Guide, Windows User Manual, Extended/Reference decoder docs, and a machine-readable LLM manual
- **EULA.txt**

## Install

No installer, no admin rights, no internet connection required.

1. Download `QectorWorkbench-Portable.exe`.
2. Double-click to launch.

For the headless MCP server:

```
QectorWorkbench-Portable.exe --mcp     # 56-tool stdio MCP server (no display needed)
```

Runtime data (logs, exported documents) is written to `%LOCALAPPDATA%\QectorWorkbench` (override with `QECTOR_DATA_DIR`).

## What's in this release

- **16 decoders**, **10 code families** (including qLDPC bicycle/bivariate_bicycle and colour codes), fully wired to the bundled qector-decoder-v3 0.7.0 backend
- **56-tool MCP server** (stdio JSON-RPC 2.0) for programmatic and agent access
- **8 GUI tabs**: Code Explorer, Decoder Lab, Benchmark, Batch & Streaming, Hardware, Diagnostics, Documentation Studio, Lab & Personal Info — plus a live Console
- **Self-Diagnostics & Auto-Debug** tab: full environment/decoder/hardware self-test, per-decoder probe, and resilient decode with automatic multi-decoder fallback (verifying `H·c == s` at every step with a full attempt trace)
- **Lab & Personal Info** tab: deposit profile (author, ORCID, affiliation, DOI, funding, keywords) for generated reports, plus decoder licence-key install with live tier readout
- **Hardware Dashboard**: auto-detects CUDA/OpenCL/CPU; honest OpenCL reporting (names *why* it's unavailable, not just "N/A"); `QECTOR_DISABLE_OPENCL=1` skip-probe escape hatch now actually works
- **SHA-256 on every data export**: all documentation exports (MD/HTML/JSON/LaTeX/PDF/SVG/Zenodo/CITATION.cff), benchmark reports, batch/streaming reports, diagnostics reports, and hardware reports now write a real SHA-256 checksum manifest or sidecar alongside the artifact
- **Distance slider** supports d3–d63 (matching the Enterprise tier's `max_distance=63`); benchmark tab d3–d21
- **Documentation export** in Markdown, HTML, JSON, LaTeX, PDF, SVG, plus `.zenodo.json` and `CITATION.cff` deposit sidecars — 8 formats with a five-figure publication suite
- **Fully self-contained**: bundles its own Python runtime, the scientific stack, and the qector_decoder_v3 wheel. On first launch the bundled wheel activates into a per-user managed site automatically. No online update checks — the app runs entirely from what ships in the box

## Verify your download

SHA-256 checksums for every file in the Windows zip:

```
70e5804948de41b25e8e67532116b6f3389fe2da8c3126a11d2d90b5f3dc494a  QectorWorkbench-Portable.exe
9c86b3d8dd58eea835d139ba0b0e0d5ee31d123e047a85071b90eb672bebf6ba  qector_decoder_v3-0.7.0-cp311-cp311-win_amd64.whl
94603350cb13fc9e18c037f9309140569a3f074de90b10d55e82c262ce88e2da  QectorWorkbench-v0.5.3-Windows-x64-Public.zip
4e1cbe370f871a9083741d190cd504b54928b250e385489de78f62b0accd066d  EULA.txt
b076436aa680a990c9f219e06a411d6efd844b689cfcfec5dd5e2b8b24d75578  README.md
96a827ab55917cd44ed1f08e67175450a87baf04f557f0d0a0478d0626913619  manuals/QECTOR_API_Reference.md
db8ba55b11cd74424062872423f97bf108447680ba30edba0f06382732763ab8  manuals/QECTOR_API_Reference.pdf
0e4133a65f7ca104e4eb6737d2a88df270a78a79b3b661c07e6787c0e37e81ec  manuals/QECTOR_API_Reference.html
d5dc26c1c84216f9b9681ba46a932c6d8336d73c5eccca64ce0690b06a0c2775  manuals/QECTOR_LLM_Manual.json
4939e5512a316dad503065c74a0560bb9286217ea247898f27c8611d4d1b9e58  manuals/QECTOR_MCP_Integration_Guide.pdf
ac8b683fcf5e63efcb0b91d89d0cfbb4164514a76c77235757b964b61e363fe2  manuals/QECTOR_Quick_Start_Guide.pdf
9e22c6282dd21983f512e19dce9b52054a8dedf65c30d0e5afaea423672129cc  manuals/QECTOR_User_Manual_Windows.pdf
d2507f674e7cb1ec67dc4c7614fa275249f0eff97415122973bfea195487bb6c  manuals/QECTOR Decoder v3 - Extended Reference (package only).md
d2507f674e7cb1ec67dc4c7614fa275249f0eff97415122973bfea195487bb6c  manuals/QECTOR Decoder v3 - Reference (package only).md
d52ee2b92229e13a4f41bd7ffa4125cbbf7c07b4f78a5a3ac3e235b7630faa4f  manuals/README.txt
```

On Windows PowerShell:

```powershell
Get-FileHash <file> -Algorithm SHA256
```

Or verify the whole zip against its checksum:

```powershell
(Get-FileHash QectorWorkbench-v0.5.3-Windows-x64-Public.zip -Algorithm SHA256).Hash.ToLower()
# should print: 94603350cb13fc9e18c037f9309140569a3f074de90b10d55e82c262ce88e2da
```

Full documentation: see the repository README.
