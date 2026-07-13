"""mcp_server.py — MCP server for QECTOR Decoder Workbench.

Two layers in one module:

1. An in-process tool registry exposing exactly 29 tools wired to the real
   backend (``get_mcp_server()``, ``call_mcp_tool()``, ``MCPError``).  Every
   tool result is passed through a JSON sanitizer so it always survives
   ``json.dumps``.
2. A real MCP stdio transport: newline-delimited JSON-RPC 2.0 over
   stdin/stdout implementing ``initialize``, ``notifications/initialized``,
   ``ping``, ``tools/list`` and ``tools/call`` (protocol version 2024-11-05).
   Run it with ``python mcp_server.py``.  All logging goes to stderr; stdout
   carries only JSON-RPC messages.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import platform
import re
import sys
import threading
import time
import traceback
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Optional

import numpy as np

try:
    import psutil
    _HAS_PSUTIL = True
except Exception:
    _HAS_PSUTIL = False

import backend as be
import utils
from mcp_resources import get_resource_manager
from version import WORKBENCH_VERSION

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "qector-workbench"

_ARRAY_SUMMARY_THRESHOLD = 200
_ARRAY_PREVIEW_LEN = 20


class MCPError(Exception):
    """Raised when an MCP tool call encounters a handled error."""


# ---------------------------------------------------------------------------
# JSON sanitizer
# ---------------------------------------------------------------------------

def _json_safe(obj: Any) -> Any:
    """Recursively convert *obj* into something ``json.dumps`` accepts.

    numpy scalars become Python numbers; small arrays become nested lists;
    arrays with more than _ARRAY_SUMMARY_THRESHOLD elements are summarized as
    {"shape", "dtype", "preview" (first _ARRAY_PREVIEW_LEN flat values),
    "summary": True}.  Anything unrecognized falls back to ``str(obj)``.
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        if obj.size > _ARRAY_SUMMARY_THRESHOLD:
            flat = obj.reshape(-1)[:_ARRAY_PREVIEW_LEN]
            return {
                "shape": [int(s) for s in obj.shape],
                "dtype": str(obj.dtype),
                "preview": [_json_safe(v) for v in flat.tolist()],
                "summary": True,
            }
        return [_json_safe(v) for v in obj.tolist()] if obj.dtype == object else obj.tolist()
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset, deque)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    if isinstance(obj, Path):
        return str(obj)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return _json_safe(dataclasses.asdict(obj))
    return str(obj)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class _ToolRegistry:
    """Registry of MCP tool definitions and their handlers."""

    def __init__(self):
        self.tools: dict[str, dict] = {}
        self._handlers: dict[str, callable] = {}

    def register(self, name: str, description: str, parameters: dict, handler: callable) -> None:
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
        }
        self._handlers[name] = handler

    def execute(self, name: str, params: Optional[dict[str, Any]]) -> Any:
        handler = self._handlers.get(name)
        if handler is None:
            raise MCPError(f"unknown tool: {name!r}")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise MCPError(f"tool parameters must be an object, got {type(params).__name__}")
        try:
            result = handler(**params)
        except MCPError:
            raise
        except TypeError as e:
            # Unknown / missing keyword arguments end up here.
            raise MCPError(f"invalid parameters for {name}: {e}") from e
        return _json_safe(result)


_server_instance: Optional["MCPServer"] = None
_server_lock = threading.Lock()
_registry: Optional[_ToolRegistry] = None


def _get_default_config() -> dict[str, Any]:
    return {
        "theme_mode": "dark",
        "log_level": "INFO",
        "max_results": 100,
        "auto_update": True,
    }


_config: dict[str, Any] = {}
_clients: dict[str, dict[str, Any]] = {}
# Stored benchmark results keyed by result_id (insertion-ordered).
_results: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Parameter validation helpers
# ---------------------------------------------------------------------------

def _require_int(name: str, value: Any) -> int:
    try:
        if isinstance(value, bool):
            raise TypeError
        return int(value)
    except (TypeError, ValueError):
        raise MCPError(f"parameter {name!r} must be an integer, got {value!r}") from None


