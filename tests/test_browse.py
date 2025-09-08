# -*- coding: utf-8 -*-

'''
Copyright 2012-2025 eBay Inc.
Authored by: Jeremy Setton
Licensed under CDDL 1.0
'''

import unittest
import json
from unittest.mock import Mock, patch

from ebaysdk.browse import Connection
from ebaysdk.exception import ConnectionError


class TestBrowseAPI(unittest.TestCase):
    """Test cases for Browse API."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = Connection(debug=False, config_file=None)
        self.api.config.set('appid', 'test_appid')
        self.api.config.set('certid', 'test_certid')
        self.api.config.set('siteid', 'EBAY_US')

        # Mock the access_token property
        self.api._token = {'access_token': 'test_token'}

    def test_connection_initialization(self):
        """Test Browse API connection initialization."""
        api = Connection(debug=False, config_file=None)

        self.assertEqual(api.config.get('domain'), 'api.ebay.com')
        self.assertEqual(api.config.get('uri'), '/buy/browse/v1')
        self.assertEqual(api.config.get('siteid'), 'EBAY-US')
        self.assertEqual(api.config.get('version'), 'v1')
        self.assertEqual(api.config.get('service'), 'BrowseAPI')

    def test_build_request_headers(self):
        """Test request header building."""
        headers = self.api.build_request_headers('search')

        expected_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer test_token",
            "User-Agent": "eBaySDK/2.3.0 Python/3.8.10 Linux/5.4.0-74-generic",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        # Check that all expected headers are present
        for key, value in expected_headers.items():
            if key == "User-Agent":
                # User-Agent format may vary, just check it exists
                self.assertIn(key, headers)
            else:
                self.assertEqual(headers[key], value)

    def test_build_request_headers_no_token(self):
        """Test request header building without access token."""
        # Remove the token to test error case
        delattr(self.api, '_token')
        with self.assertRaises(ValueError):
            self.api.build_request_headers('search')

    def test_build_request_url_search(self):
        """Test URL building for search endpoint."""
        self.api._request_dict = {'q': 'test', 'limit': 5}
        url = self.api.build_request_url('search')

        expected_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
        self.assertEqual(url, expected_url)

    def test_build_request_url_get_item(self):
        """Test URL building for getItem endpoint."""
        self.api._request_dict = {'item_id': '123456789'}
        url = self.api.build_request_url('getItem')

        expected_url = "https://api.ebay.com/buy/browse/v1/item/123456789"
        self.assertEqual(url, expected_url)

    def test_build_request_url_get_item_missing_id(self):
        """Test URL building for getItem endpoint without item_id."""
        self.api._request_dict = {}
        with self.assertRaises(ValueError):
            self.api.build_request_url('getItem')

    def test_build_request_url_check_compatibility(self):
        """Test URL building for checkCompatibility endpoint."""
        self.api._request_dict = {'item_id': '123456789'}
        url = self.api.build_request_url('checkCompatibility')

        expected_url = "https://api.ebay.com/buy/browse/v1/item/123456789/check_compatibility"
        self.assertEqual(url, expected_url)

    def test_build_request_data_get(self):
        """Test request data building for GET requests."""
        data = {'q': 'test', 'limit': 5}
        result = self.api.build_request_data('search', data, None)

        self.assertEqual(result, "")

    def test_build_request_data_post(self):
        """Test request data building for POST requests."""
        data = {'image': 'base64encodedimage', 'limit': 5}
        result = self.api.build_request_data('searchByImage', data, None)

        expected = json.dumps(data)
        self.assertEqual(result, expected)

    def test_build_request_data_none(self):
        """Test request data building with None data."""
        result = self.api.build_request_data('search', None, None)
        self.assertEqual(result, "")

    def test_build_request_query(self):
        """Test request query building for GET requests."""
        data = {'q': 'test', 'limit': 5}
        result = self.api.build_request_query('search', data)

        expected = {'q': 'test', 'limit': 5}
        self.assertEqual(result, expected)

    def test_build_request_query_post(self):
        """Test request query building for POST requests."""
        data = {'image': 'base64encodedimage', 'limit': 5}
        result = self.api.build_request_query('searchByImage', data)

        self.assertIsNone(result)

    def test_build_request_query_with_item_id(self):
        """Test request query building excludes item_id for getItem."""
        data = {'item_id': '123456789', 'fieldgroups': 'PRODUCT'}
        result = self.api.build_request_query('getItem', data)

        expected = {'fieldgroups': 'PRODUCT'}
        self.assertEqual(result, expected)

    @patch('ebaysdk.browse.Connection.build_request')
    def test_build_request_get_method(self, mock_build_request):
        """Test that GET method is used for search requests."""
        self.api.build_request('search', {'q': 'test'}, None)

        # Verify that the method was set to GET
        self.assertEqual(self.api.method, 'GET')

    @patch('ebaysdk.browse.Connection.build_request')
    def test_build_request_post_method(self, mock_build_request):
        """Test that POST method is used for searchByImage requests."""
        self.api.build_request('searchByImage', {'image': 'test'}, None)

        # Verify that the method was set to POST
        self.assertEqual(self.api.method, 'POST')

    def test_get_resp_body_errors_no_errors(self):
        """Test error parsing with no errors."""
        # Mock response with no errors
        mock_response = Mock()
        mock_response.json.return_value = {'itemSummaries': []}
        self.api.response = mock_response

        errors = self.api._get_resp_body_errors()
        self.assertEqual(errors, [])

    def test_get_resp_body_errors_with_errors(self):
        """Test error parsing with errors."""
        # Mock response with errors
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'errors': [
                {
                    'errorId': '123',
                    'message': 'Test error',
                    'category': 'ERROR'
                }
            ]
        }
        self.api.response = mock_response

        errors = self.api._get_resp_body_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn('Test error', errors[0])

    def test_get_resp_body_errors_with_warnings(self):
        """Test error parsing with warnings."""
        # Mock response with warnings
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'warnings': [
                {
                    'errorId': '456',
                    'message': 'Test warning',
                    'category': 'WARNING'
                }
            ]
        }
        self.api.response = mock_response

        errors = self.api._get_resp_body_errors()
        self.assertEqual(len(errors), 0)  # Warnings don't count as errors
        self.assertEqual(len(self.api._resp_body_warnings), 1)

    def test_get_resp_body_errors_non_200_status(self):
        """Test error parsing with non-200 status code."""
        # Mock response with non-200 status
        mock_response = Mock()
        mock_response.status_code = 400
        self.api.response = mock_response

        errors = self.api._get_resp_body_errors()
        self.assertEqual(len(errors), 0)  # Should return early for non-200 status

    @patch('ebaysdk.browse.OAuth2Session')
    def test_access_token_property_success(self, mock_oauth2_session):
        """Test successful access token property."""
        # Mock OAuth2Session and token
        mock_client = Mock()
        mock_token = {'access_token': 'new_token'}
        mock_client.fetch_token.return_value = mock_token
        mock_oauth2_session.return_value = mock_client

        # Remove existing token to force refresh
        if hasattr(self.api, '_token'):
            delattr(self.api, '_token')

        token = self.api.access_token

        self.assertEqual(token, 'new_token')
        self.assertEqual(self.api._token, mock_token)

    @patch('ebaysdk.browse.OAuth2Session')
    def test_access_token_property_failure(self, mock_oauth2_session):
        """Test failed access token property."""
        # Mock OAuth2Session to raise exception
        mock_client = Mock()
        mock_client.fetch_token.side_effect = Exception("OAuth error")
        mock_oauth2_session.return_value = mock_client

        # Remove existing token to force refresh
        if hasattr(self.api, '_token'):
            delattr(self.api, '_token')

        with self.assertRaises(ConnectionError):
            _ = self.api.access_token

    def test_access_token_property_missing_credentials(self):
        """Test access token property with missing credentials."""
        # Remove existing token and credentials
        if hasattr(self.api, '_token'):
            delattr(self.api, '_token')
        self.api.config.set('appid', None)
        self.api.config.set('certid', None)

        with self.assertRaises(ValueError):
            _ = self.api.access_token

    def test_process_response_non_200(self):
        """Test process_response with non-200 status code."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        self.api.response = mock_response

        self.api.process_response()

        self.assertEqual(self.api._response_error, "Bad Request")


