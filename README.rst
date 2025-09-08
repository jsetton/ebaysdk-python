Welcome to the python ebaysdk
=============================

This SDK is a programmatic interface into the eBay APIs. It simplifies development and cuts development time by standardizing calls, response processing, error handling, and debugging across the Browse, Finding, Shopping, Merchandising & Trading APIs.

**Important Note**: The Finding and Shopping APIs were decommissioned on February 5, 2025. Please migrate to the new Browse API for continued functionality.

Quick Example (Browse API - Recommended)::

    from ebaysdk.exception import ConnectionError
    from ebaysdk.browse import Connection

    try:
        api = Connection(appid='YOUR_APPID', certid='YOUR_CERTID', config_file=None)
        api.execute('search', {'q': 'legos', 'limit': 5})

        assert(api.response.status_code == 200)
        data = api.response.json()
        items = data.get('itemSummaries', [])
        assert(len(items) > 0)

        item = items[0]
        print(f"Title: {item.get('title')}")
        print(f"Price: {item.get('price', {}).get('value')} {item.get('price', {}).get('currency')}")

    except ConnectionError as e:
        print(e)

Legacy Example (Finding API - Deprecated)::

    import datetime
    from ebaysdk.exception import ConnectionError
    from ebaysdk.finding import Connection

    try:
        api = Connection(appid='YOUR_APPID_HERE', config_file=None)
        response = api.execute('findItemsAdvanced', {'keywords': 'legos'})

        assert(response.reply.ack == 'Success')
        assert(type(response.reply.timestamp) == datetime.datetime)
        assert(type(response.reply.searchResult.item) == list)

        item = response.reply.searchResult.item[0]
        assert(type(item.listingInfo.endTime) == datetime.datetime)
        assert(type(response.dict()) == dict)

    except ConnectionError as e:
        print(e)
        print(e.response.dict())


Migrating from Finding/Shopping APIs to Browse API
--------------------------------------------------

The Finding and Shopping APIs were decommissioned on February 5, 2025.
The Browse API is the recommended replacement that provides modern REST endpoints with JSON responses.

Key differences:
* **Authentication**: Browse API uses OAuth 2.0 Bearer tokens instead of API keys
* **Response Format**: JSON instead of XML
* **Endpoints**: Modern REST endpoints instead of SOAP-style calls
* **Features**: Enhanced search capabilities and better performance

Migration examples:

Finding API (Deprecated)::

    from ebaysdk.finding import Connection
    api = Connection(appid='YOUR_APPID')
    response = api.execute('findItemsAdvanced', {'keywords': 'iPhone'})
    items = response.reply.searchResult.item

Browse API (Recommended)::

    from ebaysdk.browse import Connection
    api = Connection(appid='YOUR_APPID', certid='YOUR_CERTID')
    response = api.execute('search', {'q': 'iPhone'})
    items = response.json().get('itemSummaries', [])

For more detailed migration examples, see the `samples/browse.py` file.

Migrating from v1 to v2
-----------------------

For a complete guide on migrating from ebaysdk v1 to v2 and see an overview of the additional features in v2 please read the `v1 to v2 guide`_


Getting Started
---------------

1) SDK Classes

* `Browse API Class`_ - modern REST API for searching and retrieving eBay items (replaces Finding & Shopping APIs).
* `Trading API Class`_ - secure, authenticated access to private eBay data.
* `Finding API Class`_ - access eBay's next generation search capabilities (DEPRECATED - use Browse API).
* `Shopping API Class`_ - performance-optimized, lightweight APIs for accessing public eBay data (DEPRECATED - use Browse API).
* `Merchandising API Class`_ - find items and products on eBay that provide good value or are otherwise popular with eBay buyers.
* `HTTP Class`_ - generic back-end class the enbles and standardized way to make API calls.
* `Parallel Class`_ - SDK support for concurrent API calls.

2) SDK Configuration

* Using the SDK without YAML configuration

   ebaysdk.finding.Connection(appid='...', config_file=None)

* `YAML Configuration`_
* `Understanding eBay Credentials`_

3) Sample code can be found in the `samples directory`_.

4) Understanding the `Request Dictionary`_.

Support
-------

For developer support regarding the SDK code base please use this project's `Github issue tracking`_.

For developer support regarding the eBay APIs please use the `eBay Developer Forums`_.

Install
-------

Installation instructions for *nix and windows can be found in the `INSTALL file`_.

License
-------

`COMMON DEVELOPMENT AND DISTRIBUTION LICENSE`_ Version 1.0 (CDDL-1.0)


.. _INSTALL file: https://github.com/timotheus/ebaysdk-python/blob/master/INSTALL
.. _COMMON DEVELOPMENT AND DISTRIBUTION LICENSE: http://opensource.org/licenses/CDDL-1.0
.. _Understanding eBay Credentials: https://github.com/timotheus/ebaysdk-python/wiki/eBay-Credentials
.. _eBay Developer Site: http://developer.ebay.com/
.. _YAML Configuration: https://github.com/timotheus/ebaysdk-python/wiki/YAML-Configuration
.. _Browse API Class: https://developer.ebay.com/api-docs/buy/browse/overview.html
.. _Trading API Class: https://github.com/timotheus/ebaysdk-python/wiki/Trading-API-Class
.. _Finding API Class: https://github.com/timotheus/ebaysdk-python/wiki/Finding-API-Class
.. _Shopping API Class: https://github.com/timotheus/ebaysdk-python/wiki/Shopping-API-Class
.. _Merchandising API Class: https://github.com/timotheus/ebaysdk-python/wiki/Merchandising-API-Class
.. _HTTP Class: https://github.com/timotheus/ebaysdk-python/wiki/HTTP-Class
.. _Parallel Class: https://github.com/timotheus/ebaysdk-python/wiki/Parallel-Class
.. _eBay Developer Forums: https://forums.developer.ebay.com
.. _Github issue tracking: https://github.com/timotheus/ebaysdk-python/issues
.. _v1 to v2 guide: https://github.com/timotheus/ebaysdk-python/wiki/Migrating-from-v1-to-v2
.. _samples directory: https://github.com/timotheus/ebaysdk-python/tree/master/samples
.. _Request Dictionary: https://github.com/timotheus/ebaysdk-python/wiki/Request-Dictionary
