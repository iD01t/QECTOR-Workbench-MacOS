"""
tests/test_entra_auth.py — Optional Entra ID readiness must stay optional.

v1.0.1 sells zero-egress operation to enterprises: Entra ID sign-in is an
opt-in convenience for online deployments, never a runtime dependency.  These
tests pin the hard guarantees of entra_auth.py:

 * Every runtime => status "disabled", zero identity traffic reachable.
 * Configuration => refused with a recorded air-gap reason.
 * Login         => refused before any MSAL import or network activity.
* Tokens/config  => written encrypted (Fernet, machine-derived key), mode 600.

No test opens a socket or contacts any identity provider.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import entra_auth
DUMMY_CLIENT = "11111111-2222-3333-4444-555555555555"
DUMMY_TENANT = "contoso.onmicrosoft.com"


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch, tmp_path):
    """Isolate config/cache in a temp data dir; clear env between tests."""
    for key in ("QECTOR_ENTRA_CLIENT_ID", "QECTOR_ENTRA_TENANT",
                "QECTOR_ENTRA_GROUP_ID", "QECTOR_ENTRA_SCOPES",
                "QECTOR_AIRGAP", "QECTOR_OFFLINE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(entra_auth, "_data_dir", lambda: tmp_path)
    yield
    for key in ("QECTOR_ENTRA_CLIENT_ID", "QECTOR_ENTRA_TENANT",
                "QECTOR_ENTRA_GROUP_ID", "QECTOR_ENTRA_SCOPES",
                "QECTOR_AIRGAP", "QECTOR_OFFLINE"):
        monkeypatch.delenv(key, raising=False)


def test_disabled_by_default():
    p = entra_auth.posture()
    assert p["status"] == "disabled"
    assert p["configured"] is False
    assert p["airgapped"] is True
    assert p["reason"] and "air-gap" in p["reason"]


def test_configure_is_refused_in_the_airgapped_product(tmp_path):
    r = entra_auth.configure(DUMMY_CLIENT, DUMMY_TENANT, group_id="g-123")
    assert r["ok"] is False
    assert r["status"] == "disabled"
    assert "air-gap" in r["reason"]
    assert not (tmp_path / "entra.json").exists()


def test_posture_after_configure(tmp_path):
    result = entra_auth.configure(DUMMY_CLIENT, DUMMY_TENANT)
    assert result["ok"] is False
    p = entra_auth.posture()
    assert p["status"] == "disabled"
    assert p["airgapped"] is True


def test_env_configuration_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("QECTOR_ENTRA_CLIENT_ID", DUMMY_CLIENT)
    monkeypatch.setenv("QECTOR_ENTRA_TENANT", DUMMY_TENANT)
    p = entra_auth.posture()
    assert p["configured"] is True
    assert p["config_source"] == "environment"
    assert p["status"] == "disabled"


def test_login_is_refused_before_msal_or_network(tmp_path):
    r = entra_auth.login()
    assert r["ok"] is False
    assert r["status"] == "disabled"
    assert "air-gap" in r["reason"]


def test_airgap_hard_disables_everything(monkeypatch, tmp_path):
    monkeypatch.setenv("QECTOR_AIRGAP", "1")
    p = entra_auth.posture()
    assert p["status"] == "disabled"
    assert p["airgapped"] is True
    r = entra_auth.login()
    assert r["ok"] is False
    assert r["status"] == "disabled"
    r = entra_auth.configure(DUMMY_CLIENT, DUMMY_TENANT)
    assert r["ok"] is False
    r = entra_auth.logout()
    assert r["ok"] is True


def test_entitlement_ok_is_none_when_not_authenticated(tmp_path):
    entra_auth.configure(DUMMY_CLIENT, DUMMY_TENANT, group_id="g-1")
    assert entra_auth.entitlement_ok() is None


def test_module_has_no_network_imports_at_top_level():
    """Module-level surface stays clean; msal is a lazy function-local import."""
    import ast
    src = Path(entra_auth.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and node.col_offset == 0:
            assert not any("msal" in a.name for a in node.names)
        if isinstance(node, ast.ImportFrom) and node.col_offset == 0:
            assert not (node.module or "").startswith("msal")
