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
        "benchmark_decoder": {"decoder_name": "blossom", "code_family": "repetition",
                              "distance": 5, "error_rate": 0.03, "n_samples": 40, "seed": 9},
        "clear_results": {"confirm": True},
        "compare_benchmarks": {"benchmarks": [bench_id]},
        "decode_single": {"family": "rotated_surface", "distance": 5,
                          "decoder_name": "sparse_blossom", "error_rate": 0.04, "seed": 11},
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
        "list_clients": {},
        "list_code_families": {},
        "list_decoders": {},
        "list_tools": {},
        "mcp_status": {},
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
        ok &= _check("tools/call list_decoders: 5 decoders in content text",
                     decoded.get("count") == 5 and len(decoded.get("decoders", [])) == 5,
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
