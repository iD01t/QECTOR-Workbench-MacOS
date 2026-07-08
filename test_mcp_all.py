#!/usr/bin/env python3
"""
test_mcp_all.py — Exhaustive test of ALL MCP Server functions/tools.
"""
import sys
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import get_mcp_server, call_mcp_tool, MCPError
from mcp_resources import get_resource_manager


async def test_all_mcp_functions():
    server = get_mcp_server()
    tools = sorted(server.tools.tools.keys())

    print("=" * 85)
    print("QECTOR MCP SERVER — COMPLETE FUNCTION TEST SUITE")
    print(f"Total tools to test: {len(tools)}")
    print("=" * 85)

    # Pre-create resources that will survive until their respective test
    rm = get_resource_manager()
    rm.allocate_resource("mcp-res-for-get", "test", {"purpose": "get_resource test"})
    rm.allocate_resource("mcp-res-for-delete", "test", {"purpose": "delete test"})

    test_params = {
        "analyze_code_family": {"family_name": "rotated_surface"},
        "benchmark_decoder": {"decoder_name": "union_find", "code_family": "repetition", "error_rate": 0.03},
        "clear_results": {"confirm": True},
        "compare_benchmarks": {"benchmarks": ["rep-uf", "surf-blossom"]},
        "delete_resource": {"resource_id": "mcp-res-for-delete", "confirm": True},
        "export_benchmark": {"format": "json", "benchmark_id": "demo"},
        "generate_documentation": {"family_key": "ring", "param": 6, "formats": ["json", "markdown", "html"]},
        "get_code_properties": {"family_name": "ring"},
        "get_config": {},
        "get_decoder_info": {"decoder_name": "bp_osd"},
        "get_hardware_info": {},
        "get_resource": {"resource_id": "mcp-res-for-get"},
        "get_resources": {},
        "get_results": {"limit": 10},
        "get_statistics": {},
        "get_system_info": {},
        "list_clients": {},
        "list_code_families": {},
        "list_decoders": {},
        "list_tools": {},
        "mcp_status": {},
        "register_client": {"client_id": "mcp-tester", "access_level": "USER"},
        "reset_config": {"confirm": True},
        "run_benchmark": {"type": "quick", "n_samples": 30, "seed": 7},
        "set_config": {"theme_mode": "dark"},
    }

    results = {}

    for tool in tools:
        params = test_params.get(tool, {})
        print(f"\n▶ {tool}")
        print(f"   params: {json.dumps(params)[:120]}")
        try:
            data = await call_mcp_tool(tool, params)
            results[tool] = (True, data)
            preview = json.dumps(data, default=str)[:160].replace("\n", " ")
            print(f"   ✅ PASS  → {preview}")
        except Exception as exc:
            results[tool] = (False, str(exc)[:180])
            print(f"   ❌ FAIL  → {type(exc).__name__}: {str(exc)[:140]}")

    print("\n" + "=" * 85)
    print("TEST RESULTS")
    print("=" * 85)

    passed = [t for t, (ok, _) in results.items() if ok]
    failed = [t for t, (ok, _) in results.items() if not ok]

    print(f"PASSED: {len(passed)} / {len(tools)}")
    for t in passed:
        print(f"  ✅ {t}")

    if failed:
        print(f"\nFAILED: {len(failed)} / {len(tools)}")
        for t in failed:
            print(f"  ❌ {t}  — {results[t][1]}")

    print("\n" + "=" * 85)
    overall = len(failed) == 0
    print("OVERALL STATUS:", "✅ ALL MCP FUNCTIONS WORKING" if overall else "⚠️  SOME TOOLS NEED ATTENTION")
    print("=" * 85)

    return overall, results


if __name__ == "__main__":
    ok, _ = asyncio.run(test_all_mcp_functions())
    sys.exit(0 if ok else 1)
