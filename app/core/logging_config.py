import json
import logging
import sys
from datetime import datetime, timezone


class SafeJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "correlation_id": getattr(record, "correlation_id", "system"),
                "operation": getattr(record, "operation", "system"),
                "outcome": getattr(record, "outcome", record.getMessage()),
                "duration_ms": getattr(record, "duration_ms", 0.0),
                "status_code": getattr(record, "status_code", None),
            },
            separators=(",", ":"),
        )


def configure_logging() -> None:
    logger = logging.getLogger("banking_api")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(getattr(handler, "_banking_json_handler", False) for handler in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(SafeJsonFormatter())
        handler._banking_json_handler = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
