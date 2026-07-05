# QECTOR Decoder Workbench v3.1: Professional Quantum Error Correction Analysis Suite

**Professional Quantum Error Correction Analysis Suite**

[![CI](https://github.com/GuillaumeLessard/qector-decoder/actions/workflows/CI.yml/badge.svg)](https://github.com/GuillaumeLessard/qector-decoder/actions/workflows/CI.yml) [![PyPI](https://img.shields.io/pypi/v/qector-decoder-v3.svg)](https://pypi.org/project/qector-decoder-v3/) [![Python](https://img.shields.io/pypi/pyversions/qector-decoder-v3.svg)](https://pypi.org/project/qector-decoder-v3/) [![License](https://img.shields.io/badge/License-Source_Available-blue)](LICENSE)

> Next-generation professional-grade platform for exploring, decoding, benchmarking, and analyzing quantum error correction codes with enterprise features, beautiful documentation export, and production-ready infrastructure.

## What's New in v3.1

### Core Enhancements
- **Professional Documentation Generation**: Export to Markdown, HTML, LaTeX, and JSON with clean, publication-ready styling
- **Persistent Settings and Configuration**: Full user preferences system with JSON config
- **Result Tracking and History**: Complete operation log with statistics and one-click export
- **Built-in Help System**: Contextual documentation accessible directly from the UI
- **Comprehensive Logging**: All actions logged to file with rotation and crash reports
- **Input Validation and Error Recovery**: Robust handling with user-friendly messages

### UI/UX Improvements
- Professional header with status indicator and quick-access buttons
- Enhanced console with log export, clear history, and improved formatting
- Dedicated Settings and Help dialogs
- Refined layout, spacing, and visual hierarchy
- Clearer error reporting throughout the application

### Developer and Infrastructure
- Structured logging to `logs/qector.log` plus timestamped crash reports
- Modern Python type hints throughout
- Local result caching for performance
- Clean modular architecture: config.py, logger.py, results_tracker.py, doc_generator.py, dialogs.py

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the application
python main.py
```

On first launch the workbench automatically creates:
- `~/.qector/.qector_config.json`
- `logs/` directory with rotation support
- `.cache/` for results

## Quick Start

1. Launch the app. Hardware is auto-detected when enabled in settings.
2. Go to the Code Explorer tab, choose a code family, configure parameters, then click Build Code.
3. Generate professional documentation in any format: Markdown, HTML, LaTeX, or JSON.
4. Use Decoder Lab, Benchmark, or Batch and Streaming tabs for deeper analysis.
5. Access Settings and Help directly from the header.

## Features by Tab

### Code Explorer
Professional code exploration and documentation:
- Families supported: Repetition, Ring, Rotated/Unrotated Surface, Toric, Heavy-hex
- Real-time parameter validation
- Code generation powered by qector_decoder_v3
- One-click export to Markdown, HTML, LaTeX, or JSON. Files are saved in the exports folder.

### Decoder Lab
Interactive single-syndrome decoding and diagnostics:
- Multiple decoder algorithms available
- Configurable error rate and reproducible random seed
- Detailed decode results with full tracking

### Benchmark
Performance and latency profiling:
- Adjustable sample sizes
- Native Rust-backed throughput measurements
- Results automatically cached and exportable

### Batch and Streaming
High-volume and real-time workflows:
- Batch Decode: CPU, CUDA, and OpenCL backends with success-rate tracking
- Streaming Session: Sliding-window multi-round decoding with live syndrome injection

### Hardware and Routing
Intelligent system detection and recommendations:
- Auto-detects CPU, CUDA, GPU, memory, and Python environment
- AI-powered decoder suggestion engine. Optimize for speed, accuracy, or balanced priority.

## Settings and Preferences

Open via the gear icon in the header. All settings persist across sessions.

| Category   | Key Options                                      |
|------------|--------------------------------------------------|
| UI         | Dark/light theme, auto hardware detection        |
| Behavior   | Logging toggle, log level, auto-open exports     |
| Defaults   | Error rate, batch size, random seed              |
| Export     | Default formats and output directory             |

Configuration file location: `~/.qector/.qector_config.json`

## File Organization

```
~/.qector/
├── .qector_config.json
├── logs/
│   ├── qector.log
│   └── crash_TIMESTAMP.log
├── .cache/
│   └── results.json
└── exports/
    └── code_doc files
```

## Logging and Diagnostics

- In-app Console: Real-time colored output
- File Log: logs/qector.log (rotating)
- Crash Reports: logs/crash_TIMESTAMP.log with complete traceback
- Export any console session with the Save Log button

## Scripting and API

Full backend access for automation and custom workflows:

```python
import backend as be

# Build a quantum error correction code
code = be.build_code('rotated_surface', 5)

# Get human-readable summary
summary = be.code_summary(code)

# Run a single decode
result = be.run_single_decode(code, error_rate=0.05, decoder='union_find', seed=42)

# Performance benchmark
bench = be.run_benchmark(code, samples=5000, seed=42)

# High-volume batch decode
batch = be.run_batch_decode(code, backend='cpu', batch_size=500, error_rate=0.05, seed=42)
```

## Troubleshooting

Missing qector_decoder_v3 module:
```bash
pip install -r requirements.txt
```

CUDA backend unavailable:
Install NVIDIA drivers and CUDA toolkit. The workbench automatically falls back to CPU.

Console not refreshing:
Click inside the application window or check logs/qector.log for details.

Missing icons:
Restart the app. Ensure Pillow is installed.

## System Requirements

- Python 3.8 or higher
- RAM: 2 GB minimum (4 GB+ recommended)
- Disk space: approximately 200 MB for logs and cache
- GPU: Optional. CUDA 11.0+ enables accelerated batch decoding

## Version History

- v3.1 (2026-07-05): Professional upgrade featuring multi-format documentation export, persistent settings, structured logging, result tracking, and refined UI/UX
- v3.0: Major infrastructure and professional tooling release
- v2.0: Expanded feature set
- v1.0: Initial release

## License

Source-available under the terms in EULA.txt.
Free for personal, academic, and non-commercial research use.
Commercial and OEM licensing available on request.

Developer: Guillaume Lessard 2026

## Acknowledgments

Built on the powerful qector_decoder_v3 quantum error correction library.

QECTOR Decoder Workbench v3.1: Professional Quantum Error Correction Analysis Suite
```
