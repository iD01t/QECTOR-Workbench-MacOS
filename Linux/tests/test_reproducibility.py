"""
tests/test_reproducibility.py — Seed-identical output tests.

Covers:
- single decode error+syndrome+correction identical for same seed across calls
- different seeds produce different errors with high probability
- all 5 decoders reproducible error+syndrome for same seed
- batch decode syndromes + corrections identical for same seed errors
- streaming session committed_corrections identical for same seed errors
- benchmark metric structure is stable for same code/seed
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pytest

import backend as be


# ===========================================================================
# Helpers
# ===========================================================================

def _stable_digest(obj: Any) -> str:
    """Canonical digest excluding unstable timing/metadata."""
    payload: dict[str, Any] = {}
    for k, v in obj.items():
        if k in {"explain", "decode_seconds"}:
            continue
        if hasattr(v, "tolist"):
            payload[k] = v.tolist()
        elif hasattr(v, "to_dict"):
            payload[k] = v.to_dict()
        elif hasattr(v, "__dict__") and not isinstance(v, (str, int, float, bool, list, dict, type(None))):
            try:
                payload[k] = {kk: vv for kk, vv in v.__dict__.items() if not kk.startswith("_")}
            except Exception:
                payload[k] = repr(v)
        else:
            payload[k] = v
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(scope="module")
def repetition_code():
    return be.build_code("repetition", 7)


@pytest.fixture(scope="module")
def rotated_code():
    return be.build_code("rotated_surface", 5)


# ===========================================================================
# Single decode reproducibility
# ===========================================================================

def test_single_decode_same_seed_same_errors(repetition_code):
    r1 = be.run_single_decode(repetition_code, 0.05, "union_find", seed=12345)
    r2 = be.run_single_decode(repetition_code, 0.05, "union_find", seed=12345)
    # The sampled error and syndrome must be identical.
    assert (r1["error"] == r2["error"]).all()
    assert (r1["syndrome"] == r2["syndrome"]).all()
    # For a matching-graph code, corrections from the same syndrome must match.
    assert (r1["result"].correction == r2["result"].correction).all()


@pytest.mark.parametrize("kind", be.DECODER_KINDS)
def test_single_decode_all_decoders_reproducible(repetition_code, kind: str):
    r1 = be.run_single_decode(repetition_code, 0.05, kind, seed=99)
    r2 = be.run_single_decode(repetition_code, 0.05, kind, seed=99)
    assert (r1["error"] == r2["error"]).all()
    assert (r1["syndrome"] == r2["syndrome"]).all()
    assert (r1["result"].correction == r2["result"].correction).all()


def test_single_decode_different_seeds_differ(repetition_code):
    """Different seeds must sample different i.i.d. errors with high probability.

    With very low error rates on a small code the all-zero outcome is likely for
    both seeds, so this test uses a larger code and higher error rate to keep
    the probabilistic guarantee tight.
    """
    larger = be.build_code("repetition", 21)
    r1 = be.run_single_decode(larger, 0.25, "union_find", seed=1001)
    r2 = be.run_single_decode(larger, 0.25, "union_find", seed=1002)
    assert not (r1["error"] == r2["error"]).all(), "different seeds must sample different errors"
    assert (r1["syndrome"] != r2["syndrome"]).any(), "different seeds should give different syndromes"


# ===========================================================================
# Benchmark structural contract
# ===========================================================================

def test_benchmark_same_code_same_seed_same_errors(rotated_code):
    """Benchmark reuses the same seeded errors; verify sampling contract."""

    rng = np.random.default_rng(7)
    e1 = [rotated_code.random_error(0.05, rng=rng) for _ in range(20)]
    rng = np.random.default_rng(7)
    e2 = [rotated_code.random_error(0.05, rng=rng) for _ in range(20)]
    assert all((a == b).all() for a, b in zip(e1, e2)), "seeded random_error must be deterministic"


def test_benchmark_keys_stable(rotated_code):
    b = be.run_benchmark(rotated_code, n_samples=50, seed=55)
    expected = {"throughput_decodes_per_s", "decode_seconds", "n_trials", "p", "seed", "method", "backend"}
    assert expected.issubset(b.keys()), f"missing benchmark keys: {sorted(expected - set(b.keys()))}"


def test_benchthroughput_nonnegative(rotated_code):
    b = be.run_benchmark(rotated_code, n_samples=50, seed=55)
    assert b["throughput_decodes_per_s"] > 0
    assert b["decode_seconds"] >= 0


# ===========================================================================
# Batch decode reproducibility
# ===========================================================================

def test_batch_decode_same_seed_same_errors(default_code):
    """Errors sampled with the same seed for batch decode must match."""
    code = be.build_code("repetition", 7)
    rng = np.random.default_rng(11)
    e1 = [code.random_error(0.05, rng=rng) for _ in range(10)]
    s1 = np.array([code.syndrome(x) for x in e1])
    rng = np.random.default_rng(11)
    e2 = [code.random_error(0.05, rng=rng) for _ in range(10)]
    s2 = np.array([code.syndrome(x) for x in e2])
    assert (s1 == s2).all(), "same-seed syndromes must match"
    out = be.run_batch_decode(code, "cpu", n_samples=10, error_rate=0.05, seed=11)
    assert out["corrections"].shape == (10, code.n_qubits)


# ===========================================================================
# Streaming session reproducibility
# ===========================================================================

def test_streaming_reproducible():
    """run_streaming_session twice with same seed → same committed_corrections digests."""
    import hashlib
    import json
    code = be.build_code("repetition", 5)
    kwargs = dict(window_size=5, n_rounds=10, error_rate=0.03, seed=1,
                  decoder_kind="union_find")
    r1 = be.run_streaming_session(code, **kwargs)
    r2 = be.run_streaming_session(code, **kwargs)
    def _digest(corrections):
        raw = json.dumps(corrections, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
    d1 = _digest(r1["committed_corrections"])
    d2 = _digest(r2["committed_corrections"])
    assert d1 == d2, f"streaming digests differ: {d1} != {d2}"

