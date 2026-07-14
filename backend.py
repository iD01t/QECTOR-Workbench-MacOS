"""backend.py — QECTOR Workbench backend wrapping qector_decoder_v3.

Provides a stable, testable API for code construction, decoding,
benchmarking, batch processing, and layout computation.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any, Optional
import numpy as np
import qector_decoder_v3 as qd
from qector_decoder_v3 import codes as _codes

PACKAGE_VERSION = qd.__version__

DECODER_KINDS = [
    "union_find",
    "fast_union_find",
    "blossom",
    "sparse_blossom",
    "bp_osd",
]

CODE_FAMILIES = {
    "repetition": _codes.repetition_code,
    "ring": _codes.ring_code,
    "rotated_surface": _codes.rotated_surface_code,
    "unrotated_surface": _codes.unrotated_surface_code,
    "toric": _codes.toric_code,
    "heavy_hex": _codes.heavy_hex_code,
}

_PARAM_MIN = {
    "repetition": 3,
    "ring": 3,
    "rotated_surface": 3,
    "unrotated_surface": 3,
    "toric": 3,
    "heavy_hex": 3,
}


class QectorError(RuntimeError):
    """Raised for invalid operations in the QECTOR backend."""


def build_code(family_key: str, param: int):
    """Build a code from a family and parameter (distance)."""
    if family_key not in CODE_FAMILIES:
        raise QectorError(f"unknown code family {family_key!r}")
    try:
        return CODE_FAMILIES[family_key](param)
    except Exception as e:
        raise QectorError(str(e)) from e


def code_summary(code) -> dict[str, Any]:
    """Return a summary dict for a code object.

    Always contains ``n_qubits`` and ``n_checks``.  Additionally contains
    ``name``, ``distance``, ``description`` and ``max_qubit_degree`` when the
    corresponding attribute exists on the code object (bound methods such as
    ``max_qubit_degree`` are called to obtain their value).
    """
    summary: dict[str, Any] = {"n_qubits": code.n_qubits, "n_checks": code.n_checks}
    for attr in ("name", "distance", "description", "max_qubit_degree"):
        if not hasattr(code, attr):
            continue
        try:
            value = getattr(code, attr)
            if callable(value):
                value = value()
        except Exception:
            continue
        summary[attr] = value
    return summary


def validate_parameter(family_key: str, param: int) -> tuple[bool, str]:
    """Validate a code family parameter (distance)."""
    if family_key not in CODE_FAMILIES:
        return False, f"unknown code family {family_key!r}"
    min_param = _PARAM_MIN.get(family_key, 3)
    if param < min_param:
        return False, f"param {param} too small for {family_key} (min {min_param})"
    if family_key in ("ring",) and param < 3:
        return False, f"param {param} too small for ring (min 3)"
    try:
        CODE_FAMILIES[family_key](param)
        return True, ""
    except Exception as e:
        return False, str(e)


def get_code_family_info(family_key: str) -> dict[str, str]:
    """Return metadata about a code family."""
    labels = {
        "repetition": "Repetition Code",
        "ring": "Ring Code",
        "rotated_surface": "Rotated Surface Code",
        "unrotated_surface": "Unrotated Surface Code",
        "toric": "Toric Code",
        "heavy_hex": "Heavy Hex Code",
    }
    return {"key": family_key, "label": labels.get(family_key, family_key)}


def _decoder_class(kind: str):
    """Return the decoder class for a given kind string."""
    mapping = {
        "union_find": qd.UnionFindDecoder,
        "fast_union_find": qd.FastUnionFindDecoder,
        "blossom": qd.BlossomDecoder,
        "sparse_blossom": qd.SparseBlossomDecoder,
        "bp_osd": qd.BPOSDDecoder,
    }
    if kind not in mapping:
        raise QectorError(f"unknown decoder kind {kind!r}")
    return mapping[kind]


def get_decoder_info(kind: str) -> dict[str, str]:
    """Return human-readable info about a decoder kind."""
    descriptions = {
        "union_find": "Union-Find — fast approximate decode; higher LER than exact MWPM. "
                      "Best as a throughput/triage lever, not a universal decoder.",
        "fast_union_find": "Fast Union-Find — optimized Union-Find hot path; approximate, "
                           "higher LER than exact MWPM. Regenerate LER on your target workload.",
        "blossom": "Blossom — weight-optimal exact MWPM. Reaches PyMatching's logical error "
                   "rate on tested surface-code workloads but is not faster than PyMatching.",
        "sparse_blossom": "Sparse Blossom — region-growing, near-optimal matching (experimental); "
                          "NOT exact. Use Blossom for exact minimum-weight matching.",
        "bp_osd": "BP-OSD — belief propagation + ordered-statistics decoding for LDPC / "
                  "quantum-LDPC codes that graphlike matching cannot decode (experimental).",
    }
    return {"name": kind, "description": descriptions.get(kind, "Unknown decoder")}


def get_compatible_decoders(code) -> list[dict[str, str]]:
    """Return decoder info for all decoders compatible with this code."""
    return [get_decoder_info(k) for k in DECODER_KINDS]


def _make_decoder(kind: str, checks) -> Any:
    """Create a decoder instance for the given kind."""
    cls = _decoder_class(kind)
    try:
        return cls(checks)
    except Exception as e:
        raise QectorError(f"failed to construct {kind} decoder: {e}") from e


def _logicals_matrix(code) -> Optional[np.ndarray]:
    """Return the code's logical-operator matrix as a 2-D integer ndarray.

    ``logicals_matrix`` is exposed by qector_decoder_v3 as a bound method that
    may return None (e.g. toric / unrotated surface codes in 0.6.6).  Returns
    None whenever a usable 2-D non-empty matrix cannot be obtained.
    """
    attr = getattr(code, "logicals_matrix", None)
    if attr is None:
        return None
    try:
        raw = attr() if callable(attr) else attr
        if raw is None:
            return None
        arr = np.asarray(raw)
    except Exception:
        return None
    if arr.ndim != 2 or arr.size == 0 or arr.dtype == object:
        return None
    return arr.astype(np.int64, copy=False)


def _logical_failure(logicals: np.ndarray, error, correction) -> bool:
    """Logical-failure test per the workbench contract.

    residual = (error + correction) % 2;
    failure  = any((logicals_matrix @ residual) % 2 != 0).
    """
    residual = (np.asarray(error, dtype=np.int64) + np.asarray(correction, dtype=np.int64)) % 2
    return bool(np.any((logicals @ residual) % 2 != 0))


def get_tanner_graph_layout(code, family: str, distance: int) -> tuple[list, list]:
    """Return qubit and check coordinates for Tanner graph layout."""
    try:
        return compute_spring_layout(code.n_qubits, code.n_checks, code.parity_check_matrix(), iterations=100)
    except Exception:
        return compute_spring_layout(code.n_qubits, code.n_checks, None, iterations=30)


def compute_spring_layout(n_qubits: int, n_checks: int, check_matrix, iterations: int = 100) -> tuple[list, list]:
    """Simple spring-layout fallback for Tanner graph."""
    n = n_qubits + n_checks
    adj = np.zeros((n, n), dtype=float)
    try:
        mat = np.asarray(check_matrix.todense() if hasattr(check_matrix, "todense") else check_matrix)
    except Exception:
        mat = np.zeros((n_checks, n_qubits), dtype=float)
    if mat.ndim == 2 and mat.shape[0] and mat.shape[1]:
        rows, cols = np.nonzero(mat)
        adj[n_qubits + rows, cols] = 1.0
        adj[cols, n_qubits + rows] = 1.0

    rng = np.random.default_rng(0)
    pos = rng.uniform(-1, 1, (n, 2)).astype(float)
    adj_bool = adj > 0
    for _ in range(min(iterations, 50)):
        force = np.zeros_like(pos)
        for i in range(n):
            delta = pos[i] - pos
            d = np.maximum(np.linalg.norm(delta, axis=1), 1e-8)
            mask_a = adj_bool[i].copy()
            mask_a[i] = False
            mask_r = ~mask_a
            mask_r[i] = False
            f_attr = np.where(mask_a[:, np.newaxis], -delta / d[:, np.newaxis] * 0.01, 0.0)
            f_rep = np.where(mask_r[:, np.newaxis], delta / (d[:, np.newaxis] ** 2 + 1e-8) * 0.001, 0.0)
            force[i] = f_attr.sum(axis=0) + f_rep.sum(axis=0)
        pos += force
        np.clip(pos, -5, 5, out=pos)

    q_coords = [(float(pos[i, 0]), float(pos[i, 1])) for i in range(n_qubits)]
    c_coords = [(float(pos[n_qubits + i, 0]), float(pos[n_qubits + i, 1])) for i in range(n_checks)]
    return q_coords, c_coords


def run_single_decode(code, error_rate: float, decoder_kind: str, seed: int) -> dict[str, Any]:
    """Run a single decode on a code with a random error.

    Returns {"error": ndarray, "syndrome": ndarray, "result": _DecodeResult}
    where the result carries the correction, its Hamming weight, whether the
    correction reproduces the observed syndrome, and whether the residual
    (error + correction) % 2 flips any logical operator (None when the code
    exposes no usable logicals matrix).
    """
    if decoder_kind not in DECODER_KINDS:
        raise QectorError(f"unknown decoder kind {decoder_kind!r}")
    decoder = _make_decoder(decoder_kind, code.check_to_qubits)
    rng = np.random.default_rng(seed)
    try:
        error = code.random_error(error_rate, rng=rng)
        syndrome = code.syndrome(error)
        correction = decoder.decode(syndrome)
        syndrome_valid = bool(np.array_equal(np.asarray(code.syndrome(correction)), np.asarray(syndrome)))
    except Exception as e:
        raise QectorError(f"single decode failed: {e}") from e
    logicals = _logicals_matrix(code)
    logical_failure = _logical_failure(logicals, error, correction) if logicals is not None else None
    return {
        "error": error,
        "syndrome": syndrome,
        "result": _DecodeResult(correction, syndrome_valid, logical_failure),
    }


class _DecodeResult:
    """Structured result of a single decode."""

    def __init__(self, correction, syndrome_valid: bool, logical_failure: Optional[bool]):
        self.correction = correction
        self.syndrome_valid = bool(syndrome_valid)
        self.logical_failure = None if logical_failure is None else bool(logical_failure)

    @property
    def hamming_weight(self) -> int:
        return int(np.sum(self.correction))

    def to_dict(self) -> dict:
        return {
            "correction": np.asarray(self.correction).tolist(),
            "hamming_weight": self.hamming_weight,
            "syndrome_valid": self.syndrome_valid,
            "logical_failure": self.logical_failure,
        }


def run_benchmark(
    code,
    n_samples: int = 1000,
    seed: int = 42,
    decoder_kind: str = "union_find",
    error_rate: float = 0.05,
) -> dict[str, Any]:
    """Run a decode benchmark on the given code.

    Samples ``n_samples`` i.i.d. errors at rate ``error_rate`` with a single
    seeded generator, decodes each syndrome with the chosen decoder while
    timing every decode individually (perf_counter), and reports throughput,
    latency statistics (mean/p50/p99/min/max in microseconds), the fraction of
    corrections that reproduce the sampled syndrome, and the logical error
    rate (None when the code exposes no usable logicals matrix).
    """
    if n_samples < 1:
        raise QectorError("n_samples must be >= 1")
    if decoder_kind not in DECODER_KINDS:
        raise QectorError(f"unknown decoder kind {decoder_kind!r}")
    p = float(error_rate)
    decoder = _make_decoder(decoder_kind, code.check_to_qubits)
    rng = np.random.default_rng(seed)
    try:
        errors = [code.random_error(p, rng=rng) for _ in range(n_samples)]
        syndromes = np.array([code.syndrome(e) for e in errors], dtype=np.uint8)
        corrections: list[np.ndarray] = []
        latencies_s = np.empty(n_samples, dtype=float)
        t0 = time.perf_counter()
        for i in range(n_samples):
            t_start = time.perf_counter()
            corrections.append(decoder.decode(syndromes[i]))
            latencies_s[i] = time.perf_counter() - t_start
        elapsed = time.perf_counter() - t0
        match_count = sum(
            1
            for s, c in zip(syndromes, corrections)
            if np.array_equal(np.asarray(code.syndrome(c), dtype=np.uint8), s)
        )
    except Exception as e:
        raise QectorError(f"benchmark failed: {e}") from e
    logicals = _logicals_matrix(code)
    if logicals is None:
        logical_error_rate: Optional[float] = None
    else:
        failure_count = sum(1 for e, c in zip(errors, corrections) if _logical_failure(logicals, e, c))
        logical_error_rate = failure_count / n_samples
    latencies_us = latencies_s * 1e6
    return {
        "throughput_decodes_per_s": n_samples / max(elapsed, 1e-9),
        "decode_seconds": elapsed,
        "n_trials": n_samples,
        "p": p,
        "seed": seed,
        "method": decoder_kind,
        "backend": "cpu",
        "latency_mean_us": float(np.mean(latencies_us)),
        "latency_p50_us": float(np.percentile(latencies_us, 50)),
        "latency_p99_us": float(np.percentile(latencies_us, 99)),
        "latency_min_us": float(np.min(latencies_us)),
        "latency_max_us": float(np.max(latencies_us)),
        "syndrome_match_rate": match_count / n_samples,
        "logical_error_rate": logical_error_rate,
    }


def _make_batch_decoder(backend: str, checks) -> Any:
    """Create the batch decoder for a validated backend name.

    Routes "cuda"/"opencl" to CUDABatchDecoder/OpenCLBatchDecoder; when the
    corresponding availability probe reports False the request fails loudly
    with QectorError — there is no silent CPU fallback.
    """
    factory: Any
    if backend == "cuda":
        if not _backend_available(qd.cuda_is_available):
            raise QectorError(
                "cuda backend unavailable on this machine (qector_decoder_v3 reports no usable "
                "CUDA device/driver); select backend='cpu' instead"
            )
        factory = qd.CUDABatchDecoder
    elif backend == "opencl":
        if not _backend_available(qd.opencl_is_available):
            raise QectorError(
                "opencl backend unavailable on this machine (qector_decoder_v3 reports no usable "
                "OpenCL runtime); select backend='cpu' instead"
            )
        factory = qd.OpenCLBatchDecoder
    else:
        factory = qd.CPUBatchDecoder
    try:
        return factory(checks)
    except Exception as e:
        raise QectorError(f"failed to initialise {backend} batch decoder: {e}") from e


def _backend_available(probe) -> bool:
    """Return the boolean result of an availability probe, False on any error."""
    try:
        return bool(probe())
    except Exception:
        return False


def run_batch_decode(code, backend: str = "cpu", n_samples: int = 100, error_rate: float = 0.05, seed: int = 1) -> dict[str, Any]:
    """Run a batch decode on the given code.

    Samples ``n_samples`` errors with one seeded generator, batch-decodes
    their syndromes on the requested backend ("cpu", "cuda" or "opencl") and
    returns corrections (uint8, shape [n_samples, n_qubits]), the sampled
    syndromes, the syndrome-match success rate, the logical error rate (None
    when the code exposes no usable logicals matrix), the mean correction
    Hamming weight, the wall-clock batch time and the backend actually used.
    """
    valid_backends = {"cpu", "cuda", "opencl"}
    if backend not in valid_backends:
        raise QectorError(f"unknown batch backend {backend!r}")
    if n_samples < 1:
        raise QectorError("n_samples must be >= 1")
    decoder = _make_batch_decoder(backend, code.check_to_qubits)
    rng = np.random.default_rng(seed)
    try:
        errors = [code.random_error(error_rate, rng=rng) for _ in range(n_samples)]
        syndromes = np.array([code.syndrome(e) for e in errors], dtype=np.uint8)
        t0 = time.perf_counter()
        corrections = decoder.batch_decode(syndromes)
        batch_seconds = time.perf_counter() - t0
        corrections = np.asarray(corrections, dtype=np.uint8)
        success_count = sum(
            1
            for s, c in zip(syndromes, corrections)
            if np.array_equal(np.asarray(code.syndrome(c), dtype=np.uint8), s)
        )
    except QectorError:
        raise
    except Exception as e:
        raise QectorError(f"{backend} batch decode failed: {e}") from e
    logicals = _logicals_matrix(code)
    if logicals is None:
        logical_error_rate: Optional[float] = None
    else:
        failure_count = sum(1 for e, c in zip(errors, corrections) if _logical_failure(logicals, e, c))
        logical_error_rate = failure_count / n_samples
    return {
        "corrections": corrections,
        "syndromes": syndromes,
        "success_rate": success_count / n_samples,
        "logical_error_rate": logical_error_rate,
        "mean_hamming_weight": float(np.mean(np.sum(corrections, axis=1, dtype=np.int64))),
        "batch_seconds": batch_seconds,
        "n_samples": n_samples,
        "backend_used": backend,
    }


def run_streaming_session(
    code,
    window_size: int = 5,
    n_rounds: int = 10,
    error_rate: float = 0.03,
    seed: int = 1,
    decoder_kind: str = "union_find",
) -> dict[str, Any]:
    """Run a sliding-window streaming decode session.

    Semantics (single-shot code-capacity model): for each round r in
    range(n_rounds), sample error e_r with rng — one numpy default_rng(seed)
    created once for the whole session; compute syndrome s_r; decode s_r with
    the chosen decoder producing correction c_r; push (e_r, c_r) into a FIFO
    window of size ``window_size``.  When a round leaves the window it is
    committed (its correction is final).  The window is flushed at session
    end, so committed_count == n_rounds.  logical_error_rate is computed over
    committed rounds via the code's logicals matrix (None when unavailable).
    The session is timed with perf_counter and is reproducible: the same seed
    yields identical committed corrections.

    Returns a dict with committed_corrections (list of uint8 ndarrays),
    committed_count, rounds, window_size, session_seconds and
    logical_error_rate.
    """
    if window_size < 1:
        raise QectorError("window_size must be >= 1")
    if n_rounds < 0:
        raise QectorError("n_rounds must be >= 0")
    if decoder_kind not in DECODER_KINDS:
        raise QectorError(f"unknown decoder kind {decoder_kind!r}")
    decoder = _make_decoder(decoder_kind, code.check_to_qubits)
    logicals = _logicals_matrix(code)
    rng = np.random.default_rng(seed)
    window: deque[tuple[np.ndarray, np.ndarray]] = deque()
    committed_corrections: list[np.ndarray] = []
    failure_count = 0

    def _commit(entry: tuple[np.ndarray, np.ndarray]) -> None:
        nonlocal failure_count
        error, correction = entry
        committed_corrections.append(np.array(correction, dtype=np.uint8, copy=True))
        if logicals is not None and _logical_failure(logicals, error, correction):
            failure_count += 1

    t0 = time.perf_counter()
    try:
        for _ in range(n_rounds):
            error = code.random_error(error_rate, rng=rng)
            syndrome = code.syndrome(error)
            correction = decoder.decode(syndrome)
            window.append((error, correction))
            if len(window) > window_size:
                _commit(window.popleft())
        while window:
            _commit(window.popleft())
    except Exception as e:
        raise QectorError(f"streaming session failed: {e}") from e
    session_seconds = time.perf_counter() - t0
    if logicals is None:
        logical_error_rate: Optional[float] = None
    else:
        logical_error_rate = failure_count / len(committed_corrections) if committed_corrections else 0.0
    return {
        "committed_corrections": committed_corrections,
        "committed_count": len(committed_corrections),
        "rounds": n_rounds,
        "window_size": window_size,
        "session_seconds": session_seconds,
        "logical_error_rate": logical_error_rate,
    }
