"""Custom exceptions for Wildbook API client."""


class WildbookError(Exception):
    """Base exception for Wildbook client errors."""
    pass


class AuthenticationError(WildbookError):
    """Raised when authentication fails."""
    pass


class NotAuthenticatedError(WildbookError):
    """Raised when trying to access protected resources without authentication."""
    pass


class NotFoundError(WildbookError):
    """Raised when a requested resource is not found."""
    pass


class BadRequestError(WildbookError):
    """Raised when the API returns a 400 Bad Request error."""
    pass


class ForbiddenError(WildbookError):
    """Raised when access to a resource is forbidden."""
    pass


class APIError(WildbookError):
    """Raised when the API returns an unexpected error."""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data
