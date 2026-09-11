class CommentCreationForbiddenError(Exception):
    """Raised when comment creation for existing ticket is forbidden."""


class TicketClosedForCommentsError(Exception):
    """Raised when comments cannot be added to a closed ticket."""


class CommentViewingForbiddenError(Exception):
    """Raised when viewing ticket comments is forbidden."""
