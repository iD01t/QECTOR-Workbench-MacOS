"""tests/test_memory.py — Memory leak guard.

Runs 200 decode iterations and monitors RSS growth.  Flags >10 MB growth
per 200 iterations, which would indicate a leak in the decoder or backend.
"""
import os
import pytest

import backend as be

N_ITERATIONS = 200
MAX_GROWTH_MB = 10.0

FAMILY = "rotated_surface"
DISTANCE = 5
DECODER = "union_find"
ERROR_RATE = 0.05


def _get_rss_mb() -> float:
    """Return current RSS in megabytes (cross-platform)."""
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    # Fallback for Windows without psutil
    try:
        import ctypes
        import ctypes.wintypes
        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.wintypes.DWORD),
                ("PageFaultCount", ctypes.wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(pmc)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
            return pmc.WorkingSetSize / (1024 * 1024)
    except Exception:
        pass
    # Last resort: /proc on Linux
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024  # kB -> MB
    except Exception:
        pass
    pytest.skip("Cannot read RSS on this platform")
    return 0.0


@pytest.mark.skipif(
    os.environ.get("QECTOR_SKIP_MEMORY") == "1",
    reason="QECTOR_SKIP_MEMORY=1",
)
def test_no_memory_leak():
    """Run N_ITERATIONS decodes and verify RSS does not grow excessively."""
    code = be.build_code(FAMILY, DISTANCE)

    # Warm up — first few decodes allocate caches, JIT, etc.
    for i in range(10):
        be.run_single_decode(code, ERROR_RATE, DECODER, seed=i)

    rss_before = _get_rss_mb()

    for i in range(N_ITERATIONS):
        be.run_single_decode(code, ERROR_RATE, DECODER, seed=1000 + i)

    rss_after = _get_rss_mb()
    growth = rss_after - rss_before

    assert growth < MAX_GROWTH_MB, (
        f"RSS grew {growth:.1f} MB over {N_ITERATIONS} iterations "
        f"(before={rss_before:.1f} MB, after={rss_after:.1f} MB, "
        f"limit={MAX_GROWTH_MB} MB)"
    )
