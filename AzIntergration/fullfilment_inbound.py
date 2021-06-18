import sys
import api_use_with_caution
import db_func
import order_sync
import uuid
import time
import datetime
import requests
import xml.etree.ElementTree as ET
from datetime import datetime as StringToDate
from requests import request
from requests.exceptions import ConnectionError

shipment_id = []
destination_fulfillment_center_id = []

carton_data = [
                ['carton001', 'sku01', '1', '0', '1'],
                ['carton001', 'sku02', '2', '1', '1'],
                ['carton002', 'sku03', '3', '3', '1'],
                ['carton002', 'sku04', '4', '1', '1'],
                ['carton002', 'sku05', '1', '1', '1'],
                ['carton003', 'sku06', '2', '1', '1']
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

inbound_shipment_plan_request_item = [
        {
            'SellerSKU': 'CPS-T4C',
            'ASIN': 'B07GX59NNC',
            'Condition': 11,
            'Quantity': 2
        }
    ]

inbound_shipment_header = {
    'ShipmentName': 'AlphaBeta',
    'ShipFromAddress': ship_from_address,
    'DestinationFulfillmentCenterid': 'AZF03',
    'LabelPrepPreference': 'SELLER_LABEL',
    'ShipmentStatus': 'WORKING'
}

inbound_shipment_items = [
    {
        'ShipmentId': 'didboji12345',
        'SellerSku' : 'CPS-T4C',
        'QuantityShipped': 2
    }
]

transport_details = {
    'Contact':
        {
            'Name': 'John Smith',
            'Phone': '250-885-6843',
            'Email': 'js@gmail.com',
            'Fax': ''
        },
    'BoxCount': 3,
    'SellerFreightClass': '',
    'FreightReadyDate': '',
    'PalletList':
        [
            {
                'Dimensions':
                {
                    'Unit': 'inch',
                    'Length': 10,
                    'Width': 10,
                    'Height': 10
                },
                'Weight':
                {
                    'Unit': 'kg',
                    'Value': 10,
                    'IsStacked': 'true'
                }
            },
        ],
    'TotalWeight':
        {
            'Unit': 'inch',
            'Value': 10
        },
    'SellerDeclaredValue':
        {
            'CurrencyCode': 'USD',
            'Value': 998
        }
}

class FulfilmentInbound:
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

    def create_inbound_shipment_(self, ship_to_country_code):
        global shipment_id
        global destination_fulfillment_center_id
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.create_inbound_shipment_plan(ship_from_address=ship_from_address, ship_to_country_code=ship_to_country_code,
                                               inbound_shipment_plan_request_items=inbound_shipment_plan_request_item)
        # response = request('Get', url)
        # xml_data = response.content
        # root = ET.fromstring(xml_data)
        # for element in root.iter():
        #     if element.tag == 'ShipmentId':
        #         shipment_id.append(element.text)
        #     if element.tag == 'DestinationFulfillmentCenterId':
        #         destination_fulfillment_center_id.append[element.text]

    def create_inbound_shipment(self, shipment_id, inbound_shipment_header, inbound_shipment_items):
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.create_inbound_shipment(shipment_id,
                                          inbound_shipment_header=inbound_shipment_header,
                                          inbound_shipment_items=inbound_shipment_items)
        # response = request('Get', url)
        # xml_data = response.content
        # root = ET.fromstring(xml_data)
        # for element in root.iter():
        #     if element.tag == 'ShipmentId':
        #         shipment_id = element.text
        #         is_success = True
        #         return True
        return False

    def put_transport_content(self, is_partnered, shipment_type):
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                                       self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.put_transport_content(shipment_id=shipment_id,
                                        is_partnered=is_partnered,
                                        shipment_type=shipment_type,
                                        transport_details=transport_details)
        response = request('Get', url)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for element in root.iter():
            if element.tag == 'TransportStatus':
                print(element.text)
                break

    def confirm_transport_request(self):
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                                       self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.confirm_transport_request(shipment_id=shipment_id)
        response = request('Get', url)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for element in root.iter():
            if element.tag == 'TransportStatus':
                print(element.text)
                break

    def create_carton_xml(self, data):
        root = ET.Element('CartonContentsRequest')
        shipment_id = ET.SubElement(root, 'ShipmentId').text = 'TEMP233'
        num_catorns = ET.SubElement(root, 'NumCartons').text = '1'
        last_carton_id = ''
        for element in data:
            current_carton_id = element[0]
            if last_carton_id == '' or last_carton_id != current_carton_id:
                carton = ET.SubElement(root, 'Carton')
                carton_id = ET.SubElement(carton, 'CartonId').text = element[0]
            item = ET.SubElement(carton, 'Item')
            sku = ET.SubElement(item, 'SKU').text = element[1]
            quantity_shipped = ET.SubElement(item, 'QuantityShipped').text = str(element[2])
            quantity_in_case = ET.SubElement(item, 'QuantityInCase').text = str(element[3])
            expiration_date = ET.SubElement(item, 'ExpirationDate') .text = element[4]
            last_carton_id = element[0]
        tree = ET.ElementTree(root)
        print('check point 2')
        tree.write('text.xml')

    def submit_carton_feed(self, data):
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                                       self.seller_id, self.secret_key, '2009-01-01', self.domain)
        url = mws.submit_feed('	_POST_FBA_INBOUND_CARTON_CONTENTS_')
        response = request('Post', data=data)
        print(response.content)

    def void_transport_request(self):
        mws = api_use_with_caution.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                                       self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.void_transport_request(shipment_id=shipment_id)
        response = request('Get', url)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for element in root.iter():
            if element.tag == 'TransportStatus':
                print(element.text)
                break

def get_start_time(input_start_time=None, db_start_time=None):
    # if the start time is provided, it need to be transfer into datetime format
    if input_start_time is not None:
        given_time = StringToDate.strptime(input_start_time, '%Y-%m-%d %H:%M:%S')
    else:
        given_time = db_start_time
    gmt_start_time = given_time - datetime.timedelta(1/3)
    return gmt_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def AzFIB(store_id, start_time, job_id):
    db_session = db_func.DataBase(store_id)
    AWSAccessKeyId, MWSAuthToken, MarketplaceId, SellerId, SecretKey, Domain = db_session.get_store(store_id)
    Inbound = FulfilmentInbound(AWSAccessKeyId, MWSAuthToken, MarketplaceId,
                    SellerId, SecretKey, '2010-10-01', Domain, start_time, store_id)
    # Inbound.put_transport_content('true', 'LTL')
    print('check point 1')
    Inbound.create_carton_xml(carton_data)


if __name__ == "__main__":
    start_time = '2019-06-10 4:00:00'
    temp = get_start_time(input_start_time=start_time)
    AzFIB(int(6000102), temp, 16)