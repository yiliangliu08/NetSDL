import sys
import re
import api_func
import db_func
import item_sync
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


EndTime = datetime.datetime.now

ItemKey = [
    'item_name',
    'item_description',
    'listing_id',
    'seller_sku',
    'price',
    'quantity',
    'open_date',
    'image_url',
    'item_is_marketplace',
    'product_id_type',
    'zshop_shipping_fee',
    'item_note',
    'item_condition',
    'zshop_category1',
    'zshop_browse_path',
    'zshop_storefront_feature',
    'asin1',
    'asin2',
    'asin3',
    'will_ship_internationally',
    'expedited_shipping',
    'zshop_boldface',
    'product_id',
    'bid_for_featured_placement',
    'add_delete',
    'pending_quantity',
    'fulfillment_channel',
    'merchant_shipping_group',
    'status'
    ]

class GetItem:
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

    def request_report(self):
        mws = api_func.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.request_report('_GET_MERCHANT_LISTINGS_ALL_DATA_')
        response = request('Post', url)
        print(response.content)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for element in root.iter():
            if element.tag.replace('{http://mws.amazonaws.com/doc/2009-01-01/}', '') == 'ReportRequestId':
                print(element.text)
                report_request_id = element.text
                break
        ready = False
        while ready is False:
            ready = self.is_report_ready(report_request_id)
        print('Report Ready')
        url = mws.get_report_list(report_request_id)
        response = request('Post', url)
        print(response.content)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for element in root.iter():
            if element.tag.replace('{http://mws.amazonaws.com/doc/2009-01-01/}', '') == 'ReportId':
                report_id = element.text
                print(report_id)
                break
        url = mws.get_report(report_id)
        print(url)
        response = request('Post', url)
        print(response.content)
        temp = str(response.content).replace('\\n', '\\t')
        report_data = temp.split('\\t')
        # file = open('C:\\Users\\Tony\\Desktop\\NetSDL\\Sample.txt', 'a')
        # for i in temp2:
        #     file.write(i)
        #     print(i)
        #     file.write('\n')
        print('data ready')
        return report_data

    def item_to_dic(self, item_data, session):
        j = 0
        k = 0
        product_ids = []
        data = {}
        product_id = ''
        for i in item_data:
            if k < 29:
                k += 1
                continue
            else:
                if j == 0:
                    is_item_exist = False
                    product_id = ''
                    id = uuid.uuid4()
                    data.update({'AzItemId': id})
                if j == 22:
                    product_id = i
                    # print(product_id)
                    if product_id in product_ids:
                        is_item_exist_before_commit = True
                    else:
                        is_item_exist_before_commit = False
                    product_ids.append(product_id)
                    is_item_exist = session.is_product_exists(product_id)
                val = re.sub(r'<(.*?)>', '', i)
                data.update({ItemKey[j]: val.replace('\\\\', '')})
                j += 1
            if j == 29:
                j = 0
                if is_item_exist is False and is_item_exist_before_commit is False:
                    data.update({'AmiStatus': 0})
                    data.update({'StoreId': self.store_id})
                    data.update({'PluginCreateTime': self.get_local_timestamp()})
                    data.update({'PluginUpdateTime': self.get_local_timestamp()})
                    # print(data)
                    session.insert_item(data)
                else:
                    del data['AzItemId']
                    data.update({'AmiStatus': 0})
                    data['PluginUpdateTime'] = self.get_local_timestamp()
                    session.update_item(data, product_id)

    def is_report_ready(self, report_request_id):
        mws = api_func.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, self.version, self.domain)
        url = mws.get_report_request_list(report_request_id)
        response = request('Post', url)
        print(response.content)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for element in root.iter():
            if element.tag.replace('{http://mws.amazonaws.com/doc/2009-01-01/}', '') == 'ReportProcessingStatus':
                if element.text == '_DONE_':
                    return True
                else:
                    print('Report Not Ready, wait for 10 seconds')
                    time.sleep(10)
                    return False
            elif element.tag.replace('{http://mws.amazonaws.com/doc/2009-01-01/}', '') == 'Error':
                print('Report Not Ready, wait for 10 seconds')
                time.sleep(10)
                return False

    def list_inventory_supply(self, query_by_time):
        mws = api_func.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, '2010-10-01', self.domain)
        global EndTime
        end_time_in_gmt, temp = self.get_timestamp()
        EndTime = temp
        print(end_time_in_gmt)
        url = mws.list_inventory_supply(query_by_time)
        print(url)
        response = request('Post', url)
        print(response.content)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        return root

    def list_inventory_supply_by_next(self, next_token):
        mws = api_func.MWS(self.aws_access_key_id, self.mws_auth_key, self.marketplace_id,
                           self.seller_id, self.secret_key, '2010-10-01', self.domain)
        end_time_in_gmt, temp = self.get_timestamp()
        print(end_time_in_gmt)
        url = mws.list_inventory_supply_by_next_token(next_token)
        print(url)
        response = request('Post', url)
        print(response.content)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        return root

    def supply_data_to_dict(self, session, root):
        next_token = ''
        for element in root.iter():
            if element.tag.replace('{http://mws.amazonaws.com/FulfillmentInventory/2010-10-01/}', '') == 'member':
                for member in element.iter():
                    if member.tag.replace('{http://mws.amazonaws.com/FulfillmentInventory/2010-10-01/}', '') == 'SellerSKU':
                        seller_sku = member.text
                    if member.tag.replace('{http://mws.amazonaws.com/FulfillmentInventory/2010-10-01/}', '') == 'InStockSupplyQuantity':
                        data = ({'quantity': member.text})
                if session.is_seller_sku_exist(seller_sku) is True:
                    session.update_item_quantity(data, seller_sku)
                else:
                    logging.warning('SellerSKU does not exist: ' + seller_sku)
            if element.tag.replace('{http://mws.amazonaws.com/FulfillmentInventory/2010-10-01/}', '') == 'NextToken':
                next_token = element.text
                print(next_token)
        return next_token

