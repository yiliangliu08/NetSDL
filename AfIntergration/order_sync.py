import sync
import json
import time
import db_func
import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
from amiauth import aes_cipher
from amiauth import Amiauth

api_keys = [

    'OrigOrdernumber',

    'OrderLineNumber',
    'OrigOrderLineStatus',
    'SkuCode',
    'Price',
    'ProductSku',
    'ProductName',
    'OrigQty',
    'ShippingDate',
    'WithTaxAmount',

    'ShipToCity',
    'ShipToCompany',
    'ShipToCountry',
    'ShipToFirstName',
    'ShipToLastName',
    'ShipToMobile',
    'ShipToPhone',
    'ShipToProvince',
    'ShipToAddress1',
    'ShipToAddress2',
    'ShipToZip',
    'CarrierNumber',
    'CarrierShippingNumber',
    'ServiceType',

    'OrderDate',
    'SettleDate',
    'BillToCity',
    'BillToCompany',
    'BillToCountry',
    'BillToFirstName',
    'BillToLastName',
    'BillToMobile',
    'BillTOPhone',
    'BillToProvince',
    'BillToAddress1',
    'BillToAddress2',
    'BillToZip',
    'CustomerCode',
    'FisrtName',
    'LastName',
    'OrigOrderStatus',
    'PaymentType',
    'DiscountAmount',
    'TotalAmount'
]

order_line_list_key = [
    'OrderLineNumber',
    'OrigOrderLineStatus',
    'SkuCode',
    'Price',
    'ProductSku',
    'ProductName',
    'OrigQty',
    'ShippingDate',
    'WithTaxAmount',
]

ship_list_key = [
    'ShipToCity',
    'ShipToCompany',
    'ShipToCountry',
    'ShipToFirstName',
    'ShipToLastName',
    'ShipToMobile',
    'ShipToPhone',
    'ShipToProvince',
    'ShipToAddress1',
    'ShipToAddress2',
    'ShipToZip',
    'CarrierNumber',
    'CarrierShippingNumber',
    'ServiceType'
]


