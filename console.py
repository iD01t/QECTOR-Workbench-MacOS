"""console.py — Console output buffer for QECTOR Workbench."""

from __future__ import annotations


class Console:
    """In-memory console buffer with optional callback on new output."""

    def __init__(self):
        self._lines: list[str] = []
        self._callbacks: list = []

    def write(self, text: str) -> None:
        self._lines.append(text)
        for cb in self._callbacks:
            try:
                cb(text)
            except Exception:
                pass

    def log(self, text: str, level: str = "INFO") -> None:
        self.write(f"[{level}] {text}\n")

    def get_text(self) -> str:
        return "".join(self._lines)

    def clear(self) -> None:
        self._lines.clear()