def _require_float(name: str, value: Any) -> float:
    try:
        if isinstance(value, bool):
            raise TypeError
        return float(value)
    except (TypeError, ValueError):
        raise MCPError(f"parameter {name!r} must be a number, got {value!r}") from None


def _require_decoder(decoder_name: Any) -> str:
    if decoder_name not in be.DECODER_KINDS:
        raise MCPError(
            f"unknown decoder kind {decoder_name!r}; valid kinds: {', '.join(be.DECODER_KINDS)}"
        )
    return decoder_name


def _build_code(family: str, distance: int):
    try:
        return be.build_code(family, distance)
    except be.QectorError as e:
        raise MCPError(str(e)) from e


# ---------------------------------------------------------------------------
# Tool handlers (alphabetical)
# ---------------------------------------------------------------------------

def _handle_analyze_code_family(family_name: str = "rotated_surface", distance: int = 5) -> dict:
    distance = _require_int("distance", distance)
    try:
        info = be.get_code_family_info(family_name)
        code = be.build_code(family_name, distance)
        summary = be.code_summary(code)
        return {"family": info, "example": summary, "distance": distance, "status": "ok"}
    except be.QectorError as e:
        raise MCPError(str(e)) from e


def _handle_batch_decode(family: str = "rotated_surface", distance: int = 5,
                         backend: str = "cpu", n_samples: int = 100,
                         error_rate: float = 0.05, seed: int = 1) -> dict:
    distance = _require_int("distance", distance)
    n_samples = _require_int("n_samples", n_samples)
    error_rate = _require_float("error_rate", error_rate)
    seed = _require_int("seed", seed)
    code = _build_code(family, distance)
    try:
        result = be.run_batch_decode(code, str(backend), n_samples, error_rate, seed)
    except be.QectorError as e:
        raise MCPError(str(e)) from e
    result["family"] = family
    result["distance"] = distance
    result["error_rate"] = error_rate
    result["seed"] = seed
    return result


def _handle_benchmark_decoder(decoder_name: str = "union_find", code_family: str = "rotated_surface",
                              distance: int = 5, error_rate: float = 0.05,
                              n_samples: int = 100, seed: int = 42) -> dict:
    _require_decoder(decoder_name)
    distance = _require_int("distance", distance)
    error_rate = _require_float("error_rate", error_rate)
    n_samples = _require_int("n_samples", n_samples)
    seed = _require_int("seed", seed)
    code = _build_code(code_family, distance)
    try:
        result = be.run_benchmark(
            code,
            n_samples=n_samples,
            seed=seed,
            decoder_kind=decoder_name,
            error_rate=error_rate,
        )
    except be.QectorError as e:
        raise MCPError(str(e)) from e
    result["code_family"] = code_family
    result["distance"] = distance
    return result


def _handle_clear_results(confirm: bool = False) -> dict:
    if not confirm:
        raise MCPError("confirmation required: set confirm=True to clear all results")
    n = len(_results)
    _results.clear()
    return {"cleared": True, "removed": n, "status": "ok"}


def _handle_compare_benchmarks(benchmarks: list) -> dict:
    if not isinstance(benchmarks, (list, tuple)):
        raise MCPError("parameter 'benchmarks' must be a list of result ids")
    comparison: list[dict] = []
    missing: list[str] = []
    for rid in benchmarks:
        rid = str(rid)
        entry = _results.get(rid)
        if entry is None:
            missing.append(rid)
            continue
        comparison.append({
            "result_id": rid,
            "method": entry.get("method"),
            "code_family": entry.get("code_family"),
            "distance": entry.get("distance"),
            "p": entry.get("p"),
            "n_trials": entry.get("n_trials"),
            "throughput_decodes_per_s": entry.get("throughput_decodes_per_s"),
            "latency_p99_us": entry.get("latency_p99_us"),
            "logical_error_rate": entry.get("logical_error_rate"),
        })
    summary: dict[str, Any] = {}
    if comparison:
        by_throughput = max(comparison, key=lambda c: c["throughput_decodes_per_s"] or 0.0)
        summary["highest_throughput"] = by_throughput["result_id"]
        with_ler = [c for c in comparison if c["logical_error_rate"] is not None]
        if with_ler:
            summary["lowest_logical_error_rate"] = min(
                with_ler, key=lambda c: c["logical_error_rate"]
            )["result_id"]
    return {"comparison": comparison, "missing": missing, "count": len(comparison),
            "summary": summary}


