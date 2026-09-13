from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "x-amz-security-token"}


@dataclass
class LogRecord:
    timestamp: str
    level: str
    logger: str
    message: str
    fields: dict[str, Any]


@dataclass
class MemoryLogger:
    name: str
    records: list[LogRecord] = field(default_factory=list)

    def _emit(self, level: str, message: str, **fields: Any) -> LogRecord:
        record = LogRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            logger=self.name,
            message=message,
            fields=fields,
        )
        self.records.append(record)
        return record

    def info(self, message: str, **fields: Any) -> LogRecord:
        return self._emit("INFO", message, **fields)

    def warn(self, message: str, **fields: Any) -> LogRecord:
        return self._emit("WARN", message, **fields)

    def error(self, message: str, **fields: Any) -> LogRecord:
        return self._emit("ERROR", message, **fields)


_LOGGERS: dict[str, MemoryLogger] = {}


def get_logger(name: str) -> MemoryLogger:
    if name not in _LOGGERS:
        _LOGGERS[name] = MemoryLogger(name)
    return _LOGGERS[name]


def reset_logs() -> None:
    _LOGGERS.clear()


def dump_logs() -> list[str]:
    lines: list[str] = []
    for logger in _LOGGERS.values():
        for record in logger.records:
            extras = " ".join(f"{key}={_fmt(value)}" for key, value in record.fields.items())
            lines.append(f"{record.timestamp} {record.level} {record.logger} {record.message} {extras}".rstrip())
    return lines


def _fmt(value: Any) -> str:
    text = str(value)
    if " " in text:
        return f"\"{text}\""
    return text


def log_request(request: Any) -> None:
    from reportly.config import settings

    logger = get_logger("reportly.http")
    payload: dict[str, Any] = {
        "rid": getattr(request, "request_id", ""),
        "method": getattr(request, "method", ""),
        "path": getattr(request, "path", ""),
    }
    headers = dict(getattr(request, "headers", {}) or {})
    if settings.log_request_headers:
        if settings.redact_secrets:
            payload["headers"] = {
                key: "***" if key.lower() in SENSITIVE_HEADERS else value
                for key, value in headers.items()
            }
        else:
            payload.update({key.lower(): value for key, value in headers.items()})
    logger.info("inbound", **payload)
