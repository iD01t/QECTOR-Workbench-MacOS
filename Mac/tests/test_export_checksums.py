"""Every data export must carry real SHA-256 digests.

Covers the utils helpers (digest, sidecar, manifest), the benchmark export's
None-tolerant logical-error-rate formatting, and the Documentation Studio's
per-run checksum manifest.
"""
import hashlib
from pathlib import Path

import utils


def _expected(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def test_sha256_of_matches_hashlib(tmp_path):
    p = tmp_path / "data.bin"
    payload = b"qector" * 200_000
    p.write_bytes(payload)
    assert utils.sha256_of(p) == _expected(payload)


def test_sha256_sidecar_is_coreutils_format(tmp_path):
    p = tmp_path / "report.html"
    p.write_text("<html/>", encoding="utf-8")
    ok, digest = utils.sha256_sidecar(p)
    assert ok
    assert digest == _expected(b"<html/>")
    sidecar = tmp_path / "report.html.sha256"
    assert sidecar.read_text(encoding="utf-8") == f"{digest}  report.html\n"


def test_write_sha256_manifest_skips_missing_files(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("a", encoding="utf-8")
    b = tmp_path / "b.json"
    b.write_text("{}", encoding="utf-8")
    ok, manifest = utils.write_sha256_manifest(tmp_path, [a, b, tmp_path / "missing.pdf"])
    assert ok
    lines = Path(manifest).read_text(encoding="utf-8").splitlines()
    body = [ln for ln in lines if ln and not ln.startswith("#")]
    assert len(body) == 2
    for line in body:
        digest, name = line.split("  ", 1)
        assert digest == _expected((tmp_path / name).read_bytes())


def test_benchmark_ler_none_renders_as_text():
    from benchmark_tab import _fmt_ler
    assert _fmt_ler(None) == "N/A (no logicals matrix)"
    assert _fmt_ler(0.25) == "0.2500"
    assert _fmt_ler(1.0) == "1.0000"


def test_rec_display_none_latency_degrades_to_text():
    from doc_generator import ProfessionalDocGenerator
    row = {"decoder": "blossom", "status": "ok", "mean_latency_ms": None,
           "logical_failure_fraction": None, "n_trials": 25, "error_rate": 0.05}
    _decoder, latency, failure, _note = ProfessionalDocGenerator._rec_display(row)
    assert latency == "n/a"
    assert failure == "N/A (no logicals matrix)"


def test_doc_export_writes_sha256_manifest(tmp_path, monkeypatch):
    import backend as be
    from doc_generator import ProfessionalDocGenerator

    # No real decodes needed to exercise the manifest step.
    monkeypatch.setattr(ProfessionalDocGenerator, "_benchmark_decoders",
                        lambda self, code, **kw: [])
    code = be.build_code("repetition", 3)
    gen = ProfessionalDocGenerator(output_dir=tmp_path)
    results = gen.generate_all(code, formats=["markdown", "json"])
    assert results and all(ok for ok, _ in results.values())

    manifests = list(tmp_path.glob("*.SHA256SUMS.txt"))
    assert len(manifests) == 1
    text = manifests[0].read_text(encoding="utf-8")
    for _fmt, (ok, path) in results.items():
        assert ok
        assert f"{utils.sha256_of(path)}  {path.name}" in text