def _handle_decode_single(family: str = "rotated_surface", distance: int = 5,
                          decoder_name: str = "union_find", error_rate: float = 0.05,
                          seed: int = 42) -> dict:
    _require_decoder(decoder_name)
    distance = _require_int("distance", distance)
    error_rate = _require_float("error_rate", error_rate)
    seed = _require_int("seed", seed)
    code = _build_code(family, distance)
    try:
        out = be.run_single_decode(code, error_rate, decoder_name, seed)
    except be.QectorError as e:
        raise MCPError(str(e)) from e
    res = out["result"]
    error = np.asarray(out["error"])
    syndrome = np.asarray(out["syndrome"])
    return {
        "family": family,
        "distance": distance,
        "decoder": decoder_name,
        "error_rate": error_rate,
        "seed": seed,
        "n_qubits": int(code.n_qubits),
        "n_checks": int(code.n_checks),
        "error_weight": int(error.sum()),
        "syndrome_weight": int(syndrome.sum()),
        "hamming_weight": res.hamming_weight,
        "syndrome_valid": res.syndrome_valid,
        "logical_failure": res.logical_failure,
        "correction": np.asarray(res.correction, dtype=np.uint8),
    }


def _handle_delete_resource(resource_id: str, confirm: bool = False) -> dict:
    if not confirm:
        raise MCPError("confirmation required: set confirm=True to delete resource")
    rm = get_resource_manager()
    ok = rm.delete_resource(resource_id)
    if not ok:
        raise MCPError(f"resource not found: {resource_id!r}")
    return {"deleted": True, "resource_id": resource_id}


def _handle_export_benchmark(benchmark_id: str, format: str = "json") -> dict:
    if format != "json":
        raise MCPError(f"unsupported export format: {format!r} (only 'json' is supported)")
    benchmark_id = str(benchmark_id)
    entry = _results.get(benchmark_id)
    if entry is None:
        raise MCPError(
            f"unknown benchmark id {benchmark_id!r}; run the run_benchmark tool first "
            f"({len(_results)} stored result(s))"
        )
    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", benchmark_id) or "benchmark"
    path = utils.get_export_dir() / f"benchmark_{safe_id}.json"
    try:
        path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
        size = int(path.stat().st_size)
    except OSError as e:
        raise MCPError(f"export failed: {e}") from e
    return {"benchmark_id": benchmark_id, "format": "json",
            "path": str(path.resolve()), "size": size}


def _handle_generate_documentation(family_key: str = "ring", param: int = 6,
                                   formats: Optional[list[str]] = None) -> dict:
    if formats is None:
        formats = ["json"]
    try:
        from doc_generator import ProfessionalDocGenerator
    except Exception as e:
        raise MCPError(f"documentation generator unavailable: {e}") from e
    try:
        code = be.build_code(family_key, _require_int("param", param))
        gen = ProfessionalDocGenerator()
        paths_map = gen.generate_all(code, formats=list(formats))
        return {
            "family": family_key,
            "param": param,
            "formats": {fmt: str(p) for fmt, (ok, p) in paths_map.items() if ok},
            "failed_formats": [fmt for fmt, (ok, _) in paths_map.items() if not ok],
            "status": "ok",
        }
    except be.QectorError as e:
        raise MCPError(str(e)) from e


