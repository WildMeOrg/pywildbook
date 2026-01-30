"""Unit tests for WildbookClient class."""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from wildbook_python_client import WildbookClient
from wildbook_python_client.exceptions import (
    AuthenticationError,
    NotAuthenticatedError,
    NotFoundError,
    BadRequestError,
    ForbiddenError,
    APIError
)


class TestClientInitialization:
    """Test client initialization."""

    def test_init_with_trailing_slash(self):
        """Test that trailing slash is removed from base URL."""
        client = WildbookClient('http://localhost:8080/')
        assert client.base_url == 'http://localhost:8080'

    def test_init_without_trailing_slash(self):
        """Test initialization with URL without trailing slash."""
        client = WildbookClient('http://localhost:8080')
        assert client.base_url == 'http://localhost:8080'

    def test_init_authenticated_false(self):
        """Test that client starts unauthenticated."""
        client = WildbookClient('http://localhost:8080')
        assert client.is_authenticated() is False


class TestLoginMethod:
    """Test login functionality."""

    @patch('wildbook_python_client.client.requests.Session.post')
    def test_login_with_explicit_credentials(self, mock_post):
        """Test login with username and password arguments."""
        # Mock successful login response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'username': 'test@example.com',
            'id': 'user-123'
        }
        mock_post.return_value = mock_response

        client = WildbookClient('http://localhost:8080')
        result = client.login('test@example.com', 'password123')

        assert result['success'] is True
        assert result['username'] == 'test@example.com'
        assert client.is_authenticated() is True

    @patch.dict(os.environ, {
        'WILDBOOK_USERNAME': 'env_user@example.com',
        'WILDBOOK_PASSWORD': 'env_password'
    })
    @patch('wildbook_python_client.client.requests.Session.post')
    def test_login_with_env_vars(self, mock_post):
        """Test login using environment variables."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'username': 'env_user@example.com',
            'id': 'user-456'
        }
        mock_post.return_value = mock_response

        client = WildbookClient('http://localhost:8080')
        result = client.login()

        assert result['success'] is True
        assert client.is_authenticated() is True
        # Verify correct credentials were sent
        call_args = mock_post.call_args
        assert call_args[1]['json']['username'] == 'env_user@example.com'
        assert call_args[1]['json']['password'] == 'env_password'

    @patch.dict(os.environ, {}, clear=True)
    def test_login_missing_username(self):
        """Test login raises error when username is missing."""
        client = WildbookClient('http://localhost:8080')
        with pytest.raises(AuthenticationError) as exc_info:
            client.login(password='password')
        assert 'WILDBOOK_USERNAME' in str(exc_info.value)

    @patch.dict(os.environ, {'WILDBOOK_USERNAME': 'test@example.com'}, clear=True)
    def test_login_missing_password(self):
        """Test login raises error when password is missing."""
        client = WildbookClient('http://localhost:8080')
        with pytest.raises(AuthenticationError) as exc_info:
            client.login()
        assert 'WILDBOOK_PASSWORD' in str(exc_info.value)

    @patch('wildbook_python_client.client.requests.Session.post')
    def test_login_failure(self, mock_post):
        """Test login failure handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'success': False,
            'error': 'invalid_credentials'
        }
        mock_post.return_value = mock_response

        client = WildbookClient('http://localhost:8080')
        with pytest.raises(AuthenticationError) as exc_info:
            client.login('test@example.com', 'wrong_password')
        assert 'Authentication error' in str(exc_info.value)


