import sys
import api_func
import db_func
import rtn_order_sync
import uuid
import time
import datetime
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime as StringToDate
from requests import request
from requests.exceptions import ConnectionError

path = ''


ReturnHeadKey = {
    'order_id',
    'order_date',
    'merchant_rma_id',
    'amazon_rma_id',
    'return_request_date',
    'return_request_status',
    'a_to_z_claim',
    'is_prime',
    'tracking_id',
    'return_carrier',
    'currency_code',
    'label_cost',
    'label_type',
    'label_to_be_paid_by',
    'return_type',
    'order_amount',
    'order_quantity',
    }
ReturnLineKey = {}

EndTime = datetime.datetime.now
IsFirst = True

class GetReturn:
    def __init__(self, aws_access_key_id, mws_auth_key, marketplace_id, seller_id, secret_key, version, domain, start_time, store_id):
        self.aws_access_key_id = aws_access_key_id
        self.mws_auth_key = mws_auth_key
        self.marketplace_id = marketplace_id
        self.seller_id = seller_id
        self.secret_key = secret_key
        self.version = version
        self.domain = domain
        self.start_time = start_time
        self.store_id = store_id

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
        global EndTime
        global IsFirst
        end_time_in_gmt, temp = self.get_timestamp()
        # Only save the first EndTime in BJS as global variable
        if IsFirst is True:
            EndTime = temp
            IsFirst = False
            # print('LastTime = ' + EndTime)
        # Both start_time and end_time are in GMT
        # print(end_time_in_gmt)
        url = mws.request_report('_GET_XML_RETURNS_DATA_BY_RETURN_DATE_',
                                 start_date=self.start_time, end_date=end_time_in_gmt)
        response = request('Post', url)
        # print(response.content)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for element in root.iter():
            if element.tag.replace('{http://mws.amazonaws.com/doc/2009-01-01/}', '') == 'ReportRequestId':
                # print(element.text)
                report_request_id = element.text
                break
        ready = False
        while ready is False:
            ready = self.is_report_ready(report_request_id)
        print('Report Ready')
        url = mws.get_report_list(report_request_id)
        response = request('Post', url)
        # print(response.content)
        xml_data = response.content
        root = ET.fromstring(xml_data)
        for element in root.iter():
            if element.tag.replace('{http://mws.amazonaws.com/doc/2009-01-01/}', '') == 'ReportId':
                report_id = element.text
                # print(report_id)
                break
        url = mws.get_report(report_id)
        print(url)
        response = request('Post', url)
        xml_data = response.content
        # print(xml_data)
        root = ET.fromstring(xml_data)
        return root

    def return_head_to_dic(self, root, session):
        for element in root.iter():
            # print(element.tag, ': ', element.text)
            head_data = {}
            line_data = {}
            if element.tag == 'return_details':
                order_id = ''
                is_order_exists = False
                for curr in element.iter():
                    if curr.tag == 'order_id':
                        order_id = curr.text
                is_order_exists = session.is_return_exists(order_id)
                head_id = uuid.uuid4()
                head_data.update({'ReturnHeadId': head_id})
                new_order_head = head_id
                for return_head in element.iter():
                    if return_head.tag == 'item_details':
                        line_id = uuid.uuid4()
                        line_data.update({'ReturnLineId': line_id})
                        line_data.update({'ReturnHeadId': new_order_head})
                        for item_details in return_head:
                            line_data.update({item_details.tag: item_details.text})
                        # print(line_data)
                        if is_order_exists is False:
                            session.insert_return_line(line_data)
                    elif return_head.tag in ReturnHeadKey:
                        head_data.update(({return_head.tag: return_head.text}))
                    else:
                        continue
                # print(head_data)
                if is_order_exists is False:
                    head_data.update({'AmiStatus': 0})
                    head_data.update({'StoreId': self.store_id})
                    head_data.update({'PluginCreateTime': self.get_local_timestamp()})
                    head_data.update({'PluginUpdateTime': self.get_local_timestamp()})
                    session.insert_return_head(head_data)
                else:
                    del head_data['ReturnHeadId']
                    head_data.update({'AmiStatus': 0})
                    head_data['PluginUpdateTime'] = self.get_local_timestamp()
                    session.update_return_head(head_data, order_id)

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
                elif element.text == '_DONE_NO_DATA_':
                    print('No data, exit')
                    exit(0)
                elif element.text == '_CANCELLED_':
                    print('Date too far, please enter a date within 60 days')
                    exit(0)
                else:
                    print('Report Not Ready, wait for 10 seconds')
                    time.sleep(10)
                    return False
            elif element.tag.replace('{http://mws.amazonaws.com/doc/2009-01-01/}', '') == 'Error':
                print('Report Not Ready, wait for 10 seconds')
                time.sleep(10)
                return False

def get_start_time(input_start_time=None, db_start_time=None):
    # if the start time is provided, it need to be transfer into datetime format
    if input_start_time is not None:
        given_time = StringToDate.strptime(input_start_time, '%Y-%m-%d %H:%M:%S')
    else:
        given_time = db_start_time
    gmt_start_time = given_time - datetime.timedelta(1 / 3)
    return gmt_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def AzReturn(store_id, start_time, job_id):
    db_session = db_func.DataBase(store_id)

    AWSAccessKeyId, MWSAuthToken, MarketplaceId, SellerId, SecretKey, Domain = db_session.get_store(store_id)
    Return = GetReturn(AWSAccessKeyId, MWSAuthToken, MarketplaceId,
                    SellerId, SecretKey, '2009-01-01', Domain, start_time, store_id)
    ReportData = Return.request_report()
    Return.return_head_to_dic(ReportData, db_session)
    db_session.session_commit()

    return_head_id_table = db_session.select_return_head()
    is_updated = db_session.is_updated(return_head_id_table)
    cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, store_no, store_name = db_session.ordersync_store_cloud(store_id)
    ifs = rtn_order_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                                   return_head_id_table, job_id, store_id, store_no, store_name,
                                   db_session.rtn_order_sync_route)
    while is_updated is False:
        ifs.synchronization()
        return_head_id_table = db_session.select_return_head()
        ifs = rtn_order_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                                       return_head_id_table, job_id, store_id, store_no, store_name,
                                       db_session.rtn_order_sync_route)
        is_updated = db_session.is_updated(return_head_id_table)
        cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key, store_no, store_name = db_session.ordersync_store_cloud(store_id)


if __name__ == "__main__":
    # start_time = '2019-01-01 08:00:00'
    store_id, start_time, job_id = sys.argv[1], sys.argv[2], sys.argv[3]
    temp = get_start_time(input_start_time=start_time)
    AzReturn(store_id, temp, job_id)