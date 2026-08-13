"""Sanitized application-service errors."""


class TaskApplicationError(Exception):
    """Base error for bounded Task use cases."""


class TaskNotFoundError(TaskApplicationError):
    """Raised when a Task is absent or outside the caller's scope."""


class TaskConflictError(TaskApplicationError):
    """Raised when a requested Task operation conflicts with canonical state."""


class WorkflowApplicationError(Exception):
    """Base error for bounded autonomous-workflow use cases."""


class WorkflowNotFoundError(WorkflowApplicationError):
    """Raised when a workflow aggregate is absent."""


class WorkflowConflictError(WorkflowApplicationError):
    """Raised when a requested workflow operation conflicts with canonical state."""


class AgentExecutionError(WorkflowApplicationError):
    """Raised when an agent provider fails to produce a usable result."""
