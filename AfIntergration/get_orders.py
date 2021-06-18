import sys
import re
import json
import api_func
import db_func
import order_sync
import uuid
import time
import datetime
import traceback
import xml.etree.ElementTree as ET
import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
from datetime import datetime as StringToDate
from requests import request
from requests.exceptions import ConnectionError

IsFirst = True
EndTime = datetime.datetime.now
previous_url = ''

order_head_key = {
    'acceptance_decision_date',
    'can_cancel',
    'channel',
    'commercial_id',
    'created_date',
    'currency_iso_code',
    'billing_address_city',
    'billing_address_company',
    'billing_address_country',
    'billing_country_iso_code',
    'billing_address_firstname',
    'billing_address_lastname',
    'billing_address_phone',
    'billing_address_phone_secondary',
    'billing_address_state',
    'billing_address_street_1',
    'billing_address_street_2',
    'billing_address_zip_code',
    'civility',
    'customer_id',
    'firstname',
    'lastname',
    'locale',
    'shipping_address_additional_info',
    'shipping_address_city',
    'shipping_address_company',
    'shipping_address_country',
    'shipping_address_country_iso_code',
    'shipping_address_firstname',
    'shipping_address_lastname',
    'shipping_address_phone',
    'shipping_address_phone_secondary',
    'shipping_address_state',
    'shipping_address_street_1',
    'shipping_address_street_2',
    'shipping_address_zip_code',
    'customer_debited_date',
    'has_customer_message',
    'has_incident',
    'has_invoice',
    'last_updated_date',
    'leadtime_to_ship',
    'order_id',
    'order_state',
    'order_state_reason_code',
    'order_state_reason_label',
    'paymentType',
    'payment_type',
    'payment_workflow',
    'total_deduced_amount',
    'quote_id',
    'shipping_carrier_code',
    'shipping_company',
    'shipping_price',
    'shipping_tracking',
    'shipping_tracking_url',
    'shipping_type_code',
    'shipping_type_label',
    'shipping_zone_code',
    'shipping_zone_label',
    'total_commission',
}

order_line_key = {
    'can_refund',
    'category_code',
    'category_label',
    'commission_fee',
    'commission_rate_vat',
    'commission_vat',
    'created_date',
    'debited_date',
    'description',
    'last_updated_date',
    'offer_id',
    'offer_sku',
    'offer_state_code',
    'order_line_id',
    'order_line_index',
    'order_line_state',
    'order_line_state_reason_code',
    'order_line_state_reason_label',
    'price',
    'price_additional_info',
    'price_unit',
    'product_sku',
    'product_title',
    'received_date',
    'shipped_date',
    'shipping_price',
    'shipping_price_additional_unit',
    'shipping_price_unit',
    'total_commission',
    'total_price'
}

