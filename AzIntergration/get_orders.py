import sys
import api_func
import db_func
import order_sync
import uuid
import time
import datetime
import traceback
import logging
import xml.etree.ElementTree as ET
from datetime import datetime as StringToDate
from requests import request
from requests.exceptions import ConnectionError
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

PriceTag = {
    'ShippingTax',
    'PromotionDiscount',
    'ShippingDiscountTax',
    'GiftWrapTax',
    'ShippingPrice',
    'GiftWrapPrice',
    'ItemPrice',
    'ItemTax',
    'ShippingDiscount',
    'PromotionDiscountTax',
    'CODFee',
    'CODFeeDiscount'
}

OrderHeadKey = {
    'AmazonOrderId',
    'SellerOrderId',
    'PurchaseDate',
    'LastUpdateDate',
    'OrderStatus',
    'FulfillmentChannel',
    'SalesChannel',
    'OrderChannel',
    'ShipServiceLevel',
    'Name',
    'AddressLine1',
    'AddressLine2',
    'AddressLine3',
    'City',
    'StateOrRegion',
    'PostalCode',
    'CountryCode',
    'Phone',
    'AddressType',
    'isAddressSharingConfidential',
    'CurrencyCode',
    'Amount',
    'NumberOfItemsShipped',
    'NumberOfItemsUnshipped',
    'PaymentMethod',
    'IsReplacementOrder',
    'ReplacedOrderId',
    'MarketplaceId',
    'BuyerEmail',
    'BuyerName',
    'CompanyLegalName',
    'TaxingRegion',
    'ShipmentServiceLevelCategory',
    'ShippedByAmazonTFM',
    'TFMShipmentStatus',
    'EasyShipShipmentStatus',
    'OrderType',
    'EarliestShipDate',
    'LatestShipDate',
    'EarliestDeliveryDate',
    'IsBusinessOrder',
    'PurchaseOrderNumber',
    'IsPrime',
    'IsPremiumOrder',
    'PromiseResponseDueDate',
    'IsEstimatedShipDateSet',
}

EndTime = datetime.datetime.now
IsFirst = True
# Counter = 0


