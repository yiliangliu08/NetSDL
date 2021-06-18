import sys
import api_use_with_caution
import db_func
import order_sync
import uuid
import time
import datetime
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime as StringToDate
from requests import request
from requests.exceptions import ConnectionError

fulfillment_outbound_keys = [
    'SellerFulfillmentOrderId',
    'DisplayableOrderId',
    'DisplayableOrderDateTime',
    'DisplayableOrderComment',
    'FirstName',
    'LastName',
    'Line1',
    'Line2',
    'Line3',
    'City',
    'StateOrProvinceCode',
    'CountryCode',
    'PostalCode',
    'PhoneNumber',
    'SellerSKU',
    'SellerFulfillmentOrderItemId',
    'Quantity'
]

item_list_keys = [
    'SellerSKU',
    'SellerFulfillmentOrderItemId',
    'Quantity'
]

address_keys = [
    'FirstName',
    'LastName',
    'Line1',
    'Line2',
    'Line3',
    'City',
    'StateOrProvinceCode',
    'CountryCode',
    'PostalCode',
    'PhoneNumber',
]

class FulfillmentOutbound:
    def __init__(self, aws_access_key_id, mws_auth_key, marketplace_id, seller_id, secret_key, version, domain, start_time, store_id):
        self.aws_access_key_id = aws_access_key_id
        self.mws_auth_key = mws_auth_key
        self.marketplace_id = marketplace_id
        self.seller_id = seller_id
        self.secret_key = secret_key
        self.version = '2010-10-01'
        self.domain = domain
        self.start_time = start_time
        self.store_id = store_id

    def sort_mcf_data(self, data):
        order_head = {}
        address = {}
        item_list = []
        is_order_head_set = False
        for element in data:
            if is_order_head_set is False:
                name = ''
                item = {}
                for i, fulfillment_outbound_key in enumerate(fulfillment_outbound_keys):
                    # print(element[i])
                    if fulfillment_outbound_key in item_list_keys:
                        if fulfillment_outbound_key == 'Quantity':
                            item.update({fulfillment_outbound_key: int(element[i])})
                        else:
                            item.update({fulfillment_outbound_key: element[i]})
                    elif fulfillment_outbound_key in address_keys:
                        if fulfillment_outbound_key == 'FirstName':
                            name += element[i]
                        elif fulfillment_outbound_key == 'LastName':
                            name += ' ' + element[i]
                            address.update({'name': element[i]})
                        else:
                            address.update({fulfillment_outbound_key: element[i]})
                    else:
                        if fulfillment_outbound_key == 'DisplayableOrderDateTime':
                            order_head.update({fulfillment_outbound_key: element[i].strftime('%Y-%m-%dT%H:%M:%SZ')})
                        elif fulfillment_outbound_key == 'DisplayableOrderComment' and element[i] is None:
                            order_head.update({fulfillment_outbound_key: 'No Comment'})
                        else:
                            order_head.update({fulfillment_outbound_key: element[i]})
                item_list.append(item)
                is_order_head_set = True
            else:
                item = {}
                for i, fulfillment_outbound_key in enumerate(fulfillment_outbound_keys):
                    if fulfillment_outbound_key in item_list_keys:
                        if fulfillment_outbound_key == 'Quantity':
                            item.update({fulfillment_outbound_key: int(element[i])})
                        else:
                            item.update({fulfillment_outbound_key: element[i]})
                item_list.append(item)
        print(order_head)
        print(address)
        print(item_list)
        return order_head, address, item_list

    def get_fulfillment_preview(self):
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.get_fulfillment_preview(address=address, items=item_list)
        # response = request('Get', url)
        # xml_data = response.content
        # root = ET.fromstring(xml_data)
        # return root

    def create_fulfillment_order(self, order_head, address, item_list ):
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                                       self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.create_fulfillment_order(destination_address=address, items=item_list, order_head=order_head)
        item_list = []
        address = {}
        order_head = {}
        # response = request('Post', url)
        # xml_data = response.content
        # root = ET.fromstring(xml_data)
        # for element in root.iter():
        #     if element.tag == 'Request_id':
        #         return True
        # return False
        return True

    def get_fulfillment_order(self, seller_fulfillment_order_id):
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                                       self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.get_fulfillment_order(seller_fulfillment_order_id)

        # response = request('Post', url)
        # xml_data = response.content
        # root = ET.fromstring(xml_data)
        # for element in root.iter():
        #     if element.tag == 'TrackingNumber':
        #         tracking_number == element.text


def get_start_time(input_start_time=None, db_start_time=None):
    # if the start time is provided, it need to be transfer into datetime format
    if input_start_time is not None:
        given_time = StringToDate.strptime(input_start_time, '%Y-%m-%d %H:%M:%S')
    else:
        given_time = db_start_time
    gmt_start_time = given_time - datetime.timedelta(1/3)
    return gmt_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def AzOutbound(store_id, start_time, job_id):
    db_session = db_func.DataBase(store_id)
    AWSAccessKeyId, MWSAuthToken, MarketplaceId, SellerId, SecretKey, Domain = db_session.get_store(store_id)
    MCF = FulfillmentOutbound(AWSAccessKeyId, MWSAuthToken, MarketplaceId,
                    SellerId, SecretKey, '2015-06-01', Domain, start_time, store_id)
    data, order_head_id = db_session.select_mcf_data()
    while data is not None:
        order_head, address, item_list = MCF.sort_mcf_data(data)
        # success = MCF.create_fulfillment_order(order_head, address, item_list)
        # if success is True:
        #     print('success')
        db_session.update_mcf_status(order_head_id, 10)
        # else:
        #     db_session.update_mcf_status(order_head_id, 5)
        #     exit()
        data, order_head_id = db_session.select_mcf_data()


if __name__ == "__main__":
    start_time = '2019-06-10 4:00:00'
    temp = get_start_time(input_start_time=start_time)
    AzOutbound(int(6000102), temp, 17)
