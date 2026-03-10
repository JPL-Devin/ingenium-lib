"""
Tests for project_config.py module
"""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Import the module under test
import project_config
import common


class TestProjectConfig:
    """Test class for project_config module functionality."""
    
    @patch('project_config.ingenium_rest_get_paginated')
    def test_get_dictionary_versions(self, mock_get_paginated):
        """Test get_dictionary_versions function."""
        mock_get_paginated.return_value = [
            {
                'dictionary_version': 'v1.0',
                'dictionary_description': 'Test Dict',
                'state': 'PUBLISHED'
            }
        ]
        
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
             patch('common.token', 'test_token'), \
             patch('common.ssl_verify', True):
            
            project_config.delete_dictionary_version(
                'https://test-server.example.com', 'flight', 'v1.0'
            )
            
            mock_delete.assert_called_once()

    @patch('requests.delete')
    def test_delete_dictionary_version_failure(self, mock_delete):
        """Test failed dictionary version deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_delete.return_value = mock_response
        
        with patch('common.response_handler', return_value=False), \
             patch('common.token', 'test_token'), \
             patch('common.ssl_verify', True):
            
            with pytest.raises(Exception):  # Should raise IngeniumLibError
                project_config.delete_dictionary_version(
                    'https://test-server.example.com', 'flight', 'v1.0'
                )

    @patch('project_config.ingenium_rest_get_paginated')
    def test_get_dictionary(self, mock_get_paginated):
        """Test get_dictionary function."""
        mock_get_paginated.return_value = [
            {'command_stem': 'TEST_CMD', 'cmd_description': 'Test command'}
        ]
        
        result = project_config.get_dictionary(
            'https://test-server.example.com', 'v1.0', 'flight', 'cmds'
        )
        
        assert len(result) == 1
        assert result[0]['command_stem'] == 'TEST_CMD'
        mock_get_paginated.assert_called_once()

    def test_constants_and_endpoints(self):
        """Test that project_config uses correct endpoints and has required functions."""
        # Verify required functions exist
        assert hasattr(project_config, 'get_dictionary_versions')
        assert hasattr(project_config, 'delete_dictionary_version')
        assert hasattr(project_config, 'get_dictionary')
        
        # Verify palette functions exist
        assert hasattr(project_config, 'get_built_in_palette')
        assert hasattr(project_config, 'update_built_in_palette')
        assert hasattr(project_config, 'get_custom_palette')
        assert hasattr(project_config, 'create_custom_palette')
        assert hasattr(project_config, 'update_custom_palette')
        assert hasattr(project_config, 'delete_custom_palette')
        
        # Test that logger is properly configured
        assert hasattr(project_config, 'logger')
        assert project_config.logger.name == 'ingenium.project_config'

    @patch('project_config.ingenium_rest_get')
    def test_get_built_in_palette(self, mock_get):
        """Test get_built_in_palette function."""
        mock_get.return_value = [
            {
                'step_type': 'MANUAL_INPUT',
                'step_display_name': 'Manual Input',
                'enable_disable': True
            }
        ]
        
        result = project_config.get_built_in_palette(
            'https://test-server.example.com', {'step_type': 'MANUAL_INPUT'}
        )
        
        assert len(result) == 1
        assert result[0]['step_type'] == 'MANUAL_INPUT'
        mock_get.assert_called_once()

    @patch('requests.patch')
    def test_update_built_in_palette_success(self, mock_patch):
        """Test successful built-in palette update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response
        
        with patch('common.response_handler', return_value=True), \
             patch('common.token', 'test_token'), \
             patch('common.ssl_verify', True):
            
            result = project_config.update_built_in_palette(
                'https://test-server.example.com', 'MANUAL_INPUT', 
                {'step_display_name': 'Updated Manual Input'}
            )
            
            mock_patch.assert_called_once()

    @patch('project_config.ingenium_rest_get_paginated')
    def test_get_custom_palette(self, mock_get_paginated):
        """Test get_custom_palette function."""
        mock_get_paginated.return_value = [
            {
                'step_id': 123,
                'display_name': 'Custom Step',
                'palette_category': 'Custom'
            }
        ]
        
        result = project_config.get_custom_palette(
            'https://test-server.example.com', {'display_name': 'Custom Step'}
        )
        
        assert len(result) == 1
        assert result[0]['step_id'] == 123
        mock_get_paginated.assert_called_once()

    @patch('requests.post')
    def test_create_custom_palette_success(self, mock_post):
        """Test successful custom palette creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'step_id': 123}
        mock_post.return_value = mock_response
        
        with patch('common.response_handler', return_value=True), \
             patch('common.token', 'test_token'), \
             patch('common.ssl_verify', True):
            
            result = project_config.create_custom_palette(
                'https://test-server.example.com', 
                [{'display_name': 'New Custom Step', 'palette_category': 'Test'}]
            )
            
            assert result['step_id'] == 123
            mock_post.assert_called_once()

    @patch('requests.post')
    def test_create_custom_palette_failure(self, mock_post):
        """Test failed custom palette creation."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        with patch('common.response_handler', return_value=False), \
             patch('common.token', 'test_token'), \
             patch('common.ssl_verify', True):
            
            with pytest.raises(Exception):  # Should raise IngeniumLibError
                project_config.create_custom_palette(
                    'https://test-server.example.com', 
                    [{'display_name': 'New Custom Step'}]
                )

    @patch('requests.patch')
    def test_update_custom_palette_success(self, mock_patch):
        """Test successful custom palette update."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'step_id': 123}
        mock_patch.return_value = mock_response
        
        with patch('common.response_handler', return_value=True), \
             patch('common.token', 'test_token'), \
             patch('common.ssl_verify', True):
            
            result = project_config.update_custom_palette(
                'https://test-server.example.com', 123,
                {'display_name': 'Updated Custom Step'}
            )
            
            assert result['step_id'] == 123
            mock_patch.assert_called_once()

    @patch('requests.patch')
    def test_update_custom_palette_failure(self, mock_patch):
        """Test failed custom palette update."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_patch.return_value = mock_response
        
        with patch('common.response_handler', return_value=False), \
             patch('common.token', 'test_token'), \
             patch('common.ssl_verify', True):
            
            with pytest.raises(Exception):  # Should raise IngeniumLibError
                project_config.update_custom_palette(
                    'https://test-server.example.com', 123,
                    {'display_name': 'Updated Custom Step'}
                )

    @patch('requests.delete')
    def test_delete_custom_palette_success(self, mock_delete):
        """Test successful custom palette deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        with patch('common.response_handler', return_value=True), \
             patch('common.token', 'test_token'), \
             patch('common.ssl_verify', True):
            
            project_config.delete_custom_palette(
                'https://test-server.example.com', 123
            )
            
            mock_delete.assert_called_once()

    @patch('requests.delete')
    def test_delete_custom_palette_failure(self, mock_delete):
        """Test failed custom palette deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_delete.return_value = mock_response
        
        with patch('common.response_handler', return_value=False), \
             patch('common.token', 'test_token'), \
             patch('common.ssl_verify', True):
            
            with pytest.raises(Exception):  # Should raise IngeniumLibError
                project_config.delete_custom_palette(
                    'https://test-server.example.com', 123
                )