class TestBrowseAPIIntegration(unittest.TestCase):
    """Integration tests for Browse API (require actual credentials)."""

    def setUp(self):
        """Set up integration test fixtures."""
        # These tests require actual OAuth credentials
        # Skip if not available
        self.skip_if_no_credentials()

    def skip_if_no_credentials(self):
        """Skip test if OAuth credentials are not available."""
        import os
        appid = os.environ.get('EBAY_APPID')
        certid = os.environ.get('EBAY_CERTID')

        if not appid or not certid:
            self.skipTest("EBAY_APPID and EBAY_CERTID environment variables required")

    def test_search_integration(self):
        """Test actual search API call."""
        import os
        appid = os.environ.get('EBAY_APPID')
        certid = os.environ.get('EBAY_CERTID')

        api = Connection(debug=False, config_file=None, appid=appid, certid=certid)

        # Perform search
        api.execute('search', {'q': 'Python programming', 'limit': 3})

        self.assertEqual(api.response.status_code, 200)
        data = api.response.json()
        self.assertIn('itemSummaries', data)

    def test_get_item_integration(self):
        """Test actual getItem API call."""
        import os
        appid = os.environ.get('EBAY_APPID')
        certid = os.environ.get('EBAY_CERTID')

        api = Connection(debug=False, config_file=None, appid=appid, certid=certid)

        # First get an item ID from search
        api.execute('search', {'q': 'iPhone', 'limit': 1})

        if api.response.status_code == 200:
            data = api.response.json()
            items = data.get('itemSummaries', [])

            if items:
                item_id = items[0].get('itemId')

                # Now get item details
                api.execute('getItem', {'item_id': item_id})

                self.assertEqual(api.response.status_code, 200)
                item_data = api.response.json()
                self.assertIn('title', item_data)


if __name__ == '__main__':
    unittest.main()
