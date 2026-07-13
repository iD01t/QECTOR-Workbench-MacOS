"""
tests/conftest.py — Shared pytest fixtures for QECTOR tests.
"""

from __future__ import annotations

import sys
import pytest

# Ensure local imports resolve without installation
sys.path.insert(0, ".")

@pytest.fixture(scope="session")
def app_imports():
    """Import all local GUI modules once per session to verify they load."""
    import app  # noqa: F401
    import backend as be  # noqa: F401
    import code_explorer_tab  # noqa: F401
    import decoder_lab_tab  # noqa: F401
    import benchmark_tab  # noqa: F401
    import batch_streaming_tab  # noqa: F401
    import hardware_tab  # noqa: F401
    import mcp_server  # noqa: F401
    import doc_generator  # noqa: F401
    import dialogs  # noqa: F401
    import documentation_tab  # noqa: F401
    import state  # noqa: F401
    import theme  # noqa: F401
    import console  # noqa: F401
    import threading_utils  # noqa: F401
    import utils  # noqa: F401
    import logger as qector_logger  # noqa: F401
    return True

@pytest.fixture(scope="session")
def backend(app_imports):
    import backend as be
    return be

@pytest.fixture(scope="session")
def code_families(backend):
    return backend.CODE_FAMILIES

@pytest.fixture(scope="session")
def decoder_kinds(backend):
    return backend.DECODER_KINDS

@pytest.fixture(scope="session")
def default_code(backend):
    return backend.build_code("rotated_surface", 5)

@pytest.fixture(scope="session")
def repetition_code(backend):
    return backend.build_code("repetition", 5)

@pytest.fixture(scope="session")
def ring_code(backend):
    return backend.build_code("ring", 6)

@pytest.fixture(scope="session")
def heavy_hex_code(backend):
    return backend.build_code("heavy_hex", 5)

@pytest.fixture(scope="session")
def toric_code(backend):
    return backend.build_code("toric", 4)
