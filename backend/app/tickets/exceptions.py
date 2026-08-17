class TicketCreationForbiddenError(Exception):
    """Raised when a user is not allowed to create tickets."""


class TicketNotFoundError(Exception):
    """Raised when a ticket does not exist or is inaccessible."""
