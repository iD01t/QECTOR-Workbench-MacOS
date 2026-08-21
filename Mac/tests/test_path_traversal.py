"""tests/test_path_traversal.py - Verify path traversal protection in utils.sanitize_export_path."""
import os
import pytest
import tempfile
from pathlib import Path

import utils


class TestSanitizeExportPath:
    """Verify that sanitize_export_path blocks escape attempts."""

    def setup_method(self):
        self._tmpdir = str(Path(tempfile.mkdtemp(prefix="qector_test_")).resolve())

    def teardown_method(self):
        import shutil
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_simple_filename_allowed(self):
        ok, result = utils.sanitize_export_path("report.html", base_dir=self._tmpdir)
        assert ok is True
        assert str(result).startswith(self._tmpdir)

    def test_dot_dot_rejected(self):
        ok, result = utils.sanitize_export_path("../../../etc/passwd", base_dir=self._tmpdir)
        assert ok is False

    def test_absolute_path_outside_rejected(self):
        ok, result = utils.sanitize_export_path("/tmp/evil.txt", base_dir=self._tmpdir)
        assert ok is False

    def test_backslash_traversal_rejected(self):
        ok, result = utils.sanitize_export_path("..\\..\\Windows\\System32\\evil.dll", base_dir=self._tmpdir)
        assert ok is False

    def test_null_byte_rejected(self):
        ok, result = utils.sanitize_export_path("report\x00.html", base_dir=self._tmpdir)
        assert ok is False

    def test_subdirectory_allowed(self):
        subdir = os.path.join(self._tmpdir, "exports")
        os.makedirs(subdir, exist_ok=True)
        ok, result = utils.sanitize_export_path("exports/report.html", base_dir=self._tmpdir)
        assert ok is True
        assert str(result).startswith(self._tmpdir)



    def test_symlink_escape_rejected(self):
        """If a symlink resolves outside base_dir, it should be rejected."""
        link_path = os.path.join(self._tmpdir, "link")
        try:
            os.symlink(tempfile.gettempdir(), link_path)
        except (OSError, NotImplementedError):
            pytest.skip("Cannot create symlinks on this OS/permission level")
        ok, result = utils.sanitize_export_path("link/../../../etc/passwd", base_dir=self._tmpdir)
        assert ok is False
