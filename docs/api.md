# QECTOR Workbench — API Reference (v3.5.0)

> The Workbench also exposes a powerful **MCP Server** (29 tools, all verified) — see `mcp_server.py` and `README_v3.md` for agent/LLM integration details.

## backend.py

### Code families

```python
import backend as be

be.CODE_FAMILIES  # dict[str, callable]
# Keys: "repetition", "ring", "rotated_surface", "unrotated_surface", "toric", "heavy_hex"
```

### Decoder kinds

```python
be.DECODER_KINDS  # list[str]
# Values: "union_find", "fast_union_find", "blossom", "sparse_blossom", "bp_osd"
```

### Build code

```python
code = be.build_code("rotated_surface", 5)
```

Returns a real `qector_decoder_v3.codes.Code`.

### Code summary

```python
summary = be.code_summary(code)
# Returns dict with keys: n_qubits, n_checks, and optional: name, distance, description, max_qubit_degree
```

### Validate parameter

```python
ok, msg = be.validate_parameter("heavy_hex", 5)
```

### Code family info

```python
info = be.get_code_family_info("rotated_surface")
# Returns dict with keys: key, label
```

### Decode

```python
result = be.run_single_decode(code, error_rate=0.05, decoder_kind="union_find", seed=42)
# returns dict with keys: error, syndrome, result
# result is an instance of _DecodeResult with attributes: correction, syndrome_valid, logical_failure, hamming_weight
result["result"].hamming_weight
result["result"].syndrome_valid
result["result"].logical_failure
result["result"].to_dict()
```

### Benchmark

```python
bench = be.run_benchmark(code, n_samples=1000, seed=42, decoder_kind="union_find", error_rate=0.05)
# returns dict with keys: throughput_decodes_per_s, decode_seconds, n_trials, p, seed, method, backend,
# latency_mean_us, latency_p50_us, latency_p99_us, latency_min_us, latency_max_us, syndrome_match_rate, logical_error_rate
```

### Batch decode

```python
out = be.run_batch_decode(code, backend="cpu", n_samples=100, error_rate=0.05, seed=1)
# returns dict with keys: corrections, syndromes, success_rate, logical_error_rate, mean_hamming_weight, batch_seconds, n_samples, backend_used
```

### Streaming decode

```python
out = be.run_streaming_session(code, window_size=5, n_rounds=10, error_rate=0.03, seed=1, decoder_kind="union_find")
# returns dict with keys: committed_corrections, committed_count, rounds, window_size, session_seconds, logical_error_rate
```

## hardware_routing.py

### Detect Hardware

```python
import hardware_routing as hr

profile = hr.detect_hardware()
# Returns HardwareProfile instance with attributes: cuda_rust (bool), gpu (str|None), opencl (bool), opencl_device (str|None)
```

### Recommend Decoder

```python
rec = hr.recommend(code_family="rotated_surface", distance=5, n_qubits=25, priority="balanced")
# Returns Recommendation instance with attributes: decoder (str), reason (str), family (str|None), priority (str), batch_size (int), hardware (str), gpu_batched_bp (bool)
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
from pathlib import Path

gen = ProfessionalDocGenerator(output_dir=Path("./exports"))
paths_map = gen.generate_all(code, formats=["markdown", "json", "html", "latex", "pdf", "svg"])
# returns dict[str, tuple[bool, Path]]
```
