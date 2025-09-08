# -*- coding: utf-8 -*-

'''
Copyright 2012-2025 eBay Inc.
Authored by: Jeremy Setton
Licensed under CDDL 1.0
'''

import json

from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2 import OAuth2Error
from ebaysdk import log, UserAgent
from ebaysdk.connection import BaseConnection, HTTP_SSL
from ebaysdk.config import Config
from ebaysdk.utils import smart_encode, smart_encode_request_data
from ebaysdk.exception import ConnectionError
from requests import Request, RequestException


class Connection(BaseConnection):
    """Browse API class

    API documentation:
    https://developer.ebay.com/api-docs/buy/browse/overview.html

    Supported calls:
    search (item_summary)
    searchByImage (item_summary)
    getItem (item)
    getItemByLegacyId (item)
    getItems (item)
    getItemsByItemGroup (item)
    checkCompatibility (item)

    Doctests:
    >>> b = Connection(config_file=os.environ.get('EBAY_YAML'))
    >>> retval = b.execute('search', {'q': 'Python programming'})
    >>> print(b.response.status_code)
    200
    >>> print(b.error())
    None
    """

    def __init__(self, **kwargs):
        """Browse class constructor.

        Keyword arguments:
        domain        -- API endpoint (default: api.ebay.com)
        config_file   -- YAML defaults (default: ebay.yaml)
        debug         -- debugging enabled (default: False)
        warnings      -- warnings enabled (default: True)
        errors        -- errors enabled (default: True)
        uri           -- API endpoint uri (default: /buy/browse/v1)
        appid         -- eBay application id (client id)
        devid         -- eBay developer id
        certid        -- eBay cert id (client secret)
        siteid        -- eBay country site id (default: EBAY-US)
        version       -- version number (default: v1)
        https         -- execute of https (default: True)
        proxy_host    -- proxy hostname
        proxy_port    -- proxy port number
        timeout       -- HTTP request timeout (default: 20)
        parallel      -- ebaysdk parallel object
        """

        super(Connection, self).__init__(method='GET', **kwargs)

        self.config = Config(domain=kwargs.get('domain', 'api.ebay.com'),
                             connection_kwargs=kwargs,
                             config_file=kwargs.get('config_file', 'ebay.yaml'))

        # override yaml defaults with args sent to the constructor
        self.config.set('domain', kwargs.get('domain', 'api.ebay.com'))
        self.config.set('uri', '/buy/browse/v1')
        self.config.set('https', True, force=True)
        self.config.set('warnings', True)
        self.config.set('errors', True)
        self.config.set('siteid', 'EBAY-US')
        self.config.set('proxy_host', None)
        self.config.set('proxy_port', None)
        self.config.set('appid', None)
        self.config.set('devid', None)
        self.config.set('certid', None)
        self.config.set('version', 'v1')
        self.config.set('service', 'BrowseAPI')
        self.config.set(
            'doc_url', 'https://developer.ebay.com/api-docs/buy/browse/overview.html')

        # Browse API uses JSON, so no datetime_nodes or base_list_nodes needed
        self.datetime_nodes = []
        self.base_list_nodes = []

    def build_request_headers(self, verb):
        """Build request headers for Browse API."""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': UserAgent,
            'X-EBAY-C-MARKETPLACE-ID': self.config.get('siteid', 'EBAY_US')
        }

    def build_request_data(self, verb, data, verb_attrs):
        """Build request data for Browse API."""
        if verb in ['searchByImage', 'checkCompatibility'] and isinstance(data, dict):
            return json.dumps(data)
        return ""

    def build_request_query(self, verb, data):
        """Build request query for Browse API."""
        if verb not in ['searchByImage', 'checkCompatibility'] and isinstance(data, dict):
            return {
                key: smart_encode(value)
                for key, value in data.items()
                if (verb not in ["getItem", "checkCompatibility"] or key != "item_id")
                and value is not None
            }
        return None

    def build_request_url(self, verb):
        """Build request URL for Browse API."""
        base_url = "%s://%s%s" % (
            HTTP_SSL[self.config.get('https', True)],
            self.config.get('domain'),
            self.config.get('uri')
        )

        # Map verb to appropriate endpoint
        endpoint_map = {
            'search': '/item_summary/search',
            'searchByImage': '/item_summary/search_by_image',
            'getItem': '/item/{item_id}',
            'getItemByLegacyId': '/item/get_item_by_legacy_id',
            'getItems': '/item/',
            'getItemsByItemGroup': '/item/get_items_by_item_group',
            'checkCompatibility': '/item/{item_id}/check_compatibility'
        }

        endpoint = endpoint_map.get(verb, f'/{verb}')

        # Handle item_id parameter for getItem and checkCompatibility
        if verb in ['getItem', 'checkCompatibility']:
            if not self._request_dict or 'item_id' not in self._request_dict:
                raise ValueError('item_id is required for getItem and checkCompatibility')
            endpoint = endpoint.format(item_id=self._request_dict['item_id'])

        return base_url + endpoint

    def build_request(self, verb, data, verb_attrs, files=None):
        """Override build_request to handle GET vs POST methods."""
        self.verb = verb
        self._request_dict = data

        # Determine HTTP method based on verb
        if verb in ['searchByImage', 'checkCompatibility']:
            self.method = 'POST'
        else:
            self.method = 'GET'

        url = self.build_request_url(verb)
        headers = self.build_request_headers(verb)
        params = self.build_request_query(verb, data)
        requestData = self.build_request_data(verb, data, verb_attrs)

        request = Request(
            self.method,
            url,
            params=params,
            data=smart_encode_request_data(requestData),
            headers=headers,
            files=files,
        )

        self.request = request.prepare()

    def process_response(self, parse_response=True):
        """Post processing of the response"""

        if self.response.status_code != 200:
            self._response_error = self.response.reason

    def _get_resp_body_errors(self):
        """Parses the response content to pull errors for Browse API JSON responses."""

        if self._resp_body_errors and len(self._resp_body_errors) > 0:
            return self._resp_body_errors

        errors = []
        warnings = []
        resp_codes = []

        if self.verb is None or self.response.status_code != 200:
            return errors

        response_data = self.response.json()

        for error in response_data.get('errors', []):
            error_code = error.get('errorId')
            error_category = error.get('category')
            error_message = error.get('message')

            if error_code not in resp_codes:
                resp_codes.append(error_code)

            msg = f"Category: {error_category}, Code: {error_code}, {error_message}"
            errors.append(msg)

        for warning in response_data.get('warnings', []):
            warning_code = warning.get('errorId')
            warning_category = warning.get('category')
            warning_message = warning.get('message')

            if warning_code not in resp_codes:
                resp_codes.append(warning_code)

            msg = f"Category: {warning_category}, Code: {warning_code}, {warning_message}"
            warnings.append(msg)

        self._resp_body_warnings = warnings
        self._resp_body_errors = errors
        self._resp_codes = resp_codes

        if self.config.get("warnings") and len(warnings) > 0:
            log.warning("%s: %s\n\n" % (self.verb, "\n".join(warnings)))

        if self.config.get("errors") and len(errors) > 0:
            log.error("%s: %s\n\n" % (self.verb, "\n".join(errors)))

        return errors

    @property
    def access_token(self):
        """Get OAuth access token using client credentials flow."""

        if not hasattr(self, '_token') or self._token.is_expired():
            client_id = self.config.get('appid')
            client_secret = self.config.get('certid')

            if not client_id or not client_secret:
                raise ValueError(
                    'appid (client id) and certid (client secret) are required for OAuth'
                )

            try:
                client = OAuth2Session(
                    client_id=client_id,
                    client_secret=client_secret,
                    scope=f'https://{self.config.get("domain")}/oauth/api_scope',
                    token_endpoint_auth_method='client_secret_basic',
                )

                self._token = client.fetch_token(
                    url=f'https://{self.config.get("domain")}/identity/v1/oauth2/token',
                    grant_type='client_credentials',
                )
            except (OAuth2Error, RequestException) as e:
                raise ConnectionError(f'Failed to get access token: {e}')

        return self._token['access_token']
