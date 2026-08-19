"""Offline regression tests for external decoder provisioning."""

from __future__ import annotations

import json
import sys

import decoder_provisioner as provisioner


def test_active_managed_site_is_preferred(tmp_path, monkeypatch):
    root = tmp_path / "decoder_site"
    site = root / "versions" / "9.9.9"
    site.mkdir(parents=True)
    (site / "qector_decoder_v3").mkdir()
    info = site / "qector_decoder_v3-9.9.9.dist-info"
    info.mkdir()
    (info / "METADATA").write_text("Name: qector-decoder-v3\nVersion: 9.9.9\n", encoding="utf-8")
    (root / "active.json").write_text(json.dumps({"version": "9.9.9"}), encoding="utf-8")
    monkeypatch.setattr(provisioner, "managed_root", lambda: root)

    assert provisioner.scan_version() == "9.9.9"
    assert provisioner.activate_site() == site
    assert sys.path[0] == str(site)


def test_bootstrap_boots_on_bundled_without_touching_managed(monkeypatch):
    """The bundled decoder imports up front, so bootstrap boots on it and never
    activates the managed site or provisions — that is what lets the app run on a
    machine with no Python/pip/network."""
    monkeypatch.setattr(provisioner, "import_ok", lambda: True)
    monkeypatch.setattr(provisioner, "_imported_version", lambda: "1.0.0")
    touched = {"activate": False, "ensure": False}
    monkeypatch.setattr(provisioner, "activate_site",
                        lambda: touched.__setitem__("activate", True))
    monkeypatch.setattr(provisioner, "ensure",
                        lambda **k: touched.__setitem__("ensure", True) or {"ok": False})

    result = provisioner.bootstrap()

    assert result["ok"] is True
    assert result["action"] in ("ready", "bundled")
    assert result["installed"] == "1.0.0"
    assert touched["activate"] is False and touched["ensure"] is False


def test_bootstrap_falls_back_to_managed_when_no_bundle(monkeypatch):
    """A source checkout has no bundled decoder: bootstrap brings the managed
    site online and boots on it, still without network provisioning."""
    seq = iter([False, True])  # bundled import fails, managed import succeeds
    monkeypatch.setattr(provisioner, "import_ok", lambda: next(seq))
    monkeypatch.setattr(provisioner, "activate_site", lambda: None)
    monkeypatch.setattr(provisioner, "scan_version", lambda: "1.0.0")
    monkeypatch.setattr(provisioner, "ensure",
                        lambda **k: (_ for _ in ()).throw(AssertionError("must not provision")))

    result = provisioner.bootstrap()

    assert result["ok"] is True
    assert result["action"] == "managed"
    assert result["installed"] == "1.0.0"


def test_frozen_build_reports_missing_compatible_python(monkeypatch):
    monkeypatch.setattr(provisioner, "is_frozen", lambda: True)
    monkeypatch.setattr(provisioner, "_candidate_pythons", lambda: [])

    argv, reason = provisioner.resolve_pip_argv()

    assert argv is None
    assert "ABI-compatible" in reason


def test_verify_import_uses_frozen_executable_when_frozen(monkeypatch, tmp_path):
    """A frozen app must verify a candidate wheel in ITSELF, not a system Python.

    This is the regression that shipped 0.6.8: the wheel imported fine under a
    full system CPython (which had `cryptography`) but not inside the frozen
    bundle, so verifying with the system interpreter let a broken release flip
    the active pointer and brick the app.
    """
    monkeypatch.setattr(provisioner, "is_frozen", lambda: True)
    monkeypatch.setattr(provisioner.sys, "executable", "FROZEN.EXE")
    captured = {}

    def fake_run(argv, timeout):
        captured["argv"] = argv
        return 0, "OK 0.6.7", ""

    monkeypatch.setattr(provisioner, "_run", fake_run)

    ok, detail = provisioner._verify_import(tmp_path)

    assert ok is True
    assert detail == "0.6.7"
    assert captured["argv"][0] == "FROZEN.EXE"
    assert "--decoder-selftest" in captured["argv"]
    assert str(tmp_path) in captured["argv"]


