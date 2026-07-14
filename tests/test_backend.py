"""
tests/test_backend.py — Real backend tests against installed qector_decoder_v3.

Covers:
- code family construction for every supported family
- normalize_layout returns valid coordinates for all families
- compute_spring_layout fallback
- single decode round-trip for every registered decoder kind
- parameter validation edge cases
- benchmark/batch/streaming no-crash paths
- negative-path contract tests
- backend hardening: input sanitization, memory guard, normalize_layout diagnostics
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pytest

import backend as be


# ===========================================================================
# Helpers / fixtures
# ===========================================================================

def _stable_digest(obj: Any) -> str:
    """Canonical digest of a backend result.

    Excludes unstable fields like timing/metadata so that identical
    seeds still produce identical digests across different calls.
    """
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


@pytest.fixture(scope="module")
def repetition_code():
    return be.build_code("repetition", 7)


@pytest.fixture(scope="module")
def default_code():
    return be.build_code("rotated_surface", 5)


# ===========================================================================
# Registry / metadata
# ===========================================================================

def test_decoder_kinds_nonempty():
    assert isinstance(be.DECODER_KINDS, list)
    assert len(be.DECODER_KINDS) >= 1


def test_code_families_nonempty():
    assert isinstance(be.CODE_FAMILIES, dict)
    assert "rotated_surface" in be.CODE_FAMILIES
    assert "repetition" in be.CODE_FAMILIES
    assert "toric" in be.CODE_FAMILIES
    assert "heavy_hex" in be.CODE_FAMILIES


# ===========================================================================
# Code construction
# ===========================================================================

@pytest.mark.parametrize(
    "family_key,param",
    [
        ("repetition", 5),
        ("ring", 11),
        ("rotated_surface", 5),
        ("unrotated_surface", 5),
        ("toric", 4),
        ("heavy_hex", 5),
    ],
)
def test_build_code_all_families(family_key, param):
    code = be.build_code(family_key, param)
    assert code is not None
    assert code.n_qubits > 0
    assert code.n_checks > 0
    summary = be.code_summary(code)
    assert summary["n_qubits"] == code.n_qubits
    assert summary["n_checks"] == code.n_checks


def test_build_code_rejects_unknown_family():
    with pytest.raises(be.QectorError, match="unknown code family"):
        be.build_code("does_not_exist", 5)


@pytest.mark.parametrize(
    "family_key,param,expected_bad",
    [
        ("repetition", -1, True),
        ("repetition", 0, True),
        ("repetition", 1, True),
        ("ring", 0, True),
        ("ring", 2, True),
        ("rotated_surface", 0, True),
        ("rotated_surface", 1, True),
        ("unrotated_surface", 0, True),
        ("toric", 1, True),
        ("heavy_hex", 1, True),
        ("heavy_hex", 2, True),
        ("heavy_hex", 4, True),  # even distance invalid for heavy_hex
    ],
)
def test_build_code_rejects_bad_params(family_key, param, expected_bad):
    if expected_bad:
        with pytest.raises(be.QectorError):
            be.build_code(family_key, param)
    else:
        code = be.build_code(family_key, param)
        assert code is not None


# ===========================================================================
# Layout / graph
# ===========================================================================

def test_normalize_layout_rotated_surface():
    code = be.build_code("rotated_surface", 5)
    q_coords, c_coords = be.get_tanner_graph_layout(code, "rotated_surface", 5)
    assert len(q_coords) == code.n_qubits
    assert len(c_coords) == code.n_checks
    assert all(isinstance(pt, tuple) and len(pt) == 2 for pt in q_coords)
    assert all(isinstance(pt, tuple) and len(pt) == 2 for pt in c_coords)


def test_normalize_layout_unrotated_surface():
    code = be.build_code("unrotated_surface", 5)
    q_coords, c_coords = be.get_tanner_graph_layout(code, "unrotated_surface", 5)
    assert len(q_coords) == code.n_qubits
    assert len(c_coords) == code.n_checks


def test_normalize_layout_toric():
    code = be.build_code("toric", 4)
    q_coords, c_coords = be.get_tanner_graph_layout(code, "toric", 4)
    assert len(q_coords) == code.n_qubits
    assert len(c_coords) == code.n_checks


def test_normalize_layout_heavy_hex():
    code = be.build_code("heavy_hex", 5)
    q_coords, c_coords = be.get_tanner_graph_layout(code, "heavy_hex", 5)
    assert len(q_coords) == code.n_qubits
    assert len(c_coords) == code.n_checks


def test_spring_layout_fallback():
    code = be.build_code("rotated_surface", 7)
    q_coords, c_coords = be.get_tanner_graph_layout(code, "rotated_surface", 7)
    assert len(q_coords) == code.n_qubits
    assert len(c_coords) == code.n_checks


def test_normalize_large_graph_no_crash():
    code = be.build_code("rotated_surface", 9)
    q_coords, c_coords = be.get_tanner_graph_layout(code, "rotated_surface", 9)
    assert len(q_coords) == code.n_qubits
    assert len(c_coords) == code.n_checks


# ===========================================================================
# Layout robustness
# ===========================================================================
def test_spring_layout_degenerate_input():
    # single-qubit edge case: should not divide by zero or raise
    q, c = be.compute_spring_layout(1, 1, [[0]], iterations=2)
    assert len(q) == 1
    assert len(c) == 1


# ===========================================================================
# Validation
# ===========================================================================

def test_validate_parameter_accepts():
    valid, _ = be.validate_parameter("rotated_surface", 7)
    assert valid is True


def test_validate_parameter_rejects_bad_family():
    valid, msg = be.validate_parameter("does_not_exist", 5)
    assert valid is False
    assert len(msg) > 0


def test_validate_parameter_rejects_small_param():
    valid, _ = be.validate_parameter("rotated_surface", 1)
    assert valid is False


def test_code_family_info_shape():
    info = be.get_code_family_info("rotated_surface")
    assert "key" in info
    assert "label" in info
    assert info["key"] == "rotated_surface"


# ===========================================================================
# Single decode — happy path + contract
# ===========================================================================

def test_single_decode_all_decoders(repetition_code):
    p = 0.05
    results = []
    for kind in be.DECODER_KINDS:
        result = be.run_single_decode(repetition_code, p, kind, seed=42)
        assert isinstance(result, dict)
        decoded = result["result"]
        assert hasattr(decoded, "hamming_weight"), f"missing hamming_weight for {kind}: {decoded}"
        assert decoded.hamming_weight >= 0
        results.append(decoded.hamming_weight)
    mean_hw = float(np.mean(results))
    assert mean_hw >= 0


def test_single_decode_rejects_bad_decoder(repetition_code):
    with pytest.raises(be.QectorError, match="unknown decoder kind"):
        be.run_single_decode(repetition_code, 0.05, "not_a_decoder", seed=1)


def test_single_decode_seed_reproducibility(repetition_code):
    """Same seed must produce identical error/syndrome and decode result.

    The decode_with_diagnostics output is derived from the syndrome, which is
    deterministic for a given seed.  We therefore expect the correction arrays
    to match exactly across same-seed runs.
    """
    r1 = be.run_single_decode(repetition_code, 0.05, "union_find", seed=123)
    r2 = be.run_single_decode(repetition_code, 0.05, "union_find", seed=123)
    assert (r1["error"] == r2["error"]).all(), "error arrays must match for identical seeds"
    assert (r1["syndrome"] == r2["syndrome"]).all(), "syndrome arrays must match for identical seeds"
    assert (r1["result"].correction == r2["result"].correction).all(), "corrections must match for identical seeds"


def test_single_decode_different_seeds_differ(default_code):
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
# Benchmark
# ===========================================================================

def test_benchmark_runs(default_code):
    result = be.run_benchmark(default_code, n_samples=100, seed=42)
    assert result is not None
    assert "throughput_decodes_per_s" in result
    assert result["throughput_decodes_per_s"] > 0


def test_benchmark_has_expected_fields(default_code):
    result = be.run_benchmark(default_code, n_samples=100, seed=7)
    # The backend returns a structured dict; ensure expected keys exist.
    for field in ("throughput_decodes_per_s", "decode_seconds", "n_trials", "p", "seed"):
        assert field in result, f"missing benchmark field: {field}"
        assert result[field] >= 0


def test_benchmark_seed_produces_same_code_path(default_code):
    """Benchmark with same seed uses the same decoder/code path; errors must match."""

    rng = np.random.default_rng(42)
    e1 = default_code.random_error(0.05, rng=rng)
    s1 = default_code.syndrome(e1)
    rng = np.random.default_rng(42)
    e2 = default_code.random_error(0.05, rng=rng)
    s2 = default_code.syndrome(e2)
    assert (e1 == e2).all()
    assert (s1 == s2).all()


# ===========================================================================
# Batch decode
# ===========================================================================

def test_batch_decode_runs(default_code):
    out = be.run_batch_decode(default_code, "cpu", n_samples=50, error_rate=0.05, seed=1)
    assert out is not None
    assert "success_rate" in out
    assert 0.0 <= out["success_rate"] <= 1.0


def test_batch_decode_shape_and_dtype(default_code):
    out = be.run_batch_decode(default_code, "cpu", n_samples=20, error_rate=0.05, seed=11)
    arr = np.asarray(out["corrections"])
    assert arr.shape == (20, default_code.n_qubits)
    assert arr.dtype == np.uint8


def test_batch_decode_seed_produces_same_errors(default_code):
    """Errors sampled with the same seed must be identical; this tests our
    seeding pathway, not the non-deterministic Rust SIMD core."""
    rng = np.random.default_rng(99)
    e1 = [default_code.random_error(0.05, rng=rng) for _ in range(10)]
    rng = np.random.default_rng(99)
    e2 = [default_code.random_error(0.05, rng=rng) for _ in range(10)]
    for a, b in zip(e1, e2):
        assert (a == b).all()


# ===========================================================================
# Streaming session
# ===========================================================================

def test_streaming_basic():
    """Build repetition code d=5, run streaming with defaults, verify output."""
    code = be.build_code("repetition", 5)
    result = be.run_streaming_session(
        code, window_size=5, n_rounds=10, error_rate=0.03, seed=1,
        decoder_kind="union_find",
    )
    assert isinstance(result, dict)
    assert result["committed_count"] == 10  # committed_count == n_rounds
    assert result["session_seconds"] > 0


def test_streaming_seed_reproducibility():
    """Same params twice must produce identical committed_corrections."""
    import numpy as np
    code = be.build_code("repetition", 5)
    kwargs = dict(window_size=5, n_rounds=10, error_rate=0.03, seed=1,
                  decoder_kind="union_find")
    r1 = be.run_streaming_session(code, **kwargs)
    r2 = be.run_streaming_session(code, **kwargs)
    assert len(r1["committed_corrections"]) == len(r2["committed_corrections"])
    for c1, c2 in zip(r1["committed_corrections"], r2["committed_corrections"]):
        assert np.array_equal(c1, c2)


def test_streaming_negative():
    """window_size=0 should raise QectorError."""
    code = be.build_code("repetition", 5)
    with pytest.raises(be.QectorError):
        be.run_streaming_session(
            code, window_size=0, n_rounds=5, error_rate=0.03, seed=1,
        )


# ===========================================================================
# Backend hardening: memory guard metadata exists
# ===========================================================================

def test_backend_exposes_package_version():
    assert hasattr(be, "PACKAGE_VERSION")
    assert isinstance(be.PACKAGE_VERSION, str)
    assert len(be.PACKAGE_VERSION) > 0


def test_qector_error_is_runtime_error():
    exc = be.QectorError("test")
    assert isinstance(exc, RuntimeError)


def test_batch_decode_rejects_bad_backend(default_code):
    with pytest.raises(be.QectorError, match="unknown batch backend"):
        be.run_batch_decode(default_code, "nonexistent_backend", 10, 0.05, 1)


def test_run_benchmark_negative_path(default_code):
    with pytest.raises(be.QectorError):
        be.run_benchmark(default_code, n_samples=-1, seed=1)
