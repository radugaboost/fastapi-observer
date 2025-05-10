from contextvars import ContextVar

context_trace_id: ContextVar[str] = ContextVar("trace_id")
