from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from app.config import settings

PACIFIC = ZoneInfo("America/Los_Angeles")


class CircuitBreakerOpenError(RuntimeError):
    pass


@dataclass
class BreakerState:
    service: str
    state: str = "closed"
    failure_count: int = 0
    last_failure_at: datetime | None = None
    last_success_at: datetime | None = None
    opened_at: datetime | None = None
    recent_events: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "fallback_mode": "risk_tiered",
            "recent_events": list(self.recent_events[-10:]),
        }


_states = {
    name: BreakerState(name)
    for name in ("item-service", "inventory-service", "seller-service")
}


def _record(state: BreakerState, event: str) -> None:
    state.recent_events.append(
        {
            "event": event,
            "state": state.state,
            "failure_count": state.failure_count,
            "timestamp": datetime.now(PACIFIC).isoformat(),
        }
    )
    state.recent_events = state.recent_events[-10:]


def _get_state(service: str) -> BreakerState:
    return _states[service]


def should_allow_request(service: str) -> tuple[bool, str]:
    state = _get_state(service)
    if not settings.enable_circuit_breakers:
        return True, state.state
    if state.state == "open":
        if state.opened_at and datetime.now(PACIFIC) - state.opened_at >= timedelta(seconds=settings.circuit_breaker_recovery_seconds):
            state.state = "half_open"
            _record(state, "half_open")
            return True, state.state
        return False, state.state
    return True, state.state


def record_success(service: str) -> None:
    state = _get_state(service)
    state.failure_count = 0
    state.last_success_at = datetime.now(PACIFIC)
    if state.state != "closed":
        state.state = "closed"
        state.opened_at = None
        _record(state, "closed")


def record_failure(service: str, _detail: str | None = None) -> None:
    state = _get_state(service)
    state.failure_count += 1
    state.last_failure_at = datetime.now(PACIFIC)
    if state.failure_count >= settings.circuit_breaker_failure_threshold:
        state.state = "open"
        state.opened_at = datetime.now(PACIFIC)
        _record(state, "open")
    else:
        _record(state, "failure")


def get_breaker_states() -> list[dict[str, Any]]:
    return [state.as_dict() for state in _states.values()]


def ensure_request_allowed(service: str) -> BreakerState:
    allowed, state_name = should_allow_request(service)
    state = _get_state(service)
    state.state = state_name
    if not allowed:
        raise CircuitBreakerOpenError(f"{service} breaker is open")
    return state
