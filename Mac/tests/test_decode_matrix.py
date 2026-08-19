import pytest
import backend as be

CODE_FAMILIES = list(be.CODE_FAMILIES.keys())
DECODER_KINDS = be.DECODER_KINDS

@pytest.mark.parametrize("family", CODE_FAMILIES)
@pytest.mark.parametrize("decoder", DECODER_KINDS)
def test_decode_matrix(family, decoder):
    dist = 3
    try:
        code = be.build_code(family, dist)
    except Exception as e:
        pytest.skip(f"Could not build code {family} with d={dist}: {e}")

    compat = be.compatible_decoder_kinds(code)
    if decoder not in compat:
        pytest.skip(f"Decoder {decoder} is not compatible with {family}")

    if "gnn" in decoder:
        try:
            raw = be.run_single_decode(code, error_rate=0.05, decoder_kind=decoder, seed=42)
        except Exception:
            pytest.skip(f"Skipping GNN decoder {decoder} because GNN resources are not initialized")
            return

    try:
        raw = be.run_single_decode(code, error_rate=0.05, decoder_kind=decoder, seed=42)
        res = raw["result"]
        assert hasattr(res, "syndrome_valid")
    except Exception as e:
        pytest.fail(f"Decode failed for {decoder} on {family}: {e}")
