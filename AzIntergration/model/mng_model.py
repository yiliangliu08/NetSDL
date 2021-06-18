from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, VARCHAR, BigInteger, DateTime

MngTable = declarative_base()


class Store(MngTable):
    __tablename__ = 'Store_define'
    StoreId = Column('Store_id', BigInteger, primary_key=True)
    ApiKey = Column('Api_key', VARCHAR(256))
    ApiSecret = Column('Api_secret', VARCHAR(256))
    ApiUrl = Column('Api_url', VARCHAR(256))
    ApiMarketId = Column('Api_market_id', VARCHAR(156))
    ApiStoreId = Column('Api_store_id', VARCHAR(128))


class Job(MngTable):
    __tablename__ = 'Job_schedule'
    ScheduleId = Column('Schedule_id', BigInteger, primary_key=True)
    LastTime = Column('Last_time', DateTime)


class StoreCloud(MngTable):
    __tablename__ = 'Store_cloud_define'
    Id = Column('Id', Integer, primary_key=True)
    StoreId = Column('Store_id', BigInteger)
    CloudSecret = Column('Cloud_secret', VARCHAR(256))
    CloudToken = Column('Cloud_token', VARCHAR(1024))
    CloudURL = Column('Cloud_url', VARCHAR(1024))
    CloudKey = Column('Cloud_key', VARCHAR(256))
    StoreNo = Column('Store_no', VARCHAR(64))
    StoreName = Column('Store_name', VARCHAR(64))




