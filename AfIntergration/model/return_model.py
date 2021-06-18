from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float, BigInteger, SmallInteger, DateTime, Integer, TIMESTAMP, NVARCHAR, VARCHAR

ReturnModel = declarative_base()


class ReturnHead(ReturnModel):
    __tablename__ = 'Af_return_head'
    ReturnHeadId = Column('Order_head_id', NVARCHAR(128), primary_key=True)

class ReturnLine(ReturnModel):
    __tablename__ = 'Af_return_line'
    ReturnLineId = Column('Order_line_id', NVARCHAR(128), primary_key=True)

