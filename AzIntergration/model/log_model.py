from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float, BigInteger, SmallInteger, DateTime, Integer, TIMESTAMP, NVARCHAR, VARCHAR

LogModel = declarative_base()


class Log(LogModel):
    __tablename__ = 'Cjs_api_log'
    Id = Column('Id', Integer, primary_key=True)
    ScheduleId = Column('Schedule_id', BigInteger)
    StoreId = Column('Store_id', BigInteger)
    StoreCloudId = Column('Store_cloud_id', BigInteger)
    RequestContent = Column('Request_content', NVARCHAR(max))
    ResponseContent = Column('Response_content', NVARCHAR(max))
    IsError = Column('IsError', SmallInteger)
    RequestTime = Column('Request_time', DateTime)
    Duration = Column('Duration', Integer)
    CreateTime = Column('Create_time', DateTime)
