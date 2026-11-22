"""Atomic per-process limits and conservative API cost reservations (not a billing ledger)."""
from collections import defaultdict, deque
from datetime import datetime, timezone
from decimal import Decimal
import threading
import time
from backend.errors import AppError


class UsageLedger:
    def __init__(self):
        self._lock = threading.Lock()
        self._events = defaultdict(deque)
        self._day = ""
        self._reserved = Decimal("0")
        self._observed = Decimal("0")
        self._tokens = 0
        self._calls = 0

    def reserve(self, session_id, estimate, settings, now=None):
        now = time.time() if now is None else now
        day = datetime.fromtimestamp(now, timezone.utc).date().isoformat()
        with self._lock:
            if day != self._day:
                self._day, self._reserved, self._observed = day, Decimal("0"), Decimal("0")
                self._tokens = self._calls = 0
            for key, limit in (("*", settings.global_rpm), (session_id, settings.session_rpm)):
                events = self._events[key]
                while events and events[0] <= now - 60:
                    events.popleft()
                if len(events) >= limit:
                    raise AppError("Request limit reached. Please wait a minute.", "rate_limit")
            if self._reserved + estimate > settings.daily_budget_usd:
                raise AppError("The server's daily API allowance is exhausted.", "budget")
            for key in ("*", session_id):
                self._events[key].append(now)
            self._reserved += estimate
            self._calls += 1
            # Prevent an unbounded map of expired anonymous sessions.
            if len(self._events) > 2000:
                self._events = defaultdict(deque, {
                    key: value for key, value in self._events.items()
                    if value and value[-1] > now - 60
                })

    def record(self, input_tokens, output_tokens, settings, *, embedding=False):
        with self._lock:
            self._tokens += input_tokens + output_tokens
            self._observed += (
                Decimal(input_tokens) * (settings.embedding_price if embedding else settings.input_price)
                + Decimal(output_tokens) * settings.output_price
            ) / Decimal(1_000_000)

    def snapshot(self):
        with self._lock:
            return {"day_utc": self._day, "requests": self._calls, "tokens": self._tokens,
                    "observed_cost_usd": str(self._observed),
                    "reserved_cost_usd": str(self._reserved)}


def estimate_request(payload: str, settings, *, embedding=False) -> Decimal:
    # UTF-8 bytes plus overhead overestimates input tokens for ordinary text.
    inputs = len(payload.encode("utf-8")) + 2048
    outputs = 0 if embedding else settings.max_output_tokens
    price = settings.embedding_price if embedding else settings.input_price
    # One original request and at most one retry.
    return Decimal(2) * (inputs * price + outputs * settings.output_price) / Decimal(1_000_000)
