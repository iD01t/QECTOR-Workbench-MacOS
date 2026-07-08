# QECTOR Workbench — API Reference (v3.4.0)

> The Workbench also exposes a powerful **MCP Server** (25 tools, all verified) — see `mcp_server.py` and `README_v3.md` for agent/LLM integration details.

**Note**: Source repo is cleaned. Build with `pyinstaller --clean` for production. See .gitignore and UPGRADE_NOTES.md.

## backend.py

### Code families

```python
import backend as be

be.CODE_FAMILIES  # dict[str, CodeFamily]
be.CODE_FAMILIES["rotated_surface"].builder
be.CODE_FAMILIES["rotated_surface"].param_name
be.CODE_FAMILIES["rotated_surface"].default
```

### Decoder kinds

```python
be.DECODER_KINDS  # list[str]
```

### Build code

```python
code = be.build_code("rotated_surface", 5)
```

Returns a real `qector_decoder_v3.codes.Code`.

### Code summary

```python
summary = be.code_summary(code)
# keys: name, n_qubits, n_checks, distance, max_qubit_degree, description
```

### Validate parameter

```python
ok, msg = be.validate_parameter("heavy_hex", 7)
```

### Code family info

```python
info = be.get_code_family_info("rotated_surface")
# keys: key, label, param_name, default, note
```

### Decode

```python
result = be.run_single_decode(code, error_rate=0.05, kind="union_find", seed=42)
# returns dict with keys: error, syndrome, result, explain
# result is qector_decoder_v3.result.DecodeResult
result["result"].hamming_weight
result["result"].syndrome_valid
result["result"].to_dict()
```

### Benchmark

```python
bench = be.run_benchmark(code, n_samples=5000, seed=42)
# keys: latency_mean_us, latency_p50_us, latency_p99_us, latency_min_us, latency_max_us, throughput
```

### Batch decode

```python
out = be.run_batch_decode(code, backend_key="cpu", n_samples=500, error_rate=0.05, seed=1)
# keys: corrections, syndromes, batch_seconds, mean_hamming_weight, success_rate
```

### Streaming decode

```python
out = be.run_streaming_session(code, window_size=5, n_rounds=40, error_rate=0.03, seed=9)
# keys: committed_corrections, committed_syndromes, committed_count, session_seconds
```

### Hardware profile

```python
profile = be.get_hardware_profile()
# attributes: cuda_rust, gpu, cpu_count, ...
```

### Recommendation

```python
rec = be.get_recommendation("rotated_surface", distance=5, n_qubits=25, priority="balanced")
# attributes: decoder, reason, family, priority, batch_size, hardware, gpu_batched_bp
```

## AppState

```python
from state import AppState

state = AppState()
state.on_code_changed(callback)
state.set_code(code, "rotated_surface", 5)
```

## ProfessionalDocGenerator

```python
from doc_generator import ProfessionalDocGenerator

gen = ProfessionalDocGenerator(output_dir=Path("./exports"))
paths_map = gen.generate_all(code, formats=["markdown", "json", "html", "latex", "svg", "pdf"])
# returns dict[str, tuple[bool, Path]]
```
