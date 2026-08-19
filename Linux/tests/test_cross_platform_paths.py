from pathlib import Path

import utils

def test_cross_platform_export_paths(tmp_path):
    """Test path sanitization and directory resolution across platforms."""
    # Test valid paths
    test_file = tmp_path / "valid_name.csv"
    ok, p = utils.sanitize_export_path(str(test_file), base_dir=tmp_path)
    assert ok is True
    assert p == Path(test_file).resolve()
    
    # Test unicode path
    unicode_file = tmp_path / "экспорт_データ.json"
    ok, p = utils.sanitize_export_path(str(unicode_file), base_dir=tmp_path)
    assert ok is True
    assert p == Path(unicode_file).resolve()

    # Test spaces in paths
    space_file = tmp_path / "my document export.json"
    ok, p = utils.sanitize_export_path(str(space_file), base_dir=tmp_path)
    assert ok is True
    assert p == Path(space_file).resolve()

    # Test rejection of absolute traversal attempts (outside base_dir)
    ok, p = utils.sanitize_export_path("/etc/passwd", base_dir=tmp_path)
    assert ok is False

    ok, p = utils.sanitize_export_path("C:\\Windows\\System32\\cmd.exe", base_dir=tmp_path)
    assert ok is False

    # Long path handling (should work up to OS limits, we just test basic long path)
    long_name = "a" * 150 + ".csv"
    long_file = tmp_path / long_name
    ok, p = utils.sanitize_export_path(str(long_file), base_dir=tmp_path)
    assert ok is True
    assert p == Path(long_file).resolve()