def _handle_get_code_properties(family_name: str = "ring", distance: int = 5) -> dict:
    distance = _require_int("distance", distance)
    try:
        code = be.build_code(family_name, distance)
        summary = be.code_summary(code)
        info = be.get_code_family_info(family_name)
        return {"properties": summary, "info": info, "status": "ok"}
    except be.QectorError as e:
        raise MCPError(str(e)) from e


def _handle_get_config() -> dict:
    return dict(_get_default_config(), **_config)


def _handle_get_decoder_info(decoder_name: str = "bp_osd") -> dict:
    _require_decoder(decoder_name)
    info = be.get_decoder_info(decoder_name)
    return {"name": info["name"], "description": info["description"], "available": True}


def _handle_get_hardware_info() -> dict:
    try:
        from hardware_routing import detect_hardware
        hw = detect_hardware()
        return {"cuda": hw.cuda_rust, "gpu": hw.gpu, "opencl": hw.opencl,
                "opencl_device": hw.opencl_device}
    except Exception:
        return {"cuda": False, "gpu": None, "opencl": False, "opencl_device": None,
                "_fallback": True}


def _handle_get_resource(resource_id: str) -> dict:
    rm = get_resource_manager()
    r = rm.get_resource(resource_id)
    if r is None:
        raise MCPError(f"resource not found: {resource_id!r}")
    return r


def _handle_get_resources() -> dict:
    rm = get_resource_manager()
    resources = rm.list_resources()
    return {"resources": resources, "count": len(resources)}


def _handle_get_results(limit: int = 10) -> dict:
    limit = _require_int("limit", limit)
    if limit < 1:
        raise MCPError("parameter 'limit' must be >= 1")
    stored = list(_results.values())
    return {"results": stored[-limit:], "total": len(stored), "limit": limit}


def _handle_get_statistics() -> dict:
    return {"total_results": len(_results), "total_clients": len(_clients),
            "config_keys": len(_config)}


def _handle_get_system_info() -> dict:
    info = {
        "platform": platform.platform(),
        "python": sys.version,
        "hostname": platform.node(),
        "workbench_version": WORKBENCH_VERSION,
        "backend_version": be.PACKAGE_VERSION,
    }
    if _HAS_PSUTIL:
        try:
            info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            info["memory_percent"] = psutil.virtual_memory().percent
        except Exception:
            pass
    return info


def _handle_list_clients() -> dict:
    return {"clients": [{"id": cid, **data} for cid, data in _clients.items()],
            "count": len(_clients)}


def _handle_list_code_families() -> dict:
    families = [be.get_code_family_info(key) for key in be.CODE_FAMILIES]
    return {"families": families, "count": len(families)}


def _handle_list_decoders() -> dict:
    return {"decoders": [be.get_decoder_info(d) for d in be.DECODER_KINDS],
            "count": len(be.DECODER_KINDS)}


def _handle_list_tools() -> dict:
    return {"tools": list(_registry.tools.values()), "count": len(_registry.tools)}


def _handle_mcp_status() -> dict:
    return {"status": "running", "uptime": time.monotonic(),
            "version": WORKBENCH_VERSION, "backend": be.PACKAGE_VERSION,
            "protocol_version": PROTOCOL_VERSION, "tools": len(_registry.tools)}


def _handle_recommend_decoder(family: str = "rotated_surface", distance: int = 5,
                              n_qubits: Optional[int] = None,
                              priority: str = "balanced") -> dict:
    try:
        from hardware_routing import recommend
    except Exception as e:
        raise MCPError(f"hardware routing unavailable: {e}") from e
    distance_v = None if distance is None else _require_int("distance", distance)
    n_qubits_v = None if n_qubits is None else _require_int("n_qubits", n_qubits)
    try:
        rec = recommend(family, distance_v, n_qubits_v, str(priority))
    except ValueError as e:
        raise MCPError(str(e)) from e
    except Exception as e:
        raise MCPError(f"recommendation failed: {e}") from e
    return dataclasses.asdict(rec)


def _handle_register_client(client_id: str, access_level: str = "USER") -> dict:
    _clients[client_id] = {"access_level": access_level, "registered_at": time.time()}
    return {"client_id": client_id, "access_level": access_level, "status": "registered"}


