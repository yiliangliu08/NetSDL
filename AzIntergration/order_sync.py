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
    'OrigOrderNumber',
    'OrderLineNumber',
    'OrigSkuCode',
    'OrigItemName',
    'OrigQty',
    'ItemTax',
    'ShippingTax',
    'GiftWrapTax',
    'ShippingDiscountTax',
    'PromotionDiscountTax',
    'StandardPrice',
    'PromotionDiscount',
    'OrderLineStatus',

    'ShippingMethod',
    'ShipToName',
    'ShipToAdd1',
    'ShipToAdd2',
    'ShipToAdd3',
    'ShipToCity',
    'ShipToProvince',
    'ShipToZip',

    'OrderDate',
    'OrigOrderStatus',
    'ProcessType',
    'BillToName',
    'BillToEmail',
    'BillToPhone',
    'ActualTotalAmount',
    'BillToAdd1',
]

order_line_list_key = [
    'OrderLineNumber',
    'OrigSkuCode',
    'OrigItemName',
    'OrigQty',
    'ItemTax',
    'ShippingTax',
    'GiftWrapTax',
    'ShippingDiscountTax',
    'PromotionDiscountTax',
    'StandardPrice',
    'PromotionDiscount',
    'OrderLineStatus'
]

ship_list_key = [
    'ShippingMethod',
    'ShipToName',
    'ShipToAdd1',
    'ShipToAdd2',
    'shipToAdd3',
    'ShipToCity',
    'ShipToProvince',
    'ShipToZip',
]


