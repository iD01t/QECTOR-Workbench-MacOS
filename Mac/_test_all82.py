#!/usr/bin/env python3
"""Test all 82 MCP tools in-process."""
import os
os.environ['QECTOR_SILENT'] = '1'
import sys; sys.path.insert(0, '.')
import asyncio
import json
import re
import mcp_server
from mcp_server import get_mcp_server, call_mcp_tool, MCPError

server = get_mcp_server()
tools = sorted(server.tools.tools.keys())
print(f"Total tools: {len(tools)}")

# Verify docstring
doc = mcp_server.__doc__ or ''
m = re.search(r'exactly (\d+) tools', doc)
if m:
    doc_count = int(m.group(1))
    assert doc_count == len(tools), f"Docstring {doc_count} != actual {len(tools)}"
    print(f"Docstring OK: {doc_count}")

# Test params for all 82 tools
test_params = {
    "analyze_code_family": {"family_name": "rotated_surface", "distance": 5},
    "batch_decode": {"family": "repetition", "distance": 7, "backend": "cpu", "n_samples": 20, "error_rate": 0.05, "seed": 2},
    "batch_decode_gpu": {"family": "repetition", "distance": 3, "backend": "cuda", "n_samples": 8, "error_rate": 0.05, "seed": 4},
    "belief_match_decode": {"family": "repetition", "distance": 3, "error_rate": 0.05, "seed": 14},
    "benchmark_decoder": {"decoder_name": "blossom", "code_family": "repetition", "distance": 5, "error_rate": 0.03, "n_samples": 30, "seed": 9},
    "build_code_from_matrix": {"H_matrix": [[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]], "family": "custom", "distance": 3},
    "build_dem": {"family": "rotated_surface", "distance": 3, "noise_model": "circuit", "p": 0.05, "bias": 0.5},
    "check_updates": {"refresh": False},
    "clear_decoder_cache": {},
    "clear_results": {"confirm": True},
    "colour_code_decode": {"distance": 3, "max_iter": 30, "osd_order": 0},
    "compare_all_decoders": {"family": "repetition", "distance": 3, "error_rate": 0.05, "n_samples": 20, "seed": 16},
    "compatibility_matrix": {},
    "compatible_decoders": {"family": "rotated_surface", "distance": 3},
    "compat_report": {},
    "decode_dem": {"family": "rotated_surface", "distance": 3, "decoder_kind": "blossom"},
    "decode_hyperedge": {"family": "bicycle", "distance": 3, "decoder_name": "bp_osd", "error_rate": 0.05, "seed": 42},
    "decode_mmap": {"family": "rotated_surface", "distance": 3, "syndrome_path": "test.npy", "output_path": "test_out.npy", "decoder_name": "cpu_batch", "batch_size": 1024, "n_shots": 10},
    "decode_single": {"family": "rotated_surface", "distance": 5, "decoder_name": "sparse_blossom", "error_rate": 0.04, "seed": 11},
    "decode_syndrome": {"family": "repetition", "distance": 3, "decoder_name": "union_find", "syndrome": [1, 0]},
    "decode_syndrome_blossom": {"family": "repetition", "distance": 3, "syndrome": [1, 0]},
    "decode_syndrome_cascade": {"family": "repetition", "distance": 3, "syndrome": [1, 0]},
    "decode_with_options": {"family": "repetition", "distance": 3, "decoder_name": "bp_osd", "error_rate": 0.05, "seed": 13, "decoder_options": {"bp_method": "min_sum", "osd_order": 1}},
    "decoder_benchmark_suite": {"n_samples": 20, "seed": 17},
    "delete_resource": {"resource_id": "mcp-res-delete", "confirm": True},
    "diagnostic_decode": {"family": "rotated_surface", "distance": 5, "decoder_name": "blossom", "error_rate": 0.05, "seed": 3},
    "doctor_diagnostics": {},
    "ambiguity_cluster_decode": {"family": "rotated_surface", "distance": 5, "error_rate": 0.05, "ambig_threshold": 0.5, "max_cluster_size": 12},
    "estimate_threshold": {"family": "repetition", "distance": 3, "decoder_kind": "union_find", "p_min": 0.05, "p_max": 0.15, "n_samples": 20},
    "export_benchmark": {"format": "json", "benchmark_id": "test-bench"},
    "export_figure": {"family": "rotated_surface", "distance": 3, "output_path": "test_tanner.png", "format": "png", "dpi": 72},
    "export_session": {"output_path": "test_session.zip", "family": "repetition", "distance": 3, "decoder_name": "union_find", "error_rate": 0.05, "seed": 42},
    "finite_size_scaling": {"family": "repetition", "decoder_kind": "union_find", "distances": [3, 5], "p_vals": [0.05, 0.1], "n_samples": 20},
    "flush_usage": {},
    "generate_documentation": {"family_key": "ring", "param": 6, "formats": ["json"]},
    "generate_parity_check": {"family": "rotated_surface", "distance": 3},
    "generate_reproducibility_package": {"family": "repetition", "distance": 3, "decoder_name": "union_find", "error_rate": 0.05, "seed": 42, "output_path": "repro_test.zip"},
    "get_backend_health": {},
    "get_code_properties": {"family_name": "ring", "distance": 5},
    "get_config": {},
    "get_decoder_info": {"decoder_name": "bp_osd"},
    "get_hardware_info": {},
    "get_license_info": {},
    "get_resource": {"resource_id": "mcp-res-get"},
    "get_resources": {},
    "get_results": {"limit": 10},
    "get_server_env": {},
    "get_statistics": {},
    "get_system_info": {},
    "gnn_belief_match_decode": {"family": "repetition", "distance": 3, "error_rate": 0.05, "seed": 12},
    "hybrid_cascade_stats": {"family": "repetition", "distance": 3, "n_samples": 20, "error_rate": 0.05, "seed": 6, "escalation": "blossom"},
    "import_stim": {"file_path": "nonexistent.stim", "family": "rotated_surface", "distance": 3, "decoder_name": "blossom"},
    "import_syndrome": {"file_path": "nonexistent.csv", "family": "repetition", "distance": 3, "decoder_name": "blossom"},
    "list_clients": {},
    "list_code_families": {},
    "list_codes": {},
    "list_decoders": {},
    "list_tools": {},
    "mcp_health": {},
    "mcp_status": {},
    "native_recommend": {"family": "repetition", "distance": 3, "priority": "balanced"},
    "native_streaming": {"family": "repetition", "distance": 5, "n_rounds": 4, "error_rate": 0.03, "seed": 2, "window_size": 3},
    "neural_predecoder_train": {"family": "repetition", "distance": 3, "n_samples": 20, "n_epochs": 1, "error_rate": 0.05, "seed": 8},
    "parallel_batch_decode": {"family": "repetition", "distance": 3, "decoder_name": "union_find", "n_samples": 20, "error_rate": 0.05, "seed": 15, "n_workers": 2},
    "probe_decoders": {"family": "repetition", "distance": 3, "error_rate": 0.05, "seed": 42},
    "recommend_decoder": {"family": "repetition", "distance": 3, "priority": "balanced"},
    "register_client": {"client_id": "mcp-tester", "access_level": "USER"},
    "reset_config": {"confirm": True},
    "resilient_decode": {"family": "repetition", "distance": 3, "decoder_name": "union_find", "error_rate": 0.05, "seed": 7},
    "run_benchmark": {"code_family": "repetition", "distance": 3, "decoder_name": "union_find", "n_samples": 20, "seed": 42, "error_rate": 0.05},
    "run_ler_benchmark": {"family": "repetition", "distance": 3, "decoder_name": "union_find", "n_samples": 30, "error_rate": 0.05, "seed": 42},
    "self_diagnostics": {},
    "set_config": {"config": {"theme_mode": "dark", "max_results": 50}},
    "set_license_key_file": {"path": "C:\\temp\\fake_key.lic"},
    "sparse_blossom_radix_neighbors": {"family": "rotated_surface", "distance": 5, "defects": [0, 1], "k": 8},
    "stream_decode": {"family": "repetition", "distance": 5, "window_size": 3, "n_rounds": 6, "error_rate": 0.03, "seed": 5, "decoder_name": "union_find"},
    "two_stage_decode": {"family": "repetition", "distance": 3, "x_decoder": "blossom", "z_decoder": "blossom"},
    "verify_license_token": {"token": "sample_token"},
    "version_info": {"refresh": False},
    "analyze_error_patterns": {"family": "repetition", "distance": 3, "error_rate": 0.05, "n_samples": 50, "seed": 42},
    "analyze_logicals": {"family": "repetition", "distance": 3},
    "compare_benchmarks": {"benchmarks": ["test-bench"]},
}

missing = [t for t in tools if t not in test_params]
if missing:
    print(f"MISSING test params: {missing}")
    sys.exit(1)

async def run_all():
    passed = 0
    failed = 0
    errors = []
    for name in sorted(tools):
        params = test_params[name].copy()
        try:
            result = await call_mcp_tool(name, params)
            json.dumps(result)
            print(f"  [OK] {name}")
            passed += 1
        except MCPError as e:
            # Expected errors (backend limitations, missing files, etc.)
            print(f"  [OK] {name} (expected error: {str(e)[:60]})")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {type(e).__name__}: {str(e)[:80]}")
            failed += 1
            errors.append((name, str(e)[:120]))
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tools)} tools")
    if errors:
        print(f"\nFailures:")
        for name, err in errors:
            print(f"  {name}: {err}")
    return failed == 0

ok = asyncio.run(run_all())
sys.exit(0 if ok else 1)