def _handle_reset_config(confirm: bool = False) -> dict:
    if not confirm:
        raise MCPError("confirmation required: set confirm=True to reset config")
    _config.clear()
    return {"reset": True, "config": _get_default_config()}


def _handle_run_benchmark(code_family: str = "rotated_surface", distance: int = 5,
                          decoder_name: str = "union_find", n_samples: int = 100,
                          seed: int = 42, error_rate: float = 0.05) -> dict:
    result = _handle_benchmark_decoder(
        decoder_name=decoder_name,
        code_family=code_family,
        distance=distance,
        error_rate=error_rate,
        n_samples=n_samples,
        seed=seed,
    )
    result_id = uuid.uuid4().hex
    entry = _json_safe(dict(result, result_id=result_id))
    _results[result_id] = entry
    return entry


def _handle_set_config(config: dict) -> dict:
    if not isinstance(config, dict):
        raise MCPError("parameter 'config' must be an object mapping keys to values")
    _config.update(config)
    return {"updated": sorted(str(k) for k in config),
            "config": dict(_get_default_config(), **_config)}


def _handle_stream_decode(family: str = "rotated_surface", distance: int = 5,
                          window_size: int = 5, n_rounds: int = 10,
                          error_rate: float = 0.03, seed: int = 1,
                          decoder_name: str = "union_find") -> dict:
    _require_decoder(decoder_name)
    distance = _require_int("distance", distance)
    window_size = _require_int("window_size", window_size)
    n_rounds = _require_int("n_rounds", n_rounds)
    error_rate = _require_float("error_rate", error_rate)
    seed = _require_int("seed", seed)
    code = _build_code(family, distance)
    try:
        result = be.run_streaming_session(
            code,
            window_size=window_size,
            n_rounds=n_rounds,
            error_rate=error_rate,
            seed=seed,
            decoder_kind=decoder_name,
        )
    except be.QectorError as e:
        raise MCPError(str(e)) from e
    result["family"] = family
    result["distance"] = distance
    result["decoder"] = decoder_name
    result["error_rate"] = error_rate
    result["seed"] = seed
    return result


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

class MCPServer:
    """MCP Server providing all QECTOR tools."""

    def __init__(self):
        self.tools = _registry

    def describe(self) -> dict:
        return {"name": SERVER_NAME, "version": WORKBENCH_VERSION,
                "backend_version": be.PACKAGE_VERSION,
                "protocol_version": PROTOCOL_VERSION,
                "tools": len(_registry.tools)}


def get_mcp_server() -> MCPServer:
    """Get or create the singleton MCP server instance."""
    global _server_instance
    if _server_instance is None:
        with _server_lock:
            if _server_instance is None:
                _build_registry()
                _server_instance = MCPServer()
    return _server_instance


