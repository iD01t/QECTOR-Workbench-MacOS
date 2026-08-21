"""Local benchmark smoke test.

Benchmark numbers are hardware-dependent and are never stored or shipped.
This test validates only that a local benchmark completes with sane fields.
"""
import math
import os
import time

import pytest

import backend as be

FAMILY = "rotated_surface"
DISTANCE = 5
DECODER = "blossom"
ERROR_RATE = 0.05
N_SAMPLES = 100
SEED = 42


def _run_benchmark() -> dict:
    code = be.build_code(FAMILY, DISTANCE)
    start = time.perf_counter()
    result = be.run_benchmark(code, N_SAMPLES, SEED, DECODER, ERROR_RATE)
    elapsed = time.perf_counter() - start
    return {
        "median_latency_ms": result.get("latency_p50_ms", elapsed * 1000 / N_SAMPLES),
        "throughput_samples_per_sec": N_SAMPLES / elapsed,
        "logical_error_rate": result.get("logical_error_rate", 0.0),
        "n_samples": N_SAMPLES,
    }


@pytest.mark.skipif(
    os.environ.get("QECTOR_SKIP_PERF") == "1",
    reason="QECTOR_SKIP_PERF=1",
)
def test_local_benchmark_has_sane_output():
    result = _run_benchmark()
    assert result["n_samples"] == N_SAMPLES
    assert math.isfinite(result["median_latency_ms"])
    assert result["median_latency_ms"] >= 0
    assert math.isfinite(result["throughput_samples_per_sec"])
    assert result["throughput_samples_per_sec"] > 0
    assert 0 <= result["logical_error_rate"] <= 1
