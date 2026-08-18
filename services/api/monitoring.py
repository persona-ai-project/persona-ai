"""
monitoring.py
=============
Application monitoring and metrics collection.
"""
from __future__ import annotations

import time
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional
from contextlib import contextmanager

from logging_config import get_logger

logger = get_logger("monitoring")


class MetricsCollector:
    """In-memory metrics collector."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._counters = defaultdict(int)
        self._gauges = {}
        self._histograms = defaultdict(list)
        self._start_time = time.time()
    
    def increment(self, name: str, value: int = 1):
        """Increment a counter."""
        with self._lock:
            self._counters[name] += value
    
    def decrement(self, name: str, value: int = 1):
        """Decrement a counter."""
        with self._lock:
            self._counters[name] -= value
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge value."""
        with self._lock:
            self._gauges[name] = value
    
    def observe(self, name: str, value: float):
        """Record a histogram observation."""
        with self._lock:
            self._histograms[name].append(value)
            # Keep only last 1000 observations
            if len(self._histograms[name]) > 1000:
                self._histograms[name] = self._histograms[name][-1000:]
    
    def get_counter(self, name: str) -> int:
        """Get counter value."""
        return self._counters.get(name, 0)
    
    def get_gauge(self, name: str) -> Optional[float]:
        """Get gauge value."""
        return self._gauges.get(name)
    
    def get_histogram_stats(self, name: str) -> dict:
        """Get histogram statistics."""
        values = self._histograms.get(name, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p95": 0}
        
        sorted_values = sorted(values)
        return {
            "count": len(values),
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(values) / len(values),
            "p95": sorted_values[int(len(sorted_values) * 0.95)],
        }
    
    def get_all_metrics(self) -> dict:
        """Get all metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self._histograms
            },
        }
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._start_time = time.time()


# Global metrics instance
metrics = MetricsCollector()


@contextmanager
def track_request(endpoint: str, method: str = "GET"):
    """Track request metrics."""
    start_time = time.time()
    metrics.increment("requests_total")
    metrics.increment(f"requests_{method}")
    
    try:
        yield
        metrics.increment("requests_success")
    except Exception as e:
        metrics.increment("requests_error")
        raise
    finally:
        duration = time.time() - start_time
        metrics.observe("request_duration_seconds", duration)
        metrics.observe(f"request_duration_{endpoint}", duration)


def track_api_call(endpoint: str, status_code: int, duration_ms: float):
    """Track API call metrics."""
    metrics.increment("api_calls_total")
    metrics.increment(f"api_calls_{status_code}")
    metrics.observe("api_latency_ms", duration_ms)
    metrics.observe(f"api_latency_{endpoint}", duration_ms)
    
    if status_code >= 400:
        metrics.increment("api_errors_total")
    if status_code >= 500:
        metrics.increment("api_server_errors")


def track_twin_chat(twin_id: str, response_time_ms: float, knowledge_used: int):
    """Track twin chat metrics."""
    metrics.increment("twin_chats_total")
    metrics.observe("twin_chat_latency_ms", response_time_ms)
    metrics.observe("twin_chat_knowledge_used", knowledge_used)
    metrics.set_gauge("twin_chat_last_response_time_ms", response_time_ms)


def track_voice_chat(twin_id: str, duration_ms: float):
    """Track voice chat metrics."""
    metrics.increment("voice_chats_total")
    metrics.observe("voice_chat_latency_ms", duration_ms)


def track_source_upload(twin_id: str, source_type: str, size_bytes: int):
    """Track source upload metrics."""
    metrics.increment("source_uploads_total")
    metrics.increment(f"source_uploads_{source_type}")
    metrics.observe("source_upload_size_bytes", size_bytes)


def get_metrics_summary() -> dict:
    """Get a summary of all metrics."""
    return {
        "uptime_seconds": time.time() - metrics._start_time,
        "metrics": metrics.get_all_metrics(),
    }
