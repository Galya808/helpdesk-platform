class TicketCreationForbiddenError(Exception):
    """Raised when a user is not allowed to create tickets."""


class TicketNotFoundError(Exception):
    """Raised when a ticket does not exist or is inaccessible."""


class TicketAssignmentForbiddenError(Exception):
    """Raised when a user cannot assign tickets."""


class TicketAlreadyAssignedError(Exception):
    """Raised when a ticket is already assigned."""


class TicketNotAssignableError(Exception):
    """Raised when a ticket cannot be assigned in its current state."""


class TicketStatusChangeForbiddenError(Exception):
    """Raised when a ticket status cannot be changed."""


class InvalidTicketStatusTransitionError(Exception):
    """Raised when a transition is not possible."""
