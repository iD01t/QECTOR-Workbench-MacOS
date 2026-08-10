import sys
import unittest.mock
from pathlib import Path
import pytest
import zipfile

import decoder_provisioner as dp

def test_offline_provisioning_blocks_network(tmp_path, monkeypatch):
    """Test that provisioning succeeds even if socket/network is blocked."""
    
    # We want to mock out dp.managed_root() to point to tmp_path
    monkeypatch.setattr(dp, "managed_root", lambda: tmp_path / "offline_site")
    
    # We need to simulate that it's NOT already importable
    monkeypatch.setattr(dp, "import_ok", lambda: False)
    
    # Provide a dummy wheel
    wheel_dir = tmp_path / "wheels"
    wheel_dir.mkdir()
    wheel_path = wheel_dir / "qector_decoder_v3-1.0.0-py3-none-any.whl"
    
    # A real wheel is a zip file, let's create a minimal zip
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("qector_decoder/__init__.py", "__version__ = '1.0.0'\n")
        
    # We want find_local_wheels to return this wheel
    monkeypatch.setattr(dp, "find_local_wheels", lambda: [wheel_path])
    
    # We need to mock _extract_wheel_direct to succeed and then set import_ok to True
    original_extract = dp._extract_wheel_direct
    def mock_extract(wpath):
        res = original_extract(wpath)
        monkeypatch.setattr(dp, "import_ok", lambda: True)
        monkeypatch.setattr(dp, "scan_version", lambda: "1.0.0")
        return res
        
    monkeypatch.setattr(dp, "_extract_wheel_direct", mock_extract)
    
    # Block network explicitly
    def mock_urlopen(*args, **kwargs):
        raise OSError("Network is offline")
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    # Run provisioner using local wheel only
    result = dp.bootstrap()
    
    # Check that it extracted and verified the local wheel
    assert result["ok"] is True
    assert result["action"] == "bundled_wheel"
    assert result["installed"] == "1.0.0"
