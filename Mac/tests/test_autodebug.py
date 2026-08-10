"""
tests/test_autodebug.py — Tests for the resilient self/auto-debug backend.

Covers resilient single decode (happy path + fallback), the per-decoder probe,
resilient batch decode with hardware fallback, the self-diagnostics report, and
the GUI-independent text formatters.
"""

from __future__ import annotations

import pytest

import autodebug
import backend as be


# ---------------------------------------------------------------------------
# Resilient single decode
# ---------------------------------------------------------------------------

def test_resilient_single_decode_happy_path():
    res = autodebug.resilient_single_decode("rotated_surface", 3, decoder="union_find", seed=7).to_dict()
    assert res["success"] is True
    assert res["fallback_used"] is False
    assert res["used_decoder"] == "union_find"
    assert res["syndrome_valid"] is True
    assert res["attempts"][0]["method"] == "union_find"
    assert res["attempts"][0]["ok"] is True


@pytest.mark.parametrize("kind", be.DECODER_KINDS)
def test_resilient_every_decoder_first_try(kind):
    res = autodebug.resilient_single_decode("repetition", 5, decoder=kind, seed=3).to_dict()
    assert res["success"] is True, kind
    assert res["used_decoder"] == kind
    assert res["fallback_used"] is False


def test_resilient_falls_back_on_bad_requested_decoder():
    res = autodebug.resilient_single_decode("repetition", 5, decoder="does_not_exist", seed=1).to_dict()
    assert res["success"] is True
    assert res["fallback_used"] is True
    assert res["attempts"][0]["method"] == "does_not_exist"
    assert res["attempts"][0]["ok"] is False
    assert res["used_decoder"] in be.DECODER_KINDS
    assert res["syndrome_valid"] is True


def test_resilient_bad_family_reports_failure_without_raising():
    res = autodebug.resilient_single_decode("nonexistent_family", 3).to_dict()
    assert res["success"] is False
    assert "code build failed" in res["message"]
    assert res["used_decoder"] is None


def test_resilient_recovers_on_qldpc_incompatible_decoder():
    """On a bivariate_bicycle (qLDPC) code, union_find cannot construct; the
    resilient layer must record that failure and recover with a compatible
    decoder (bp_osd / blossom / hybrid / …)."""
    res = autodebug.resilient_single_decode(
        "bivariate_bicycle", 3, decoder="union_find", seed=2).to_dict()
    assert res["success"] is True
    assert res["fallback_used"] is True
    assert res["attempts"][0]["method"] == "union_find"
    assert res["attempts"][0]["ok"] is False
    assert res["used_decoder"] in ("blossom", "sparse_blossom", "bp_osd", "hybrid", "predecoded")
    assert res["syndrome_valid"] is True


def test_resilient_respects_custom_fallback_chain():
    res = autodebug.resilient_single_decode(
        "repetition", 5, decoder="does_not_exist",
        fallback_chain=["blossom"], seed=2).to_dict()
    assert res["success"] is True
    assert res["used_decoder"] == "blossom"


# ---------------------------------------------------------------------------
# Probe
# ---------------------------------------------------------------------------

def test_probe_decoders_all_working():
    probe = autodebug.probe_decoders("rotated_surface", 3, seed=5)
    assert set(probe["working"]) == set(be.DECODER_KINDS)
    assert probe["failing"] == []
    assert len(probe["results"]) == len(be.DECODER_KINDS)


def test_probe_decoders_bad_family():
    probe = autodebug.probe_decoders("nope", 3)
    assert probe["working"] == [] and "setup failed" in probe["message"]


# ---------------------------------------------------------------------------
# Resilient batch decode
# ---------------------------------------------------------------------------

def test_resilient_batch_cpu_direct():
    res = autodebug.resilient_batch_decode("repetition", 5, backend="cpu", n_samples=16, seed=1)
    assert res["success"] is True
    assert res["backend_used"] == "cpu"
    assert res["fallback_used"] is False


def test_resilient_batch_cuda_falls_back_to_cpu():
    import qector_decoder_v3 as qd
    if qd.cuda_is_available() or qd.opencl_is_available():
        pytest.skip("GPU backend available; the cpu-fallback path is not exercised here")
    res = autodebug.resilient_batch_decode("repetition", 5, backend="cuda", n_samples=16, seed=1)
    assert res["success"] is True
    assert res["backend_used"] == "cpu"
    assert res["fallback_used"] is True
    assert any(a["backend"] == "cuda" and not a["ok"] for a in res["attempts"])


# ---------------------------------------------------------------------------
# Self-diagnostics
# ---------------------------------------------------------------------------

def test_self_diagnostics_structure_and_status():
    rep = autodebug.run_self_diagnostics().to_dict()
    assert rep["overall_status"] in ("pass", "degraded", "fail")
    assert rep["backend_version"]
    names = {c["name"] for c in rep["checks"]}
    for expected in ("backend import", "backend version", "code families", "decoders"):
        assert expected in names
    assert set(rep["summary"]["working_decoders"]) == set(be.DECODER_KINDS)


def test_self_diagnostics_healthy_install_never_fails():
    rep = autodebug.run_self_diagnostics()
    # A working install may be "degraded" (no GPU) but must never be "fail".
    assert rep.overall_status in ("pass", "degraded")


def test_scipy_is_optional_dependency(monkeypatch):
    """scipy is declared but not imported at runtime; its absence (e.g. in a
    frozen bundle) must be a warning, never a hard failure."""
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "scipy" or name.startswith("scipy."):
            raise ImportError("No module named 'scipy'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    rep = autodebug.run_self_diagnostics().to_dict()
    scipy_check = next(c for c in rep["checks"] if c["name"] == "dependency scipy")
    assert scipy_check["status"] == "warn"
    assert rep["overall_status"] != "fail"


# ---------------------------------------------------------------------------
# Formatters (import from the tab module; GUI-independent)
# ---------------------------------------------------------------------------

def test_text_formatters():
    from diagnostics_tab import format_diagnostics, format_probe, format_resilient
    assert "OVERALL" in format_diagnostics(autodebug.run_self_diagnostics().to_dict())
    assert "Decoder probe" in format_probe(autodebug.probe_decoders("repetition", 5))
    assert "Resilient decode" in format_resilient(
        autodebug.resilient_single_decode("repetition", 5).to_dict())
