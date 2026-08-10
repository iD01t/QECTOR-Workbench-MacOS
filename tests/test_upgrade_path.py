import json
from pathlib import Path
import pytest

import decoder_provisioner as dp
import version

def test_upgrade_path_clears_old_version(tmp_path, monkeypatch):
    """Test simulating upgrading from an older decoder version."""
    
    # We want to mock out dp.managed_root() to point to tmp_path
    monkeypatch.setattr(dp, "managed_root", lambda: tmp_path / "upgrade_site")
    
    # Create the old site structure
    managed = dp.managed_root()
    versions_dir = managed / "versions"
    versions_dir.mkdir(parents=True)
    
    # Create an old version dir
    old_version = "0.6.9"
    old_dir = versions_dir / old_version
    old_dir.mkdir()
    old_dir.joinpath("dummy.txt").write_text("old data")
    
    # Also create the pointer file
    pointer = managed / "active.json"
    pointer.write_text(json.dumps({"version": old_version}), encoding="utf-8")
    
    # Run the purge function explicitly
    purged = dp.purge_outdated_managed_sites(minimum_ver="1.0.0")
    
    assert old_version in purged
    assert not old_dir.exists()
    assert not pointer.exists()
