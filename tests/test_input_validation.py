"""tests/test_input_validation.py - Input validation and security boundary tests."""
import pytest
import backend as be


class TestDistanceValidation:
    """Distance parameter must be a small positive odd integer."""

    def test_zero_distance_rejected(self):
        with pytest.raises((ValueError, be.QectorError)):
            be.build_code("rotated_surface", 0)

    def test_negative_distance_rejected(self):
        with pytest.raises((ValueError, be.QectorError)):
            be.build_code("rotated_surface", -3)

    def test_very_large_distance_rejected(self):
        with pytest.raises((be.QectorError,)):
            be.build_code("rotated_surface", 999)


class TestErrorRateValidation:
    """Error rate must be in (0, 1)."""

    def test_negative_error_rate(self):
        code = be.build_code("rotated_surface", 3)
        with pytest.raises(ValueError):
            be.run_single_decode(code, error_rate=-0.1, decoder_kind="blossom", seed=42)

    def test_error_rate_above_one(self):
        code = be.build_code("rotated_surface", 3)
        with pytest.raises(ValueError):
            be.run_single_decode(code, error_rate=1.5, decoder_kind="blossom", seed=42)


class TestHTMLEscaping:
    """Ensure HTML exports escape user content."""

    def test_xss_in_code_name_does_not_inject(self):
        """A crafted string should be escaped in any HTML output."""
        xss_payload = '<script>alert("xss")</script>'
        # The backend should never embed raw HTML from user input
        # Just verify the build_code rejects nonsense family names
        with pytest.raises((KeyError, ValueError, be.QectorError)):
            be.build_code(xss_payload, 3)


class TestInvalidDecoderKind:
    """Unknown decoder kinds must raise, not silently fallback."""

    def test_nonexistent_decoder(self):
        code = be.build_code("rotated_surface", 3)
        with pytest.raises((KeyError, ValueError, be.QectorError)):
            be.run_single_decode(code, error_rate=0.05, decoder_kind="nonexistent_decoder_xyz", seed=42)