class OrderSync:
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
                order_amount = 0
                for i, Ifs_key in enumerate(api_keys):
                    if Ifs_key in order_line_list_key:
                        if Ifs_key == 'StandardPrice':
                            if order_line_data['RequestQty'] != 0:
                                order_line_data[Ifs_key] = ('%.2f' % (element[i]/order_line_data['RequestQty']))
                                order_line_data['StandardAmount'] = element[i]
                                order_amount += element[i]
                            else:
                                order_line_data[Ifs_key] = 0.0
                                order_line_data['StandardAmount'] = 0.0
                                order_amount += 0.0
                        elif Ifs_key == 'OrigSkuCode':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['SkuCode'] = element[i]
                        elif Ifs_key == 'OrigQty':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['RequestQty'] = element[i]
                        elif 'Tax' in Ifs_key:
                            tax_amount += element[i]
                            order_line_data['TaxAmount'] = tax_amount
                        elif Ifs_key == 'PromotionDiscount':
                            if order_line_data['RequestQty'] != 0:
                                amount_after_discount = order_line_data['StandardAmount']-element[i]
                                order_line_data['Price'] = (
                                        '%.2f' % (amount_after_discount/order_line_data['RequestQty']))
                                order_line_data['Amount'] = amount_after_discount
                                amount_with_tax = order_line_data['Amount']+tax_amount
                                order_line_data['WithTaxPrice'] = (
                                        '%.2f' % (amount_with_tax/order_line_data['RequestQty']))
                                order_line_data['WithTaxAmount'] = amount_with_tax
                                order_line_data['ActualPrice'] = (
                                        '%.2f' % (amount_with_tax/order_line_data['RequestQty']))
                                order_line_data['ActualAmount'] = amount_with_tax
                                order_line_data['ShipId'] = 1
                            else:
                                order_line_data['Price'] = 0.0
                                order_line_data['Amount'] = 0.0
                                order_line_data['WithTaxPrice'] = 0.0
                                order_line_data['WithTaxAmount'] = 0.0
                                order_line_data['ActualPrice'] = 0.0
                                order_line_data['ActualAmount'] = 0.0
                                order_line_data['ShipId'] = 1
                        elif Ifs_key == 'OrderLineStatus':
                            if element[i] == 'Pending':
                                order_line_data[Ifs_key] = 0
                            elif element[i] == 'Unshipped':
                                order_line_data[Ifs_key] = 1
                            elif element[i] == 'Shipped':
                                order_line_data[Ifs_key] = 60
                            elif element[i]  == 'Canceled':
                                order_line_data[Ifs_key] = 99
                        else:
                            order_line_data[Ifs_key] = element[i]
                    elif Ifs_key in ship_list_key:
                        if len(ship_list_data) == 0:
                            ship_list_data['ShipId'] = 1
                        if Ifs_key == 'ShipToName':
                            if element[i] != '':
                                split_name = element[i].split(' ')
                                ship_list_data[Ifs_key] = split_name[0]
                                ship_list_data['ShipToName1'] = split_name[-1]
                                # If the customer does not have a middle name
                                try:
                                    if len(split_name) == 2:
                                        ship_list_data['ShipToName2'] = ''
                                    else:
                                        ship_list_data['ShipToName2'] = split_name[1]
                                except IndexError:
                                    logging.warning('Weird Name  ' + str(IndexError))
                                    ship_list_data['ShipToName2'] = ''
                            else:
                                ship_list_data[Ifs_key] = ''
                                ship_list_data['ShipToName1'] = ''
                                ship_list_data['ShipToName2'] = ''
                        elif Ifs_key == 'ShipToAdd2':
                            temp = element[i] + element[i+1]
                            ship_list_data[Ifs_key] = temp
                        elif Ifs_key == 'ShipToAdd3':
                            continue
                        else:
                            ship_list_data[Ifs_key] = element[i]
                    elif Ifs_key != 'ShipToAdd3':
                        if Ifs_key == 'OrderDate':
                            fixed_time = element[i].replace('T', ' ').replace('Z', '')
                            order_data[Ifs_key] = fixed_time
                            order_data['SettleDate'] = fixed_time
                            order_data['CreateDate'] = fixed_time
                        elif Ifs_key == 'ActualTotalAmount':
                            order_data[Ifs_key] = element[i]
                            order_data['TotalAmount'] = element[i]
                            order_data['PayAmount'] = element[i]
                            order_data['OrderAmount'] = order_amount
                        elif Ifs_key == 'BillToAdd1':
                            order_data[Ifs_key] = ship_list_data['ShipToAdd1']
                            order_data['BillToAdd2'] = ship_list_data['ShipToAdd2']
                            order_data['BillToCity'] = ship_list_data['ShipToCity']
                            order_data['BillToProvince'] = ship_list_data['ShipToProvince']
                            order_data['BillToZip'] = ship_list_data['ShipToZip']
                            order_data['CustomerName'] = order_data['BillToName']
                            order_data['CHCode'] = self.store_no
                            order_data['CHName'] = self.store_name
                            order_data['StoreCode'] = self.store_no
                            order_data['StoreName'] = self.store_name
                        elif Ifs_key == 'OrigOrderStatus':
                            if element[i] == 'Pending':
                                order_data['OrderStatus'] = 0
                            elif element[i] == 'Unshipped':
                                order_data['OrderStatus'] = 1
                            elif element[i] == 'Shipped':
                                order_data['OrderStatus'] = 60
                            elif element[i]  == 'Canceled':
                                order_data['OrderStatus'] = 99
                            order_data[Ifs_key] = element[i]
                        else:
                            order_data[Ifs_key] = element[i]
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
                        if Ifs_key == 'StandardPrice':
                            if order_line_data['RequestQty'] != 0:
                                order_line_data[Ifs_key] = ('%.2f' % (element[i]/order_line_data['RequestQty']))
                                order_line_data['StandardAmount'] = element[i]
                                order_amount += element[i]
                            else:
                                order_line_data[Ifs_key] = 0.0
                                order_line_data['StandardAmount'] = 0.0
                                order_amount += 0.0
                        elif Ifs_key == 'OrigSkuCode':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['SkuCode'] = element[i]
                        elif Ifs_key == 'OrigQty':
                            order_line_data[Ifs_key] = element[i]
                            order_line_data['RequestQty'] = element[i]
                        elif 'Tax' in Ifs_key:
                            tax_amount += element[i]
                            order_line_data['TaxAmount'] = tax_amount
                        elif Ifs_key == 'PromotionDiscount':
                            if order_line_data['RequestQty'] != 0:
                                amount_after_discount = order_line_data['StandardAmount']-element[i]
                                order_line_data['Price'] = (
                                        '%.2f' % (amount_after_discount/order_line_data['RequestQty']))
                                order_line_data['Amount'] = amount_after_discount
                                amount_with_tax = order_line_data['Amount']+tax_amount
                                order_line_data['WithTaxPrice'] = (
                                        '%.2f' % (amount_with_tax/order_line_data['RequestQty']))
                                order_line_data['WithTaxAmount'] = amount_with_tax
                                order_line_data['ActualPrice'] = (
                                        '%.2f' % (amount_with_tax/order_line_data['RequestQty']))
                                order_line_data['ActualAmount'] = amount_with_tax
                                order_line_data['ShipId'] = 1
                            else:
                                order_line_data['Price'] = 0.0
                                order_line_data['Amount'] = 0.0
                                order_line_data['WithTaxPrice'] = 0.0
                                order_line_data['WithTaxAmount'] = amount_with_tax
                                order_line_data['ActualPrice'] = 0.0
                                order_line_data['ActualAmount'] = 0.0
                                order_line_data['ShipId'] = 1
                        elif Ifs_key == 'OrderLineStatus':
                            if element[i] == 'Pending':
                                order_line_data[Ifs_key] = 0
                            elif element[i] == 'Unshipped':
                                order_line_data[Ifs_key] = 1
                            elif element[i] == 'Shipped':
                                order_line_data[Ifs_key] = 60
                            elif element[i] == 'Canceled':
                                order_line_data[Ifs_key] = 99
                        else:
                            order_line_data[Ifs_key] = element[i]
                OrderLine.append(order_line_data)
                # print(order_line_data)
        # Append everything to List of Order in the required format
            order_data['OrderAmount'] = order_amount
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
        # print(ListOfOrder)
        return ListOfOrder

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