# class OrderSync(sync.Sync):
class OrderSync():
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
        # sync.Sync.__init__(self, session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, temp,
        #                    job_id, store_id, store_no, store_name, order_sync_route)
        logging.basicConfig(level=logging.DEBUG, filename=db_func.path,
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def get_data(self):
        data = self.session.select_order_data(self.temp)
        return data

    def sort_order(self):
        Order_head_id_list = []
        data = self.get_data()
        ListOfOrder = []
        current_order_number = ''
        last_order_number = ''
        order_data = {}
        order_line_data = {}
        OrderLine = []
        Ship = []
        order_amount = 0
        # Only one OrderHead and one Shiplist required at this moment
        # Iterate through all data
        for element in data:
            # Reset OrderLine for every new Order
            tax_amount = 0
            order_number = element[0]
            # If it is a new order number
            if order_number != current_order_number:
                order_data = {}
                ship_list_data = {}
                order_line_data = {}
                OrderLine = []
                Ship = []
                for i, Ifs_key in enumerate(api_keys):
                    if Ifs_key in order_line_list_key:
                        if Ifs_key == 'WithTaxAmount':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['Amount'] = element[i]
                            order_line_data['StandardAmount'] = element[i]
                            order_line_data['ActualAmount'] = element[i]
                            order_line_data['TotalAmount'] = element[i]
                        elif Ifs_key == 'Price':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['WithTaxPrice'] = element[i]
                            order_line_data['ActualPrice'] = element[i]
                            order_line_data['StandardPrice'] = element[i]
                        elif Ifs_key == 'OrigQty':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['RequestQty'] = element[i]
                            order_line_data['ShipId'] = 1
                        elif Ifs_key == 'OrigOrderLineStatus':
                            order_line_data[Ifs_key] = element[i]
                            if element[i] == 'WAITING ACCEPTANCE':
                                order_line_data['OrderLineStatus'] = 0
                            elif element[i] == 'WAITING DEBIT':
                                order_line_data['OrderLineStatus'] = 0
                            elif element[i] == 'WAITING_DEBIT_PAYMENT':
                                order_line_data['OrderLineStatus'] = 0
                            elif element[i] == 'INCIDENT_OPEN':
                                order_line_data['OrderLineStatus'] = 0
                            elif element[i] == 'SHIPPING':
                                order_line_data['OrderLineStatus'] = 1
                            elif element[i] == 'SHIPPED':
                                order_line_data['OrderLineStatus'] = 60
                            elif element[i] == 'RECEIVED':
                                order_line_data['OrderLineStatus'] = 100
                            elif element[i] == 'REFUSED':
                                order_line_data['OrderLineStatus'] = 99
                            elif element[i] == 'CLOSED':
                                order_line_data['OrderLineStatus'] = 99
                            elif element[i] == 'CANCELED':
                                order_line_data['OrderLineStatus'] = 99
                            elif element[i] == 'REFUNDED':
                                order_line_data['OrderLineStatus'] = 99
                            elif element[i] == 'INCIDENT_CLOSED':
                                order_line_data['OrderLineStatus'] = 99
                        else:
                            order_line_data[Ifs_key] = element[i]
                    elif Ifs_key in ship_list_key:
                        if Ifs_key == 'ShipToFirstName':
                            ship_list_data['ShipToName'] = element[i]+' '+element[i+1]
                        elif Ifs_key == 'ShipToLastName':
                            ship_list_data['ShipId'] = 1
                        else:
                            ship_list_data[Ifs_key] = element[i]
                    else:
                        if Ifs_key == 'SettleDate' and element[i] == '':
                            order_data[Ifs_key] = order_data['OrderDate']
                        elif Ifs_key == 'BillToFirstName':
                            order_data['BillToName'] = element[i]+' '+element[i+1]
                        elif Ifs_key == 'BillToLastName':
                            continue
                        elif Ifs_key == 'FirstName':
                            order_data['CustomerName'] = element[i]+' '+element[i+1]
                        elif Ifs_key == 'LastName':
                            continue
                        elif Ifs_key == 'TotalAmount':
                            order_data[Ifs_key] = element[i]
                            order_data['OrderAmount'] = element[i]
                            order_data['ActualTotalAmount'] = element[i]
                            order_data['PayAmount'] = element[i]
                            order_data['OrderWithTaxAmount'] = element[i]
                            order_data['CHCode'] = self.store_no
                            order_data['CHName'] = self.store_name
                            order_data['StoreCode'] = self.store_no
                            order_data['StoreName'] = self.store_name
                        elif Ifs_key == 'OrigOrderStatus':
                            if element[i] == 'WAITING_ACCEPTANCE':
                                order_data['OrderStatus'] = 0
                            elif element[i] == 'WAITING_DEBIT':
                                order_data['OrderStatus'] = 0
                            elif element[i] == 'WAITING_DEBIT_PAYMENT':
                                order_data['OrderStatus'] = 0
                            elif element[i] == 'SHIPPING':
                                order_data['OrderStatus'] = 1
                            elif element[i] == 'INCIDENT_OPEN':
                                order_data['OrderStatus'] = 0
                            elif element[i] == 'SHIPPED':
                                order_data['OrderStatus'] = 60
                            elif element[i] == 'RECEIVED':
                                order_data['OrderStatus'] = 100
                            elif element[i] == 'REFUSED':
                                order_data['OrderStatus'] = 99
                            elif element[i] == 'CLOSED':
                                order_data['OrderStatus'] = 99
                            elif element[i] == 'CANCELED':
                                order_data['OrderStatus'] = 99
                            elif element[i] == 'INCIDENT_CLOSED':
                                order_data['OrderLineStatus'] = 99
                            order_data[Ifs_key] = element[i]
                        else:
                            order_data[Ifs_key] = element[i]
                print(order_line_data)
                # print(ship_list_data)
                # print(order_data)
                current_order_number = order_number
                Order_head_id_list.append(current_order_number)
                Ship.append(ship_list_data)
                OrderLine.append(order_line_data)
                # print(order_data)
                # print(ship_list_data)
                # print(order_line_data)
            # If it is the same order number, generate OrderLine only
            else:
                order_line_data = {}
                for i, Ifs_key in enumerate(api_keys):
                    if Ifs_key in order_line_list_key:
                        if Ifs_key == 'WithTaxAmount':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['ActualAmount'] = element[i]
                            order_line_data['TotalAmount'] = element[i]
                        elif Ifs_key == 'Price':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['WithTaxPrice'] = element[i]
                            order_line_data['ActualPrice'] = element[i]
                        elif Ifs_key == 'OrigQty':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['RequestQty'] = element[i]
                            order_line_data['ShipId'] = 1
                        elif Ifs_key == 'OrigOrderLineStatus':
                            order_line_data[Ifs_key] = element[i]
                            if element[i] == 'WAITING ACCEPTANCE':
                                order_line_data['OrderLineStatus'] = 0
                            elif element[i] == 'WAITING DEBIT':
                                order_line_data['OrderLineStatus'] = 0
                            elif element[i] == 'WAITING_DEBIT_PAYMENT':
                                order_line_data['OrderLineStatus'] = 0
                            elif element[i] == 'INCIDENT_OPEN':
                                order_line_data['OrderLineStatus'] = 0
                            elif element[i] == 'SHIPPING':
                                order_line_data['OrderLineStatus'] = 1
                            elif element[i] == 'SHIPPED':
                                order_line_data['OrderLineStatus'] = 60
                            elif element[i] == 'RECEIVED':
                                order_line_data['OrderLineStatus'] = 100
                            elif element[i] == 'REFUSED':
                                order_line_data['OrderLineStatus'] = 99
                            elif element[i] == 'CLOSED':
                                order_line_data['OrderLineStatus'] = 99
                            elif element[i] == 'CANCELED':
                                order_line_data['OrderLineStatus'] = 99
                            elif element[i] == 'REFUNDED':
                                order_line_data['OrderLineStatus'] = 99
                            elif element[i] == 'INCIDENT_CLOSED':
                                order_line_data['OrderLineStatus'] = 99
                        else:
                            order_line_data[Ifs_key] = element[i]
                OrderLine.append(order_line_data)
                print(order_line_data)
        # Append everything to List of Order in the required format
        # print(order_data)
        # print(order_data)
        # print(ship_list_data)
            order_data.update({'OrderLineList': OrderLine})
            order_data.update({'ShipList': Ship})
            if current_order_number == last_order_number or last_order_number == '':
                if len(ListOfOrder) != 0:
                    ListOfOrder.pop()
                ListOfOrder.append(order_data)
                last_order_number = current_order_number
            else:
                ListOfOrder.append(order_data)
                last_order_number = current_order_number
        print(ListOfOrder)
        return ListOfOrder, Order_head_id_list

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
        data, order_head_id = self.sort_order()
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
            logging.error(errCode + errMsg)
            self.session.insert_log(self.job_id, self.store_id, self.cloud_define_id,
                                    request_url, response, is_error, request_time, duration)

    def get_log_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime("%Y-%m-%d %H:%M:%S", local_time)