class TestSearchMethods:
    """Test search functionality."""

    @patch('wildbook_python_client.client.requests.Session.post')
    def test_search_without_authentication(self, mock_post):
        """Test that search raises error when not authenticated."""
        client = WildbookClient('http://localhost:8080')
        with pytest.raises(NotAuthenticatedError):
            client.search_encounters({'match_all': {}})

    @patch('wildbook_python_client.client.requests.Session.get')
    @patch('wildbook_python_client.client.requests.Session.post')
    def test_query_wrapping(self, mock_post, mock_get):
        """Test that queries are properly wrapped in 'query' key."""
        # Mock login
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {'success': True, 'username': 'test@example.com'}

        # Mock search
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {'hits': []}

        mock_post.return_value = search_response
        mock_post.side_effect = [login_response, search_response]

        client = WildbookClient('http://localhost:8080')
        client.login('test@example.com', 'password')

        # Search with unwrapped query
        query = {'match_all': {}}
        client.search_encounters(query)

        # Verify the query was wrapped
        search_call = mock_post.call_args_list[1]
        sent_body = search_call[1]['json']
        assert 'query' in sent_body
        assert sent_body['query'] == {'match_all': {}}

    @patch('wildbook_python_client.client.requests.Session.post')
    def test_query_already_wrapped(self, mock_post):
        """Test that already wrapped queries are not double-wrapped."""
        # Mock login and search
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {'success': True, 'username': 'test@example.com'}

        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {'hits': []}

        mock_post.side_effect = [login_response, search_response]

        client = WildbookClient('http://localhost:8080')
        client.login('test@example.com', 'password')

        # Search with pre-wrapped query
        query = {'query': {'match_all': {}}}
        client.search_encounters(query)

        # Verify the query was not double-wrapped
        search_call = mock_post.call_args_list[1]
        sent_body = search_call[1]['json']
        assert sent_body == {'query': {'match_all': {}}}


class TestContextManager:
    """Test context manager functionality."""

    @patch('wildbook_python_client.client.requests.Session.post')
    def test_context_manager_logout(self, mock_post):
        """Test that context manager calls logout on exit."""
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {'success': True, 'username': 'test@example.com'}

        logout_response = Mock()
        logout_response.status_code = 200
        logout_response.json.return_value = {'success': True}

        mock_post.side_effect = [login_response, logout_response]

        with WildbookClient('http://localhost:8080') as client:
            client.login('test@example.com', 'password')
            assert client.is_authenticated() is True

        # Verify logout was called
        assert mock_post.call_count == 2
        assert not client.is_authenticated()


class TestErrorHandling:
    """Test error handling for different HTTP status codes."""

    @patch('wildbook_python_client.client.requests.Session.post')
    def test_404_raises_not_found(self, mock_post):
        """Test that 404 status raises NotFoundError."""
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {'success': True, 'username': 'test@example.com'}

        mock_post.return_value = login_response

        client = WildbookClient('http://localhost:8080')
        client.login('test@example.com', 'password')

        # Mock 404 response for get_encounter
        with patch('wildbook_python_client.client.requests.Session.get') as mock_get:
            error_response = Mock()
            error_response.status_code = 404
            error_response.json.return_value = {'error': 'not found'}
            mock_get.return_value = error_response

            with pytest.raises(NotFoundError):
                client.get_encounter('invalid-uuid')

    @patch('wildbook_python_client.client.requests.Session.post')
    def test_403_raises_forbidden(self, mock_post):
        """Test that 403 status raises ForbiddenError."""
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {'success': True, 'username': 'test@example.com'}

        forbidden_response = Mock()
        forbidden_response.status_code = 403
        forbidden_response.json.return_value = {'error': 'forbidden'}

        mock_post.side_effect = [login_response, forbidden_response]

        client = WildbookClient('http://localhost:8080')
        client.login('test@example.com', 'password')

        with pytest.raises(ForbiddenError):
            client.search_encounters({'match_all': {}})

    @patch('wildbook_python_client.client.requests.Session.post')
    def test_400_raises_bad_request(self, mock_post):
        """Test that 400 status raises BadRequestError."""
        login_response = Mock()
        login_response.status_code = 200
        login_response.json.return_value = {'success': True, 'username': 'test@example.com'}

        bad_request_response = Mock()
        bad_request_response.status_code = 400
        bad_request_response.json.return_value = {
            'errors': [{'message': 'Invalid query'}]
        }

        mock_post.side_effect = [login_response, bad_request_response]

        client = WildbookClient('http://localhost:8080')
        client.login('test@example.com', 'password')

        with pytest.raises(BadRequestError) as exc_info:
            client.search_encounters({'invalid': 'query'})
        assert 'Invalid query' in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
