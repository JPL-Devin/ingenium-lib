"""
Tests for the venue module - venue and venue group CRUD operations.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock
import venue
import common
from common import IngeniumLibError


MOCK_SERVER = 'https://mock-ingenium.example.com'


@pytest.fixture(autouse=True)
def _set_store():
    """Set up common._store with a valid token and ssl_verify for venue functions."""
    original = common._store.copy()
    common._store['token'] = 'Bearer test-tok'
    common._store['ssl_verify'] = True
    yield
    common._store.update(original)


class TestCreateVenueGroup:
    """Nominal and off-nominal tests for create_venue_group."""

    @patch('venue.response_handler', return_value=True)
    @patch('venue.requests.post')
    def test_success(self, mock_post, mock_handler):
        mock_post.return_value.json.return_value = {'id': 'vg-1', 'name': 'TestGroup'}
        result = venue.create_venue_group(MOCK_SERVER, {'name': 'TestGroup'})
        assert result['id'] == 'vg-1'
        mock_post.assert_called_once()

    @patch('venue.requests.post', side_effect=requests.ConnectionError("refused"))
    def test_connection_error(self, mock_post):
        with pytest.raises(IngeniumLibError, match="Failed to communicate"):
            venue.create_venue_group(MOCK_SERVER, {'name': 'TestGroup'})

    @patch('venue.response_handler', return_value=False)
    @patch('venue.requests.post')
    def test_bad_response(self, mock_post, mock_handler):
        with pytest.raises(IngeniumLibError, match="not completed successfully"):
            venue.create_venue_group(MOCK_SERVER, {'name': 'TestGroup'})


class TestGetVenueGroups:
    """Nominal and off-nominal tests for get_venue_groups."""

    @patch('venue.ingenium_rest_get_paginated')
    def test_success(self, mock_paginated):
        mock_paginated.return_value = [{'id': 'vg-1'}, {'id': 'vg-2'}]
        result = venue.get_venue_groups(MOCK_SERVER)
        assert len(result) == 2

    @patch('venue.ingenium_rest_get_paginated')
    def test_with_query_params(self, mock_paginated):
        mock_paginated.return_value = [{'id': 'vg-1'}]
        result = venue.get_venue_groups(MOCK_SERVER, query={'name': 'test'})
        assert len(result) == 1
        assert mock_paginated.call_args[1]['query_params'] == {'name': 'test'}

    @patch('venue.ingenium_rest_get_paginated', return_value=[])
    def test_empty_result(self, mock_paginated):
        assert venue.get_venue_groups(MOCK_SERVER) == []


class TestGetVenueGroup:
    """Nominal and off-nominal tests for get_venue_group."""

    @patch('venue.ingenium_rest_get')
    def test_success(self, mock_get):
        mock_get.return_value = {'id': 'vg-1', 'name': 'TestGroup'}
        result = venue.get_venue_group(MOCK_SERVER, 'vg-1')
        assert result['name'] == 'TestGroup'


class TestUpdateVenueGroup:
    """Nominal and off-nominal tests for update_venue_group."""

    @patch('venue.response_handler', return_value=True)
    @patch('venue.requests.patch')
    def test_success(self, mock_patch_req, mock_handler):
        mock_patch_req.return_value.json.return_value = {'id': 'vg-1', 'name': 'Updated'}
        result = venue.update_venue_group(MOCK_SERVER, 'vg-1', {'name': 'Updated'})
        assert result['name'] == 'Updated'

    @patch('venue.requests.patch', side_effect=requests.ConnectionError("timeout"))
    def test_connection_error(self, mock_patch_req):
        with pytest.raises(IngeniumLibError, match="Failed to communicate"):
            venue.update_venue_group(MOCK_SERVER, 'vg-1', {'name': 'x'})

    @patch('venue.response_handler', return_value=False)
    @patch('venue.requests.patch')
    def test_bad_response(self, mock_patch_req, mock_handler):
        with pytest.raises(IngeniumLibError, match="not completed successfully"):
            venue.update_venue_group(MOCK_SERVER, 'vg-1', {'name': 'x'})


class TestCreateIngeniumVenue:
    """Nominal and off-nominal tests for create_ingenium_venue."""

    @patch('venue.response_handler', return_value=True)
    @patch('venue.requests.post')
    def test_success(self, mock_post, mock_handler):
        mock_post.return_value.json.return_value = {'id': 'v-1', 'name': 'Testbed'}
        result = venue.create_ingenium_venue(MOCK_SERVER, {'name': 'Testbed'})
        assert result['id'] == 'v-1'

    @patch('venue.requests.post', side_effect=requests.ConnectionError("refused"))
    def test_connection_error(self, mock_post):
        with pytest.raises(IngeniumLibError, match="Failed to communicate"):
            venue.create_ingenium_venue(MOCK_SERVER, {'name': 'Testbed'})

    @patch('venue.response_handler', return_value=False)
    @patch('venue.requests.post')
    def test_bad_response(self, mock_post, mock_handler):
        with pytest.raises(IngeniumLibError, match="not completed successfully"):
            venue.create_ingenium_venue(MOCK_SERVER, {'name': 'Testbed'})


class TestUpdateIngeniumVenue:
    """Nominal and off-nominal tests for update_ingenium_venue."""

    @patch('venue.response_handler', return_value=True)
    @patch('venue.requests.patch')
    def test_success(self, mock_patch_req, mock_handler):
        mock_patch_req.return_value.json.return_value = {'id': 'v-1', 'status': 'active'}
        result = venue.update_ingenium_venue(MOCK_SERVER, 'v-1', {'status': 'active'})
        assert result['status'] == 'active'

    @patch('venue.requests.patch', side_effect=requests.ConnectionError("timeout"))
    def test_connection_error(self, mock_patch_req):
        with pytest.raises(IngeniumLibError, match="Failed to communicate"):
            venue.update_ingenium_venue(MOCK_SERVER, 'v-1', {'status': 'x'})

    @patch('venue.response_handler', return_value=False)
    @patch('venue.requests.patch')
    def test_bad_response(self, mock_patch_req, mock_handler):
        with pytest.raises(IngeniumLibError, match="not completed successfully"):
            venue.update_ingenium_venue(MOCK_SERVER, 'v-1', {'status': 'x'})


class TestGetIngeniumVenues:
    """Nominal and off-nominal tests for get_ingenium_venues."""

    @patch('venue.ingenium_rest_get_paginated')
    def test_success(self, mock_paginated):
        mock_paginated.return_value = [{'id': 'v-1'}, {'id': 'v-2'}]
        result = venue.get_ingenium_venues(MOCK_SERVER)
        assert len(result) == 2

    @patch('venue.ingenium_rest_get_paginated', return_value=[])
    def test_empty(self, mock_paginated):
        assert venue.get_ingenium_venues(MOCK_SERVER) == []


class TestGetIngeniumVenue:
    """Nominal and off-nominal tests for get_ingenium_venue."""

    @patch('venue.ingenium_rest_get')
    def test_success(self, mock_get):
        mock_get.return_value = {'id': 'v-1', 'name': 'WSTS'}
        result = venue.get_ingenium_venue(MOCK_SERVER, 'v-1')
        assert result['name'] == 'WSTS'
