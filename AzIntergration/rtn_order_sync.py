import json
import time
import db_func
from amiauth import aes_cipher
from amiauth import Amiauth
import os
import sync
import json
import traceback
from amiauth import aes_cipher
from amiauth import Amiauth
import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

api_keys = [
    'OrigOrderNumber',

    'OrderLineNumber',
    'ProductName',
    'OrigSkuCode',
    'RequestQty',
    'CurrencyType',
    'Amount',
    'OrigRefundStatus',

    'CarrierShippingNumber',
    'CarrierNumber',
    
    'RefOrderNumber',
    'RequestDate',
    'Order',
    'OrderAmount'
]

return_line_list_key = [
    'OrderLineNumber',
    'ProductName',
    'OrigSkuCode',
    'RequestQty',
    'CurrencyType',
    'Amount',
    'OrigRefundStatus'
]

ship_list_key = [
    'CarrierShippingNumber',
    'CarrierNumber'
]


class OrderSync:
    def __init__(self, session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, temp,
                 job_id, store_id, store_no, store_name, rtn_order_sync_route):
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
        self.order_sync_route = rtn_order_sync_route
        logging.basicConfig(level=logging.DEBUG, filename=db_func.path,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def get_data(self):
        data = self.session.select_return_data(self.temp)
        return data

    def sort_order(self):
        Return_head_id_list = []
        data = self.get_data()
        ListOfReturn = []
        current_return_number = ''
        last_return_number = ''
        return_data = {}
        return_line_data = {}
        ReturnLine = []
        Ship = []
        return_amount = 0
        # Only one OrderHead and one Shiplist required at this moment
        # Iterate through all data
        for element in data:
            # Reset OrderLine for every new Order
            tax_amount = 0
            return_number = element[0]
            # If it is a new order number
            if return_number != current_return_number:
                return_data = {}
                ship_list_data = {}
                return_line_data = {}
                ReturnLine = []
                Ship = []
                for i, Ifs_key in enumerate(api_keys):
                    if Ifs_key in return_line_list_key:
                        if Ifs_key == 'Amount':
                            if return_line_data['RequestQty'] != 0:
                                return_line_data['Price'] = 0
                                return_line_data['ShipId'] = 1
                            else:
                                return_line_data['Price'] = element[i]/data['RequestQty']
                                return_line_data['ShipId'] = 1
                            return_line_data[Ifs_key] = element[i]
                        else:
                            return_line_data[Ifs_key] = element[i]
                    elif Ifs_key in ship_list_key:
                        ship_list_data['ShipId'] = 1
                        ship_list_data[Ifs_key] = element[i]
                    else:
                        if Ifs_key == 'RefOrderNumber':
                            return_data['CHCode'] = 'AZ'
                            return_data['CHName'] = 'Amazon'
                        return_data[Ifs_key] = element[i]
                current_return_number = return_number
                Return_head_id_list.append(current_return_number)
                Ship.append(ship_list_data)
                ReturnLine.append(return_line_data)
                print(return_data)
                print(ship_list_data)
                print(return_line_data)
            # If it is the same order number, generate OrderLine only
            else:
                return_line_data = {}
                if Ifs_key in return_line_list_key:
                    if Ifs_key == 'Amount':
                        if data['RequestQty'] != 0:
                            return_line_data['Price'] = 0
                        else:
                            return_line_data['Price'] = element[i] / data['RequestQty']
                        return_line_data[Ifs_key] = element[i]
                ReturnLine.append(return_line_data)
                # print(order_line_data)
        # Append everything to List of Order in the required format
            return_data['OrderAmount'] = return_amount
        # print(order_data)
        # print(order_data)
        # print(ship_list_data)
            return_data.update({'RtnOrderLineList': ReturnLine})
            return_data.update({'ShipList': Ship})
            if current_return_number == last_return_number or last_return_number == '':
                if len(ListOfReturn) != 0:
                    ListOfReturn.pop()
                ListOfReturn.append(return_data)
                last_return_number = current_return_number
            else:
                ListOfReturn.append(return_data)
                last_return_number = current_return_number
        print(ListOfReturn)
        return ListOfReturn

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