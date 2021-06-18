import re
import amiconn
import time
import datetime
import traceback
from time import strftime
import warnings
import logging
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
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
from model import mcf_model
from model.mcf_model import *

from sqlalchemy.orm import sessionmaker
from sqlalchemy import *
from sqlalchemy import exc as sa_exc

path = ''
counter = 0

Head = order_model.OrderHead
Line = order_model.OrderLine
Store = mng_model.Store
Job = mng_model.Job
Log = log_model
ReturnHead = return_model.ReturnHead
ReturnLine = return_model.ReturnLine
StoreDefine = mng_model.StoreCloud
Item = item_model.Item
MCFShipping = mcf_model.MCF

CONFIG_FILE = 'app.cfg'
QUERY_STATUS = 10
DONE_STATUS = 20


class DataBase:
    def __init__(self, store_id):
        p = Path(__file__)
        confPath = Path.joinpath(p.dirname(), CONFIG_FILE)
        if Path.exists(confPath):
            self.removeBom(confPath)
            self.config = ConfigParser()
            self.config.read(confPath)
            global path
            path = self.set_current_path(self.config, store_id)
            self.update_limit = self.config.get('gen', 'REQUEST_LIMIT')
            self.order_session = self.create_session('CJS_DATA_CONN_HANDLE')
            self.mng_session = self.create_session('CJS_MNG_CONN_HANDLE')
            self.log_session = self.create_session('CJS_LOG_CONN_HANDLE')
            self.order_sync_route = self.config.get('route', 'ORDER_API_ROUTE')
            self.rtn_order_sync_route = self.config.get('route', 'RTNORDER_API_ROUTE')
            self.product_sync_route = self.config.get('route', 'PRODUCT_API_ROUTE')
            self.mcf_session = self.create_session('CJS_MCF_CONN_HANDLE')
            logging.basicConfig(level=logging.DEBUG, filename=path,
                                format='%(asctime)s %(levelname)s %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
        # self.session = self.create_session(host, port, database, username, password)

    def removeBom(self, cfg_path):
        content = open(cfg_path).read()
        content = re.sub(r'\xfe\xff', '', content)
        content = re.sub(r'\xff\xfe', '', content)
        content = re.sub(r'\xef\xbb\xbf', '', content)
        open(cfg_path, 'w').write(content)

    def create_session(self, handle):
        connection = amiconn.GetMsSqlConnStringByConnName(self.config.get('db', handle),
                                                          self.config.get('db', 'SQL_CLIENT'))
        engine = create_engine(connection)
        if handle == 'CJS_DATA_CONN_HANDLE':
            self.create_table(engine)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        return Session()

    def is_product_exists(self, product_id):
        try:
            repeat = self.order_session.query(Item).filter(Item.product_id == product_id).count()
            # print(repeat)
            if repeat != 0:
                return True
            else:
                return False
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.is_product_exists(product_id)

    def create_table(self, eng):
        OrderModel.metadata.create_all(eng)
        ReturnModel.metadata.create_all(eng)
        ItemModel.metadata.create_all(eng)

    def get_store(self, store_id):
        try:
            query = self.mng_session.query(Store).filter(Store.StoreId == store_id)
            for i in query:
                AWSAccessKeyId = i.ApiKey
                MWSAuthToken = ''
                MarketplaceId = i.ApiMarketId
                SellerId = i.ApiStoreId
                SecretKey = i.ApiSecret
                Domain = i.ApiUrl
                return AWSAccessKeyId, MWSAuthToken, MarketplaceId, SellerId, SecretKey, Domain
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.get_store(store_id)

    def last_to_start(self, job_id):
        try:
            query = self.mng_session.query(Job.LastTime).filter(Job.ScheduleId == job_id)
            for i in query:
                start_time = i.LastTime
                return start_time
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.last_to_start(job_id)

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

    def update_item(self, data, product_id):
        self.order_session.query(Item).filter(Item.product_id == product_id).update(data)

    def ordersync_store_cloud(self, store_id):
        try:
            query = self.mng_session.query(StoreDefine).filter(StoreDefine.StoreId == store_id)
            for i in query:
                Id = i.Id
                CloudSecret = i.CloudSecret
                CloudToken = i.CloudToken
                CloudURL = i.CloudURL
                CloudKey = i.CloudKey
                StoreNo = i.StoreNo
                StoreName = i.StoreName
                return Id, CloudSecret, CloudToken, CloudURL, CloudKey, StoreNo, StoreName
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.ordersync_store_cloud(store_id)

    def select_order_head(self):
        try:
            temp = self.order_session.query(Head.OrderHeadId.label('OrderHeadId')) \
                .filter(Head.UpdateStatus == 10) \
                .limit(self.update_limit) \
                .subquery()
            return temp
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.select_order_head()

    def is_updated(self, temp):
        try:
            query = self.order_session.query(temp).count()
            if query != 0:
                print('Retrieving another batch of orders')
                return False
            else:
                print('All orders have been updated')
                return True
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.is_updated(temp)

    def update_order_status(self, temp):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)
            try:
                query = self.order_session.query(Head) \
                    .filter(Head.OrderHeadId == temp.c.OrderHeadId). \
                    update({Head.UpdateStatus: 20,
                            Head.PluginUpdateTime: self.get_time()})
            except sa_exc.DisconnectionError as err:
                logging.error('Connection to SQLServer lost: ' + str(err))
                print('Connection Error, retry in 30 seconds')
                time.sleep(30)
                self.recreate_session()
                self.update_order_status(temp)
        self.session_commit()
        self.order_session.close()

    def update_return_status(self, temp):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)
            try:
                query = self.order_session.query(ReturnHead) \
                    .filter(ReturnHead.ReturnHeadId == temp.c.ReturnHeadId). \
                    update({ReturnHead.UpdateStatus: 20,
                            ReturnHead.PluginUpdateTime: self.get_time()})
            except sa_exc.DisconnectionError as err:
                logging.error('Connection to SQLServer lost: ' + str(err))
                print('Connection Error, retry in 30 seconds')
                time.sleep(30)
                self.recreate_session()
                self.update_return_status(temp)
        self.session_commit()
        self.order_session.close()

    def select_return_head(self):
        try:
            temp = self.order_session.query(ReturnHead.ReturnHeadId.label("ReturnHeadId")) \
                .filter(ReturnHead.UpdateStatus == 10) \
                .limit(self.update_limit) \
                .subquery()
            result = self.order_session.query(temp.c.ReturnHeadId).all()
            for i in result:
                print(i)
            return temp
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.select_return_head()

    def insert_log(self, schedule_id, store_id, store_cloud_id, request_content, response_content,
                   is_error, request_time, duration):
        response_content_decoded = response_content.decode(encoding='utf-8')
        time_in_millisecond = int(duration.seconds * 1000) + int(duration.microseconds / 1000)
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
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            self.session_commit()

    def set_current_path(self, config, store_id):
        global path
        current_path = config.get('log', 'LOG_PATH')
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = date + '.txt'
        path = current_path + '\\' + str(store_id) + '\\' + filename
        print(path)
        return path

    def output_to_log(self, content):
        file = open(path, 'a')
        file.write(content)
        file.write('\n')
        file.close()

    def is_order_exists(self, order_id):
        try:
            repeat = self.order_session.query(Head).filter(Head.AmazonOrderId == order_id).scalar()
            if repeat is not None:
                return True
            else:
                return False
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.is_order_exists(order_id)

    def is_return_exists(self, order_id):
        try:
            repeat = self.order_session.query(ReturnHead).filter(ReturnHead.order_id == order_id).count()
            if repeat != 0:
                return True
            else:
                return False
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.is_return_exists(order_id)

    def is_seller_sku_exist(self, seller_sku):
        print(seller_sku)
        try:
            repeat = self.order_session.query(Item).filter(Item.seller_sku == seller_sku, Item.status == 'Active').scalar()
            if repeat is not None:
                return True
            else:
                return False
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.is_asin_exists(seller_sku)

    def update_order_head(self, data, order_id):
        # order_head = self.order_session.query(Head).filter(Head.AmazonOrderId == order_id).first()
        self.order_session.query(Head).filter(Head.AmazonOrderId == order_id).update(data)


    def update_return_head(self, data, order_id):
        # order_head = self.order_session.query(Head).filter(Head.AmazonOrderId == order_id).first()
        self.order_session.query(ReturnHead).filter(ReturnHead.order_id == order_id).update(data)

    def update_item_quantity(self, data, seller_sku):
        self.order_session.query(Item).filter(Item.seller_sku == seller_sku, Item.status == 'Active').update(data)

    def select_order_data(self, temp):
        try:
            result = self.order_session.query(
                Head.AmazonOrderId,
                Line.OrderLineId, Line.SellerSKU, Line.Title, Line.QuantityOrdered,
                Line.ItemTaxAmount, Line.ShippingTaxAmount, Line.GiftWrapTaxAmount,
                Line.ShippingDiscountTaxAmount, Line.PromotionDiscountTaxAmount,
                Line.ItemPriceAmount, Line.PromotionDiscountAmount, Head.OrderStatus,
                Head.ShipServiceLevel, Head.Name, Head.AddressLine1, Head.AddressLine2, Head.AddressLine3,
                Head.City, Head.StateOrRegion, Head.PostalCode,
                Head.PurchaseDate, Head.OrderStatus, Head.FulfillmentChannel,
                Head.BuyerName, Head.BuyerEmail, Head.Phone, Head.Amount)\
                .join(Line, Head.OrderHeadId == Line.OrderHeadId)\
                .join(temp, Head.OrderHeadId == temp.c.OrderHeadId)\
                .order_by(Head.OrderHeadId)\
                .all()
            return result
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.select_order_data(temp)
        # for i in result:
        #     print(i)

    def select_return_data(self, temp):
        result = self.order_session.query(
            ReturnHead.amazon_rma_id, ReturnLine.ReturnLineId, ReturnLine.item_name,
            ReturnLine.merchant_sku, ReturnLine.return_quantity, ReturnHead.currency_code ,
            ReturnLine.refund_amount, ReturnHead.return_request_status, ReturnHead.return_carrier, ReturnHead.tracking_id,
            ReturnHead.order_id, ReturnHead.return_request_date,
            ReturnHead.return_request_status, ReturnHead.order_amount
            ) \
            .join(ReturnLine, ReturnLine.ReturnHeadId == ReturnHead.ReturnHeadId) \
            .join(temp, ReturnHead.ReturnHeadId == temp.c.ReturnHeadId) \
            .order_by(ReturnHead.ReturnHeadId) \
            .all()
        for i in result:
            print(i)
        return result

    def select_mcf_data(self):
        temp = self.mcf_session.query(MCFShipping.Scan_job_id) \
                .filter(MCFShipping.If_status == 1) \
                .first()
        if temp is not None:
            i = temp.Scan_job_id
            # i = '1B1C4BB8-FBA7-4CA7-85BF-AA5D0124049B'
            result = self.mcf_session.query(
                MCFShipping.Scan_job_no, MCFShipping.Scan_job_no, MCFShipping.Sj_create_time, MCFShipping.Remark,
                MCFShipping.Ship_to_name, MCFShipping.Ship_to_name_1,
                MCFShipping.Ship_to_add_1, MCFShipping.Ship_to_add_2, MCFShipping.Ship_to_add_3,
                MCFShipping.Ship_to_city,
                MCFShipping.Ship_to_province, MCFShipping.Ship_to_country, MCFShipping.Ship_to_zip,
                MCFShipping.Ship_to_mobile,
                MCFShipping.Sku_cd, MCFShipping.Sku_id, MCFShipping.Req_qty
                )\
                .filter(MCFShipping.Scan_job_id == i) \
                .order_by(MCFShipping.Order_head_id) \
                .all()
            print(result)
            return result, i
        else:
            return None, None

    def select_order_data_to_mcf(self):
        result = self.order_session.query(
            Head.OrderHeadId, Head.SellerOrderId, Head.AmazonOrderId,
            Head.Name, Head.AddressLine1, Head.AddressLine2, Head.AddressLine3,
            Head.City, Head.StateOrRegion, Head.CountryCode, Head.PostalCode, Head.Phone, Line.OrderItemId,
            Line.SellerSKU, Line.QuantityOrdered
            )\
            .join(Line, Head.OrderHeadId == Line.OrderHeadId)\
            .all()
        return result

    def insert_mcf_data(self, data):
        self.mcf_session.add(MCFShipping(**data))
        self.mcf_session.commit()

    def update_mcf_status(self, order_head_id, order_status):
        query = self.mcf_session.query(MCFShipping)\
            .filter(MCFShipping.Scan_job_id == order_head_id)\
            .update({MCFShipping.If_status: order_status,
                     MCFShipping.Operate_time: self.get_log_time()})
        self.mcf_session.commit()

    def recreate_session(self):
        global counter
        p = Path(__file__)
        confPath = Path.joinpath(p.dirname(), CONFIG_FILE)
        if Path.exists(confPath):
            self.removeBom(confPath)
            self.config = ConfigParser()
            self.config.read(confPath)
            try:
                self.order_session = self.create_session('CJS_DATA_CONN_HANDLE')
                self.mng_session = self.create_session('CJS_MNG_CONN_HANDLE')
                self.log_session = self.create_session('CJS_LOG_CONN_HANDLE')
                self.mcf_session = self.create_session('CJS_MCF_CONN_HANDLE')
            except sa_exc.DisconnectionError as err:
                if counter == 3:
                    logging.error('Connection retry limit reached, abort: ' + str(err))
                    exit(0)
                else:
                    counter += 1
                    logging.exception('Retry connection: ' + str(err) + ' Attempt ' + str(counter))
                    self.recreate_session()
        counter = 0
        return

    def select_item(self):
        try:
            temp = self.order_session.query(Item.AzItemId.label('AzItemId')) \
                .filter(Item.UpdateStatus == 10) \
                .limit(self.update_limit) \
                .subquery()
            return temp
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.select_return()

    def select_item_data(self, temp):
        try:
            result = self.order_session.query(
                Item.product_id, Item.item_name, Item.price,
                Item.quantity, Item.status, Item.open_date)\
                .join(temp, Item.AzItemId == temp.c.AzItemId)\
                .order_by(Item.AzItemId)\
                .all()
            return result
        except sa_exc.DisconnectionError as err:
            logging.error('Connection to SQLServer lost: ' + str(err))
            print('Connection Error, retry in 30 seconds')
            time.sleep(30)
            self.recreate_session()
            return self.select_item_data(temp)
        # for i in result:
        #     print(i)

    def update_item_status(self, temp):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=sa_exc.SAWarning)
            try:
                query = self.order_session.query(Item) \
                    .filter(Item.AzItemId == temp.c.AzItemId). \
                    update({Item.UpdateStatus: 20,
                            Item.PluginUpdateTime: self.get_time()})
            except sa_exc.DisconnectionError as err:
                logging.error('Connection to SQLServer lost: ' + str(err))
                print('Connection Error, retry in 30 seconds')
                time.sleep(30)
                self.recreate_session()
                self.update_return_status(temp)
        self.session_commit()
        self.order_session.close()
