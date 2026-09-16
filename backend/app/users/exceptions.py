class EmailAlreadyRegisteredError(Exception):
    """Raised when a user tries to register an existing email"""


class InvalidCredentialsError(Exception):
    """Raised when a user tries to log in with nonexisting credentials"""


class BlockedUserError(Exception):
    """Raised when a blocked user tries to log in"""


class UserManagementForbiddenError(Exception):
    """Raised when a non-admin tries to manage users."""


class UserNotFoundError(Exception):
    """Raised when a managed user does not exist."""


class UserSelfManagementForbiddenError(Exception):
    """Raised when an administrator tries to change their own account."""
