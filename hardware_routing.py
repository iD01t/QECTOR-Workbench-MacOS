"""
hardware_routing.py - local replacement for qector_decoder_v3.routing.

The installed qector_decoder_v3 wheel (v0.5.9) no longer ships a
'routing' submodule -- backend.py was written against an older package
build (v0.5.8) that had it. Rather than depend on a private package
internal that has since been removed, this module reimplements the two
pieces of surface area the app actually needs (HardwareProfile,
Recommendation, detect_hardware(), recommend()) directly on top of the
current, real, public API: qector_decoder_v3.cuda_is_available() /
opencl_is_available().

No fabricated benchmark numbers are used here. The recommendation logic
is a plain, documented heuristic derived from the decoder docstrings
shipped in the installed package (Blossom/SparseBlossom = highest
accuracy MWPM family; UnionFind/FastUnionFind = highest throughput,
~3x higher LER than Blossom; batch decode should prefer CUDA > OpenCL
> CPU when available).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import qector_decoder_v3 as qec


@dataclass(frozen=True)
class HardwareProfile:
    """Detected hardware/backends relevant to decode routing."""

    cuda_rust: bool
    gpu: Optional[str] = None
    opencl: bool = False
    opencl_device: Optional[str] = None


@dataclass(frozen=True)
class Recommendation:
    """A decoder recommendation for a given code / priority."""

    decoder: str
    reason: str
    family: Optional[str]
    priority: str
    batch_size: int
    hardware: str
    gpu_batched_bp: bool


def detect_hardware() -> HardwareProfile:
    """Detect real GPU/CUDA/OpenCL availability via the installed package."""
    cuda = bool(qec.cuda_is_available())
    opencl = bool(qec.opencl_is_available())

    gpu_name: Optional[str] = None
    if cuda:
        gpu_name = _safe_device_name("cuda")

    opencl_name: Optional[str] = None
    if opencl:
        opencl_name = _safe_device_name("opencl")

    return HardwareProfile(cuda_rust=cuda, gpu=gpu_name, opencl=opencl, opencl_device=opencl_name)


def _safe_device_name(kind: str) -> Optional[str]:
    """Best-effort device name probe; a tiny 1-qubit decoder is enough to
    read .device_name without doing any real decode work."""
    try:
        if kind == "cuda":
            dec = qec.CUDABatchDecoder([[0]], 1)
        else:
            dec = qec.OpenCLBatchDecoder([[0]], 1)
        return str(dec.device_name)
    except Exception:
        return None


# Decoders in accuracy order (best LER first) per the installed package's
# own docstrings (Blossom/SparseBlossom = exact MWPM; UnionFind family
# trades accuracy for raw speed).
_ACCURACY_ORDER = ["blossom", "sparse_blossom", "bp_osd", "fast_union_find", "union_find"]
_SPEED_ORDER = ["fast_union_find", "union_find", "cpu_batch", "sparse_blossom", "blossom"]


def recommend(
    code_family: Optional[str],
    distance: Optional[int],
    n_qubits: Optional[int],
    priority: str,
) -> Recommendation:
    """Heuristic decoder recommendation (deterministic, no model call).

    Mirrors the removed qector_decoder_v3.routing.recommend: priority is
    one of "balanced", "speed", "accuracy".
    """
    priority = (priority or "balanced").strip().lower()
    if priority not in ("balanced", "speed", "accuracy"):
        raise ValueError(f"unknown priority {priority!r}; choose from balanced/speed/accuracy")

    hw = detect_hardware()
    large_n = bool(n_qubits and n_qubits >= 200)
    high_distance = bool(distance and distance >= 9)

    if priority == "accuracy":
        decoder = "blossom"
        reason = "Exact MWPM (Blossom) minimizes logical error rate; sparse_blossom scales better for large codes."
        if large_n:
            decoder = "sparse_blossom"
            reason = "Large qubit count: sparse_blossom keeps MWPM accuracy with better scaling than Blossom."
    elif priority == "speed":
        decoder = "fast_union_find"
        reason = "FastUnionFind gives the lowest per-decode latency; accept higher LER (about 3x Blossom)."
        if hw.cuda_rust and large_n:
            decoder = "cpu_batch"
            reason = "CUDA available with a large batch: use a batch backend (cuda/cpu_batch) for max throughput."
    else:  # balanced
        if high_distance or large_n:
            decoder = "sparse_blossom"
            reason = "Balanced priority on a large/high-distance code: sparse_blossom trades a little speed for MWPM accuracy at scale."
        else:
            decoder = "union_find"
            reason = "Balanced priority on a small/medium code: union_find is a solid speed/accuracy middle ground."

    batch_size = 1024 if (hw.cuda_rust or hw.opencl) else 256
    hardware_label = "cuda" if hw.cuda_rust else ("opencl" if hw.opencl else "cpu")

    return Recommendation(
        decoder=decoder,
        reason=reason,
        family=code_family,
        priority=priority,
        batch_size=batch_size,
        hardware=hardware_label,
        gpu_batched_bp=bool(hw.cuda_rust and priority != "speed"),
    )