class GetOrder:
    def __init__(self, aws_access_key_id, mws_auth_key, marketplace_id, seller_id, secret_key, version, domain, start_time, store_id, path):
        self.aws_access_key_id = aws_access_key_id
        self.mws_auth_key = mws_auth_key
        self.marketplace_id = marketplace_id
        self.seller_id = seller_id
        self.secret_key = secret_key
        self.version = version
        self.domain = domain
        self.start_time = start_time
        self.store_id = store_id
        logging.basicConfig(level=logging.DEBUG, filename=path,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def get_timestamp(self):
        # set the time submit to amazon mws as gmt time
        # directly using current time will cause error, so subtract three minutes from current time
        # using GMT Time for searching order data, storing Local time into job schedule table
        current_time = datetime.datetime.now()
        server_time = current_time-datetime.timedelta(1/3)-datetime.timedelta(minutes=3)
        global_end_time = (current_time-datetime.timedelta(minutes=3)).strftime('%Y-%m-%d %H:%M:%S:%f')
        return server_time.strftime('%Y-%m-%dT%H:%M:%SZ'), global_end_time[:-3]

    def get_local_timestamp(self):
        # set timestamp in database as local time
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', local_time)

    def get_order_head(self):
        mws = api_func.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, self.version, self.domain)
        # url = mws.list_orders('2019-04-20T15:59:30Z', '2019-05-07T02:54:22Z')
        # start_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', self.start_time)
        global EndTime
        global IsFirst
        end_time_in_gmt, temp = self.get_timestamp()
        # Only save the first EndTime in BJS as global variable
        if IsFirst is True:
            EndTime = temp
            IsFirst = False
            print('LastTime = ' + EndTime)
        # Both start_time and end_time are in GMT
        print(end_time_in_gmt)
        url = mws.list_orders(createdafter=self.start_time, createdbefore=end_time_in_gmt)
        print(url)
        try:
            response = request('Get', url)
        except ConnectionError as err:
            logging.error('Request Limit Reached: '+str(err))
            print('Connection Error, retry in 1 minute')
            time.sleep(60)
            response = request('Get', url)
        # print(response.content)
        xml_data = response.content
        # xml_data = ET.parse('test.xml')
        root = ET.fromstring(xml_data)
        return root

    def get_order_by_next(self, token):
        mws = api_func.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.list_orders_by_next(token)
        print(url)
        try:
            response = request('Get', url)
        except ConnectionError as err:
            logging.error('Request Limit Reached: ' + str(err))
            print('Connection Error, retry in 1 minute')
            time.sleep(60)
            response = request('Get', url)
        # print(response.content)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        return root

    def get_order_line(self):
        mws = api_func.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.list_order_items(new_order_id)
        # print(url)
        try:
            response = request('Get', url)
        except ConnectionError as err:
            logging.error('Request Limit Reached: ' + str(err))
            # traceback.print_exc(file=open(db_func.path, 'a'))
            print('Connection Error, Retry in 1 minute')
            time.sleep(60)
            response = request('Get', url)
        xml_data = response.content
        # print(response.content)
        # global Counter
        # Counter += 1
        # print(Counter)
        root = ET.fromstring(xml_data)

        # if throttling error, retry
        for element in root.iter():
            if element.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '') == 'Error':
                for error in element.iter():
                    if element.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '') == 'Message':
                        logging.error(error.text)
                        print("Error, retry in 10 seconds")
                        time.sleep(10)
                        root = self.get_order_line()
                        break
        return root
        # print(xml_data)
        # print('\n')

    def order_head_to_dic(self, root, session):
        # root = head_xml_data.getroot()
        # root = ET.fromstring(head_xml_data)
        token = ''
        for element in root.iter():
            data = {}
            # Look for Order
            if element.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '') == 'Order':
                head_id = uuid.uuid4()
                data.update({'OrderHeadId': head_id})
                # print(head_id)
                global new_order_head
                new_order_head = head_id
                for order_head in element.iter():
                    if "\n" not in order_head.text:
                        temp = order_head.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '')
                        if temp in OrderHeadKey:
                            # print(temp, order_head.text)
                            data.update({temp: order_head.text})
                global new_order_id
                new_order_id = data['AmazonOrderId']
                if session.is_order_exists(data['AmazonOrderId']) is False:
                    data.update({'AmiStatus': 0})
                    data.update({'StoreId': self.store_id})
                    data.update({'PluginCreateTime': self.get_local_timestamp()})
                    data.update({'PluginUpdateTime': self.get_local_timestamp()})
                    session.insert_order_head(data)
                    # print(data.keys(), data.values())
                    # print('\n')
                    # line_xml_data = ET.parse('testline.xml')
                    line_xml_data = self.get_order_line()
                    self.order_line_to_dic(line_xml_data, session)

                    # Wait for the quota to restore
                    time.sleep(0.5)

                # If AmazonOrderId exists, update order head instead
                else:
                    # Prevent Order Head being overwritten
                    del data['OrderHeadId']
                    data.update({'AmiStatus': 0})
                    data['PluginUpdateTime'] = self.get_local_timestamp()
                    session.update_order_head(data, new_order_id)
                    line_data = self.get_order_line()
                    self.order_line_to_dic(line_data, session)
            # Save the next Token
            if element.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '') == 'NextToken':
                token = element.text
            # Ignore the rest
            else:
                continue
        return token

    def order_line_to_dic(self, root, session):
        # root = line_xml_data.getroot()
        # root = ET.fromstring(line_xml_data)
        for element in root.iter():
            # Look for OrderItem
            if element.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '') == 'OrderItem':
                line_id = uuid.uuid4()
                data = {
                    "OrderLineId": line_id
                }
                data.update({'OrderHeadId': new_order_head})
                # print(new_order_head)
                # Append price tag to the 'CurrencyCode' and 'Amount'
                for order_line in element.iter():
                    if order_line.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '') in PriceTag:
                        temp1 = order_line.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '')
                        for leaf in order_line.iter():
                            temp2 = leaf.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '')
                            if "\n" not in leaf.text:
                                data.update({temp1 + temp2: leaf.text})
                    # Ignore the Key 'PromotionId', as it returns a list of Promotion Code
                    elif order_line.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}','') == 'PromotionId':
                        continue
                    elif "\n" not in order_line.text:
                            temp = order_line.tag.replace('{https://mws.amazonservices.com/Orders/2013-09-01}', '')
                            data.update({temp: order_line.text})
                # Remove meaningless CurrencyCode and Amount
                if 'CurrencyCode' in data.keys():
                    del data['CurrencyCode']
                if 'Amount' in data.keys():
                    del data['Amount']
                # Append AmazonOrderId to the OrderLine
                data.update({'AmazonOrderId': new_order_id})
                # print(data['AmazonOrderId'])
                session.insert_order_line(data)
            else:
                continue

    def get_log_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    def output_to_log(self, content):
        file = open(db_func.path, 'a')
        file.write(content)
        file.write('\n')
        file.close()


