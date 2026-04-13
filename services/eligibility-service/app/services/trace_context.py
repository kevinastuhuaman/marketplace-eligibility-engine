from __future__ import annotations

from contextvars import ContextVar
from time import perf_counter

from shared.contracts.eligibility import TraceStep

_trace_steps: ContextVar[list[TraceStep] | None] = ContextVar("trace_steps", default=None)


def start_trace() -> None:
    _trace_steps.set([])


def clear_trace() -> None:
    _trace_steps.set(None)


def get_trace() -> list[dict]:
    steps = _trace_steps.get() or []
    return [step.model_dump() for step in steps]


def begin_step(service: str, operation: str, request_summary: dict | None = None) -> tuple[int, float]:
    trace = _trace_steps.get()
    if trace is None:
        return 0, perf_counter()
    step_no = len(trace) + 1
    trace.append(
        TraceStep(
            step=step_no,
            service=service,
            operation=operation,
            request_summary=request_summary or {},
        )
    )
    _trace_steps.set(trace)
    return step_no, perf_counter()


def end_step(
    step_no: int,
    started_at: float,
    response_summary: dict | None = None,
    *,
    cache_hit: bool = False,
    state: str | None = None,
) -> None:
    trace = _trace_steps.get()
    if trace is None or step_no <= 0 or step_no > len(trace):
        return
    step = trace[step_no - 1]
    step.response_summary = response_summary or {}
    step.duration_ms = int((perf_counter() - started_at) * 1000)
    step.cache_hit = cache_hit
    step.state = state
    trace[step_no - 1] = step
    _trace_steps.set(trace)


def record_trace(
    *,
    service: str,
    operation: str,
    request_summary: dict | None = None,
    response_summary: dict | None = None,
    duration_ms: int = 0,
    cache_hit: bool = False,
    state: str | None = None,
) -> None:
    trace = _trace_steps.get()
    if trace is None:
        return
    trace.append(
        TraceStep(
            step=len(trace) + 1,
            service=service,
            operation=operation,
            request_summary=request_summary or {},
            response_summary=response_summary or {},
            duration_ms=duration_ms,
            cache_hit=cache_hit,
            state=state,
        )
    )
    _trace_steps.set(trace)
