# -*- coding: utf-8 -*-
'''
Copyright 2012-2025 eBay Inc.
Authored by: Jeremy Setton
Licensed under CDDL 1.0
'''

import os
import sys
from optparse import OptionParser

sys.path.insert(0, '%s/../' % os.path.dirname(__file__))

import ebaysdk
from ebaysdk.exception import ConnectionError
from ebaysdk.browse import Connection as Browse


def init_options():
    """Initialize command line options."""
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)

    parser.add_option('-d', '--debug', action='store_true', dest='debug',
                        help='Enabled debug output')
    parser.add_option('-y', '--yaml', dest='yaml', default='ebay.yaml',
                        help='Specifies the name of the YAML defaults file. Default: ebay.yaml')
    parser.add_option('-a', '--appid', dest='appid', default=None,
                        help='Specifies the eBay application id to use.')
    parser.add_option('-c', '--certid', dest='certid', default=None,
                        help='Specifies the eBay cert id to use.')
    parser.add_option('--domain', dest='domain', default='api.ebay.com',
                        help='Specifies the eBay domain to use (e.g., api.ebay.com).')

    (opts, args) = parser.parse_args()
    return opts, args


def run_search_sample(opts):
    """Run a basic search sample."""

    try:
        api = Browse(
            debug=opts.debug,
            config_file=opts.yaml,
            appid=opts.appid,
            certid=opts.certid,
            domain=opts.domain,
        )

        api_request = {
            'q': 'Python programming books',
            'limit': 5,
            'filter': 'conditionIds:{3000|4000}',  # New or Used condition
            'sort': 'price',
            'order': 'asc'
        }

        print(f"Searching for: {api_request['q']}")
        api.execute('search', api_request)

        print(f"Response Status: {api.response.status_code}")

        if api.response.status_code == 200:
            data = api.response.json()
            items = data.get('itemSummaries', [])
            print(f"Found {len(items)} items")

            for i, item in enumerate(items, 1):
                title = item.get('title', 'No title')
                price = item.get('price', {}).get('value', 'N/A')
                currency = item.get('price', {}).get('currency', '')
                condition = item.get('condition', 'Unknown')
                print(f"{i}. {title[:50]}... - {currency} {price} ({condition})")
        else:
            print(f"Error: {api.error()}")

    except ConnectionError as e:
        print(f"Connection Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")


def run_get_item_sample(opts):
    """Run a get item sample."""

    try:
        api = Browse(
            config_file=opts.yaml,
            appid=opts.appid,
            certid=opts.certid,
            domain=opts.domain,
        )

        # First, get an item ID from a search
        search_request = {
            'q': 'iPhone',
            'limit': 1
        }

        print("Getting an item ID from search...")
        api.execute('search', search_request)

        if api.response.status_code == 200:
            data = api.response.json()
            items = data.get('itemSummaries', [])

            if items:
                item_id = items[0].get('itemId')
                print(f"Using item ID: {item_id}")

                # Now get detailed item information
                item_request = {
                    'item_id': item_id,
                    'fieldgroups': 'PRODUCT'
                }

                print("Getting detailed item information...")
                api.execute('getItem', item_request)

                if api.response.status_code == 200:
                    item_data = api.response.json()
                    print(f"Item Title: {item_data.get('title', 'N/A')}")
                    print(f"Item Price: {item_data.get('price', {}).get('value', 'N/A')} {item_data.get('price', {}).get('currency', '')}")
                    print(f"Item Condition: {item_data.get('condition', 'N/A')}")
                    print(f"Item Description: {item_data.get('description', 'N/A')[:100]}...")
                else:
                    print(f"Error getting item details: {api.error()}")
            else:
                print("No items found in search")
        else:
            print(f"Error in search: {api.error()}")

    except ConnectionError as e:
        print(f"Connection Error: {e}")


def main():
    """Main function."""
    opts, args = init_options()

    print("eBay Browse API Samples for version %s" % ebaysdk.get_version())
    print("=====================")
    print("Note: This sample requires OAuth credentials (appid and certid).")
    print("The Browse API replaces the deprecated Finding and Shopping APIs.")
    print()

    # Run samples
    run_search_sample(opts)
    run_get_item_sample(opts)

    print("\nSample completed!")


if __name__ == "__main__":
    main()
