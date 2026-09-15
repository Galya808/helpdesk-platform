import json
import logging
from datetime import UTC, datetime
from typing import Any

HTTP_LOG_FIELDS = (
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in HTTP_LOG_FIELDS:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        if record.exc_info is not None:
            log_data["exception"] = self.formatException(
                record.exc_info,
            )

        return json.dumps(
            log_data,
            ensure_ascii=False,
        )
