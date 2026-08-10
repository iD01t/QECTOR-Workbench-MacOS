"""
tests/test_hardware_routing.py — Decoder recommendation correctness.

The key invariant: a recommendation must never name a decoder that cannot
construct on the code it is recommended for.  This regression-guards the qLDPC
case where union-find / AutoDecoder cannot handle high-weight checks.
"""

from __future__ import annotations

import pytest

import backend as be
from hardware_routing import recommend


@pytest.mark.parametrize("family", list(be.CODE_FAMILIES))
@pytest.mark.parametrize("priority", ["balanced", "speed", "accuracy"])
def test_recommendation_is_always_constructible(family, priority):
    rec = recommend(family, 3, None, priority)
    # "cpu_batch" is a batch-backend routing hint, not a single-shot decoder.
    if rec.decoder == "cpu_batch":
        return
    assert rec.decoder in be.DECODER_KINDS, f"{rec.decoder!r} is not a known decoder"
    code = be.build_code(family, 3)
    # Must actually construct — raises QectorError if the recommendation is bad.
    be.make_decoder(code, rec.decoder)


def test_qldpc_families_recommend_bp_osd():
    for family in sorted(be.QLDPC_FAMILIES):
        for priority in ("balanced", "speed", "accuracy"):
            rec = recommend(family, 3, None, priority)
            assert rec.decoder == "bp_osd", (family, priority, rec.decoder)
            assert "qLDPC" in rec.reason


def test_graphlike_families_keep_priority_behaviour():
    # A small graphlike code with speed priority still prefers the fast path.
    assert recommend("repetition", 3, None, "speed").decoder == "fast_union_find"
    assert recommend("rotated_surface", 3, None, "accuracy").decoder == "blossom"


def test_recommend_rejects_bad_priority():
    with pytest.raises(ValueError):
        recommend("repetition", 3, None, "nonsense")
