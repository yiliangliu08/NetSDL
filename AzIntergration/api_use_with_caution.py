# -*- coding: utf-8 -*-
from __future__ import absolute_import

from time import gmtime, strftime
import base64
import hashlib
import hmac
import time
from requests import request
from urllib.parse import quote

Feeds = {'SubmitFeed'}

FulfillmentInboundShipment = {'CreateInboundShipmentPlan',
                              'CreateInboundShipment',
                              'UpdateInboundShipment',
                              'PutTransportContent',
                              'GetTransportContent',
                              'ConfirmTransportRequest',
                              'VoidTransportRequest',
                              'GetPalletLabels',
                              'GetUniquePackageLabels'
                              }

MerchantFulfillment = {'GetEligibleShippingServices',
                       'CreateShipment',
                       'GetShipment',
                       'CancelShipment'
                       }

FulfillmentOutboundShipment = {'GetFulfillmentPreview',
                               'CreateFulfillmentOrder',
                               'UpdateFulfillmentOrder',
                               'ListAllFulfillmentOrders',
                               'GetFulfillmentOrder',
                               'ListAllFulfillmentOrderByNextToken',
                               'GetPackageTrackingDetails',
                               'CancelFulfillmentOrder',
                               'CreateFulfillmentReturn'
}


shipping_request_details = {}


