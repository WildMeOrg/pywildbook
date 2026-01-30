"""Python client for the Wildbook v3 API.

This package provides a simple interface for authenticating with Wildbook
and searching for encounters, individuals, and other wildlife data.

Example:
    >>> from wildbook_python_client import WildbookClient
    >>> from wildbook_python_client.queries import filter_by_species, filter_by_year_range, combine_queries
    >>>
    >>> client = WildbookClient('http://localhost:8080')
    >>> client.login('user@example.com', 'password')
    >>>
    >>> # Search for encounters
    >>> species_query = filter_by_species('Megaptera', 'novaeangliae')
    >>> year_query = filter_by_year_range(2020, 2023)
    >>> query = combine_queries(species_query, year_query)
    >>> results = client.search_encounters(query, size=50)
    >>>
    >>> client.logout()
"""

from .client import WildbookClient
from .exceptions import (
    WildbookError,
    AuthenticationError,
    NotAuthenticatedError,
    NotFoundError,
    BadRequestError,
    ForbiddenError,
    APIError,
)

__version__ = "0.1.0"

__all__ = [
    "WildbookClient",
    "WildbookError",
    "AuthenticationError",
    "NotAuthenticatedError",
    "NotFoundError",
    "BadRequestError",
    "ForbiddenError",
    "APIError",
]
