"""Framework-independent domain validation errors."""


class DomainValidationError(ValueError):
    """Raised when a domain value or aggregate violates an invariant."""


class InvalidLifecycleStateError(DomainValidationError):
    """Raised when a lifecycle state is not valid for the owning record."""


class InvalidWorkflowTransitionError(DomainValidationError):
    """Raised when a workflow state transition is not permitted."""


class PolicyDeniedError(DomainValidationError):
    """Raised when a requested action or tool execution is denied by policy."""


class PolicyEvaluationError(DomainValidationError):
    """Raised when an unrecoverable error occurs during policy evaluation."""
