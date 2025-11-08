from __future__ import annotations

import json
import os
import platform
import socket
import sys
import time
from datetime import UTC, datetime
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def detect_run_metadata(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    md: dict[str, Any] = {
        "ts_iso": _utc_now_iso(),
        "ts_unix": time.time(),
        "host": socket.gethostname(),
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "cwd": os.getcwd(),
        "env": {
            k: os.environ.get(k)
            for k in [
                "GITHUB_RUN_ID",
                "GITHUB_RUN_NUMBER",
                "GITHUB_REPOSITORY",
                "GITHUB_SHA",
                "GITHUB_REF",
                "GITHUB_WORKFLOW",
                "pythonLocation",
                "CI",
            ]
            if os.environ.get(k) is not None
        },
    }
    if extra:
        md.update(extra)
    return md


class NDJSONWriter:
    """
    Minimal newline-delimited JSON writer with flush-on-write semantics.
    Use as a context manager: `with NDJSONWriter(path) as w: ...`.
    """

    def __init__(self, path: str, mode: str = "a", auto_flush: bool = True):
        self.path = path
        self.mode = mode
        self.auto_flush = auto_flush
        self._fp = None  # type: Optional[object]
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def write(self, record: dict[str, Any]) -> None:
        if self._fp is None:
            raise RuntimeError("NDJSONWriter not opened; use `with NDJSONWriter(...)`.")
        self._fp.write(json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n")
        if self.auto_flush:
            self._fp.flush()

    def close(self) -> None:
        if self._fp is not None:
            try:
                self._fp.flush()
            finally:
                self._fp.close()
                self._fp = None

    def __enter__(self):
        # Open here; keep handle for the duration of the with-block.
        self._fp = open(self.path, self.mode, encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


def event(
    kind: str,
    payload: dict[str, Any],
    run_id: str | None = None,
    component: str = "sim",
    level: str = "info",
) -> dict[str, Any]:
    return {
        "ts": _utc_now_iso(),
        "kind": kind,
        "level": level,
        "component": component,
        "run_id": run_id,
        "payload": payload,
        "version": 1,
    }
