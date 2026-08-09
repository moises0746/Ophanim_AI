"""Sanitized application-service errors."""


class TaskApplicationError(Exception):
    """Base error for bounded Task use cases."""


class TaskNotFoundError(TaskApplicationError):
    """Raised when a Task is absent or outside the caller's scope."""


class TaskConflictError(TaskApplicationError):
    """Raised when a requested Task operation conflicts with canonical state."""
