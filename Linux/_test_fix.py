#!/usr/bin/env python3
"""Check which backend functions exist and work."""
import os
os.environ['QECTOR_SILENT'] = '1'
import sys; sys.path.insert(0, '.')

import backend as be

# Test all backend functions used by MCP handlers
tests = {
    'build_code': lambda: be.build_code('repetition', 3),
    'build_code_from_matrix': lambda: be.build_code_from_matrix(__import__('numpy').array([[1,1,0],[0,1,1]], dtype='uint8')),
    'code_summary': lambda: be.code_summary(be.build_code('repetition', 3)),
    'build_dem_from_code': lambda: be.build_dem_from_code(be.build_code('repetition', 3), noise_model='circuit'),
    'decode_dem': lambda: be.decode_dem(be.build_code('repetition', 3), decoder_kind='union_find'),
    'import_stim_circuit': 'check if exists',
    'estimate_threshold': lambda: be.estimate_threshold(be.build_code('repetition', 3), decoder_kind='union_find', p_range=(0.05, 0.15), n_samples=10),
    'finite_size_scaling': lambda: be.finite_size_scaling('repetition', decoder_kind='union_find', distances=[3, 5], p_vals=[0.05, 0.1], n_samples=10),
    'generate_parity_check_matrix': lambda: be.generate_parity_check_matrix(be.build_code('repetition', 3)),
    'analyze_logicals': lambda: be.analyze_logicals(be.build_code('repetition', 3)) if hasattr(be, 'analyze_logicals') else 'NOT FOUND',
    'analyze_error_patterns': lambda: be.analyze_error_patterns(be.build_code('repetition', 3), n_samples=10) if hasattr(be, 'analyze_error_patterns') else 'NOT FOUND',
}

for name, fn in tests.items():
    if fn == 'check if exists':
        exists = hasattr(be, name)
        print(f'  {name}: {"EXISTS" if exists else "NOT FOUND"}')
        continue
    try:
        result = fn()
        print(f'  [OK] {name}')
    except Exception as e:
        print(f'  [FAIL] {name}: {type(e).__name__}: {str(e)[:80]}')

# Check what DEM noise models work
print("\n=== DEM noise models ===")
for nm in ['depolarizing', 'biased', 'correlated', 'circuit']:
    try:
        code = be.build_code('repetition', 3)
        dem = be.build_dem_from_code(code, noise_model=nm)
        print(f'  [OK] {nm}')
    except Exception as e:
        print(f'  [FAIL] {nm}: {str(e)[:60]}')
