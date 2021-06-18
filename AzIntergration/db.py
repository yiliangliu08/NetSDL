import re
import amiconn
import time
import datetime
import traceback
import warnings
from path import Path
from configparser import ConfigParser

from model import order_model
from model.order_model import *
from model import mng_model
from model.mng_model import *
from model import log_model
from model.log_model import *
from model import return_model
from model.return_model import *
from model import item_model
from model.item_model import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy import *
from sqlalchemy import exc as sa_exc

path = ''

Head = order_model.OrderHead
Line = order_model.OrderLine

ReturnHead = return_model.ReturnHead
ReturnLine = return_model.ReturnLine

Item = item_model.Item

Store = mng_model.Store
Job = mng_model.Job
StoreDefine = mng_model.StoreCloud

Log = log_model

counter = 0

CONFIG_FILE = 'app.cfg'
QUERY_STATUS = 10
DONE_STATUS = 20


class DataBase(object):
    def __init__(self):
        p = Path(__file__)
        confPath = Path.joinpath(p.dirname(), CONFIG_FILE)

        if Path.exists(confPath):
            self.removeBom(confPath)
            self.config = ConfigParser()
            self.config.read(confPath)

            global path
            path = self.set_current_path(self.config)
            self.update_limit = self.config.get('gen', 'REQUEST_LIMIT')
            self.order_session = self.create_session('CJS_DATA_CONN_HANDLE')
            self.mng_session = self.create_session('CJS_MNG_CONN_HANDLE')
            self.log_session = self.create_session('CJS_LOG_CONN_HANDLE')

        # self.session = self.create_session(host, port, database, username, password)

    def removeBom(self, cfg_path):
        content = open(cfg_path).read()
        content = re.sub(r'\xfe\xff', '', content)
        content = re.sub(r'\xff\xfe', '', content)
        content = re.sub(r'\xef\xbb\xbf', '', content)
        open(cfg_path, 'w').write(content)

    def create_session(self, handle):
        connection = amiconn.GetMsSqlConnStringByConnName(self.config.get('db', handle), self.config.get('db', 'SQL_CLIENT'))
        engine = create_engine(connection)
        if handle == 'CJS_DATA_CONN_HANDLE':
            self.create_table(engine)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return Session()

    def is_product_exists(self, seller_sku):
        try:
            repeat = self.order_session.query(Item).filter(Item.seller_sku == seller_sku).count()
        except sa_exc as err:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in checking if AmazonOrderId exists, OrderId ', seller_sku)
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            repeat = self.order_session.query(Item).filter(Item.seller_sku == seller_sku).count()
        if repeat != 0:
            return True
        else:
            return False

    def create_table(self, eng):
        OrderModel.metadata.create_all(eng)
        ReturnModel.metadata.create_all(eng)
        ItemModel.metadata.create_all(eng)

    def get_store(self, store_id):
        try:
            query = self.mng_session.query(Store).filter(Store.StoreId == store_id)
        except sa_exc as err:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in getting store id ', store_id)
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            query = self.mng_session.query(Store).filter(Store.StoreId == store_id)
        for i in query:
            AWSAccessKeyId = i.ApiKey
            MWSAuthToken = ''
            MarketplaceId = i.ApiMarketId
            SellerId = i.ApiStoreId
            SecretKey = i.ApiSecret
            Domain = i.ApiUrl
            break
        return AWSAccessKeyId, MWSAuthToken, MarketplaceId, SellerId, SecretKey, Domain

    def last_to_start(self, job_id):
        try:
            query = self.mng_session.query(Job.LastTime).filter(Job.ScheduleId == job_id)
        except sa_exc as err:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in getting LastTime from JobSchedule, job_id ', job_id)
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            query = self.mng_session.query(Job.LastTime).filter(Job.ScheduleId == job_id)
        for i in query:
            start_time = i.LastTime
            break
        return start_time

    def set_job(self, job_id, EndTime):
        my_job = self.mng_session.query(Job).filter(Job.ScheduleId == job_id).update({Job.LastTime: EndTime})
        self.session_commit()

    def insert_order_line(self, data):
        self.order_session.add(Line(**data))
        # for qr in session.query(Head):
        #     print(qr)

    def insert_order_head(self, data):
        self.order_session.add(Head(**data))
        # for qr in session.query(Head):
        #     print(qr)

    def insert_return_line(self, data):
        self.order_session.add(ReturnLine(**data))
        # for qr in session.query(Head):
        #     print(qr)

    def insert_return_head(self, data):
        self.order_session.add(ReturnHead(**data))
        # for qr in session.query(Head):
        #     print(qr)

    def insert_item(self, data):
        self.order_session.add(Item(**data))
        # for qr in session.query(Head):
        #     print(qr)

    def update_item(self, data, seller_sku):
        for key, value in data.items():
            self.order_session.query(Item).filter(Item.seller_sku == seller_sku).update({key: value})

    def ordersync_store_cloud(self, store_id):
        try:
            query = self.mng_session.query(StoreDefine).filter(StoreDefine.StoreId == store_id)
        except sa_exc as err:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in getting store cloud, store_id ', store_id)
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            query = self.mng_session.query(StoreDefine).filter(StoreDefine.StoreId == store_id)
        for i in query:
            Id = i.Id
            CloudSecret = i.CloudSecret
            CloudToken = i.CloudToken
            CloudURL = i.CloudURL
            CloudKey = i.CloudKey
            StoreNo = i.StoreNo
            StoreName = i.StoreName
            break
        return Id, CloudSecret, CloudToken, CloudURL, CloudKey, StoreNo, StoreName

    def select_order_head(self):
        try:
            temp = self.order_session.query(Head.OrderHeadId.label('OrderHeadId'))\
                .filter(Head.UpdateStatus == 10)\
                .limit(self.update_limit)\
                .subquery()
        except sa_exc as err:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in retrieving OrderHeadId')
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            temp = self.order_session.query(Head.OrderHeadId.label("OrderHeadId")) \
                .filter(Head.UpdateStatus == 10) \
                .limit(self.update_limit) \
                .subquery()
        return temp

    def is_updated(self, temp):
        try:
            query = self.order_session.query(temp).count()
        except sa_exc as err:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in checking if all order is updated to 10')
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            query = self.order_session.query(temp).count()
        if query != 0:
            print('Retrieving another batch of orders')
            return False
        else:
            print('All orders have been updated')
            return True

    def update_order_status(self, temp):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)
            try:
                query = self.order_session.query(Head)\
                    .filter(Head.OrderHeadId == temp.c.OrderHeadId).\
                    update({Head.UpdateStatus: 20,
                            Head.PluginUpdateTime: self.get_time()})
            except sa_exc as err:
                self.output_to_log(self.get_log_time())
                self.output_to_log('Error in updating status to 20')
                traceback.print_exc(file=open(path, 'a'))
                print('Connection Error, retry in 30 seconds')
                time.sleep(30)
                query = self.order_session.query(Head)\
                    .filter(Head.OrderHeadId == temp.c.OrderHeadId).\
                    update({Head.UpdateStatus: 20,
                            Head.PluginUpdateTime: self.get_time()})
        self.session_commit()
        self.order_session.close()

    def update_return_status(self, temp):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)
            try:
                query = self.order_session.query(ReturnHead)\
                    .filter(ReturnHead.ReturnHeadId == temp.c.ReturnHeadId).\
                    update({ReturnHead.UpdateStatus: 20,
                            ReturnHead.PluginUpdateTime: self.get_time()})
            except sa_exc as err:
                self.output_to_log(self.get_log_time())
                self.output_to_log('Error in updating status to 20')
                traceback.print_exc(file=open(path, 'a'))
                print('Connection Error, retry in 30 seconds')
                time.sleep(30)
                query = self.order_session.query(ReturnHead) \
                    .filter(ReturnHead.ReturnHeadId == temp.c.ReturnHeadId). \
                    update({ReturnHead.UpdateStatus: 20,
                            ReturnHead.PluginUpdateTime: self.get_time()})
        self.session_commit()
        self.order_session.close()

    def select_return_head(self):
        try:
            temp = self.order_session.query(ReturnHead.ReturnHeadId.label("ReturnHeadId")) \
                .filter(ReturnHead.UpdateStatus == 10) \
                .limit(self.update_limit) \
                .subquery()
        except sa_exc as err:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in retrieving OrderHeadId')
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            temp = self.order_session.query(ReturnHead.ReturnHeadId.label("ReturnHeadId")) \
                .filter(ReturnHead.UpdateStatus == 10) \
                .limit(self.update_limit) \
                .subquery()
        result = self.order_session.query(temp.c.ReturnHeadId).all()
        for i in result:
            print(i)
        return temp

    def insert_log(self, schedule_id, store_id, store_cloud_id, request_content, response_content,
                   is_error, request_time, duration):
        response_content_decoded = response_content.decode(encoding='utf-8')
        time_in_millisecond = int(duration.seconds*1000)+int(duration.microseconds/1000)
        # print(time_in_millisecond)
        new_log = log_model.Log(ScheduleId=schedule_id, StoreId=store_id, StoreCloudId=store_cloud_id,
                                RequestContent=request_content, ResponseContent=response_content_decoded,
                                IsError=is_error, RequestTime=request_time,
                                Duration=time_in_millisecond, CreateTime=self.get_time())
        self.log_session.add(new_log)
        self.log_session.commit()

    def get_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', local_time)

    def get_log_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime("%Y-%m-%d %H:%M:%S", local_time)

    def session_commit(self):
        global counter
        try:
            self.order_session.commit()
            self.log_session.commit()
            self.mng_session.commit()
        except sa_exc as err:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in committing change to database')
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.order_session.commit()
            self.log_session.commit()
            self.mng_session.commit()

    def set_current_path(self, config):
        current_path = config.get('log', 'LOG_PATH')
        return current_path

    def output_to_log(self, content):
        file = open(path, 'a')
        file.write(content)
        file.write('\n')
        file.close()
