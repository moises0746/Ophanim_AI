"""Framework-independent domain validation errors."""


class DomainValidationError(ValueError):
    """Raised when a domain value or aggregate violates an invariant."""


class InvalidLifecycleStateError(DomainValidationError):
    """Raised when a lifecycle state is not valid for the owning record."""
