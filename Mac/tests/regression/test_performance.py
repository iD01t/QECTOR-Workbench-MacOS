"""tests/regression/test_performance.py — Performance regression guard.

Runs a standard benchmark (rotated_surface d=5, blossom, 100 samples) and
compares against a stored JSON baseline.  Flags >30% regression on median
latency or >50% regression on throughput.

The baseline is auto-created on first run.  To update it after an intentional
change, delete ``tests/regression/baseline.json`` and re-run.
"""
import json
import os
import time
from pathlib import Path

import pytest

import backend as be

BASELINE_PATH = Path(__file__).parent / "baseline.json"
FAMILY = "rotated_surface"
DISTANCE = 5
DECODER = "blossom"
ERROR_RATE = 0.05
N_SAMPLES = 100
SEED = 42

# Regression thresholds
LATENCY_REGRESSION_THRESHOLD = 0.30   # 30% slower median latency
THROUGHPUT_REGRESSION_THRESHOLD = 0.50  # 50% lower throughput


def _run_benchmark() -> dict:
    code = be.build_code(FAMILY, DISTANCE)
    start = time.perf_counter()
    result = be.run_benchmark(
        code, N_SAMPLES, SEED, DECODER, ERROR_RATE,
    )
    elapsed = time.perf_counter() - start
    return {
        "median_latency_ms": result.get("latency_p50_ms", elapsed * 1000 / N_SAMPLES),
        "throughput_samples_per_sec": N_SAMPLES / elapsed,
        "logical_error_rate": result.get("logical_error_rate", 0.0),
        "n_samples": N_SAMPLES,
    }


def _load_baseline() -> dict | None:
    if not BASELINE_PATH.exists():
        return None
    try:
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_baseline(data: dict) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


@pytest.mark.skipif(
    os.environ.get("QECTOR_SKIP_PERF") == "1",
    reason="QECTOR_SKIP_PERF=1",
)
def test_performance_regression():
    """Run standard benchmark and compare against stored baseline."""
    current = _run_benchmark()
    baseline = _load_baseline()

    if baseline is None:
        _save_baseline(current)
        pytest.skip(f"No baseline found — created {BASELINE_PATH}")
        return

    # Check latency regression
    base_lat = baseline["median_latency_ms"]
    curr_lat = current["median_latency_ms"]
    if base_lat > 0:
        lat_ratio = (curr_lat - base_lat) / base_lat
        if lat_ratio >= LATENCY_REGRESSION_THRESHOLD:
            msg = (
                f"Latency regression detected: {curr_lat:.2f}ms vs baseline {base_lat:.2f}ms "
                f"({lat_ratio:+.0%}, threshold {LATENCY_REGRESSION_THRESHOLD:+.0%})"
            )
            if os.environ.get("QECTOR_STRICT_PERF") == "1":
                assert lat_ratio < LATENCY_REGRESSION_THRESHOLD, msg
            else:
                import warnings
                warnings.warn(msg, UserWarning)

    # Check throughput regression
    base_tp = baseline["throughput_samples_per_sec"]
    curr_tp = current["throughput_samples_per_sec"]
    if base_tp > 0:
        tp_ratio = (base_tp - curr_tp) / base_tp
        if tp_ratio >= THROUGHPUT_REGRESSION_THRESHOLD:
            msg = (
                f"Throughput regression detected: {curr_tp:.1f}/s vs baseline {base_tp:.1f}/s "
                f"({tp_ratio:+.0%}, threshold {THROUGHPUT_REGRESSION_THRESHOLD:+.0%})"
            )
            if os.environ.get("QECTOR_STRICT_PERF") == "1":
                assert tp_ratio < THROUGHPUT_REGRESSION_THRESHOLD, msg
            else:
                import warnings
                warnings.warn(msg, UserWarning)
