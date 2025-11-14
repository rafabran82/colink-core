import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class NDJSONLogger:
    """
    Simple NDJSON logger for AMM events (swaps, LP actions, snapshots).
    """

    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_file(self, name: str) -> Path:
        path = self.base_dir / name
        if not path.exists():
            # touch file
            path.write_text("", encoding="utf-8")
        return path

    def append_event(self, name: str, payload: Dict[str, Any]) -> None:
        """
        Append a single JSON object as one line to <name>.ndjson.
        """
        path = self._ensure_file(f"{name}.ndjson")
        # Ensure timestamps are ISO strings if present
        data = payload.copy()
        ts = data.get("timestamp")
        if isinstance(ts, datetime):
            data["timestamp"] = ts.isoformat()

        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, separators=(",", ":")) + "\n")
