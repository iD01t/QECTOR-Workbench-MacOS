#!/usr/bin/env python3
"""test_mcp_all.py — Exhaustive test of ALL MCP Server tools.

Two sections, both must pass for exit code 0:

1. In-process: every registered tool is invoked through ``call_mcp_tool``
   with realistic parameters and its result must survive a strict
   ``json.dumps`` (no ``default=`` escape hatch).
2. Stdio round-trip: spawns ``python mcp_server.py`` and drives the real
   newline-delimited JSON-RPC 2.0 transport (initialize -> initialized ->
   ping -> tools/list -> tools/call), including protocol error paths.
"""
import asyncio
import json
import queue
import re
import subprocess
import sys
import threading
from pathlib import Path

REPO_DIR = Path(__file__).parent
sys.path.insert(0, str(REPO_DIR))

import mcp_server
from mcp_server import get_mcp_server, call_mcp_tool, MCPError  # noqa: F401
from mcp_resources import get_resource_manager

PROTOCOL_VERSION = "2024-11-05"
STDIO_TIMEOUT = 60.0  # generous first-response timeout (imports numpy/backend)


# ---------------------------------------------------------------------------
# Section 1: in-process pass over every registered tool
# ---------------------------------------------------------------------------

async def test_all_mcp_functions():
    server = get_mcp_server()
    tools = sorted(server.tools.tools.keys())

    print("=" * 85)
    print("QECTOR MCP SERVER - COMPLETE FUNCTION TEST SUITE (in-process)")
    print(f"Total tools to test: {len(tools)}")
    print("=" * 85)

    # The module docstring must state the exact tool count.
    doc = mcp_server.__doc__ or ""
    m = re.search(r"exactly (\d+) tools", doc)
    if m is None:
        print("FAIL: module docstring does not state the tool count")
        return False, {}
    doc_count = int(m.group(1))
    if doc_count != len(tools):
        print(f"FAIL: docstring claims {doc_count} tools but {len(tools)} are registered")
        return False, {}
    print(f"Docstring tool count OK: exactly {doc_count} tools")

    rm = get_resource_manager()
    rm.allocate_resource("mcp-res-for-get", "test", {"purpose": "get_resource test"})
    rm.allocate_resource("mcp-res-for-delete", "test", {"purpose": "delete test"})

    # Run a quick benchmark first to get a valid benchmark_id for export_benchmark
    bench_res = await call_mcp_tool(
        "run_benchmark", {"code_family": "repetition", "n_samples": 30, "seed": 7})
    bench_id = bench_res.get("result_id", "demo")

    test_params = {
        "analyze_code_family": {"family_name": "rotated_surface", "distance": 5},
        "batch_decode": {"family": "repetition", "distance": 7, "backend": "cpu",
                         "n_samples": 40, "error_rate": 0.05, "seed": 2},
        "batch_decode_gpu": {"family": "repetition", "distance": 3, "backend": "cuda",
                             "n_samples": 8, "error_rate": 0.05, "seed": 4},
        "belief_match_decode": {"family": "repetition", "distance": 3,
                                "error_rate": 0.05, "seed": 14},
        "benchmark_decoder": {"decoder_name": "blossom", "code_family": "repetition",
                              "distance": 5, "error_rate": 0.03, "n_samples": 40, "seed": 9},
        "clear_results": {"confirm": True},
        "compare_benchmarks": {"benchmarks": [bench_id]},
        "compatible_decoders": {"family": "rotated_surface", "distance": 3},
        "decode_single": {"family": "rotated_surface", "distance": 5,
                          "decoder_name": "sparse_blossom", "error_rate": 0.04, "seed": 11},
        "decode_syndrome": {"family": "repetition", "distance": 3,
                            "decoder_name": "union_find", "syndrome": [1, 0]},
        "decode_with_options": {"family": "repetition", "distance": 3,
                                "decoder_name": "bp_osd", "error_rate": 0.05, "seed": 13,
                                "decoder_options": {"bp_method": "min_sum", "osd_order": 1}},
        "delete_resource": {"resource_id": "mcp-res-for-delete", "confirm": True},
        "export_benchmark": {"format": "json", "benchmark_id": bench_id},
        "generate_documentation": {"family_key": "ring", "param": 6,
                                   "formats": ["json", "markdown", "html"]},
        "get_code_properties": {"family_name": "ring", "distance": 5},
        "get_config": {},
        "get_decoder_info": {"decoder_name": "bp_osd"},
        "get_hardware_info": {},
        "get_resource": {"resource_id": "mcp-res-for-get"},
        "get_resources": {},
        "get_results": {"limit": 10},
        "get_statistics": {},
        "get_system_info": {},
        "gnn_belief_match_decode": {"family": "repetition", "distance": 3,
                                    "error_rate": 0.05, "seed": 12},
        "hybrid_cascade_stats": {"family": "repetition", "distance": 3, "n_samples": 24,
                                 "error_rate": 0.05, "seed": 6, "escalation": "blossom"},
        "list_clients": {},
        "list_code_families": {},
        "list_decoders": {},
        "list_tools": {},
        "mcp_status": {},
        "neural_predecoder_train": {"family": "repetition", "distance": 3, "n_samples": 40,
                                    "n_epochs": 2, "error_rate": 0.05, "seed": 8},
        "recommend_decoder": {"family": "rotated_surface", "distance": 5,
                              "priority": "balanced"},
        "register_client": {"client_id": "mcp-tester", "access_level": "USER"},
        "reset_config": {"confirm": True},
        "run_benchmark": {"code_family": "repetition", "distance": 7,
                          "decoder_name": "union_find", "n_samples": 30,
                          "seed": 7, "error_rate": 0.05},
        "set_config": {"config": {"theme_mode": "dark", "max_results": 50}},
        "stream_decode": {"family": "repetition", "distance": 9, "window_size": 4,
                          "n_rounds": 8, "error_rate": 0.03, "seed": 5,
                          "decoder_name": "union_find"},
        "probe_decoders": {"family": "rotated_surface", "distance": 3,
                           "error_rate": 0.05, "seed": 42},
        "resilient_decode": {"family": "rotated_surface", "distance": 3,
                             "decoder_name": "union_find", "error_rate": 0.05, "seed": 7},
        "self_diagnostics": {},
        "version_info": {"refresh": False},
        "check_updates": {"refresh": False},
        "diagnostic_decode": {"family": "rotated_surface", "distance": 5,
                              "decoder_name": "blossom", "error_rate": 0.05, "seed": 3},
        "native_recommend": {"family": "bivariate_bicycle", "distance": 3, "priority": "balanced"},
        "native_streaming": {"family": "repetition", "distance": 5, "n_rounds": 6,
                             "error_rate": 0.03, "seed": 2, "window_size": 3},
        "list_codes": {},
        "compat_report": {},
        "sparse_blossom_radix_neighbors": {"family": "rotated_surface", "distance": 5, "defects": [0, 1], "k": 8},
        "clear_decoder_cache": {},
        "flush_usage": {},
        "doctor_diagnostics": {},
        "verify_license_token": {"token": "sample_token"},
        "set_license_key_file": {"path": "C:\\temp\\fake_key.lic"},
        "parallel_batch_decode": {"family": "repetition", "distance": 9, "decoder_name": "union_find",
                                  "n_samples": 24, "error_rate": 0.05, "seed": 15, "n_workers": 2},
        "mcp_health": {},
        "compare_all_decoders": {"family": "rotated_surface", "distance": 3, "error_rate": 0.05,
                                 "n_samples": 24, "seed": 16},
        "compatibility_matrix": {},
        "decoder_benchmark_suite": {"n_samples": 24, "seed": 17},
        "get_backend_health": {},
        "two_stage_decode": {"family": "rotated_surface", "distance": 5, "x_decoder": "blossom", "z_decoder": "blossom"},
        "ambiguity_cluster_decode": {"family": "rotated_surface", "distance": 5, "error_rate": 0.05, "ambig_threshold": 0.5, "max_cluster_size": 12},
        "colour_code_decode": {"distance": 3, "max_iter": 30, "osd_order": 0},
        "build_dem": {"family": "rotated_surface", "distance": 3, "noise_model": "circuit", "p": 0.05, "bias": 0.5},
        "decode_dem": {"family": "rotated_surface", "distance": 3, "decoder_kind": "blossom"},
        "import_stim": {"file_path": "nonexistent.stim", "family": "rotated_surface", "distance": 3, "decoder_name": "blossom"},
        "build_code_from_matrix": {"H_matrix": [[1, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 1]], "family": "custom", "distance": 3},
        "estimate_threshold": {"family": "repetition", "distance": 3, "decoder_kind": "union_find", "p_min": 0.05, "p_max": 0.15, "n_samples": 20},
        "finite_size_scaling": {"family": "repetition", "decoder_kind": "union_find", "distances": [3, 5], "p_vals": [0.05, 0.1], "n_samples": 20},
        "run_ler_benchmark": {"family": "repetition", "distance": 3, "decoder_name": "union_find", "n_samples": 30, "error_rate": 0.05, "seed": 42},
        "generate_parity_check": {"family": "rotated_surface", "distance": 3},
        "get_license_info": {},
        "generate_reproducibility_package": {"family": "repetition", "distance": 3, "decoder_name": "union_find", "error_rate": 0.05, "seed": 42, "output_path": "repro_test.zip"},
        "export_figure": {"family": "rotated_surface", "distance": 3, "output_path": "test_tanner.png", "format": "png", "dpi": 72},
        "get_server_env": {},
        "decode_hyperedge": {"family": "bicycle", "distance": 3, "decoder_name": "bp_osd", "error_rate": 0.05, "seed": 42},
        "decode_syndrome_blossom": {"family": "rotated_surface", "distance": 3, "syndrome": [1, 0, 1, 0]},
        "decode_syndrome_cascade": {"family": "rotated_surface", "distance": 3, "syndrome": [1, 0, 1, 0]},
        "decode_mmap": {"family": "rotated_surface", "distance": 3, "syndrome_path": "nonexistent.npy", "output_path": "test_out.npy", "decoder_name": "cpu_batch", "batch_size": 1024, "n_shots": 10},
        "analyze_error_patterns": {"family": "repetition", "distance": 3, "error_rate": 0.05, "n_samples": 50, "seed": 42},
        "analyze_logicals": {"family": "repetition", "distance": 3},
        "compare_benchmarks": {"benchmarks": ["test-bench"]},
        "export_session": {"output_path": "test_session.zip", "family": "repetition", "distance": 3, "decoder_name": "union_find", "error_rate": 0.05, "seed": 42},
    }

    missing_params = [t for t in tools if t not in test_params]
    if missing_params:
        print(f"FAIL: no test parameters defined for: {', '.join(missing_params)}")
        return False, {}

    results = {}

    for tool in tools:
        params = test_params[tool].copy()
        if tool in ("compare_benchmarks", "export_benchmark"):
            # clear_results may have wiped the store; get a fresh id.
            bench_res = await call_mcp_tool(
                "run_benchmark", {"code_family": "repetition", "n_samples": 30, "seed": 7})
            curr_id = bench_res.get("result_id", "demo")
            if tool == "compare_benchmarks":
                params["benchmarks"] = [curr_id]
            else:
                params["benchmark_id"] = curr_id
        print(f"\n  TOOL: {tool}")
        print(f"   params: {json.dumps(params)[:120]}")
        try:
            data = await call_mcp_tool(tool, params)
            encoded = json.dumps(data)  # strict: every result must be JSON-safe
            results[tool] = (True, data)
            print(f"   PASS  -> {encoded[:160]}")
        except Exception as exc:
            results[tool] = (False, str(exc)[:180])
            print(f"   FAIL  -> {type(exc).__name__}: {str(exc)[:140]}")

    # Targeted honesty checks on top of the blanket pass.
    checks_ok = True

    ok, bench = results.get("benchmark_decoder", (False, None))
    if ok and (bench.get("method") != "blossom" or bench.get("p") != 0.03
               or bench.get("n_trials") != 40):
        print("\nFAIL: benchmark_decoder did not honor decoder_name/error_rate/n_samples")
        checks_ok = False

    ok, comp = results.get("compare_benchmarks", (False, None))
    if ok and (comp.get("count") != 1 or comp.get("missing") != []):
        print("\nFAIL: compare_benchmarks did not resolve the stored result id")
        checks_ok = False
    missing_probe = await call_mcp_tool(
        "compare_benchmarks", {"benchmarks": ["no-such-result-id"]})
    if missing_probe.get("missing") != ["no-such-result-id"]:
        print("\nFAIL: compare_benchmarks did not report unknown ids as missing")
        checks_ok = False

    ok, exp = results.get("export_benchmark", (False, None))
    if ok and not (Path(exp["path"]).is_file() and exp["size"] > 2):
        print("\nFAIL: export_benchmark did not write a non-empty file")
        checks_ok = False
    try:
        await call_mcp_tool("export_benchmark", {"benchmark_id": "no-such-id"})
        print("\nFAIL: export_benchmark accepted an unknown benchmark id")
        checks_ok = False
    except MCPError:
        pass

    # --- 0.6.9 tools: targeted contract/honesty checks ------------------------
    ok, dwo = results.get("decode_with_options", (False, None))
    if ok and not (dwo.get("options_applied") is True
                   and dwo.get("decoder_options") == {"bp_method": "min_sum", "osd_order": 1}
                   and dwo.get("syndrome_valid") is True):
        print("\nFAIL: decode_with_options did not apply/echo the validated decoder_options")
        checks_ok = False
    try:
        await call_mcp_tool("decode_with_options", {"family": "repetition", "distance": 3,
                                                    "decoder_options": {"bogus_key": 1}})
        print("\nFAIL: decode_with_options accepted an unknown decoder_options key")
        checks_ok = False
    except MCPError:
        pass

    ok, ds = results.get("decode_syndrome", (False, None))
    if ok and not (ds.get("syndrome_valid") is True and ds.get("logical_failure") is None
                   and ds.get("hamming_weight") == 1):
        print("\nFAIL: decode_syndrome contract broken "
              "(syndrome_valid / honest null logical_failure / correction weight)")
        checks_ok = False
    try:
        await call_mcp_tool("decode_syndrome", {"family": "repetition", "distance": 3,
                                                "syndrome": [1, 0, 0]})
        print("\nFAIL: decode_syndrome accepted a wrong-length syndrome")
        checks_ok = False
    except MCPError:
        pass

    ok, hcs = results.get("hybrid_cascade_stats", (False, None))
    if ok and not (hcs.get("n_samples") == 24 and hcs.get("decoder") == "hybrid_cascade"
                   and isinstance(hcs.get("prefilter_hits"), int)
                   and isinstance(hcs.get("escalations"), int)
                   and 0.0 <= hcs.get("prefilter_hit_rate", -1.0) <= 1.0
                   and hcs.get("logical_error_rate_kind") in ("logical", "syndrome_validity")):
        print("\nFAIL: hybrid_cascade_stats counters missing/out of range")
        checks_ok = False
    try:
        await call_mcp_tool("hybrid_cascade_stats", {"family": "repetition", "distance": 3,
                                                     "escalation": "bogus"})
        print("\nFAIL: hybrid_cascade_stats accepted a bogus escalation")
        checks_ok = False
    except MCPError:
        pass

    ok, npt = results.get("neural_predecoder_train", (False, None))
    if ok and not (npt.get("n_samples") == 40 and npt.get("n_epochs") == 2
                   and npt.get("n_holdout") == 16
                   and 0.0 <= npt.get("exact_match_rate", -1.0) <= 1.0
                   and 0.0 <= npt.get("syndrome_validity_rate", -1.0) <= 1.0):
        print("\nFAIL: neural_predecoder_train held-out metrics missing or out of range")
        checks_ok = False

    ok, bg = results.get("batch_decode_gpu", (False, None))
    if ok:
        avail = bg.get("availability", {})
        if bg.get("status") == "ok":
            if not avail.get(bg.get("backend"), False):
                print("\nFAIL: batch_decode_gpu ran on a backend it reported unavailable")
                checks_ok = False
        elif bg.get("status") in ("unavailable", "error"):
            if not bg.get("reason"):
                print("\nFAIL: batch_decode_gpu unavailable or errored without an honest reason")
                checks_ok = False
        else:
            print(f"\nFAIL: batch_decode_gpu returned unexpected status {bg.get('status')!r}")
            checks_ok = False

    ok, cd = results.get("compatible_decoders", (False, None))
    if ok and not (cd.get("count") == len(cd.get("compatible_kinds", []))
                   and cd.get("total_kinds") == len(cd.get("compatible_kinds", []))
                   + len(cd.get("incompatible_kinds", []))):
        print("\nFAIL: compatible_decoders counts are inconsistent")
        checks_ok = False

    for _tool, _kind in (("gnn_belief_match_decode", "gnn_belief_matching"),
                         ("belief_match_decode", "belief_matching")):
        ok, r = results.get(_tool, (False, None))
        if ok and not (r.get("decoder") == _kind and r.get("syndrome_valid") is True):
            print(f"\nFAIL: {_tool} did not produce a valid decode with pinned kind {_kind}")
            checks_ok = False

    print("\n" + "=" * 85)
    print("IN-PROCESS TEST RESULTS")
    print("=" * 85)

    passed = [t for t, (ok, _) in results.items() if ok]
    failed = [t for t, (ok, _) in results.items() if not ok]

    print(f"PASSED: {len(passed)} / {len(tools)}")
    for t in passed:
        print(f"  PASS {t}")

    if failed:
        print(f"\nFAILED: {len(failed)} / {len(tools)}")
        for t in failed:
            print(f"  FAIL {t}  - {results[t][1]}")

    print("\n" + "=" * 85)
    overall = len(failed) == 0 and checks_ok
    print("IN-PROCESS STATUS:", "ALL MCP FUNCTIONS OK" if overall else "SOME TOOLS NEED ATTENTION")
    print("=" * 85)

    return overall, results