def _build_registry() -> None:
    global _registry
    _registry = _ToolRegistry()
    _decoder_desc = "One of: " + ", ".join(be.DECODER_KINDS)
    _family_desc = "One of: " + ", ".join(be.CODE_FAMILIES)

    _registry.register(
        "analyze_code_family", "Analyze a code family with an example code instance",
        {"family_name": {"type": "string", "default": "rotated_surface", "description": _family_desc},
         "distance": {"type": "integer", "default": 5}},
        _handle_analyze_code_family)
    _registry.register(
        "batch_decode", "Batch-decode sampled syndromes on cpu/cuda/opencl via backend.run_batch_decode",
        {"family": {"type": "string", "default": "rotated_surface", "description": _family_desc},
         "distance": {"type": "integer", "default": 5},
         "backend": {"type": "string", "default": "cpu",
                     "description": "One of: cpu, cuda, opencl (no silent fallback)"},
         "n_samples": {"type": "integer", "default": 100},
         "error_rate": {"type": "number", "default": 0.05},
         "seed": {"type": "integer", "default": 1}},
        _handle_batch_decode)
    _registry.register(
        "benchmark_decoder", "Benchmark a decoder on a code family via backend.run_benchmark "
                             "(latency percentiles, throughput, logical error rate)",
        {"decoder_name": {"type": "string", "default": "union_find", "description": _decoder_desc},
         "code_family": {"type": "string", "default": "rotated_surface", "description": _family_desc},
         "distance": {"type": "integer", "default": 5},
         "error_rate": {"type": "number", "default": 0.05},
         "n_samples": {"type": "integer", "default": 100},
         "seed": {"type": "integer", "default": 42}},
        _handle_benchmark_decoder)
    _registry.register(
        "clear_results", "Clear all stored benchmark results",
        {"confirm": {"type": "boolean", "default": False}},
        _handle_clear_results)
    _registry.register(
        "compare_benchmarks", "Compare stored benchmark results side by side "
                              "(throughput, p99 latency, logical error rate)",
        {"benchmarks": {"type": "array", "items": {"type": "string"},
                        "description": "result_id values returned by the run_benchmark tool"}},
        _handle_compare_benchmarks)
    _registry.register(
        "decode_single", "Run one seeded decode and report correction weight, syndrome validity "
                         "and logical failure",
        {"family": {"type": "string", "default": "rotated_surface", "description": _family_desc},
         "distance": {"type": "integer", "default": 5},
         "decoder_name": {"type": "string", "default": "union_find", "description": _decoder_desc},
         "error_rate": {"type": "number", "default": 0.05},
         "seed": {"type": "integer", "default": 42}},
        _handle_decode_single)
    _registry.register(
        "delete_resource", "Delete a resource by ID",
        {"resource_id": {"type": "string"},
         "confirm": {"type": "boolean", "default": False}},
        _handle_delete_resource)
    _registry.register(
        "export_benchmark", "Export a stored benchmark result (by result_id) to the export directory",
        {"benchmark_id": {"type": "string",
                          "description": "result_id returned by the run_benchmark tool"},
         "format": {"type": "string", "default": "json"}},
        _handle_export_benchmark)
    _registry.register(
        "generate_documentation", "Generate code documentation files",
        {"family_key": {"type": "string", "default": "ring", "description": _family_desc},
         "param": {"type": "integer", "default": 6},
         "formats": {"type": "array", "default": ["json"],
                     "description": "Any of: json, markdown, html, latex, pdf"}},
        _handle_generate_documentation)
    _registry.register(
        "get_code_properties", "Get properties of a code family",
        {"family_name": {"type": "string", "default": "ring", "description": _family_desc},
         "distance": {"type": "integer", "default": 5}},
        _handle_get_code_properties)
    _registry.register(
        "get_config", "Get current server configuration", {},
        _handle_get_config)
    _registry.register(
        "get_decoder_info", "Get information about a decoder",
        {"decoder_name": {"type": "string", "default": "bp_osd", "description": _decoder_desc}},
        _handle_get_decoder_info)
    _registry.register(
        "get_hardware_info", "Get hardware/backend availability", {},
        _handle_get_hardware_info)
    _registry.register(
        "get_resource", "Get a specific resource by ID",
        {"resource_id": {"type": "string"}},
        _handle_get_resource)
    _registry.register(
        "get_resources", "List all resources", {},
        _handle_get_resources)
    _registry.register(
        "get_results", "Get stored benchmark results (most recent first-in order)",
        {"limit": {"type": "integer", "default": 10}},
        _handle_get_results)
    _registry.register(
        "get_statistics", "Get server statistics", {},
        _handle_get_statistics)
    _registry.register(
        "get_system_info", "Get system information", {},
        _handle_get_system_info)
    _registry.register(
        "list_clients", "List registered clients", {},
        _handle_list_clients)
    _registry.register(
        "list_code_families", "List available code families", {},
        _handle_list_code_families)
    _registry.register(
        "list_decoders", "List available decoders", {},
        _handle_list_decoders)
    _registry.register(
        "list_tools", "List all available MCP tools", {},
        _handle_list_tools)
    _registry.register(
        "mcp_status", "Get MCP server status", {},
        _handle_mcp_status)
    _registry.register(
        "recommend_decoder", "Recommend a decoder for a code/priority using detected hardware",
        {"family": {"type": "string", "default": "rotated_surface", "description": _family_desc},
         "distance": {"type": "integer", "default": 5},
         "n_qubits": {"type": ["integer", "null"], "default": None},
         "priority": {"type": "string", "default": "balanced",
                      "description": "One of: balanced, speed, accuracy"}},
        _handle_recommend_decoder)
    _registry.register(
        "register_client", "Register a client",
        {"client_id": {"type": "string"},
         "access_level": {"type": "string", "default": "USER"}},
        _handle_register_client)
    _registry.register(
        "reset_config", "Reset configuration to defaults",
        {"confirm": {"type": "boolean", "default": False}},
        _handle_reset_config)
    _registry.register(
        "run_benchmark", "Run a benchmark and store the result under a generated result_id",
        {"code_family": {"type": "string", "default": "rotated_surface", "description": _family_desc},
         "distance": {"type": "integer", "default": 5},
         "decoder_name": {"type": "string", "default": "union_find", "description": _decoder_desc},
         "n_samples": {"type": "integer", "default": 100},
         "seed": {"type": "integer", "default": 42},
         "error_rate": {"type": "number", "default": 0.05}},
        _handle_run_benchmark)
    _registry.register(
        "set_config", "Merge key/value pairs into the server configuration",
        {"config": {"type": "object",
                    "description": "Key/value pairs merged into the current configuration"}},
        _handle_set_config)
    _registry.register(
        "stream_decode", "Run a sliding-window streaming decode session via "
                         "backend.run_streaming_session",
        {"family": {"type": "string", "default": "rotated_surface", "description": _family_desc},
         "distance": {"type": "integer", "default": 5},
         "window_size": {"type": "integer", "default": 5},
         "n_rounds": {"type": "integer", "default": 10},
         "error_rate": {"type": "number", "default": 0.03},
         "seed": {"type": "integer", "default": 1},
         "decoder_name": {"type": "string", "default": "union_find", "description": _decoder_desc}},
        _handle_stream_decode)


