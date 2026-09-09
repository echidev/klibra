from __future__ import annotations

import datetime as dt
import enum


class State(str, enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, cooldown_seconds: float = 60) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.state = State.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: dt.datetime | None = None

    def allow_request(self) -> bool:
        if self.state == State.CLOSED:
            return True
        if self.state == State.OPEN:
            if self.last_failure_time is None:
                return False
            elapsed = (dt.datetime.now(dt.UTC) - self.last_failure_time).total_seconds()
            if elapsed >= self.cooldown_seconds:
                self.state = State.HALF_OPEN
                return True
            return False
        return True

    def record_success(self) -> None:
        if self.state == State.HALF_OPEN:
            self.state = State.CLOSED
            self.failure_count = 0
            self.success_count = 0
        else:
            self.failure_count = 0

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = dt.datetime.now(dt.UTC)
        if self.state == State.HALF_OPEN:
            self.state = State.OPEN
        elif self.failure_count >= self.failure_threshold:
            self.state = State.OPEN
