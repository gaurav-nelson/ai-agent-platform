from app.config import settings
from prometheus_client import Counter, Histogram, start_http_server

agent_requests_total = Counter(
    "agent_requests_total",
    "Total number of agent requests",
    ["agent_name", "status"],
)

agent_tool_calls_total = Counter(
    "agent_tool_calls_total",
    "Total number of tool calls made by agents",
    ["agent_name", "tool_name"],
)

agent_request_duration_seconds = Histogram(
    "agent_request_duration_seconds",
    "Duration of agent requests in seconds",
    ["agent_name"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

agent_tokens_used_total = Counter(
    "agent_tokens_used_total",
    "Total tokens used by agents",
    ["agent_name", "direction"],
)


def start_metrics_server():
    start_http_server(settings.METRICS_PORT)