async def call_mcp_tool(name: str, params: dict[str, Any]) -> Any:
    """Call an MCP tool by name with the given parameters (JSON-safe result)."""
    server = get_mcp_server()
    try:
        return server.tools.execute(name, params)
    except MCPError:
        raise
    except Exception as e:
        raise MCPError(f"{name} failed: {e}") from e


# ---------------------------------------------------------------------------
# MCP stdio transport (newline-delimited JSON-RPC 2.0)
# ---------------------------------------------------------------------------

class _MethodNotFound(Exception):
    """Requested JSON-RPC method is not implemented."""


class _InvalidParams(Exception):
    """JSON-RPC params are structurally invalid."""


def _log(msg: str) -> None:
    """Log to stderr only — stdout is reserved for JSON-RPC messages."""
    try:
        print(f"[{SERVER_NAME}] {msg}", file=sys.stderr, flush=True)
    except Exception:
        pass


def _error_response(msg_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _tool_input_schema(parameters: dict) -> dict:
    """Build a JSON Schema object from a registry parameter table."""
    properties: dict[str, dict] = {}
    required: list[str] = []
    for pname, spec in parameters.items():
        prop: dict[str, Any] = {}
        if "type" in spec:
            prop["type"] = spec["type"]
        if "description" in spec:
            prop["description"] = spec["description"]
        if "items" in spec:
            prop["items"] = spec["items"]
        if "default" in spec:
            prop["default"] = _json_safe(spec["default"])
        else:
            required.append(pname)
        properties[pname] = prop
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _list_tools_payload() -> dict:
    server = get_mcp_server()
    return {
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": _tool_input_schema(t["parameters"]),
            }
            for t in server.tools.tools.values()
        ]
    }


