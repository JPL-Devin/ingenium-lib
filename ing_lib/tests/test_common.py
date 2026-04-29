"""
Tests for common.py module - nominal and off-nominal coverage.
"""

import pytest
import requests
import datetime
from unittest.mock import patch, MagicMock

import common

MOCK_BASE_URL = "https://mock-ingenium.example.com"
MOCK_API_ENDPOINT = f"{MOCK_BASE_URL}/api/v1/test"


class TestIngeniumLibError:
    """Tests for the IngeniumLibError exception class."""

    def test_raise_with_message(self):
        """Test IngeniumLibError with a message."""
        with pytest.raises(common.IngeniumLibError) as exc_info:
            raise common.IngeniumLibError("Test error message")
        assert str(exc_info.value) == "Test error message"

    def test_raise_without_message(self):
        """Test IngeniumLibError without a message."""
        with pytest.raises(common.IngeniumLibError):
            raise common.IngeniumLibError()

    def test_is_exception_subclass(self):
        """Verify IngeniumLibError is a proper Exception subclass."""
        assert issubclass(common.IngeniumLibError, Exception)


class TestResponseHandler:
    """Tests for response_handler - nominal and off-nominal."""

    def _make_response(self, status_code, text="", url=MOCK_API_ENDPOINT, method="GET"):
        r = MagicMock()
        r.status_code = status_code
        r.url = url
        r.request.method = method
        r.text = text
        return r

    @pytest.mark.parametrize("code", [200, 201, 202, 204])
    def test_success_codes(self, code):
        """Test response_handler returns True for 2xx codes."""
        assert common.response_handler(self._make_response(code)) is True

    @pytest.mark.parametrize("code", [400, 401, 403, 404, 500, 502, 503])
    def test_failure_codes(self, code):
        """Test response_handler returns False for non-2xx codes."""
        assert common.response_handler(self._make_response(code, text="err")) is False

    def test_bad_request_body_logged(self):
        """Test 400 response body is handled."""
        resp = self._make_response(400, text='{"error":"bad"}')
        assert common.response_handler(resp) is False

    def test_boundary_code_300(self):
        """Test 300 is treated as failure."""
        assert common.response_handler(self._make_response(300, text="redirect")) is False


class TestConstants:
    """Verify module-level constants and endpoints."""

    def test_token_durations(self):
        """Test token duration constants."""
        assert common._TOKEN_REFRESH_DURATION == 3000
        assert common._TOKEN_DURATION == 3600

    def test_endpoints_exist(self):
        """Test that endpoint constants are defined."""
        assert hasattr(common, "auth_endpoint")
        assert hasattr(common, "refresh_endpoint")
        assert hasattr(common, "venue_endpoint")
        assert hasattr(common, "dictionary_endpoint")

    def test_endpoints_start_with_slash(self):
        """Test endpoint strings start with /."""
        for ep in [common.auth_endpoint, common.refresh_endpoint,
                    common.venue_endpoint, common.dictionary_endpoint]:
            assert ep.startswith("/")

    def test_dictionary_endpoint_ends_with_slash(self):
        """Test dictionary_endpoint ends with /."""
        assert common.dictionary_endpoint.endswith("/")


