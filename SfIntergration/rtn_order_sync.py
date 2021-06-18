import json
import time
import db_func
from amiauth import aes_cipher
from amiauth import Amiauth

api_keys = [
    'OrderNumber',

    'OrderLineNumber',
    'RequestQty',
    'Amount',
    'TaxAmount',
    'OrigProductName',
    'SkuCode',
    'ProductName',
    'OrigOrderStatus',

    'OrigOrderNumber',
    'RequestDate',
    'Remark'
]

return_line_list_key = [
    'OrderLineNumber',
    'RequestQty',
    'Amount',
    'TaxAmount',
    'OrigProductName',
    'SkuCode',
    'ProductName',
    'OrigOrderStatus'
]

class OrderSync:
    def __init__(self, session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, temp,
                 job_id, store_id):
        self.cloud_define_id = cloud_define_id
        self.cloud_secret = cloud_secret
        self.cloud_token = cloud_token
        self.cloud_url = cloud_url
        self.cloud_key = cloud_key
        self.session = session
        self.temp = temp
        self.job_id = job_id
        self.store_id = store_id

    def get_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', local_time)

    def get_data(self):
        data = self.session.select_return_data(self.temp)
        return data

    def sort_order(self):
        data = self.get_data()
        Return_head_id_list = []
        ListOfReturn = []
        current_return_number = ''
        last_return_number = ''
        return_data = {}
        return_line_data = {}
        ReturnLine = []
        for element in data:
            # Reset OrderLine for every new Order
            tax_amount = 0
            return_number = element[0]
            # If it is a new order number
            if return_number != current_return_number:
                return_data = {}
                return_line_data = {}
                ReturnLine = []
                for i, Ifs_key in enumerate(api_keys):
                    if Ifs_key in return_line_list_key:
                        if Ifs_key == 'OrigOrderStatus':
                            return_line_data['ShipId'] = 1
                        return_line_data[Ifs_key] = element[i]
                    else:
                        if Ifs_key == 'RequestDate':
                            fixed_time = element[i].replace('T', ' ')
                            return_data[Ifs_key] = fixed_time
                        elif Ifs_key == 'Remark':
                            return_data['CHCode'] = 'SF03'
                            return_data['CHName'] = 'Shopify'
                            return_data[Ifs_key] = element[i]
                        else:
                            return_data[Ifs_key] = element[i]
                current_return_number = return_number
                Return_head_id_list.append(current_return_number)
                ReturnLine.append(return_line_data)
                print(return_data)
                print(return_line_data)
            # If it is the same order number, generate OrderLine only
            else:
                if Ifs_key in return_line_list_key:
                    return_line_data[Ifs_key] = element[i]
                ReturnLine.append(return_line_data)
                # print(order_line_data)
        # Append everything to List of Order in the required format
        # print(order_data)
        # print(order_data)
        # print(ship_list_data)
            return_data.update({'RtnOrderLineList': ReturnLine})
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

    def list_to_json(self, list_of_order):
        OrderList = {}
        OrderList['RTNORDERLIST'] = list_of_order
        order_list_str = json.dumps(OrderList, ensure_ascii=False, separators=(',', ':'))
        # print(order_list_str)
        return order_list_str

    def ami_encryption(self, order_list_str):
        print(self.cloud_secret, self.cloud_token, self.cloud_url, self.cloud_key)
        signature = aes_cipher(self.cloud_secret, order_list_str)
        print(signature)
        errCode, errMsg, response, request_url, request_time, duration\
            = Amiauth(self.cloud_key, self.cloud_token, order_list_str, signature, self.cloud_url)
        return errCode, errMsg, response, request_url, request_time, duration

    def synchronization(self):
        data = self.sort_order()
        json_string = self.list_to_json(data)
        print (json_string)
        errCode, errMsg, response, request_url, request_time, duration = self.ami_encryption(json_string)
        print(self.cloud_token)
        print('ErrCode: ', errCode)
        print('ErrMsg: ', errMsg)
        if errCode == 0:
            is_error = 0
            self.session.update_status(self.temp)
        else:
            is_error = 1
            self.output_to_log(json_string)
            self.output_to_log(errMsg)
            self.session.insert_log(self.job_id, self.store_id, self.cloud_define_id,
                                    request_url, response, is_error, request_time, duration)

    def get_log_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    def output_to_log(self, content):
        file = open(db_func.path, 'a')
        file.write(content)
        file.write('\n')
        file.close()