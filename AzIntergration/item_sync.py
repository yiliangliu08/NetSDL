import json
import time
from amiauth import aes_cipher
from amiauth import Amiauth
import sync
import db_func
import get_orders
import json
import traceback
import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

CONFIG_FILE = 'app.cfg'

api_keys = [
    'ProductId',
    'ProductName',
    'StandardSalesPrice',
    'InventoryQuantity',
    'OrigStatus',
    'CreateDate'
    ]


class OrderSync:
    def __init__(self, session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, temp,
                 job_id, store_id, store_no, store_name, product_sync_route):
        self.cloud_define_id = cloud_define_id
        self.cloud_secret = cloud_secret
        self.cloud_token = cloud_token
        self.cloud_url = cloud_url
        self.cloud_key = cloud_key
        self.session = session
        self.temp = temp
        self.job_id = job_id
        self.store_id = store_id
        self.store_no = store_no
        self.store_name = store_name
        self.order_sync_route = product_sync_route
        logging.basicConfig(level=logging.DEBUG, filename=db_func.path,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def get_data(self):
        data = self.session.select_item_data(self.temp)
        return data

    def sort_order(self):
        data = self.get_data()
        ListOfItem = []
        # Only one OrderHead and one Shiplist required at this moment
        # Iterate through all data
        for element in data:
            sku_list = []
            product_data = {}
            sku_data = {}
            is_active = True
            for i, Ifs_key in enumerate(api_keys):
                if Ifs_key in api_keys:
                    if Ifs_key == 'InventoryQuantity':
                        product_data.update({Ifs_key: element[i]})
                        sku_data.update({Ifs_key: element[i]})
                    elif Ifs_key == 'CreateDate':
                        product_data.update({Ifs_key: element[i]})
                        sku_data.update({Ifs_key: element[i]})
                    elif Ifs_key == 'OrigStatus':
                        product_data.update({Ifs_key: element[i]})
                        sku_data.update({Ifs_key: element[i]})
                        if element[i] == 'Active':
                            product_data.update({'Status': 1})
                            sku_data.update({'Status': 1})
                        else:
                            product_data.update({'Status': 0})
                            is_active = False
                    elif Ifs_key == 'ProductId':
                        product_data.update({Ifs_key: element[i]})
                        product_data.update({'CHCode': self.store_no})
                        product_data.update({'CHName': self.store_name})
                        sku_data.update({'SkuId': element[i]})
                    else:
                        product_data.update({Ifs_key: element[i]})
            if is_active is True:
                sku_list.append(sku_data)
            product_data.update({'SkuList': sku_list})
            ListOfItem.append(product_data)
        return ListOfItem

    #-------------------------------------------------------------------------------------------------------------------
    # Below code can be commented if import sync as object

    def get_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', local_time)

    def list_to_json(self, list_of_order, list_name):
        OrderList = {}
        OrderList[list_name] = list_of_order
        order_list_str = json.dumps(OrderList, ensure_ascii=False, separators=(',', ':'))
        print(order_list_str)
        return order_list_str

    def ami_encryption(self, order_list_str):
        url = self.cloud_url+'/'+self.order_sync_route
        print(self.cloud_secret, self.cloud_token, url, self.cloud_key)
        signature = aes_cipher(self.cloud_secret, order_list_str)
        # print(signature)
        errCode, errMsg, response, request_url, request_time, duration\
            = Amiauth(self.cloud_key, self.cloud_token, order_list_str, signature, url)
        return errCode, errMsg, response, request_url, request_time, duration

    def synchronization(self):
        if self.order_sync_route == 'RtnOrder/RtnOrderSync':
            list_name = 'RTNORDERLIST'
        elif self.order_sync_route == 'Product/ChannelProductSync':
            list_name = 'ITEMLIST'
        else:
            list_name = 'ORDERLIST'
        data = self.sort_order()
        json_string = self.list_to_json(data, list_name)
        errCode, errMsg, response, request_url, request_time, duration = self.ami_encryption(json_string)
        print(self.cloud_token)
        print('ErrCode: ', errCode)
        print('ErrMsg: ', errMsg)
        if errCode == 0:
            if self.order_sync_route == 'RtnOrder/RtnOrderSync':
                self.session.update_return_status(self.temp)
            elif self.order_sync_route == 'Product/ChannelProductSync':
                self.session.update_item_status(self.temp)
            else:
                self.session.update_order_status(self.temp)
        else:
            is_error = 1
            logging.error(errCode+errMsg)
            self.session.insert_log(self.job_id, self.store_id, self.cloud_define_id,
                                    request_url, response, is_error, request_time, duration)

    def get_log_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime("%Y-%m-%d %H:%M:%S", local_time)
