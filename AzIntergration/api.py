# -*- coding: utf-8 -*-
from __future__ import absolute_import

from time import gmtime, strftime
import base64
import hashlib
import hmac
import time

from requests import request
from urllib.parse import quote,unquote


class MWS(object):
    def __init__(self, access_key, mws_auth_token, market_id, seller_id, secret_key, domain):
        self.access_key = access_key
        self.mws_auth_token = mws_auth_token
        self.market_id = market_id
        self.seller_id = seller_id
        self.secret_key = secret_key
        self.version = '2013-09-01'
        self.domain = domain

    def get_timestamp(self):
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', gmtime())

    def calc_signature(self, method, data):
        sig_data = '\n'.join([
            method,
            self.domain.replace('https://', '').lower(),
            '/Orders/2013-09-01',
            data
        ])
        # print(sig_data)
        return base64.b64encode(hmac.new(self.secret_key.encode(), sig_data.encode(), hashlib.sha256).digest())

    def list_orders(self, lastupdatedafter=None, lastupdatedbefore=None, max_result='100'):
        data = dict(Action='ListOrders',
                    LastUpdatedAfter=lastupdatedafter,
                    LastUpdatedBefore=lastupdatedbefore,
                    MaxResultsPerPage=max_result
                    )
        return self.make_request(data)

    def list_orders_by_next(self, token=None):
        data = dict(Action='ListOrdersByNextToken',
                    NextToken=token
                    )
        return self.make_request(data)

    def list_order_items(self, amazon_order_id, max_result='100'):
        data = dict(Action='ListOrderItems',
                    AmazonOrderId=amazon_order_id,
                    MaxResultsPerPage=max_result
                    )
        return self.make_request(data)

    def list_orders_items_by_next(self, token=None):
        data = dict(Action='ListOrderItemsByNextToken',
                    NextToken=token
                    )
        return self.make_request(data)

    def get_data(self):
        data = {
            'AWSAccessKeyId': self.access_key,
            'MWSAuthToken': self.mws_auth_token,
            'MarketplaceId': self.market_id,
            'SellerId': self.seller_id,
            'Version': self.version,
            'SignatureVersion': '2',
            'SignatureMethod': 'HmacSHA256',
            'Timestamp': self.get_timestamp()
        }
        return data

    def make_request(self, order_data):
        data = self.get_data()
        data.update(order_data)
        request_description = ''
        for key in sorted(data):
            if data[key] != '' and data[key] is not None:
                encoded_value = quote(data[key], safe='-_.~')
                request_description += '&{}={}'.format(key, encoded_value)
        temp = request_description[1:]
        request_description = temp
        signature = self.calc_signature('GET', request_description)
        # print(signature)
        # print(quote(signature).replace('/', '%2F'))
        # print(quote(signature).replace('/', '%2F'))
        url = '{domain}{uri}?{description}&Signature={signature}'.format(
            domain=self.domain,
            uri='/Orders/2013-09-01',
            description=request_description,
            signature=quote(signature).replace('/', '%2F')
        )
        # print(url)
        return url