# ---------------------------------------------------------------------------
# Section 2: real stdio JSON-RPC round-trip against `python mcp_server.py`
# ---------------------------------------------------------------------------

class _StdioClient:
    """Line-oriented JSON-RPC client over a child process's pipes (Windows-safe)."""

    def __init__(self, argv, cwd):
        self.proc = subprocess.Popen(
            argv, cwd=str(cwd),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1)
        self._out_q: "queue.Queue[str]" = queue.Queue()
        self.stderr_lines: list[str] = []
        self._threads = [
            threading.Thread(target=self._pump, args=(self.proc.stdout, self._out_q),
                             daemon=True),
            threading.Thread(target=self._pump_err, daemon=True),
        ]
        for t in self._threads:
            t.start()

    @staticmethod
    def _pump(stream, q):
        try:
            for line in stream:
                q.put(line)
        except Exception:
            pass

    def _pump_err(self):
        try:
            for line in self.proc.stderr:
                self.stderr_lines.append(line.rstrip())
        except Exception:
            pass

    def send_raw(self, text: str) -> None:
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def send(self, msg: dict) -> None:
        self.send_raw(json.dumps(msg))

    def recv(self, timeout: float = STDIO_TIMEOUT) -> dict:
        try:
            line = self._out_q.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(
                f"no stdio response within {timeout}s; "
                f"stderr tail: {self.stderr_lines[-5:]}") from None
        return json.loads(line)

    def close(self) -> int:
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            return self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=15)
            return -1


