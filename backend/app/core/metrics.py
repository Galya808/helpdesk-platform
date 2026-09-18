from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

METRICS_REGISTRY = CollectorRegistry()

HTTP_REQUESTS_TOTAL = Counter(
    "helpdesk_http_requests",
    "Total number of completed HTTP requests",
    labelnames=["method", "route", "status_code"],
    registry=METRICS_REGISTRY,
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "helpdesk_http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "route", "status_code"],
    registry=METRICS_REGISTRY,
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "helpdesk_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    labelnames=["method"],
    registry=METRICS_REGISTRY,
)