def get_start_time(input_start_time=None, db_start_time=None):
    # if the start time is provided, it need to be transfer into datetime format
    if input_start_time is not None:
        given_time = StringToDate.strptime(input_start_time, '%Y-%m-%d %H:%M:%S')
    else:
        given_time = db_start_time
    gmt_start_time = given_time - datetime.timedelta(1/3)
    return gmt_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def AzOrders(store_id, start_time, job_id):
    db_session = db_func.DataBase(store_id)

    # Get time from Job_Schedule and turn it into gmt time
    # bjs_start_time = db_session.last_to_start(job_id)
    # gmt_start_time = get_start_time(db_start_time=bjs_start_time)

    # Get Store Info from Store_define
    AWSAccessKeyId, MWSAuthToken, MarketplaceId, SellerId, SecretKey, Domain = db_session.get_store(store_id)
    Order = GetOrder(AWSAccessKeyId, MWSAuthToken, MarketplaceId,
                    SellerId, SecretKey, '2013-09-01', Domain, start_time, store_id, db_func.path)
    logging.info('Begin to Download Orders')
    OrderData = Order.get_order_head()
    NextToken = Order.order_head_to_dic(OrderData, db_session)
    db_session.session_commit()
    logging.info('Task successful，100 orders imported')
    print('Batch Order Committed')
    print(NextToken)
    while True:
        # if NextToken is empty, that's the end of order, break and update the time in job schedule
        if NextToken == '':
            break

        # otherwise keep looping until there is no NextToken
        else:
            # Get another batch of order with NextToken, and retrieve a new NextToken
            logging.info('Begin to Download Orders')
            OrderData = Order.get_order_by_next(NextToken)
            NextToken = Order.order_head_to_dic(OrderData, db_session)
            print('Batch Order Committed')
            db_session.session_commit()
            logging.info('Task successful，100 orders imported')
            print(NextToken)

    # Update the LastTime on Job Schedule
    db_session.set_job(job_id, EndTime)
    print('LastTime = ', EndTime)

    order_head_id_table = db_session.select_order_head()
    is_updated = db_session.is_updated(order_head_id_table)
    cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, store_no, store_name = db_session.ordersync_store_cloud(store_id)
    ifs = order_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                               order_head_id_table, job_id, store_id, store_no, store_name,
                               db_session.order_sync_route)
    ifs.synchronization()
    while is_updated is False:
        ifs.synchronization()
        order_head_id_table = db_session.select_order_head()
        ifs = order_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                                   order_head_id_table, job_id, store_id, store_no, store_name,
                                   db_session.order_sync_route)
        is_updated = db_session.is_updated(order_head_id_table)
        cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, StoreNo, StoreName = db_session.ordersync_store_cloud(store_id)


if __name__ == "__main__":
    # Using console start time
    store_id, start_time, job_id = sys.argv[1], sys.argv[2], sys.argv[3]

    # Using db start time
    # store_id, job_id = sys.argv[1], sys.argv[2]

    # Turn BJS time to GMT Time
    temp = get_start_time(input_start_time=start_time)
    #
    print(temp)
    AzOrders(int(store_id), temp, job_id)
    print('Done')
