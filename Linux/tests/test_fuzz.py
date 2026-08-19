import pytest
import numpy as np
import backend as be

def test_fuzz_syndromes():
    code = be.build_code("rotated_surface", 3)
    decoders = ["blossom", "union_find", "bp_osd"]
    
    # 1. All-zeros syndrome
    zero_syn = np.zeros(code.n_checks, dtype=np.uint8)
    for dec in decoders:
        try:
            res = be.decode_syndrome(code, zero_syn, dec)
            assert res["result"].syndrome_valid
        except Exception as e:
            pytest.fail(f"All-zeros syndrome crashed decoder {dec}: {e}")

    # 2. All-ones syndrome
    one_syn = np.ones(code.n_checks, dtype=np.uint8)
    for dec in decoders:
        try:
            res = be.decode_syndrome(code, one_syn, dec)
            assert hasattr(res["result"], "syndrome_valid")
        except Exception:
            # Errors/exceptions are fine as long as they don't crash Python
            pass

    # 3. Out-of-bounds values (e.g. 2, 5, 255)
    invalid_val_syn = np.full(code.n_checks, 5, dtype=np.uint8)
    for dec in decoders:
        try:
            be.decode_syndrome(code, invalid_val_syn, dec)
        except Exception:
            pass

    # 4. NaNs or Inf values
    nan_syn = np.full(code.n_checks, np.nan)
    for dec in decoders:
        try:
            be.decode_syndrome(code, nan_syn, dec)
        except Exception:
            pass

    # 5. Wrong length
    short_syn = np.zeros(code.n_checks - 1, dtype=np.uint8)
    for dec in decoders:
        with pytest.raises(be.QectorError):
            be.decode_syndrome(code, short_syn, dec)
