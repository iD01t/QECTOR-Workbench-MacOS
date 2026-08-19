# QECTOR Decoder Workbench v1.0.1 - Linux

The Linux release is a portable, air-gapped application. It includes the
decoder wheel locally and never downloads packages or contacts an external
service at runtime.

## Portable AppImage

```bash
chmod +x QectorWorkbench-1.0.1-x86_64.AppImage
./QectorWorkbench-1.0.1-x86_64.AppImage
```

The AppImage contains the GUI, CLI, MCP server, documentation generators, and
the local decoder wheel. The first launch activates the wheel in a local
per-user directory; it does not use PyPI.

## Verification

```bash
./QectorWorkbench-1.0.1-x86_64.AppImage --cli --json entra status
./QectorWorkbench-1.0.1-x86_64.AppImage --cli --json compliance
./QectorWorkbench-1.0.1-x86_64.AppImage --mcp
```

Expected Entra state is `disabled` with `airgapped: true`. Expected compliance
state is `compliant: true` with an active egress guard.

## Local Data

Runtime state is stored under the platform data directory. Override it with
`QECTOR_DATA_DIR` when a lab policy requires an explicitly managed location.
No cloud synchronization, telemetry, update check, or browser action is
performed by the application.

## Hardware Measurements

Benchmark results are not included in the release. Run benchmarks locally on
the target machine when hardware-specific measurements are required.

## Support Files

- `EULA.txt` - license terms
- `manuals/` - current user, API, MCP, and quick-start manuals
- `checksums-sha256.txt` - release integrity manifest
