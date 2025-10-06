import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog


def _configure_structlog() -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger()


_logger = None

def get_logger() -> structlog.stdlib.BoundLogger:
    global _logger
    if _logger is None:
        _logger = _configure_structlog()
    return _logger


class Tracer:
    """Persist traces as a JSON array on disk and in memory."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()
        self._in_memory: List[Dict[str, Any]] = []
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")
        else:
            try:
                self._in_memory = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(self._in_memory, list):
                    self._in_memory = []
            except Exception:
                self._in_memory = []

    def add(self, entry: Dict[str, Any]) -> None:
        with self._lock:
            self._in_memory.append(entry)
            try:
                self.path.write_text(json.dumps(self._in_memory, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                # Fail silently to avoid breaking user flow
                pass

    def read_all(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._in_memory)

    def read_one(self, trace_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            for item in self._in_memory:
                if item.get("id") == trace_id:
                    return item
        return None
