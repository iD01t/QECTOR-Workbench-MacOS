# QECTOR Decoder Workbench v3.1 — Professional QEC Analysis Suite

## Welcome to the Next Generation of QECTOR

Welcome to **QECTOR Decoder Workbench v3** — a complete professional-grade quantum error correction analysis platform. This application has been comprehensively upgraded with enterprise-level features, professional documentation, and production-ready infrastructure.

## What's New in v3

### ✨ Core Enhancements

- **📊 Professional Documentation Generation**: Export code analysis in Markdown, HTML, LaTeX, and JSON formats with beautiful styling
- **⚙️ Settings Management**: Persistent user preferences and configuration system
- **📋 Result Tracking**: Complete history of all operations with statistics and export
- **🔍 Help System**: Built-in documentation accessible from the UI
- **📝 Comprehensive Logging**: All actions logged to file for debugging and auditing
- **💾 Configuration Persistence**: User settings saved between sessions

### 🎨 UI/UX Improvements

- **Professional Header**: Better layout with status indicator and quick access buttons
- **Enhanced Console**: Export logs, clear history, better formatting
- **Settings Dialog**: Customize behavior, defaults, and preferences
- **Help Dialog**: Quick access to feature documentation
- **Better Error Messages**: User-friendly error reporting
- **Improved Layout**: Better spacing and organization

### 🛠️ Developer Features

- **Comprehensive Logging**: Debug log file at `logs/qector.log`
- **Crash Reporting**: Detailed crash logs with full traceback
- **Input Validation**: All user inputs validated before processing
- **Type Hints**: Modern Python type annotations throughout
- **Error Recovery**: Graceful handling of failures
- **Results Caching**: Local JSON cache for performance

### 📦 New Infrastructure Modules

| Module | Purpose |
|--------|---------|
| `config.py` | Centralized configuration management |
| `logger.py` | Professional logging system with rotation |
| `utils.py` | Common utilities and helpers |
| `results_tracker.py` | Operation result tracking |
| `doc_generator.py` | Multi-format documentation export |
| `dialogs.py` | Professional dialog windows |

## Getting Started

### Installation

```bash
# Install/update dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### First Run

1. The application will auto-create configuration files
2. Hardware will be auto-detected (if enabled in settings)
3. Logs will be created in the `logs/` directory
4. Configuration saved to `.qector_config.json`

## Features Guide

### Code Explorer Tab

**Explore quantum error correction codes with professional documentation.**

1. **Select a Code Family**
   - Repetition code
   - Ring code
   - Rotated/Unrotated surface codes
   - Toric code
   - Heavy-hex code

2. **Set Parameters**
   - Each family has specific parameter constraints
   - Validation ensures valid parameters

3. **Build Code**
   - Real code generation from qector_decoder_v3
   - Summary displays key properties

4. **Generate Documentation**
   - ✓ Markdown - Clean readable format
   - ✓ HTML - Beautiful web-viewable docs
   - ✓ JSON - Structured data export
   - ✓ LaTeX - Academic publishing format
   - Files saved to `exports/` directory

### Decoder Lab Tab

**Test individual syndromes and decoders interactively.**

- Select decoder algorithm
- Set physical error rate
- Choose random seed for reproducibility
- View decode results and diagnostics
- Result tracked and saved

### Benchmark Tab

**Performance testing and latency analysis.**

- Run latency benchmarks
- Configurable sample size
- Get throughput statistics
- Real Rust-native measurements
- Results exported and cached

### Batch & Streaming Tab

**Process multiple syndromes efficiently.**

- **Batch Decode**: Decode many syndromes in parallel
  - CPU backend (always available)
  - CUDA backend (if GPU present)
  - OpenCL backend (if available)
  - Track success rate and performance

- **Streaming Session**: Multi-round decoding
  - Sliding window decoder
  - Real-time error correction
  - Multiple rounds of syndrome injection

### Hardware & Routing Tab

**System detection and decoder recommendations.**

- **Hardware Detection**
  - CPU info
  - CUDA support detection
  - GPU availability
  - Memory info
  - Python version

- **Decoder Recommendation**
  - Input code family and parameters
  - Get optimal decoder suggestion
  - Choose priority (speed/accuracy/balanced)
  - AI-powered recommendation engine

## Advanced Features

### Settings & Preferences

Click **⚙️** in the header to access settings:

- **UI Preferences**
  - Theme mode (dark/light)
  - Auto-detect hardware on startup

- **Behavior**
  - Enable/disable logging
  - Set log level (DEBUG/INFO/WARNING/ERROR)
  - Auto-open exported files

- **Defaults**
  - Default error rate
  - Default batch size
  - Default seed

- **Export**
  - Default formats
  - Export directory
  - Auto-open exports

### Result Export

From any tab's results, export to:
- **CSV**: Spreadsheet-compatible format
- **JSON**: Machine-readable structured data
- **HTML**: Beautiful web-viewable documents
- **LaTeX**: Academic paper format

### Help System

Click **?** in the header to access:
- Feature overview for each tab
- Quick usage tips
- Best practices

### Logging System

All actions automatically logged to:
- **Console**: Real-time colored output in the app
- **File**: `logs/qector.log` (rotates at 50MB)
- **Crashes**: `logs/crash_TIMESTAMP.log` (detailed traceback)

Export console logs using the "Save Log" button.

## File Organization

```
~/.qector/
├── .qector_config.json    # User configuration
├── logs/
│   ├── qector.log         # Main application log
│   └── crash_*.log         # Crash reports
├── .cache/
│   └── results.json       # Cached operation results
└── exports/
    └── code_doc.*         # Exported documentation
