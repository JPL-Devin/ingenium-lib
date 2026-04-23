"""
Tests for project_config.py module
"""

import pytest
from unittest.mock import patch, MagicMock

import common
import project_config


class TestProjectConfig:
    """Test class for project_config module functionality."""
    
    @patch('common._stale_token', return_value=False)
    @patch('project_config.ingenium_rest_get_paginated')
    def test_get_dictionary_versions(self, mock_get_paginated, _mock_stale):
        """Test get_dictionary_versions function."""
        mock_get_paginated.return_value = [
            {
                'dictionary_version': 'v1.0',
                'dictionary_description': 'Test Dict',
                'state': 'PUBLISHED'
            }
        ]
        
        with patch.dict('common._store', {'token': 'Bearer tok', 'ssl_verify': True}):
            result = project_config.get_dictionary_versions(
                'https://test-server.example.com', 'flight'
            )
        
        assert len(result) == 1
        assert result[0]['dictionary_version'] == 'v1.0'
        mock_get_paginated.assert_called_once()

    @patch('requests.delete')
    def test_delete_dictionary_version_success(self, mock_delete):
        """Test successful dictionary version deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        with patch('common.response_handler', return_value=True), \
             patch.dict('common._store', {'token': 'Bearer test_token', 'ssl_verify': True}):
            
            project_config.delete_dictionary_version(
                'https://test-server.example.com', 'flight', 'v1.0'
            )
            
            mock_delete.assert_called_once()

    @patch('requests.delete')
    def test_delete_dictionary_version_failure(self, mock_delete):
        """Test failed dictionary version deletion raises IngeniumLibError."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_delete.return_value = mock_response
        
        with patch('common.response_handler', return_value=False), \
             patch.dict('common._store', {'token': 'Bearer test_token', 'ssl_verify': True}):
            
            with pytest.raises(common.IngeniumLibError):
                project_config.delete_dictionary_version(
                    'https://test-server.example.com', 'flight', 'v1.0'
                )

    @patch('common._stale_token', return_value=False)
    @patch('project_config.ingenium_rest_get_paginated')
    def test_get_dictionary(self, mock_get_paginated, _mock_stale):
        """Test get_dictionary function."""
        mock_get_paginated.return_value = [
            {'command_stem': 'TEST_CMD', 'cmd_description': 'Test command'}
        ]
        
        with patch.dict('common._store', {'token': 'Bearer tok', 'ssl_verify': True}):
            result = project_config.get_dictionary(
                'https://test-server.example.com', 'v1.0', 'flight', 'cmds'
            )
        
        assert len(result) == 1
        assert result[0]['command_stem'] == 'TEST_CMD'
        mock_get_paginated.assert_called_once()

    def test_constants_and_endpoints(self):
        """Test that project_config uses correct endpoints and has required functions."""
        assert hasattr(project_config, 'get_dictionary_versions')
        assert hasattr(project_config, 'delete_dictionary_version')
        assert hasattr(project_config, 'get_dictionary')

        assert hasattr(project_config, 'logger')
        assert 'project_config' in project_config.logger.name          