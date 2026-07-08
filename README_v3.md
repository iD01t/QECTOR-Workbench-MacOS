# QECTOR Decoder Workbench v3.4 — Scientific QEC Analysis Suite (Production Ready)

## What this is

QECTOR Decoder Workbench is a scientific desktop application for constructing quantum error correction (QEC) codes, inspecting their parity-check structure, running decoders, benchmarking decode latency, batch-decoding syndrome ensembles, running streaming decoding sessions, and exporting analyzed results.

It is built on `qector-decoder-v3` and surfaces real backend APIs through a CustomTkinter desktop GUI and an optional MCP server bridge.

## Current release surface

- **Desktop GUI**: 7 tabs — Code Explorer, Decoder Lab, Benchmark, Batch & Streaming, Hardware & Routing, Console, Documentation Studio.
- **Real backend wrappers**: `backend.py` is a thin wrapper over the installed `qector_decoder_v3` package. It does not simulate decoders.
- **Documentation export**: Premium 10/10 outputs — modern self-contained HTML, clean MD with TOC, production LaTeX, rich JSON. Full provenance + repro code included.
- **UI/UX**: Professional dark quantum theme, refined controls, high-quality embedded plots, consistent premium card layouts across all tabs.
- **MCP server**: stdio/HTTP bridge exposing real tools for code building, decoding, hardware detection, and doc generation. **25 tools fully tested**.
- **Reproducible packaging**: PyInstaller build spec, GitHub Actions CI, release artifact checksum generation.

## Installation

```bash
python -m pip install --upgrade pip
pip install -e .[dev]
python -m pytest -q
python app.py
```

## MCP Server

... (full details in docs) 

## License

See `EULA.txt`.

**Developer**: Guillaume Lessard © 2026

## Acknowledgments

Built on `qector_decoder_v3`.