```

## Configuration File

Edit `~/.qector_config.json` to customize:
- Window size and position
- Default parameters
- Export formats
- Logging level
- Hardware detection
- And more...

Example:
```json
{
  "theme_mode": "dark",
  "default_error_rate": 0.05,
  "default_batch_size": 500,
  "enable_logging": true,
  "log_level": "INFO"
}
```

## Keyboard Shortcuts

(Keyboard shortcuts infrastructure ready for expansion)

- **Ctrl+Q**: Quit application
- **Ctrl+Shift+E**: Export results
- **Ctrl+L**: Clear console
- More shortcuts coming in future versions

## Error Handling

If an error occurs:
1. Check the console output for error message
2. Review `logs/qector.log` for details
3. Check `logs/crash_*.log` if app crashed
4. Report issues with crash log details

## Performance Tips

1. **Batch Operations**: Use batch decoding for multiple syndromes
2. **Caching**: Results are automatically cached locally
3. **Hardware**: GPU backends available if CUDA/OpenCL installed
4. **Memory**: Old results cleaned up automatically (100 max)

## System Requirements

- **Python**: 3.8 or higher
- **RAM**: 2GB minimum, 4GB+ recommended
- **Disk**: 200MB for logs and cache
- **GPU**: Optional - CUDA 11.0+ for accelerated decoding

## Troubleshooting

### Missing Dependencies
```
Error: No module named 'qector_decoder_v3'
Solution: pip install -r requirements.txt
```

### CUDA Not Available
- Install NVIDIA drivers and CUDA toolkit
- Batch decoding will fall back to CPU

### Icon Display Issues
- App will work without icons, just restart
- Ensure PIL/Pillow is installed: `pip install Pillow`

### Console Not Updating
- Try clicking in the app to focus it
- Check logs/qector.log for issues

## Advanced Usage

### Command Line Help
```bash
python main.py --help     # Future: command-line options
```

### Log Levels
Set in settings or config:
- **DEBUG**: Verbose output, all details
- **INFO**: Standard logging
- **WARNING**: Only warnings and errors
- **ERROR**: Only errors

### Result Analysis
Export results to JSON and analyze programmatically:
```python
import json
with open('exports/results.json') as f:
    results = json.load(f)
# Analyze results...
```

## API Documentation

Core functions available for scripting:

```python
import backend as be

# Build a code
code = be.build_code('rotated_surface', 5)

# Get code summary
summary = be.code_summary(code)

# Run single decode
result = be.run_single_decode(code, 0.05, 'union_find', seed=42)

# Run benchmark
bench = be.run_benchmark(code, 5000, seed=42)

# Batch decode
batch = be.run_batch_decode(code, 'cpu', 500, 0.05, seed=42)
```

## FAQ

**Q: How do I export my results?**
A: Use the export buttons in each tab, or the "Save Log" button for console output.

**Q: Can I use different error rates?**
A: Yes! Set defaults in Settings dialog, or override per-operation in each tab.

**Q: Does it work on Linux/Mac?**
A: Yes! The app is cross-platform. Install Python 3.8+ and follow standard install steps.

**Q: How do I report bugs?**
A: Include the crash log from `logs/crash_*.log` if available, and `logs/qector.log`.

**Q: Can I use my own decoder?**
A: The qector_decoder_v3 backend provides the decoders. Custom decoders coming in future versions.

## Support & Contact

- **Report Issues**: Include crash logs and steps to reproduce
- **Feature Requests**: Describe use case and expected behavior
- **Questions**: Check Help dialog and documentation first

## Version History

- **v3.0** (2026-07-04): Complete professional upgrade
  - Configuration system
  - Logging infrastructure
  - Multi-format documentation
  - Settings dialog
  - Result tracking
  - Professional UI/UX

- **v2.0**: Previous release with basic features
- **v1.0**: Initial release

## License

See EULA.txt for full license terms.

**Developer**: Guillaume Lessard © 2026

## Acknowledgments

Built on top of the excellent **qector_decoder_v3** library.

---

**QECTOR Decoder Workbench v3** — Professional Quantum Error Correction Analysis Suite

*Your gateway to understanding and analyzing quantum error correction codes.*