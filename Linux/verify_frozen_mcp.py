#!/usr/bin/env python3
"""verify_frozen_mcp.py — Drive the frozen portable exe's --mcp transport.

Spawns dist/QectorWorkbench-Portable.exe --mcp and runs a real newline-delimited
JSON-RPC 2.0 session: initialize -> initialized -> tools/list (must be 56 tools,
including the 0.6.9/0.7.0 tool additions) -> tools/call hybrid_cascade_stats ->
clean EOF exit.  Exit code 0 only when every check passes.
"""
import json
import queue
import subprocess
import sys
import threading

EXE = r"dist\QectorWorkbench-Portable.exe"
PROTO = "2024-11-05"
NEW_TOOLS = {"batch_decode_gpu", "belief_match_decode", "compatible_decoders",
             "decode_syndrome", "decode_with_options", "gnn_belief_match_decode",
             "hybrid_cascade_stats", "neural_predecoder_train"}


def main() -> int:
    proc = subprocess.Popen([EXE, "--mcp"], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding="utf-8", bufsize=1)
    out_q: "queue.Queue[str]" = queue.Queue()
    err_lines: list[str] = []

    def _pump():
        try:
            for line in proc.stdout:
                out_q.put(line)
        except Exception:
            pass

    def _pump_err():
        try:
            for line in proc.stderr:
                err_lines.append(line.rstrip())
        except Exception:
            pass

    threading.Thread(target=_pump, daemon=True).start()
    threading.Thread(target=_pump_err, daemon=True).start()

    def send(msg: dict) -> None:
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()

    def recv(timeout: float = 180.0) -> dict:
        return json.loads(out_q.get(timeout=timeout))

    ok = True
    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"protocolVersion": PROTO, "capabilities": {},
                         "clientInfo": {"name": "frozen-verify", "version": "1.0"}}})
        res = recv().get("result", {})
        print("initialize:", res.get("protocolVersion"), res.get("serverInfo"))
        ok &= res.get("protocolVersion") == PROTO
        ok &= res.get("serverInfo", {}).get("name") == "qector-workbench"

        send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = recv().get("result", {}).get("tools", [])
        names = {t.get("name") for t in tools}
        print("tools/list count:", len(tools))
        print("new 0.6.9 tools present:", sorted(NEW_TOOLS & names))
        ok &= len(tools) == 56
        ok &= NEW_TOOLS <= names

        send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
              "params": {"name": "hybrid_cascade_stats",
                         "arguments": {"family": "repetition", "distance": 3,
                                       "n_samples": 16, "error_rate": 0.05, "seed": 6}}})
        res = recv().get("result", {})
        content = res.get("content") or [{}]
        payload = {}
        if content[0].get("type") == "text":
            try:
                payload = json.loads(content[0].get("text", ""))
            except json.JSONDecodeError:
                payload = {}
        print("hybrid_cascade_stats isError:", res.get("isError"),
              "| prefilter_hits:", payload.get("prefilter_hits"),
              "| escalations:", payload.get("escalations"))
        ok &= res.get("isError") is False and "prefilter_hits" in payload

        send({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
              "params": {"name": "decode_with_options",
                         "arguments": {"family": "repetition", "distance": 3,
                                       "decoder_name": "bp_osd", "error_rate": 0.05,
                                       "seed": 13,
                                       "decoder_options": {"bp_method": "min_sum",
                                                           "osd_order": 1}}}})
        res = recv().get("result", {})
        content = res.get("content") or [{}]
        payload = {}
        if content[0].get("type") == "text":
            try:
                payload = json.loads(content[0].get("text", ""))
            except json.JSONDecodeError:
                payload = {}
        print("decode_with_options isError:", res.get("isError"),
              "| syndrome_valid:", payload.get("syndrome_valid"),
              "| options_applied:", payload.get("options_applied"))
        ok &= res.get("isError") is False and payload.get("syndrome_valid") is True
    except Exception as exc:
        print(f"FROZEN MCP VERIFY crashed: {type(exc).__name__}: {exc}")
        ok = False
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            code = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            code = -1
        print("server exit code on EOF:", code)
        ok &= code == 0

    print("FROZEN MCP VERIFY:", "PASS" if ok else "FAIL")
    if not ok:
        print("stderr tail:", err_lines[-8:])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