class MWS(object):
    def __init__(self, access_key, mws_auth_token, market_id, seller_id, secret_key, version, domain):
        self.access_key = access_key
        self.mws_auth_token = mws_auth_token
        self.market_id = market_id
        self.seller_id = seller_id
        self.secret_key = secret_key
        self.version = version
        self.domain = domain

    def get_timestamp(self):
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', gmtime())

    def calc_signature(self, method, data, api):
        sig_data = '\n'.join([
            method,
            self.domain.replace('https://', '').lower(),
            api,
            data
        ])
        print(sig_data)
        return base64.b64encode(hmac.new(self.secret_key.encode(), sig_data.encode(), hashlib.sha256).digest())

    def recursive_iter(self, obj, keys=()):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from self.recursive_iter(v, keys + (k,))
        elif any(isinstance(obj, t) for t in (list, tuple)):
            for idx, item in enumerate(obj):
                yield from self.recursive_iter(item, keys + (idx,))
        else:
            yield keys, obj

    def submit_feed(self, feed_type=None):
        data = dict(Action='SubmitFeed',
                    FeedType=feed_type)
        return self.make_request(data)

    def get_eligible_shipping_service(self, amazon_order_id=None, seller_order_id=None, item_list=None,
                                      ship_from_address=None, package_dimensions=None, weight=None,
                                      must_arrive_by_date=None, ship_date=None, shipping_service_options=None,
                                      label_customization=None):
        item_list_dict={}
        for k, v in self.recursive_iter(item_list):
            item_list_dict.update({'ShipmentRequestDetails.ItemList.Item.'+k[1]+'.'+str(k[0]+1): str(v)})
        ship_from_address_dict = {}
        for k, v in self.recursive_iter(ship_from_address):
            ship_from_address_dict.update({'ShipmentRequestDetails.ShipFromAddress.'+k[0]: str(v)})
        package_dimensions_dict = {}
        for k, v in self.recursive_iter(package_dimensions):
            package_dimensions_dict.update({'ShipmentRequestDetails.PackageDimensions.'+k[0]: str(v)})
        weight_dict = {}
        for k, v in self.recursive_iter(weight):
            weight_dict.update({'ShipmentRequestDetails.Weight.'+k[0]: str(v)})
        shipping_service_options_dict = {}
        for k, v in self.recursive_iter(shipping_service_options):
            shipping_service_options_dict.update({'ShipmentRequestDetails.ShippingServiceOptions.'+k[0]: str(v)})
        data = dict(Action='GetEligibleShippingService',
                    AmazonOrderId=amazon_order_id,
                    SellerOrderId=seller_order_id,
                    MustArriveByDate=must_arrive_by_date,
                    ShipDate=ship_date
                    )
        data.update(item_list_dict)
        data.update(ship_from_address_dict)
        data.update(package_dimensions_dict)
        data.update(shipping_service_options_dict)
        global shipping_request_details
        shipping_request_details = data
        return self.make_request(data)

    def create_shipment(self, shipping_service_id=None, shipping_service_offer_id=None, hazmat_type=None):
        data = dict(Action='CreateShipment',
                    ShippingServiceId=shipping_service_id,
                    ShippingServiceOfferId=shipping_service_offer_id,
                    HazmatType=hazmat_type
                    )
        data.update(shipping_request_details)
        return self.make_request(data)

    def get_shipment(self, shipment_id):
        data = dict(Action='GetShipment',
                    ShipmentId=shipment_id
                    )
        return self.make_request(data)

    def cancel_shipment(self, shipment_id):
        data = dict(Action='CancelShipment',
                    ShipmentId=shipment_id
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

    def create_inbound_shipment_plan(self, ship_from_address=None, ship_to_country_code=None,
                                     label_prep_preference=None,  inbound_shipment_plan_request_items=None):
        data = dict(Action='CreateInboundShipmentPlan',
                    ShipToCountryCode=ship_to_country_code,
                    LabelPrepPreference=label_prep_preference
                    )
        ship_from_address_dict = {}
        for k, v in self.recursive_iter(ship_from_address):
            ship_from_address_dict.update({'ShipFromAddress.' + k[0]: str(v)})
        inbound_shipment_plan_request_items_dict = {}
        for k, v in self.recursive_iter(inbound_shipment_plan_request_items):
            # print(k)
            inbound_shipment_plan_request_items_dict.update({'InboundShipmentPlanRequestItems.member.'
                                                             + str(k[0]+1) + '.' + k[1]: str(v)})
        data.update(ship_from_address_dict)
        data.update(inbound_shipment_plan_request_items_dict)
        return self.make_request(data)

    def create_inbound_shipment(self, shipment_id=None, inbound_shipment_header=None, inbound_shipment_items=None):
        data = dict(Action='CreateInboundShipment',
                    ShipmentId=shipment_id
                    )
        inbound_shipment_header_dict = {}
        for k, v in self.recursive_iter(inbound_shipment_header):
            inbound_shipment_header_dict.update({'InboundShipmentHeader.' + k[0]: str(v)})
        inbound_shipment_items_dict = {}
        for k, v in self.recursive_iter(inbound_shipment_items):
            inbound_shipment_items_dict.update({'InboundShipmentItems.member.'+str(k[0]+1)+'.'+k[1]: str(v)})
        data.update(inbound_shipment_header_dict)
        data.update(inbound_shipment_items_dict)
        return self.make_request(data)

    def update_inbound_shipment(self, shipment_id=None, inbound_shipment_header=None, inbound_shipment_items=None):
        data = dict(Action='UpdateInboundShipment',
                    ShipmentId=shipment_id
                    )
        inbound_shipment_header_dict = {}
        for k, v in self.recursive_iter(inbound_shipment_header):
            inbound_shipment_header_dict.update({'InboundShipmentHeader.' + k[0]: str(v)})
        inbound_shipment_items_dict = {}
        for k, v in self.recursive_iter(inbound_shipment_items):
            inbound_shipment_items_dict.update({'InboundShipmentItems.member.'+k[1]+'.'+str(k[0]+1): str(v)})
        data.update(inbound_shipment_header_dict)
        data.update(inbound_shipment_items_dict)
        return self.make_request(data)

    def put_transport_content(self, shipment_id=None, is_partnered=None, shipment_type=None, transport_details=None):
        data = dict(Action='PutTransportContent',
                    ShipmentId=shipment_id,
                    IsPartnered=is_partnered,
                    ShipmentType=shipment_type
                    )
        transport_details_dict = {}
        if shipment_type == 'SP':
            if is_partnered == 'true':
                for k, v in self.recursive_iter(transport_details):
                    if len(k) == 1:
                        transport_details_dict.update({'TransportDetails.PartneredSmallParcelData.'+k[0]: v})
                    else:
                        transport_details_dict.update({'TransportDetails.PartneredSmallParcelData.'+k[0]+'.'+'member.'
                                                       + str(k[1]+1)+'.'+k[2]+'.'+k[3]: v})
            else:
                for k, v in self.recursive_iter(transport_details):
                    if len(k) == 1:
                        transport_details_dict.update({'TransportDetails.PartneredSmallParcelData.' + k[0]: str(v)})
                    else:
                        transport_details_dict.update({'TransportDetails.NonPartneredSmallParcelData.'+k[0]+'.'
                                                       + 'member.'+str(k[1]+1)+'.'+k[2]: str(v)})
                        transport_details_dict.update({'TransportDetails.NonPartneredSmallParcelData.'+k[0]+'.'
                                                       + 'member.'+str(k[1])+1+'.'+k[2]: str(v)})
        if shipment_type == 'LTL':
            if is_partnered == 'true':
                for k, v in self.recursive_iter(transport_details):
                    print(k)
                    if len(k) == 2:
                        transport_details_dict.update({'TransportDetails.PartneredLtlData.'+k[0]+'.'+k[1]: str(v)})
                    elif len(k) == 4:
                        transport_details_dict.update({'TransportDetails.PartneredLtlData.'+k[0]+'.'+'member.'
                                                       + str(k[1]+1)+'.'+k[2]+'.'+k[3]: str(v)})
                    else:
                        transport_details_dict.update({'TransportDetails.PartneredLtlData.'+k[0]: str(v)})
            else:
                for k, v in self.recursive_iter(transport_details):
                    transport_details_dict.update({'TransportDetails.NonPartneredLtlData.' + k[0]: str(v)})
        print(transport_details_dict)
        data.update(transport_details_dict)
        return self.make_request(data)

    def estimate_transport_request(self, shipment_id):
        data = dict(Action='EstimateTransportRequest',
                    ShipmentId=shipment_id)
        return self.make_request(data)

    def void_transport_request(self,shipment_id):
        data = dict(Action='VoidTransportRequest',
                    ShipmentId=shipment_id)
        return self.make_request(data)

    def get_transport_content(self, shipment_id):
        data = dict(Action='GetTransportContent',
                    ShipmentId=shipment_id)
        return self.make_request(data)

    def confirm_transport_request(self, shipment_id):
        data = dict(Action='ConfirmTransportRequest',
                    ShipmentId=shipment_id)
        return self.make_request(data)

    def get_unique_package_labels(self, shipment_id, page_type, package_labels_to_print):
        data = dict(Action='GetUniquePackageLabels',
                    ShipmentId=shipment_id,
                    PageType=page_type,
                    PackageLabelsToPrint=package_labels_to_print)
        return self.make_request(data)

    def get_pallet_labels(self, shipment_id, page_type, package_labels_to_print):
        data = dict(Action='GetPalletLabels',
                    ShipmentId=shipment_id,
                    PageType=page_type,
                    PackageLabelsToPrint=package_labels_to_print)
        return self.make_request(data)

    def get_fulfillment_preview(self, market_place_id=None, address=None, items=None, shipping_speed_categories=None,
                                include_cod_fulfillment_preview=None, include_delivery_windows=None):
        data = dict(Action='GetFulfilmentPreview',
                    MarketplaceId=market_place_id,
                    IncludeCODFulfillmentPreview=include_cod_fulfillment_preview,
                    IncludeDeliveryWindows=include_delivery_windows)
        address_dict = {}
        for k, v in self.recursive_iter(address):
            address_dict.update({'Address.' + k[0]: str(v)})
        items_dict = {}
        for k, v in self.recursive_iter(items):
            items_dict.update({'Items.member.' + str(k[0]+1) + '.' + k[1]: str(v)})
        if shipping_speed_categories is not None:
            shipping_speed_categories_dict = {}
            for k, v in self.recursive_iter(shipping_speed_categories):
                shipping_speed_categories_dict.update({k[1] + '.' + str(k[0]+1): str(v)})
        data.update(address_dict)
        data.update(items_dict)
        data.update(shipping_speed_categories_dict)
        return self.make_request(data)

    def create_fulfillment_order(self, market_place_id=None, order_head=None, fulfillment_action=None, destination_address=None,
                                 fulfillment_policy=None, notification_email_list=None, cod_settings=None, items=None):
        data = dict(Action='CreateFulfillmentOrder',
                    MarketplaceId=market_place_id,
                    FulfillmentAction=fulfillment_action,
                    FulfillmentPolicy=fulfillment_policy)
        data.update(order_head)
        destination_address_dict = {}
        for k, v in self.recursive_iter(destination_address):
            destination_address_dict.update({'DestinationAddress.' + k[0]: str(v)})
        items_dict = {}
        for k, v in self.recursive_iter(items):
            if len(k) == 3:
                items_dict.update({'Items.member.' + str(k[0]+1) + '.' + k[1] + '.' + k[2]: str(v)})
            else:
                items_dict.update({'Items.member.' + str(k[0]+1) + '.' + k[1]: str(v)})
        for k, v in items_dict.items():
            print(k, v)
        if notification_email_list is not None:
            email_dict = {}
            for k, v in self.recursive_iter(notification_email_list):
                email_dict.update({k[1] + '.' + str(k[0] + 1): str(v)})
            data.update(email_dict)
        if cod_settings is not None:
            cod_settings_dict = {}
            for k, v in self.recursive_iter(cod_settings):
                cod_settings_dict.update({'CODSettings.' + k[0]: str(v)})
            data.update(cod_settings_dict)
        data.update(destination_address_dict)
        data.update(items_dict)
        return self.make_request(data)

    def update_fulfillment_order(self, market_place_id=None, order_head=None, fulfillment_action=None, destination_address=None,
                                 fulfillment_policy=None, notification_email_list=None, cod_settings=None, items=None):
        data = dict(Action='UpdateFulfillmentOrder',
                    MarketplaceId=market_place_id,
                    FulfillmentAction=fulfillment_action,
                    FulfillmentPolicy=fulfillment_policy)
        data.update(order_head)
        destination_address_dict = {}
        for k, v in self.recursive_iter(destination_address):
            destination_address_dict.update({'DestinationAddress.' + k[0]: str(v)})
        items_dict = {}
        for k, v in self.recursive_iter(items):
            if len(k) == 3:
                items_dict.update({'Items.member.' + str(k[0] + 1) + '.' + k[1] + '.' + k[2]: str(v)})
            else:
                items_dict.update({'Items.member.' + str(k[0] + 1) + '.' + k[1]: str(v)})
        for k, v in items_dict.items():
            print(k, v)
        email_dict = {}
        for k, v in self.recursive_iter(notification_email_list):
            email_dict.update({k[1] + '.' + str(k[0] + 1): str(v)})
        cod_settings_dict = {}
        for k, v in self.recursive_iter(cod_settings):
            cod_settings_dict.update({'CODSettings.' + k[0]: str(v)})
        data.update(destination_address_dict)
        data.update(items_dict)
        data.update(email_dict)
        data.update(cod_settings_dict)

    def list_all_fulfillment_orders(self, query_start_datetime=None):
        data = dict(Action='ListAllFulfillmentOrders',
                    QueryStartDateTime=query_start_datetime)
        return self.make_request(data)

    def list_all_fulfillment_orders_by_next_token(self, next_token=None):
        data = dict(Action='ListAllFulfillmentOrdersByNextToken',
                    NextToken=next_token)
        return self.make_request(data)

    def get_fulfillment_order(self, seller_fulfillment_order_id=None):
        data = dict(Action='GetFulfillmentOrder',
                    SellerFulfillmentOrdeId=seller_fulfillment_order_id)
        return self.make_request(data)

    def get_package_tracking_details(self, package_number=None):
        data = dict(Action='GetPackageTrackingDetails',
                    PackageNumber=package_number)
        return self.make_request(data)

    def get_package_tracking_details(self, package_number=None):
        data = dict(Action='GetPackageTrackingDetails',
                    PackageNumber=package_number)
        return self.make_request(data)

    def cancel_fulfillment_order(self, seller_fulfillment_order_id=None):
        data = dict(Action='CancelFulfillmentOrder',
                    SellerFulfillmentOrderid=seller_fulfillment_order_id)
        return self.make_request(data)

    def make_request(self, api_data):
        data = self.get_data()
        data.update(api_data)
        request_description = ''
        print(data)
        if data['Action'] in FulfillmentInboundShipment:
            method = 'POST'
            uri = 'FulfillmentInboundShipment/2010-10-01/'
        elif data['Action'] in MerchantFulfillment:
            method = 'POST'
            uri = 'MerchantFulfillment/2015-06-01/'
        elif data['Action'] in FulfillmentOutboundShipment:
            method = 'POST'
        elif data['Action'] in Feeds:
            method = 'POST'
            uri = '/Feeds/2009-01-01/'
        for key in sorted(data):
            if data[key] != '' and data[key] is not None:
                encoded_value = quote(data[key], safe='-_.~')
                request_description += '&{}={}'.format(key, encoded_value)
        temp = request_description[1:]
        request_description = temp
        print(request_description)
        signature = self.calc_signature(method, request_description, uri)
        print(signature)
        print(quote(signature).replace('/', '%2F'))
        url = '{domain}/{uri}?{description}&Signature={signature}'.format(
            domain=self.domain,
            uri=uri,
            description=request_description,
            signature=quote(signature).replace('/', '%2F')
        )
        print(url)
        return url
