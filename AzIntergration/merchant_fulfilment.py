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

item_list = [
    {
        'OrderItemId': '112-4820722-7211418',
        'Quantity': 1
    },
    {
        'OrderItemId': '112-0975814-0977004',
        'Quantity': 2
    }
]

ship_from_address = {
    'Name': 'George Neffner',
    'AddressLine1': '4639 DOUGLAS AVE',
    'AddressLine2': None,
    'AddressLine3': None,
    'StateOrRegion': 'WI',
    'Email': '516bfnkg6kx8gqc@marketplace.amazon.com',
    'City': 'RACINE',
    'PostalCode': '53402',
    'CountryCode': 'US',
    'Phone': '2508856843'
}

package_dimensions = {
    'Length': 10,
    'Width': 10,
    'Hieght': 10,
    'Unit': 'inches'
}

weight = {
    'Value': 10,
    'Unit': 'kg'
}

shipping_service_options = {
    'DeliveryExperience': 'DeliveryConfirmationWithAdultSignature',
    'DeclaredValue': 0,
    'CarrierWillPickUp': 'true'
}


class CreateMCF:
    def __init__(self, aws_access_key_id, mws_auth_key, marketplace_id, seller_id, secret_key, version, domain, start_time, store_id):
        self.aws_access_key_id = aws_access_key_id
        self.mws_auth_key = mws_auth_key
        self.marketplace_id = marketplace_id
        self.seller_id = seller_id
        self.secret_key = secret_key
        self.version = version
        self.domain = domain
        self.start_time = start_time
        self.store_id = store_id

    def get_eligible_shipping_service(self):
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.get_eligible_shipping_service(item_list=item_list, ship_from_address=ship_from_address,
                                                package_dimensions=package_dimensions, weight=weight,
                                                shipping_service_options=shipping_service_options)
        # response = request('Get', url)
        # xml_data = response.content
        # root = ET.fromstring(xml_data)
        # return root

    def create_shipment(self, root):
        shipping_service_id = ''
        shipping_service_offer_id = ''
        for element in root.iter():
            if element.tag == 'ShippingServiceId':
                shipping_service_id = element.text
            if element.tag == 'ShippingServiceOfferId':
                shipping_service_offer_id = element.text


def get_start_time(input_start_time=None, db_start_time=None):
    # if the start time is provided, it need to be transfer into datetime format
    if input_start_time is not None:
        given_time = StringToDate.strptime(input_start_time, '%Y-%m-%d %H:%M:%S')
    else:
        given_time = db_start_time
    gmt_start_time = given_time - datetime.timedelta(1/3)
    return gmt_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def AzMCF(store_id, start_time, job_id):
    db_session = db_func.DataBase()
    AWSAccessKeyId, MWSAuthToken, MarketplaceId, SellerId, SecretKey, Domain = db_session.get_store(store_id)
    MCF = CreateMCF(AWSAccessKeyId, MWSAuthToken, MarketplaceId,
                    SellerId, SecretKey, '2015-06-01', Domain, start_time, store_id)
    url = MCF.get_eligible_shipping_service()


if __name__ == "__main__":
    start_time = '2019-06-10 4:00:00'
    temp = get_start_time(input_start_time=start_time)
    AzMCF(int(6000102), temp, 16)