class TestStoreAccessors:
    """Tests for get_token / get_ssl_verify / get_refresh_time / _auth_header / _stale_token."""

    def setup_method(self):
        common._store['token'] = None
        common._store['refresh_time'] = None
        common._store['ssl_verify'] = True

    def teardown_method(self):
        common._store['token'] = None
        common._store['refresh_time'] = None
        common._store['ssl_verify'] = True

    def test_get_token_default_none(self):
        """Test default token is None."""
        assert common.get_token() is None

    def test_get_token_after_set(self):
        """Test token value after setting."""
        common._store['token'] = "Bearer abc"
        assert common.get_token() == "Bearer abc"

    def test_get_ssl_verify_default_true(self):
        """Test default ssl_verify is True."""
        assert common.get_ssl_verify() is True

    def test_get_ssl_verify_false(self):
        """Test ssl_verify when set to False."""
        common._store['ssl_verify'] = False
        assert common.get_ssl_verify() is False

    def test_get_ssl_verify_ca_bundle_path(self):
        """Test ssl_verify with CA bundle path string."""
        common._store['ssl_verify'] = "/path/to/ca.crt"
        assert common.get_ssl_verify() == "/path/to/ca.crt"

    def test_get_refresh_time_default_none(self):
        """Test default refresh_time is None."""
        assert common.get_refresh_time() is None

    def test_auth_header_with_token(self):
        """Test _auth_header returns correct Authorization header."""
        common._store['token'] = "Bearer xyz"
        assert common._auth_header() == {"Authorization": "Bearer xyz"}

    def test_auth_header_no_token_raises(self):
        """Test _auth_header raises IngeniumLibError when no token set."""
        common._store['token'] = None
        with pytest.raises(common.IngeniumLibError):
            common._auth_header()

    def test_stale_token_none_token(self):
        """Test _stale_token returns True when token is None."""
        assert common._stale_token() is True

    def test_stale_token_none_refresh_time(self):
        """Test _stale_token returns True when refresh_time is None."""
        common._store['token'] = "Bearer t"
        common._store['refresh_time'] = None
        assert common._stale_token() is True

    def test_stale_token_fresh(self):
        """Test _stale_token returns False for a fresh token."""
        common._store['token'] = "Bearer t"
        common._store['refresh_time'] = datetime.datetime.utcnow()
        assert common._stale_token() is False

    def test_stale_token_expired(self):
        """Test _stale_token returns True for an expired token."""
        common._store['token'] = "Bearer t"
        common._store['refresh_time'] = datetime.datetime.utcnow() - datetime.timedelta(seconds=4000)
        assert common._stale_token() is True


class TestExtractServer:
    """Tests for _extact_server helper."""

    def test_extract_https(self):
        """Test extracting server from HTTPS URL."""
        assert common._extact_server("https://host.com/api/v1/foo") == "https://host.com"

    def test_extract_http_with_port(self):
        """Test extracting server from HTTP URL with port."""
        assert common._extact_server("http://host.com:8080/path") == "http://host.com:8080"


class TestIngeniumRestGet:
    """Tests for ingenium_rest_get - nominal and off-nominal."""

    def setup_method(self):
        common._store['token'] = "Bearer test_token"
        common._store['refresh_time'] = datetime.datetime.utcnow()
        common._store['ssl_verify'] = True

    def teardown_method(self):
        common._store['token'] = None
        common._store['refresh_time'] = None
        common._store['ssl_verify'] = True

    @patch('requests.get')
    def test_success(self, mock_get):
        """Test successful GET request."""
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"data": "ok"}
        mock_get.return_value = resp

        result = common.ingenium_rest_get(MOCK_API_ENDPOINT)
        assert result == {"data": "ok"}
        mock_get.assert_called_once_with(
            MOCK_API_ENDPOINT,
            headers={'Authorization': 'Bearer test_token'},
            verify=True,
        )

    @patch('requests.get')
    def test_ssl_disabled(self, mock_get):
        """Test GET request with SSL verification disabled."""
        common._store['ssl_verify'] = False
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"ssl": "off"}
        mock_get.return_value = resp

        result = common.ingenium_rest_get(MOCK_API_ENDPOINT)
        assert result == {"ssl": "off"}
        assert mock_get.call_args.kwargs['verify'] is False

    @patch('requests.get')
    def test_failure_raises(self, mock_get):
        """Test failed GET raises IngeniumLibError."""
        resp = MagicMock(status_code=500, url=MOCK_API_ENDPOINT, text="err")
        resp.request.method = "GET"
        mock_get.return_value = resp

        with pytest.raises(common.IngeniumLibError, match="Response not completed"):
            common.ingenium_rest_get(MOCK_API_ENDPOINT)

    @patch('requests.get')
    def test_connection_error(self, mock_get):
        """Test ConnectionError propagates."""
        mock_get.side_effect = requests.ConnectionError("refused")
        with pytest.raises(requests.ConnectionError):
            common.ingenium_rest_get(MOCK_API_ENDPOINT)

    @patch('requests.get')
    def test_json_decode_error(self, mock_get):
        """Test JSON decode error propagates."""
        resp = MagicMock(status_code=200)
        resp.json.side_effect = ValueError("bad json")
        mock_get.return_value = resp

        with pytest.raises(ValueError):
            common.ingenium_rest_get(MOCK_API_ENDPOINT)

    @patch('requests.get')
    def test_timeout_error(self, mock_get):
        """Test Timeout error propagates."""
        mock_get.side_effect = requests.Timeout("timed out")
        with pytest.raises(requests.Timeout):
            common.ingenium_rest_get(MOCK_API_ENDPOINT)


