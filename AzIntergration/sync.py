import json
import time
import db
from amiauth import aes_cipher
from amiauth import Amiauth


class Sync(object):
    def __init__(self, session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, temp,
                 job_id, store_id, store_no, store_name, order_sync_route):
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
        self.order_sync_route = order_sync_route

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
        else:
            list_name = 'ORDERLIST'
        data = self.sort_order()
        json_string = self.list_to_json(data, list_name)
        errCode, errMsg, response, request_url, request_time, duration = self.ami_encryption(json_string)
        print(self.cloud_token)
        print('ErrCode: ', errCode)
        print('ErrMsg: ', errMsg)
        if errCode == 0:
            is_error = 0
            if self.order_sync_route == 'RtnOrder/RtnOrderSync':
                self.session.update_return_status(self.temp)
            else:
                self.session.update_order_status(self.temp)
        else:
            is_error = 1
            self.output_to_log(json_string)
            self.output_to_log(errCode)
            self.output_to_log(errMsg)
            self.session.insert_log(self.job_id, self.store_id, self.cloud_define_id,
                                    request_url, response, is_error, request_time, duration)

    def get_log_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    def output_to_log(self, content):
        file = open(get_orders.path, 'a')
        file.write(content)
        file.write('\n')
        file.close()