async def _handle_tools_call(params: Any) -> dict:
    if not isinstance(params, dict):
        raise _InvalidParams("params must be an object with 'name' and 'arguments'")
    name = params.get("name")
    if not isinstance(name, str) or not name:
        raise _InvalidParams("params.name (tool name) is required")
    arguments = params.get("arguments")
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise _InvalidParams("params.arguments must be an object")
    try:
        result = await call_mcp_tool(name, arguments)
    except MCPError as e:
        # Tool-level error: JSON-RPC success with isError=True per MCP spec.
        return {"content": [{"type": "text", "text": str(e)}], "isError": True}
    try:
        text = json.dumps(result)
    except (TypeError, ValueError) as e:
        _log(f"result serialization failed for {name}: {e}")
        return {"content": [{"type": "text", "text": f"result serialization failed: {e}"}],
                "isError": True}
    return {"content": [{"type": "text", "text": text}], "isError": False}


async def _dispatch_method(method: Any, params: Any) -> Any:
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": WORKBENCH_VERSION},
        }
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {}
    if method == "tools/list":
        return _list_tools_payload()
    if method == "tools/call":
        return await _handle_tools_call(params)
    raise _MethodNotFound(str(method))


async def _dispatch_line(line: str) -> Optional[dict]:
    """Handle one JSON-RPC line; return the response dict or None (notification)."""
    try:
        msg = json.loads(line)
    except json.JSONDecodeError as e:
        return _error_response(None, -32700, f"parse error: {e}")
    if not isinstance(msg, dict):
        return _error_response(None, -32600, "invalid request: expected a JSON object")
    is_notification = "id" not in msg
    msg_id = msg.get("id")
    method = msg.get("method")
    try:
        result = await _dispatch_method(method, msg.get("params"))
    except _MethodNotFound:
        if is_notification:
            _log(f"ignoring unknown notification {method!r}")
            return None
        return _error_response(msg_id, -32601, f"method not found: {method!r}")
    except _InvalidParams as e:
        if is_notification:
            return None
        return _error_response(msg_id, -32602, f"invalid params: {e}")
    except Exception as e:
        _log(f"handler for {method!r} crashed:\n{traceback.format_exc()}")
        if is_notification:
            return None
        return _error_response(msg_id, -32603, f"internal error: {e}")
    if is_notification:
        return None
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _write_message(stdout, message: dict) -> None:
    try:
        text = json.dumps(message)
    except (TypeError, ValueError) as e:
        _log(f"response serialization failed: {e}")
        text = json.dumps(_error_response(message.get("id"), -32603,
                                          "internal error: unserializable response"))
    try:
        stdout.write(text + "\n")
        stdout.flush()
    except Exception as e:
        _log(f"stdout write failed: {e}")


async def serve_stdio() -> int:
    """Serve MCP over newline-delimited JSON-RPC 2.0 on stdin/stdout.

    The loop never dies from a handler exception; it exits cleanly on EOF.
    """
    server = get_mcp_server()
    loop = asyncio.get_running_loop()
    stdin = sys.stdin
    stdout = sys.stdout
    _log(f"stdio server ready: {len(server.tools.tools)} tools, protocol {PROTOCOL_VERSION}, "
         f"workbench {WORKBENCH_VERSION}, backend {be.PACKAGE_VERSION}")
    while True:
        try:
            line = await loop.run_in_executor(None, stdin.readline)
        except Exception as e:
            _log(f"stdin read failed: {e}")
            return 1
        if line == "":
            _log("stdin closed; shutting down")
            return 0
        line = line.strip()
        if not line:
            continue
        try:
            response = await _dispatch_line(line)
        except Exception as e:  # absolute last resort — keep serving
            _log(f"dispatch crashed:\n{traceback.format_exc()}")
            response = _error_response(None, -32603, f"internal error: {e}")
        if response is not None:
            _write_message(stdout, response)


def main() -> int:
    """Entry point for `python mcp_server.py` — run the stdio MCP server."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        return asyncio.run(serve_stdio())
    except KeyboardInterrupt:
        _log("interrupted; shutting down")
        return 0


if __name__ == "__main__":
    sys.exit(main())