class GetOrder:
    def __init__(self, shop_key, shop_url, start_time, store_id):
        self.shop_key = shop_key
        self.shop_url = shop_url
        self.start_time = start_time
        self.store_id = store_id
        logging.basicConfig(level=logging.DEBUG, filename=db_func.path,
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

    def recursive_iter(self, obj, keys=()):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from self.recursive_iter(v, keys + (k,))
        elif any(isinstance(obj, t) for t in (list, tuple)):
            for idx, item in enumerate(obj):
                yield from self.recursive_iter(item, keys + (idx,))
        else:
            yield keys, obj

    def get_orders(self):
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
        api = api_func.Afound(self.shop_key, self.shop_url)
        data, next_page_token = api.list_orders(limit=100, date_updated_start=self.start_time, date_updated_end=end_time_in_gmt)
        print(data)
        xml_data = ET.fromstring(data)
        print(xml_data)
        return xml_data, next_page_token
        # temp = json.loads(data.decode(encoding='utf-8'))

    def get_next_url(self, next_page_token):
        global previous_url
        temp = next_page_token.strip(previous_url)
        next_url = re.findall(r'(?<=<)(.*?)(?=>)', temp)
        print('Next URL is', next_url)
        if len(next_url) != 0:
            previous_url = '<'+next_url[0]+'>'
            return next_url[0]
        else:
            return

    def get_next_orders(self, next_url):
        api = api_func.Afound(self.shop_key, self.shop_url)
        data, next_page_token = api.list_next_orders(next_url)
        print(data)
        xml_data = ET.fromstring(data)
        print(xml_data)
        return xml_data, next_page_token

    def orders_to_dict(self, data, session):
        switch = session.accept_switch
        is_order_on_hold = False
        # XML response
        for element in data.iter():
            # print(element.tag, element.text)
            if element.tag == 'order':
                head_id = uuid.uuid4()
                order_head_dict = {
                    "OrderHeadId": head_id
                }
                is_price_set = False
                is_total_price_set = False
                pending_order_line = []
                for order_head in element.iter():
                    if order_head.tag == 'order_state' and switch is True:
                        if order_head.text == 'WAITING_ACCEPTANCE':
                            is_order_on_hold = True
                        else:
                            is_order_on_hold = False
                        if order_head.text is None:
                            order_head_dict.update({order_head.tag: ''})
                        else:
                            order_head_dict.update({order_head.tag: order_head.text})
                    elif order_head.tag == 'total_price' and is_total_price_set is False:
                        order_head_dict.update({order_head.tag: order_head.text})
                        is_total_price_set = True
                    elif order_head.tag == 'order_line':
                        line_id = uuid.uuid4()
                        order_line_dict = {
                            "OrderLineId": line_id,
                            "OrderHeadId": head_id
                        }
                        is_quantity_set = False
                        for order_line in order_head.iter():
                            if order_line.tag == 'order_line_id':
                                order_line_dict.update({'Afd_order_line_id': order_line.text})
                            elif order_line.tag == 'quantity' and is_quantity_set is False:
                                order_line_dict.update({order_line.tag: order_line.text})
                                is_quantity_set = True
                            elif order_line.tag == 'order_line_additional_fields':
                                is_discount_set = False
                                for additional_field in order_line.iter():
                                    if additional_field.text == 'discountamount':
                                        order_line_dict.update({'discount_amount': 233})
                                    if additional_field.tag == 'value' and is_discount_set is False:
                                        order_line_dict.update({'discount_amount': additional_field.text})
                                        is_discount_set = True
                            elif order_line.tag in order_line_key:
                                if order_line.text is None:
                                    order_line_dict.update({order_line.tag: ''})
                                else:
                                    order_line_dict.update({order_line.tag: order_line.text})
                        print(order_line_dict)
                        if is_order_on_hold is False:
                            if session.is_order_line_exists(order_line_dict['Afd_order_line_id']) is False:
                                session.insert_order_line(order_line_dict)
                            else:
                                session.update_order_line(order_line_dict, order_line_dict['Afd_order_line_id'])
                        elif order_line_dict['order_line_state'] == 'WAITING_ACCEPTANCE':
                            pending_order_line.append(order_line_dict['Afd_order_line_id'])
                    elif order_head.tag == 'billing_address':
                        for billing_address in order_head.iter():
                            temp_tag = order_head.tag + '_' + billing_address.tag
                            if temp_tag in order_head_key:
                                if billing_address.text is None:
                                    order_head_dict.update({temp_tag: ''})
                                else:
                                    order_head_dict.update({temp_tag: billing_address.text})
                    elif order_head.tag == 'shipping_address':
                        for shipping_address in order_head.iter():
                            temp_tag = order_head.tag + '_' + shipping_address.tag
                            if temp_tag in order_head_key:
                                if shipping_address.text is None:
                                    order_head_dict.update({temp_tag: ''})
                                else:
                                    order_head_dict.update({temp_tag: shipping_address.text})
                    elif order_head.tag == 'price' and is_price_set is False:
                        order_head_dict.update({order_head.tag: order_head.text})
                        is_price_set = True
                    elif order_head.tag in order_head_key:
                        if order_head.text is None:
                            order_head_dict.update({order_head.tag: ''})
                        else:
                            order_head_dict.update({order_head.tag: order_head.text})
                if is_order_on_hold is False:
                    if session.is_order_head_exists(order_head_dict['order_id'])is False:
                        order_head_dict.update({'AmiStatus': 0})
                        order_head_dict.update({'StoreId': self.store_id})
                        order_head_dict.update({'PluginCreateTime': self.get_local_timestamp()})
                        order_head_dict.update({'PluginUpdateTime': self.get_local_timestamp()})
                        print(order_head_dict)
                        session.insert_order_head(order_head_dict)
                    else:
                        order_head_dict.update({'UpdateStatus': 10})
                        order_head_dict.update({'PluginUpdateTime': self.get_local_timestamp()})
                        session.update_order_head(order_head_dict, order_head_dict['order_id'])
                        print(order_head_dict)
                else:
                    file = open('PendingOrders.txt', 'a')
                    file.write(order_head_dict['order_id'])
                    file.write('\n')
                    file.close()
                    self.accept_order_line(order_head_dict['order_id'], pending_order_line)
                print('End of Order\n')

        # Json response
        # for k, v in self.recursive_iter(data):
        #     if 'order_lines' in k:
        #         current_item = k[2]
        #         if len(k) == 5:
        #             temp = "{k} = Column('{k}', NVARCHAR(64), default='')".format(
        #                 k=k[-1]
        #             )
        #             order_line.update({k[-1]: v})
        #         elif len(k) == 7:
        #             temp = "{k} = Column('{k}', NVARCHAR(64), default='')".format(
        #                 k=k[-3]+'_'+k[-1]
        #             )
        #             order_line.update({k[-3]+'_'+k[-1]: v})
        #         last_item = k[2]
        #     else:
        #         if len(k) == 5:
        #             order_line.update({k[-2]+'_'+k[-1]: v})
        #         else:
        #             order_head.update({k[-1]: v})

    def accept_order_line(self, order_id, pending_order_line):
        api = api_func.Afound(self.shop_key, self.shop_url)
        response = api.accept_or_refuse(order_id, pending_order_line)

    def update_carrier_tracking(self, order_id, carrier_code=None, carrier_name=None, tracking_number=None):
        api = api_func.Afound(self.shop_key, self.shop_url)
        response = api.update_carrier_tracking(order_id, carrier_code, carrier_name, tracking_number)


def get_start_time(input_start_time=None, db_start_time=None):
    # if the start time is provided, it need to be transfer into datetime format
    if input_start_time is not None:
        given_time = StringToDate.strptime(input_start_time, '%Y-%m-%d %H:%M:%S')
    else:
        given_time = db_start_time
    gmt_start_time = given_time - datetime.timedelta(1/3)
    return gmt_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def AfIntergration(store_id, start_time, job_id):
    db_session = db_func.DataBase(store_id)
    shop_key, shop_url = db_session.get_store(store_id)
    Order = GetOrder(shop_key, shop_url, start_time, store_id)
    OrderData, next_page_token = Order.get_orders()
    Order.orders_to_dict(OrderData, db_session)
    db_session.session_commit()

    while next_page_token is not None:
        next_url = Order.get_next_url(next_page_token)
        OrderData, next_page_token = Order.get_next_orders(next_url)
        Order.orders_to_dict(OrderData, db_session)
        db_session.session_commit()

    db_session.set_job(job_id, EndTime)
    print('LastTime = ', EndTime)

    order_head_id_table = db_session.select_order_head()
    is_updated = db_session.is_updated(order_head_id_table)
    cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, store_no, store_name = db_session.ordersync_store_cloud(store_id)
    ifs = order_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                               order_head_id_table, job_id, store_id, store_no, store_name,
                               db_session.order_sync_route)
    while is_updated is False:
        ifs.synchronization()
        order_head_id_table = db_session.select_order_head()
        ifs = order_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                                   order_head_id_table, job_id, store_id, store_no, store_name,
                                   db_session.order_sync_route)
        is_updated = db_session.is_updated(order_head_id_table)
        cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, StoreNo, StoreName = db_session.ordersync_store_cloud(store_id)


    # Testing Code
    # Accept = Order.accept_order_line('PG-1234-5678', 'PG-1234-5678-1')


if __name__ == '__main__':
    store_id, start_time, job_id = sys.argv[1], sys.argv[2], sys.argv[3]

    # Using db start time
    # store_id, job_id = sys.argv[1], sys.argv[2]

    # Turn BJS time to GMT Time
    temp = get_start_time(input_start_time=start_time)
    print(temp)
    AfIntergration(int(store_id), temp, job_id)