class TestIngeniumRestGetPaginated:
    """Tests for ingenium_rest_get_paginated - nominal and off-nominal."""

    def setup_method(self):
        common._store['token'] = "Bearer test_token"
        common._store['refresh_time'] = datetime.datetime.utcnow()
        common._store['ssl_verify'] = True

    def teardown_method(self):
        common._store['token'] = None
        common._store['refresh_time'] = None
        common._store['ssl_verify'] = True

    @patch('requests.get')
    def test_single_page(self, mock_get):
        """Test paginated GET with a single page of results."""
        resp = MagicMock(status_code=200)
        resp.json.return_value = [{"item": 1}, {"item": 2}]
        resp.headers = {'x-total-count': '2'}
        mock_get.return_value = resp

        result = common.ingenium_rest_get_paginated(MOCK_API_ENDPOINT)
        assert result == [{"item": 1}, {"item": 2}]
        assert mock_get.call_args.kwargs['params']['limit'] == 1000
        assert mock_get.call_args.kwargs['params']['offset'] == 0

    @patch('requests.get')
    def test_multi_page(self, mock_get):
        """Test paginated GET with multiple pages."""
        page1 = MagicMock(status_code=200)
        page1.json.return_value = [{"i": n} for n in range(1000)]
        page1.headers = {'x-total-count': '1500'}

        page2 = MagicMock(status_code=200)
        page2.json.return_value = [{"i": n} for n in range(1000, 1500)]
        page2.headers = {'x-total-count': '1500'}

        mock_get.side_effect = [page1, page2]

        result = common.ingenium_rest_get_paginated(MOCK_API_ENDPOINT)
        assert len(result) == 1500
        assert mock_get.call_count == 2

    @patch('requests.get')
    def test_with_query_params(self, mock_get):
        """Test paginated GET preserves additional query params."""
        resp = MagicMock(status_code=200)
        resp.json.return_value = [{"a": 1}]
        resp.headers = {'x-total-count': '1'}
        mock_get.return_value = resp

        result = common.ingenium_rest_get_paginated(MOCK_API_ENDPOINT, query_params={'filter': 'x'})
        assert result == [{"a": 1}]
        params = mock_get.call_args.kwargs['params']
        assert params['filter'] == 'x'
        assert params['limit'] == 1000

    @patch('requests.get')
    def test_failure_raises(self, mock_get):
        """Test paginated GET raises on server error."""
        resp = MagicMock(status_code=500, url=MOCK_API_ENDPOINT, text="err")
        resp.request.method = "GET"
        mock_get.return_value = resp

        with pytest.raises(common.IngeniumLibError):
            common.ingenium_rest_get_paginated(MOCK_API_ENDPOINT)

    @patch('requests.get')
    def test_empty_result(self, mock_get):
        """Test paginated GET with empty result set."""
        resp = MagicMock(status_code=200)
        resp.json.return_value = []
        resp.headers = {'x-total-count': '0'}
        mock_get.return_value = resp

        result = common.ingenium_rest_get_paginated(MOCK_API_ENDPOINT)
        assert result == []