def get_start_time(input_start_time=None, db_start_time=None):
    # if the start time is provided, it need to be transfer into datetime format
    if input_start_time is not None:
        given_time = StringToDate.strptime(input_start_time, '%Y-%m-%d %H:%M:%S')
    else:
        given_time = db_start_time
    gmt_start_time = given_time - datetime.timedelta(1/3)
    return gmt_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def AzItems(store_id, start_time, job_id):
    db_session = db_func.DataBase(store_id)
    AWSAccessKeyId, MWSAuthToken, MarketplaceId, SellerId, SecretKey, Domain = db_session.get_store(store_id)
    Item = GetItem(AWSAccessKeyId, MWSAuthToken, MarketplaceId,
                    SellerId, SecretKey, '2009-01-01', Domain, start_time, store_id, db_func.path)
    report_data = Item.request_report()
    Item.item_to_dic(report_data, db_session)
    db_session.session_commit()
    data = Item.list_inventory_supply(start_time)
    next_token = Item.supply_data_to_dict(db_session, data)
    db_session.session_commit()
    db_session.set_job(job_id, EndTime)
    print('LastTime = ', EndTime)
    while True:
        # if NextToken is empty, that's the end of order, break and update the time in job schedule
        if next_token == '':
            break

        # otherwise keep looping until there is no NextToken
        else:
            # Get another batch of order with NextToken, and retrieve a new NextToken
            logging.info('Begin to Download Orders')
            data = Item.list_inventory_supply_by_next(next_token)
            next_token = Item.supply_data_to_dict(db_session, data)
            print('Batch Order Committed')
            db_session.session_commit()
            logging.info('Task successful，100 orders imported')
            print(next_token)

    item_id_table = db_session.select_item()
    is_updated = db_session.is_updated(item_id_table)
    cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, store_no, store_name\
        = db_session.ordersync_store_cloud(store_id)
    print(db_session.product_sync_route)
    ifs = item_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                              item_id_table, job_id, store_id, store_no, store_name, db_session.product_sync_route)
    while is_updated is False:
        ifs.synchronization()
        item_id_table = db_session.select_item()
        ifs = item_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                                  item_id_table, job_id, store_id, store_no, store_name, db_session.product_sync_route)
        is_updated = db_session.is_updated(item_id_table)
        cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, StoreNo, StoreName \
            = db_session.ordersync_store_cloud(store_id)


if __name__ == "__main__":
    store_id, start_time, job_id = sys.argv[1], sys.argv[2], sys.argv[3]
    temp = get_start_time(input_start_time=start_time)
    AzItems(store_id, temp, job_id)

