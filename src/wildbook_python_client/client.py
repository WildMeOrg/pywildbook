"""Wildbook API client for authentication and resource management."""

from typing import Optional, Dict, Any, List
import requests
from urllib.parse import urljoin

from .exceptions import (
    AuthenticationError,
    NotAuthenticatedError,
    NotFoundError,
    BadRequestError,
    ForbiddenError,
    APIError,
)


class WildbookClient:
    """Client for interacting with the Wildbook v3 API.

    This client handles session-based authentication and provides methods
    for searching and managing wildlife data.

    Args:
        base_url: The base URL of the Wildbook instance (e.g., 'http://localhost:8080')

    Example:
        >>> client = WildbookClient('http://localhost:8080')
        >>> client.login('user@example.com', 'password')
        >>> results = client.search_encounters({'match_all': {}})
        >>> client.logout()
    """

    def __init__(self, base_url: str):
        """Initialize the Wildbook client.

        Args:
            base_url: The base URL of the Wildbook instance
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self._authenticated = False
        self._user_info: Optional[Dict[str, Any]] = None

    def _make_url(self, path: str) -> str:
        """Construct full URL from path.

        Args:
            path: API endpoint path (e.g., '/api/v3/login')

        Returns:
            Full URL
        """
        return urljoin(self.base_url + '/', path.lstrip('/'))

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
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
            errors = data.get('errors', [])
            error_msg = ', '.join([e.get('message', str(e)) for e in errors]) if errors else 'Bad request'
            raise BadRequestError(f"Bad request: {error_msg}")
        else:
            error_msg = data.get('error', f'HTTP {response.status_code}')
            raise APIError(error_msg, status_code=response.status_code, response_data=data)

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with the Wildbook API.

        Args:
            username: User's username or email
            password: User's password

        Returns:
            User information dictionary containing id, username, fullName, etc.

        Raises:
            AuthenticationError: If login fails

        Example:
            >>> client.login('user@example.com', 'password123')
            {'success': True, 'id': '...', 'username': 'user@example.com', ...}
        """
        url = self._make_url('/api/v3/login')
        payload = {
            'username': username,
            'password': password
        }

        response = self.session.post(url, json=payload)
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
        url = self._make_url('/api/v3/logout')

        try:
            response = self.session.post(url)
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

    def get_current_user(self) -> Dict[str, Any]:
        """Get information about the currently authenticated user.

        Returns:
            User information dictionary

        Raises:
            NotAuthenticatedError: If not logged in

        Example:
            >>> user = client.get_current_user()
            >>> print(user['username'])
        """
        if not self._authenticated:
            raise NotAuthenticatedError("Not authenticated. Call login() first.")

        url = self._make_url('/api/v3/user')
        response = self.session.get(url)
        return self._handle_response(response)

    def get_user_home(self) -> Dict[str, Any]:
        """Get dashboard data for the current user.

        Returns:
            Dashboard data including recent encounters, individuals, projects, etc.

        Raises:
            NotAuthenticatedError: If not logged in

        Example:
            >>> home = client.get_user_home()
            >>> print(home['latestEncounters'])
        """
        if not self._authenticated:
            raise NotAuthenticatedError("Not authenticated. Call login() first.")

        url = self._make_url('/api/v3/home')
        response = self.session.get(url)
        return self._handle_response(response)

    def search_encounters(
        self,
        query: Dict[str, Any],
        from_: int = 0,
        size: int = 10,
        sort: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> Dict[str, Any]:
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
        if not self._authenticated:
            raise NotAuthenticatedError("Not authenticated. Call login() first.")

        url = self._make_url('/api/v3/search/encounter')
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

        response = self.session.post(url, json=search_body, params=params)
        return self._handle_response(response)

    def get_encounter(self, encounter_id: str) -> Dict[str, Any]:
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
        if not self._authenticated:
            raise NotAuthenticatedError("Not authenticated. Call login() first.")

        url = self._make_url(f'/api/v3/encounters/{encounter_id}')
        response = self.session.get(url)
        return self._handle_response(response)

    def search_individuals(
        self,
        query: Dict[str, Any],
        from_: int = 0,
        size: int = 10,
        sort: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> Dict[str, Any]:
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
        if not self._authenticated:
            raise NotAuthenticatedError("Not authenticated. Call login() first.")

        url = self._make_url('/api/v3/search/individual')
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

        response = self.session.post(url, json=search_body, params=params)
        return self._handle_response(response)

    def get_individual(self, individual_id: str) -> Dict[str, Any]:
        """Get details of a specific individual by UUID.

        Args:
            individual_id: Individual UUID

        Returns:
            Individual details dictionary

        Raises:
            NotAuthenticatedError: If not logged in
            NotFoundError: If individual doesn't exist
        """
        if not self._authenticated:
            raise NotAuthenticatedError("Not authenticated. Call login() first.")

        url = self._make_url(f'/api/v3/individuals/{individual_id}')
        response = self.session.get(url)
        return self._handle_response(response)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures logout is called."""
        if self._authenticated:
            self.logout()
        return False
