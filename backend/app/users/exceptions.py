class EmailAlreadyRegisteredError(Exception):
    """Raised when a user tries to register an existing email"""


class InvalidCredentialsError(Exception):
    """Raised when a user tries to log in with nonexisting credentials"""


class BlockedUserError(Exception):
    """Raised when a blocked user tries to log in"""