class TestAuthenticate:
    """Tests for authenticate - nominal and off-nominal."""

    def setup_method(self):
        common._store['token'] = None
        common._store['refresh_time'] = None
        common._store['ssl_verify'] = True

    def teardown_method(self):
        common._store['token'] = None
        common._store['refresh_time'] = None
        common._store['ssl_verify'] = True

    @patch('requests.get')
    def test_success(self, mock_get):
        """Test successful authentication."""
        resp = MagicMock(status_code=200, text='{"access_token": "tok123"}')
        mock_get.return_value = resp

        result = common.authenticate(MOCK_BASE_URL, username="u", password="p")
        assert result is True
        assert common.get_token() == "Bearer tok123"
        assert common.get_refresh_time() is not None

        expected_url = f"{MOCK_BASE_URL}{common.auth_endpoint}"
        mock_get.assert_called_once()
        assert mock_get.call_args[0][0] == expected_url

    @patch('requests.get')
    def test_already_authenticated_skips(self, mock_get):
        """Test that re-authentication is skipped when token exists."""
        common._store['token'] = "Bearer existing"
        result = common.authenticate(MOCK_BASE_URL, username="u", password="p")
        assert result is True
        mock_get.assert_not_called()

    @patch('requests.get')
    def test_force_re_auth(self, mock_get):
        """Test forced re-authentication overrides existing token."""
        common._store['token'] = "Bearer existing"
        resp = MagicMock(status_code=200, text='{"access_token": "new"}')
        mock_get.return_value = resp

        result = common.authenticate(MOCK_BASE_URL, username="u", password="p", force=True)
        assert result is True
        assert common.get_token() == "Bearer new"

    @patch('getpass.getuser', return_value='sysuser')
    @patch('getpass.getpass', return_value='secret')
    @patch('requests.get')
    def test_prompts_for_credentials(self, mock_get, mock_pass, mock_user):
        """Test credentials are prompted when not provided."""
        resp = MagicMock(status_code=200, text='{"access_token": "t"}')
        mock_get.return_value = resp

        common.authenticate(MOCK_BASE_URL)
        mock_user.assert_called_once()
        mock_pass.assert_called_once()

    @patch('getpass.getpass', return_value='rsa_code')
    @patch('getpass.getuser', return_value='rsa_user')
    @patch('requests.get')
    def test_rsa_auth(self, mock_get, mock_user, mock_pass):
        """Test RSA authentication sets X-AUTH-METHOD header."""
        resp = MagicMock(status_code=200, text='{"access_token": "rsa_tok"}')
        mock_get.return_value = resp

        result = common.authenticate(MOCK_BASE_URL, rsa=True)
        assert result is True
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs['headers'] == {'X-AUTH-METHOD': 'rsa'}

    @patch('requests.get')
    def test_failed_login(self, mock_get):
        """Test authentication failure returns False."""
        resp = MagicMock(status_code=401, url=MOCK_BASE_URL, text="Unauthorized")
        resp.request.method = "GET"
        mock_get.return_value = resp

        result = common.authenticate(MOCK_BASE_URL, username="u", password="p")
        assert result is False

    @patch('requests.get')
    def test_connection_error(self, mock_get):
        """Test authentication failure on connection error."""
        mock_get.side_effect = requests.ConnectionError("unreachable")
        result = common.authenticate(MOCK_BASE_URL, username="u", password="p")
        assert result is False


class TestRefreshAuth:
    """Tests for refresh_auth - nominal and off-nominal."""

    def setup_method(self):
        common._store['token'] = "Bearer old"
        common._store['refresh_time'] = datetime.datetime.utcnow() - datetime.timedelta(seconds=4000)
        common._store['ssl_verify'] = True

    def teardown_method(self):
        common._store['token'] = None
        common._store['refresh_time'] = None
        common._store['ssl_verify'] = True

    @patch('requests.post')
    def test_force_refresh_calls_endpoint(self, mock_post):
        """Test forced refresh calls the refresh endpoint."""
        resp = MagicMock(status_code=200, text='{"access_token": "refreshed"}')
        mock_post.return_value = resp

        common.refresh_auth(MOCK_BASE_URL, force=True)
        mock_post.assert_called_once()
        assert common.get_token() == "Bearer refreshed"
        expected_url = f"{MOCK_BASE_URL}{common.refresh_endpoint}"
        assert mock_post.call_args[0][0] == expected_url

    def test_no_refresh_when_fresh(self):
        """Test refresh is skipped when token is still fresh."""
        common._store['refresh_time'] = datetime.datetime.utcnow()
        common.refresh_auth(MOCK_BASE_URL, force=False)

    @patch('requests.post')
    def test_connection_error_raises(self, mock_post):
        """Test ConnectionError during refresh raises IngeniumLibError."""
        mock_post.side_effect = requests.ConnectionError("down")
        with pytest.raises(common.IngeniumLibError):
            common.refresh_auth(MOCK_BASE_URL, force=True)

    @patch('requests.post')
    def test_failed_refresh_raises(self, mock_post):
        """Test failed refresh (non-2xx) raises an error."""
        resp = MagicMock(status_code=401, url=MOCK_BASE_URL, text="denied")
        resp.request.method = "POST"
        mock_post.return_value = resp

        with pytest.raises(common.IngeniumLibError):
            common.refresh_auth(MOCK_BASE_URL, force=True)     