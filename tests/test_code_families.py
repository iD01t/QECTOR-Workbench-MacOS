"""
tests/test_code_families.py — Coverage for all code families, including the
v0.6.6 qLDPC additions (bicycle, bivariate_bicycle).

The qLDPC families are non-graphlike: bicycle happens to accept every wired
decoder, while bivariate_bicycle (the IBM BB code family, e.g. the [[72,12,6]]
"gross" code) only accepts the exact-matching / LDPC / heuristic decoders and
rejects the union-find family. These tests pin that behaviour down with real
decodes — no mocks.
"""

from __future__ import annotations

import pytest

import backend as be

EXPECTED_FAMILIES = ["repetition", "ring", "rotated_surface", "unrotated_surface",
                     "toric", "heavy_hex", "bicycle", "bivariate_bicycle",
                     "hypergraph_product", "color_code"]
# Decoders that cannot handle non-graphlike qLDPC checks.
BB_INCOMPATIBLE = {"union_find", "fast_union_find", "lookup_table"}
# auto_router routes bivariate_bicycle to BP-OSD internally, and since v0.6.8
# the plain `auto` policy decoder also dispatches BB to a compatible backend,
# so both are usable.
BB_COMPATIBLE = ["blossom", "sparse_blossom", "bp_osd", "hybrid", "predecoded",
                 "auto_router", "auto", "gnn_belief_matching", "hybrid_cascade"]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def test_all_expected_families_registered():
    for fam in EXPECTED_FAMILIES:
        assert fam in be.CODE_FAMILIES, f"{fam} missing from CODE_FAMILIES"
    assert len(be.CODE_FAMILIES) == len(EXPECTED_FAMILIES)
    assert be.QLDPC_FAMILIES == {"bicycle", "bivariate_bicycle"}


@pytest.mark.parametrize("fam", EXPECTED_FAMILIES)
def test_every_family_builds_and_summarises(fam):
    code = be.build_code(fam, 3)
    summary = be.code_summary(code)
    assert summary["n_qubits"] >= 1
    assert summary["n_checks"] >= 1
    info = be.get_code_family_info(fam)
    assert info["key"] == fam and info["label"]


@pytest.mark.parametrize("fam", EXPECTED_FAMILIES)
def test_validate_parameter_accepts_min(fam):
    ok, msg = be.validate_parameter(fam, 3)
    assert ok is True, msg


# ---------------------------------------------------------------------------
# bicycle — a qLDPC code that every decoder can handle
# ---------------------------------------------------------------------------

def test_bicycle_param_is_circulant_size():
    # n_qubits == 2 * n_circulant, n_checks == n_circulant (verified against v0.6.6)
    for n in (3, 5, 8):
        code = be.build_code("bicycle", n)
        assert code.n_qubits == 2 * n
        assert code.n_checks == n


def test_bicycle_all_decoders_valid():
    code = be.build_code("bicycle", 5)
    for kind in be.DECODER_KINDS:
        out = be.run_single_decode(code, 0.08, kind, seed=4)
        assert out["result"].syndrome_valid is True, f"bicycle/{kind} invalid"


def test_bicycle_compatible_is_all_decoders():
    code = be.build_code("bicycle", 5)
    assert len(be.compatible_decoder_kinds(code)) >= 15
    assert "blossom" in be.compatible_decoder_kinds(code)


# ---------------------------------------------------------------------------
# bivariate_bicycle — the IBM BB code family (partial decoder support)
# ---------------------------------------------------------------------------

def test_bivariate_bicycle_presets_select_distinct_codes():
    # param selects a preset (clamped); different params give different sizes.
    gross = be.build_code("bivariate_bicycle", 3)      # [[72,12,6]]
    assert (gross.n_qubits, gross.n_checks) == (72, 36)
    bigger = be.build_code("bivariate_bicycle", 7)     # largest preset (clamped)
    assert bigger.n_qubits > gross.n_qubits


@pytest.mark.parametrize("kind", BB_COMPATIBLE)
def test_bivariate_bicycle_compatible_decoders_valid(kind):
    code = be.build_code("bivariate_bicycle", 3)
    out = be.run_single_decode(code, 0.04, kind, seed=2)
    assert out["result"].syndrome_valid is True
    # qLDPC codes expose no usable logicals matrix in v0.6.6.
    assert out["result"].logical_failure is None


@pytest.mark.parametrize("kind", sorted(BB_INCOMPATIBLE))
def test_bivariate_bicycle_incompatible_decoders_fail_cleanly(kind):
    code = be.build_code("bivariate_bicycle", 3)
    with pytest.raises(be.QectorError):
        be.run_single_decode(code, 0.05, kind, seed=1)


def test_bivariate_bicycle_compatible_probe_excludes_union_find():
    code = be.build_code("bivariate_bicycle", 3)
    compat = set(be.compatible_decoder_kinds(code))
    assert compat == set(BB_COMPATIBLE), compat
    assert not (compat & BB_INCOMPATIBLE)


def test_bivariate_bicycle_benchmark_with_bp_osd():
    code = be.build_code("bivariate_bicycle", 3)
    b = be.run_benchmark(code, n_samples=12, seed=1, decoder_kind="bp_osd", error_rate=0.03)
    assert b["n_trials"] == 12
    assert b["throughput_decodes_per_s"] > 0
    assert b["logical_error_rate"] is None  # no logicals matrix for qLDPC
