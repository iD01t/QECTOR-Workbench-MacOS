"""threading_utils.py — Threading utilities for QECTOR Workbench."""

from __future__ import annotations

import threading
from typing import Callable, Optional


def run_in_background(target: Callable, args: tuple = (), daemon: bool = True) -> threading.Thread:
    """Run a function in a background thread."""
    t = threading.Thread(target=target, args=args, daemon=daemon)
    t.start()
    return t


class CancelToken:
    """Cooperative cancellation token for background tasks."""

    def __init__(self):
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()