def test_verify_import_reports_traceback_tail_on_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(provisioner, "is_frozen", lambda: True)
    monkeypatch.setattr(
        provisioner, "_run",
        lambda argv, timeout: (1, "", "line1\nModuleNotFoundError: No module named 'cryptography'"),
    )

    ok, detail = provisioner._verify_import(tmp_path)

    assert ok is False
    assert "cryptography" in detail


def test_install_best_steps_down_past_broken_latest(monkeypatch, tmp_path):
    """A latest release that installs but does not import must self-heal to the
    next-lower release instead of failing the whole boot."""
    monkeypatch.setattr(provisioner, "managed_root", lambda: tmp_path)
    calls = []

    def fake_install(spec, timeout, on_log):
        calls.append(spec)
        if spec == "qector-decoder-v3==0.6.8":
            return False, "0.6.8 does not import in this runtime", "0.6.8"
        if spec == "qector-decoder-v3<0.6.8":
            return True, "installed qector-decoder-v3 0.6.7", "0.6.7"
        raise AssertionError(f"unexpected spec {spec}")

    monkeypatch.setattr(provisioner, "_install", fake_install)

    ok, message, version = provisioner._install_best("0.6.8", 10, None)

    assert ok is True
    assert version == "0.6.7"
    assert calls == ["qector-decoder-v3==0.6.8", "qector-decoder-v3<0.6.8"]
    # The broken release is remembered so it is never re-downloaded next launch.
    assert "0.6.8" in provisioner._load_blocklist()


def test_install_best_skips_known_bad_latest(monkeypatch, tmp_path):
    monkeypatch.setattr(provisioner, "managed_root", lambda: tmp_path)
    provisioner._add_blocklist("0.6.8")
    seen = []

    def fake_install(spec, timeout, on_log):
        seen.append(spec)
        return True, "installed qector-decoder-v3 0.6.7", "0.6.7"

    monkeypatch.setattr(provisioner, "_install", fake_install)

    ok, _message, version = provisioner._install_best("0.6.8", 10, None)

    assert ok is True and version == "0.6.7"
    # 0.6.8 already known-bad: it is skipped, not re-attempted as an exact pin.
    assert seen == ["qector-decoder-v3<0.6.8"]


def test_install_best_gives_up_when_pip_cannot_install(monkeypatch, tmp_path):
    monkeypatch.setattr(provisioner, "managed_root", lambda: tmp_path)
    monkeypatch.setattr(provisioner, "_install", lambda *a, **k: (False, "no compatible wheel", None))

    ok, _message, version = provisioner._install_best("0.6.8", 10, None)

    assert ok is False
    assert version is None


def test_install_best_is_bounded(monkeypatch, tmp_path):
    """A pathological index where every release installs but never imports must
    terminate, not spin forever."""
    monkeypatch.setattr(provisioner, "managed_root", lambda: tmp_path)
    counter = {"n": 0}

    def fake_install(spec, timeout, on_log):
        counter["n"] += 1
        return False, "broken", "0.6.%02d" % (90 - counter["n"])

    monkeypatch.setattr(provisioner, "_install", fake_install)

    ok, _message, version = provisioner._install_best("0.6.90", 10, None)

    assert ok is False and version is None
    assert counter["n"] == provisioner._MAX_INSTALL_ATTEMPTS


def test_blocklist_round_trips(monkeypatch, tmp_path):
    monkeypatch.setattr(provisioner, "managed_root", lambda: tmp_path)
    assert provisioner._load_blocklist() == set()
    provisioner._add_blocklist("0.6.8")
    provisioner._add_blocklist("0.6.8")  # idempotent
    provisioner._add_blocklist(None)     # ignored
    assert provisioner._load_blocklist() == {"0.6.8"}
