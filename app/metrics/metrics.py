"""Prometheus metrics for LLM Gateway API."""

from prometheus_client import Counter, Histogram

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "endpoint", "status_code"],
)

http_errors_total = Counter(
    "http_errors_total",
    "Total HTTP errors",
    labelnames=["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "endpoint", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# LLM metrics
llm_calls_total = Counter(
    "llm_calls_total",
    "Total LLM API calls",
    labelnames=["provider", "model", "outcome"],
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    labelnames=["provider", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

llm_grounding_total = Counter(
    "llm_grounding_total",
    "Total LLM grounding requests",
    labelnames=["reason"],
)

llm_fallback_total = Counter(
    "llm_fallback_total",
    "Total LLM fallback invocations",
    labelnames=["primary_provider", "fallback_provider"],
)
