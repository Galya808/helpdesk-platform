import json
import logging

from app.core.logging import JsonFormatter


def test_json_formatter_produces_structured_log() -> None:
    # Arrange
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request completed",
        args=(),
        exc_info=None,
    )

    # Act
    formatted_log = formatter.format(record)
    log_data = json.loads(formatted_log)

    # Assert
    assert log_data["level"] == "INFO"
    assert log_data["logger"] == "app.test"
    assert log_data["message"] == "request completed"
    assert log_data["timestamp"] is not None


def test_json_formatter_includes_http_context() -> None:
    # Arrange
    formatter = JsonFormatter()
    record = logging.makeLogRecord(
        {
            "name": "app.http",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "request completed",
            "args": (),
            "request_id": "request-id",
            "method": "GET",
            "path": "/health",
            "status_code": 200,
            "duration_ms": 12.5,
        }
    )

    # Act
    formatted_log = formatter.format(record)
    log_data = json.loads(formatted_log)

    # Assert
    assert log_data["request_id"] == "request-id"
    assert log_data["method"] == "GET"
    assert log_data["path"] == "/health"
    assert log_data["status_code"] == 200
    assert log_data["duration_ms"] == 12.5


def test_json_formatter_ignores_sensitive_extra_fields() -> None:
    # Arrange
    formatter = JsonFormatter()
    record = logging.makeLogRecord(
        {
            "name": "app.http",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "request completed",
            "args": (),
            "request_id": "request-id",
            "password": "secret-password",
            "authorization": "Bearer secret-token",
            "access_token": "secret-token",
        }
    )

    # Act
    formatted_log = formatter.format(record)
    log_data = json.loads(formatted_log)

    # Assert
    assert "password" not in log_data
    assert "authorization" not in log_data
    assert "access_token" not in log_data

    assert log_data["request_id"] == "request-id"
