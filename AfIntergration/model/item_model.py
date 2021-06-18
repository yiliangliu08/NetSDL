from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float, BigInteger, SmallInteger, DateTime, Integer, TIMESTAMP, NVARCHAR, VARCHAR

ItemModel = declarative_base()

class Item(ItemModel):
    __tablename__ = 'AfProduct'
    AfItemId = Column('Product_id', NVARCHAR(128), primary_key=True)
