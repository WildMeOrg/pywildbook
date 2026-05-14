"""Wildbook API client for authentication and resource management."""

import functools
import os
from typing import Any
from urllib.parse import urljoin

import requests

from .exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    NotAuthenticatedError,
    NotFoundError,
)

# API Endpoint Constants
API_LOGIN = '/api/v3/login'
API_LOGOUT = '/api/v3/logout'
API_USER = '/api/v3/user'
API_HOME = '/api/v3/home'
API_SEARCH_ENCOUNTER = '/api/v3/search/encounter'
API_ENCOUNTERS_BASE = '/api/v3/encounters/'
API_SEARCH_INDIVIDUAL = '/api/v3/search/individual'
API_INDIVIDUALS_BASE = '/api/v3/individuals/'
API_SEARCH_OCCURRENCE = '/api/v3/search/occurrence'
API_OCCURRENCES_BASE = '/api/v3/occurrences/'

DEFAULT_TIMEOUT = 30  # seconds


def _requires_auth(func):
    """Decorator to ensure that a method is called on an authenticated client."""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.is_authenticated():
            raise NotAuthenticatedError("Not authenticated. Call login() first.")
        return func(self, *args, **kwargs)
    return wrapper


class WildbookClient:
    """Client for interacting with the Wildbook v3 API.

    This client handles session-based authentication and provides methods
    for searching and managing wildlife data.

    Args:
        base_url: The base URL of the Wildbook instance (e.g., 'http://localhost:8080').
            If not provided, reads from the WILDBOOK_URL environment variable.

    Example:
        >>> client = WildbookClient('http://localhost:8080')
        >>> client.login('user@example.com', 'password')
        >>> results = client.search_encounters({'match_all': {}})
        >>> client.logout()
    """

    def __init__(self, base_url: str | None = None):
        """Initialize the Wildbook client.

        Args:
            base_url: The base URL of the Wildbook instance. If not provided,
                reads from the WILDBOOK_URL environment variable.

        Raises:
            ValueError: If base_url is not provided and WILDBOOK_URL is not set.
        """
        if base_url is None:
            base_url = os.environ.get('WILDBOOK_URL')
            if base_url is None:
                raise ValueError("base_url not provided and WILDBOOK_URL environment variable not set.")
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self._authenticated = False
        self._user_info: dict[str, Any] | None = None

    def _make_url(self, path: str) -> str:
        """Construct full URL from path.

        Args:
            path: API endpoint path (e.g., '/api/v3/login')

        Returns:
            Full URL
        """
        return urljoin(self.base_url + '/', path.lstrip('/'))

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """Handle API response and raise appropriate exceptions.

        Args:
            response: The requests Response object

        Returns:
            Parsed JSON response

        Raises:
            AuthenticationError: For 401 errors
            ForbiddenError: For 403 errors
            NotFoundError: For 404 errors
            BadRequestError: For 400 errors
            APIError: For other HTTP errors
        """
        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code == 200:
            return data
        elif response.status_code == 401:
            error_msg = data.get('error', 'Authentication failed')
            raise AuthenticationError(f"Authentication error: {error_msg}")
        elif response.status_code == 403:
            raise ForbiddenError("Access forbidden")
        elif response.status_code == 404:
            raise NotFoundError("Resource not found")
        elif response.status_code == 400:
            # Handle list of errors or single error message
            errors = data.get('errors', [])
            if isinstance(errors, list) and errors:
                error_msg = ', '.join([e.get('message', str(e)) if isinstance(e, dict) else str(e) for e in errors])
            else:
                error_msg = data.get('error', data.get('message', 'Bad request'))
            raise BadRequestError(f"Bad request: {error_msg}")
        else:
            error_msg = data.get('error', f'HTTP {response.status_code}')
            raise APIError(error_msg, status_code=response.status_code, response_data=data)

    def login(self, username: str | None = None, password: str | None = None) -> dict[str, Any]:
        """Authenticate with the Wildbook API.

        Args:
            username: User's username or email. If not provided, attempts to read from WILDBOOK_USERNAME environment variable.
            password: User's password. If not provided, attempts to read from WILDBOOK_PASSWORD environment variable.

        Returns:
            User information dictionary containing id, username, fullName, etc.

        Raises:
            AuthenticationError: If login fails due to incorrect credentials or missing credentials.

        Example:
            >>> # Using explicit arguments
            >>> client.login('user@example.com', 'password123')
            >>> # Using environment variables (WILDBOOK_USERNAME, WILDBOOK_PASSWORD set)
            >>> client.login()
            {'success': True, 'id': '...', 'username': 'user@example.com', ...}
        """
        if username is None:
            username = os.environ.get('WILDBOOK_USERNAME')
        if password is None:
            password = os.environ.get('WILDBOOK_PASSWORD')

        if not username:
            raise AuthenticationError("Username not provided and WILDBOOK_USERNAME environment variable not set.")
        if not password:
            raise AuthenticationError("Password not provided and WILDBOOK_PASSWORD environment variable not set.")

        url = self._make_url(API_LOGIN)
        payload = {
            'username': username,
            'password': password
        }

        response = self.session.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        data = self._handle_response(response)

        if data.get('success'):
            self._authenticated = True
            self._user_info = data
            return data
        else:
            raise AuthenticationError(f"Login failed: {data.get('error', 'Unknown error')}")

    def logout(self) -> bool:
        """End the current session and log out.

        Returns:
            True if logout was successful

        Example:
            >>> client.logout()
            True
        """
        url = self._make_url(API_LOGOUT)

        try:
            response = self.session.post(url, timeout=DEFAULT_TIMEOUT)
            data = self._handle_response(response)
            self._authenticated = False
            self._user_info = None
            return data.get('success', False)
        except Exception:
            # Even if logout fails, clear local session state
            self._authenticated = False
            self._user_info = None
            return False

    def is_authenticated(self) -> bool:
        """Check if the client is currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._authenticated

    @_requires_auth
    def get_current_user(self) -> dict[str, Any]:
        """Get information about the currently authenticated user.

        Returns:
            User information dictionary

        Raises:
            NotAuthenticatedError: If not logged in

        Example:
            >>> user = client.get_current_user()
            >>> print(user['username'])
        """
        url = self._make_url(API_USER)
        response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    @_requires_auth
    def get_user_home(self) -> dict[str, Any]:
        """Get dashboard data for the current user.

        Returns:
            Dashboard data including recent encounters, individuals, projects, etc.

        Raises:
            NotAuthenticatedError: If not logged in

        Example:
            >>> home = client.get_user_home()
            >>> print(home['latestEncounters'])
        """
        url = self._make_url(API_HOME)
        response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    @_requires_auth
    def _search(
        self,
        endpoint_path: str,
        query: dict[str, Any],
        from_: int = 0,
        size: int = 10,
        sort: str | None = None,
        sort_order: str | None = None
    ) -> dict[str, Any]:
        """Internal method to handle common search logic."""
        url = self._make_url(endpoint_path)
        params = {
            'from': from_,
            'size': size
        }
        if sort:
            params['sort'] = sort
        if sort_order:
            params['sortOrder'] = sort_order

        # Wrap query in "query" key if not already wrapped
        if 'query' not in query:
            search_body = {'query': query}
        else:
            search_body = query

        response = self.session.post(url, json=search_body, params=params, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def search_encounters(
        self,
        query: dict[str, Any],
        from_: int = 0,
        size: int = 10,
        sort: str | None = None,
        sort_order: str | None = None
    ) -> dict[str, Any]:
        """Search for encounters using OpenSearch/Elasticsearch query syntax.

        Args:
            query: OpenSearch query dictionary (e.g., {'match_all': {}})
            from_: Pagination offset (default: 0)
            size: Number of results to return (default: 10)
            sort: Field to sort by (optional)
            sort_order: Sort order 'asc' or 'desc' (optional)

        Returns:
            Search results with hits array and metadata

        Raises:
            NotAuthenticatedError: If not logged in
            BadRequestError: If query is invalid

        Example:
            >>> # Search for all encounters
            >>> results = client.search_encounters({'match_all': {}})
            >>>
            >>> # Search with filters
            >>> query = {
            ...     'bool': {
            ...         'must': [
            ...             {'term': {'sex': 'female'}},
            ...             {'range': {'year': {'gte': 2020}}}
            ...         ]
            ...     }
            ... }
            >>> results = client.search_encounters(query, size=50)
        """
        return self._search(
            API_SEARCH_ENCOUNTER,
            query,
            from_,
            size,
            sort,
            sort_order
        )

    @_requires_auth
    def get_encounter(self, encounter_id: str) -> dict[str, Any]:
        """Get details of a specific encounter by UUID.

        Args:
            encounter_id: Encounter UUID

        Returns:
            Encounter details dictionary

        Raises:
            NotAuthenticatedError: If not logged in
            NotFoundError: If encounter doesn't exist

        Example:
            >>> encounter = client.get_encounter('123e4567-e89b-12d3-a456-426614174000')
        """
        url = self._make_url(f'{API_ENCOUNTERS_BASE}{encounter_id}')
        response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def search_occurrences(
        self,
        query: dict[str, Any],
        from_: int = 0,
        size: int = 10,
        sort: str | None = None,
        sort_order: str | None = None
    ) -> dict[str, Any]:
        """Search for occurrences using OpenSearch/Elasticsearch query syntax.

        Args:
            query: OpenSearch query dictionary (e.g., {'match_all': {}})
            from_: Pagination offset (default: 0)
            size: Number of results to return (default: 10)
            sort: Field to sort by (optional)
            sort_order: Sort order 'asc' or 'desc' (optional)

        Returns:
            Search results with hits array and metadata. Each hit includes fields
            such as sightingPlatform, fieldSurveyCode, groupComposition,
            groupBehavior, numAdults, numJuveniles, numCalves, transect fields,
            and comments.

        Raises:
            NotAuthenticatedError: If not logged in
            BadRequestError: If query is invalid

        Example:
            >>> results = client.search_occurrences({'match_all': {}})
            >>> for occ in results.get('hits', []):
            ...     print(occ['id'], occ.get('sightingPlatform'))
        """
        return self._search(
            API_SEARCH_OCCURRENCE,
            query,
            from_,
            size,
            sort,
            sort_order
        )

    @_requires_auth
    def get_occurrence(self, occurrence_id: str) -> dict[str, Any]:
        """Get details of a specific occurrence by UUID.

        Args:
            occurrence_id: Occurrence UUID

        Returns:
            Occurrence details dictionary

        Raises:
            NotAuthenticatedError: If not logged in
            NotFoundError: If occurrence doesn't exist

        Example:
            >>> occurrence = client.get_occurrence('123e4567-e89b-12d3-a456-426614174000')
        """
        url = self._make_url(f'{API_OCCURRENCES_BASE}{occurrence_id}')
        response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def search_individuals(
        self,
        query: dict[str, Any],
        from_: int = 0,
        size: int = 10,
        sort: str | None = None,
        sort_order: str | None = None
    ) -> dict[str, Any]:
        """Search for individuals using OpenSearch/Elasticsearch query syntax.

        Args:
            query: OpenSearch query dictionary
            from_: Pagination offset (default: 0)
            size: Number of results to return (default: 10)
            sort: Field to sort by (optional)
            sort_order: Sort order 'asc' or 'desc' (optional)

        Returns:
            Search results with hits array and metadata

        Raises:
            NotAuthenticatedError: If not logged in
        """
        return self._search(
            API_SEARCH_INDIVIDUAL,
            query,
            from_,
            size,
            sort,
            sort_order
        )

    @_requires_auth
    def get_individual(self, individual_id: str) -> dict[str, Any]:
        """Get details of a specific individual by UUID.

        Args:
            individual_id: Individual UUID

        Returns:
            Individual details dictionary

        Raises:
            NotAuthenticatedError: If not logged in
            NotFoundError: If individual doesn't exist
        """
        url = self._make_url(f'{API_INDIVIDUALS_BASE}{individual_id}')
        response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    @_requires_auth
    def filter_current_user(self) -> dict[str, Any]:
        """Create a query to find encounters assigned to the current user.

        Returns:
            Query dictionary filtering by the logged-in user's username.

        Raises:
            NotAuthenticatedError: If not logged in.

        Example:
            >>> client.login()
            >>> query = client.filter_current_user()
            >>> my_encounters = client.search_encounters(query)
        """
        return {
            'bool': {
                'filter': [
                    {'terms': {'assignedUsername': [self._user_info['username']]}}
                ]
            }
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures logout is called."""
        if self._authenticated:
            self.logout()
        return False