def _check(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f"  - {detail}" if (detail and not condition) else ""
    print(f"  {status} {label}{suffix}")
    return condition


def test_stdio_roundtrip(expected_tool_count: int) -> bool:
    print("\n" + "=" * 85)
    print("MCP STDIO TRANSPORT ROUND-TRIP (JSON-RPC 2.0 over pipes)")
    print("=" * 85)

    client = _StdioClient([sys.executable, "mcp_server.py"], cwd=REPO_DIR)
    ok = True
    try:
        # -- initialize ------------------------------------------------------
        client.send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": PROTOCOL_VERSION,
                                "capabilities": {},
                                "clientInfo": {"name": "test_mcp_all", "version": "1.0"}}})
        resp = client.recv()
        res = resp.get("result", {})
        ok &= _check("initialize: protocolVersion",
                     res.get("protocolVersion") == PROTOCOL_VERSION, json.dumps(resp)[:200])
        ok &= _check("initialize: serverInfo.name == qector-workbench",
                     res.get("serverInfo", {}).get("name") == "qector-workbench")
        ok &= _check("initialize: tools capability advertised",
                     "tools" in res.get("capabilities", {}))

        # -- notifications/initialized (no id => no response) -----------------
        client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        # -- ping --------------------------------------------------------------
        client.send({"jsonrpc": "2.0", "id": 2, "method": "ping"})
        resp = client.recv()
        ok &= _check("ping returns {} (and initialized got no response)",
                     resp.get("id") == 2 and resp.get("result") == {},
                     json.dumps(resp)[:200])

        # -- tools/list --------------------------------------------------------
        client.send({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        resp = client.recv()
        tool_list = resp.get("result", {}).get("tools", [])
        ok &= _check(f"tools/list: exactly {expected_tool_count} tools",
                     len(tool_list) == expected_tool_count,
                     f"got {len(tool_list)}")
        bad_schema = [t.get("name") for t in tool_list
                      if not (isinstance(t.get("inputSchema"), dict)
                              and t["inputSchema"].get("type") == "object"
                              and isinstance(t["inputSchema"].get("properties"), dict))]
        ok &= _check("tools/list: every tool has a proper inputSchema",
                     not bad_schema, f"bad: {bad_schema}")
        new_069 = {"batch_decode_gpu", "belief_match_decode", "compatible_decoders",
                   "decode_syndrome", "decode_with_options", "gnn_belief_match_decode",
                   "hybrid_cascade_stats", "neural_predecoder_train"}
        listed = {t.get("name") for t in tool_list}
        ok &= _check("tools/list: all 8 new 0.6.9 tools advertised",
                     new_069 <= listed, f"missing: {sorted(new_069 - listed)}")

        # -- tools/call list_decoders -----------------------------------------
        client.send({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                     "params": {"name": "list_decoders", "arguments": {}}})
        resp = client.recv()
        res = resp.get("result", {})
        content = res.get("content") or [{}]
        decoded = {}
        if content[0].get("type") == "text":
            try:
                decoded = json.loads(content[0].get("text", ""))
            except json.JSONDecodeError:
                decoded = {}
        ok &= _check("tools/call list_decoders: isError false",
                     res.get("isError") is False, json.dumps(resp)[:200])
        import backend as _be
        _n_dec = len(_be.DECODER_KINDS)
        ok &= _check(f"tools/call list_decoders: {_n_dec} decoders in content text",
                     decoded.get("count") == _n_dec and len(decoded.get("decoders", [])) == _n_dec,
                     json.dumps(decoded)[:200])

        # -- tools/call decode_single -----------------------------------------
        client.send({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                     "params": {"name": "decode_single",
                                "arguments": {"family": "repetition", "distance": 7,
                                              "decoder_name": "union_find",
                                              "error_rate": 0.05, "seed": 3}}})
        resp = client.recv()
        res = resp.get("result", {})
        content = res.get("content") or [{}]
        decoded = {}
        if content[0].get("type") == "text":
            try:
                decoded = json.loads(content[0].get("text", ""))
            except json.JSONDecodeError:
                decoded = {}
        ok &= _check("tools/call decode_single: isError false",
                     res.get("isError") is False, json.dumps(resp)[:200])
        ok &= _check("tools/call decode_single: summary fields present",
                     "hamming_weight" in decoded and "syndrome_valid" in decoded
                     and "logical_failure" in decoded, json.dumps(decoded)[:200])

        # -- tools/call hybrid_cascade_stats (0.6.9 tool over the wire) ---------
        client.send({"jsonrpc": "2.0", "id": 8, "method": "tools/call",
                     "params": {"name": "hybrid_cascade_stats",
                                "arguments": {"family": "repetition", "distance": 3,
                                              "n_samples": 16, "error_rate": 0.05,
                                              "seed": 6}}})
        resp = client.recv()
        res = resp.get("result", {})
        content = res.get("content") or [{}]
        decoded = {}
        if content[0].get("type") == "text":
            try:
                decoded = json.loads(content[0].get("text", ""))
            except json.JSONDecodeError:
                decoded = {}
        ok &= _check("tools/call hybrid_cascade_stats: isError false",
                     res.get("isError") is False, json.dumps(resp)[:200])
        ok &= _check("tools/call hybrid_cascade_stats: cascade counters present",
                     "prefilter_hits" in decoded and "escalations" in decoded
                     and "prefilter_hit_rate" in decoded, json.dumps(decoded)[:200])

        # -- tools/call with a bad tool name => tool-level error, not JSON-RPC --
        client.send({"jsonrpc": "2.0", "id": 6, "method": "tools/call",
                     "params": {"name": "no_such_tool", "arguments": {}}})
        resp = client.recv()
        ok &= _check("tools/call unknown tool: isError true (not a JSON-RPC error)",
                     "error" not in resp and resp.get("result", {}).get("isError") is True,
                     json.dumps(resp)[:200])

        # -- unknown method with an id => -32601 --------------------------------
        client.send({"jsonrpc": "2.0", "id": 7, "method": "does/not/exist"})
        resp = client.recv()
        ok &= _check("unknown method: JSON-RPC error -32601",
                     resp.get("error", {}).get("code") == -32601, json.dumps(resp)[:200])

        # -- malformed JSON line => -32700 with null id --------------------------
        client.send_raw("{this is not json")
        resp = client.recv()
        ok &= _check("malformed JSON: error -32700 with null id",
                     resp.get("error", {}).get("code") == -32700 and resp.get("id") is None,
                     json.dumps(resp)[:200])
    except Exception as exc:
        print(f"  FAIL stdio round-trip crashed: {type(exc).__name__}: {exc}")
        ok = False
    finally:
        exit_code = client.close()
        ok &= _check("server exited cleanly on EOF", exit_code == 0,
                     f"exit code {exit_code}; stderr tail: {client.stderr_lines[-5:]}")

    print("\nSTDIO STATUS:", "STDIO ROUND-TRIP PASS" if ok else "STDIO ROUND-TRIP FAIL")
    print("=" * 85)
    return ok


if __name__ == "__main__":
    inproc_ok, _ = asyncio.run(test_all_mcp_functions())
    n_tools = len(get_mcp_server().tools.tools)
    stdio_ok = test_stdio_roundtrip(expected_tool_count=n_tools)
    print("\nOVERALL:", "ALL SECTIONS PASS" if (inproc_ok and stdio_ok) else "FAILURES PRESENT")
    sys.exit(0 if (inproc_ok and stdio_ok) else 1)
