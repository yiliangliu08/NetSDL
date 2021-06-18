import re
import amiconn
import time
import datetime
import traceback
from time import strftime
import warnings
from path import Path
from configparser import ConfigParser

from model import mng_model
from model.mng_model import *
from model import return_model
from model.return_model import *
from model import log_model
from model.log_model import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy import *
from sqlalchemy import exc as sa_exc

path = ''
ReturnHead = return_model.SfReturnHead
ReturnLine = return_model.SfReturnLine
StoreDefine = mng_model.StoreCloud
Log = log_model

CONFIG_FILE = 'app.cfg'
QUERY_STATUS = 10
DONE_STATUS = 20

Store = mng_model.Store


class DataBase:
    def __init__(self):
        p = Path(__file__)
        confPath = Path.joinpath(p.dirname(), CONFIG_FILE)

        if Path.exists(confPath):
            self.removeBom(confPath)
            self.config = ConfigParser()
            self.config.read(confPath)

            # self.copy_cd = self.config.get('gen', 'COPY_CD')
            # self.count = int(self.config.get('gen', 'COUNT'))
            # self.type = self.config.get('gen', 'TYPE')
            # self.sp = self.config.get('gen', 'SP_NAME')

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
        print(connection)
        engine = create_engine(connection)
        if handle == 'CJS_DATA_CONN_HANDLE':
            self.create_table(engine)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return Session()

    def create_table(self, eng):
        ReturnModel.metadata.create_all(eng)

    def ordersync_store_cloud(self, store_id):
        try:
            query = self.mng_session.query(StoreDefine).filter(StoreDefine.StoreId == store_id)
        except sa_exc.SQLAlchemyError:
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
            break
        return Id, CloudSecret, CloudToken, CloudURL, CloudKey

    def get_store(self, store_domain):
        try:
            query = self.mng_session.query(Store).filter(Store.StoreDomain == store_domain)
        except sa_exc.SQLAlchemyError:
            self.output_to_log(self.get_log_time())
            query = self.mng_session.query(Store).filter(Store.StoreDomain == store_domain)
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            query = self.mng_session.query(Store).filter(Store.StoreDomain == store_domain)
        for i in query:
            store_id = i.StoreId
            username = i.ApiKey
            password = i.ApiToken
            url = i.ApiUrl
            break
        return store_id, username, password, url

    def is_order_exists(self, return_id):
        try:
            repeat = self.order_session.query(ReturnHead).filter(ReturnHead.id == return_id).scalar()
        except sa_exc.SQLAlchemyError:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in checking if AmazonOrderId exists, OrderId ', id)
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            repeat = self.order_session.query(ReturnHead).filter(ReturnHead.id == id).scalar()
        if repeat is not None:
            return True
        else:
            return False

    def insert_return_head(self, data):
        self.order_session.add(ReturnHead(**data))

    def update_return_head(self, data):
        for key, value in data.items():
            self.order_session.query(ReturnHead).filter(ReturnHead.id == data['id']).update({key: value})

    def insert_return_line(self, data):
        self.order_session.add(ReturnLine(**data))

    def is_updated(self, temp):
        try:
            query = self.order_session.query(temp).count()
        except sa_exc.SQLAlchemyError:
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

    def select_return_head(self):
        try:
            temp = self.order_session.query(ReturnHead.ReturnHeadId.label("ReturnHeadId")) \
                .filter(ReturnHead.UpdateStatus == 1) \
                .limit(self.update_limit) \
                .subquery()
        except sa_exc.SQLAlchemyError:
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

    def select_return_data(self, temp):
        result = self.order_session.query(
            ReturnHead.id, ReturnLine.id, ReturnLine.quantity,
            ReturnLine.subtotal, ReturnLine.total_tax, ReturnLine.line_item_title,
            ReturnLine.line_item_sku, ReturnLine.line_item_name, ReturnLine.line_item_fulfillment_status,
            ReturnHead.order_id,
            ReturnHead.created_at, ReturnHead.note,
        ) \
            .join(ReturnLine, ReturnLine.ReturnHeadId == ReturnHead.ReturnHeadId) \
            .join(temp, ReturnHead.ReturnHeadId == temp.c.ReturnHeadId) \
            .order_by(ReturnHead.ReturnHeadId) \
            .all()
        for i in result:
            print(i)
        return result

    def update_status(self, temp):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)
            try:
                query = self.order_session.query(ReturnHead)\
                    .filter(ReturnHead.ReturnHeadId == temp.c.ReturnHeadId).\
                    update({ReturnHead.UpdateStatus: 20,
                            ReturnHead.PluginUpdateTime: self.get_time()})
            except sa_exc.SQLAlchemyError:
                self.output_to_log(self.get_log_time())
                self.output_to_log('Error in updating status to 20')
                traceback.print_exc(file=open(path, 'a'))
                print('Connection Error, retry in 30 seconds')
                time.sleep(30)
                query = self.order_session.query(ReturnHead)\
                    .filter(ReturnHead.OrderHeadId == temp.c.OrderHeadId).\
                    update({ReturnHead.UpdateStatus: 20,
                            ReturnHead.PluginUpdateTime: self.get_time()})
        self.session_commit()
        self.order_session.close()

    def get_time(self):
        ct = time.time()
        local_time = time.localtime(ct)
        return time.strftime('%Y-%m-%dT%H:%M:%SZ', local_time)

    def session_commit(self):
        global counter
        try:
            self.order_session.commit()
            self.log_session.commit()
            self.mng_session.commit()
        except sa_exc.SQLAlchemyError:
            self.output_to_log(self.get_log_time())
            self.output_to_log('Error in committing change to database')
            traceback.print_exc(file=open(path, 'a'))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.order_session.commit()
            self.log_session.commit()
            self.mng_session.commit()

    def set_current_path(self, config):
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = date + '.txt'
        current_path = config.get('log', 'LOG_PATH')
        new_path = current_path + filename
        return new_path

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
