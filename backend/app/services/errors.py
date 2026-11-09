"""Domain errors translated to HTTP responses by the API layer."""


class NotFoundError(Exception):
    """Requested session, question or result does not exist."""


class ConflictError(Exception):
    """Action not allowed in the current session state."""


class InvalidAnswerError(Exception):
    """Submitted answer failed validation."""
