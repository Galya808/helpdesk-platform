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


class TicketPriorityChangeForbiddenError(Exception):
    """Raised when a user cannot change ticket priority."""


class ClosedTicketPriorityChangeError(Exception):
    """Raised when priority cannot be changed for a closed ticket."""


class TicketReassignmentForbiddenError(Exception):
    """Raised when a user cannot reassign tickets."""


class InvalidTicketAssigneeError(Exception):
    """Raised when the target user is not an active support agent."""


class ClosedTicketReassignmentError(Exception):
    """Raised when a closed ticket cannot be reassigned."""
