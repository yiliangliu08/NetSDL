from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float, BigInteger, SmallInteger, DateTime, Integer, TIMESTAMP, NVARCHAR, VARCHAR

ReturnModel = declarative_base()


class ReturnHead(ReturnModel):
    __tablename__ = 'Az_return_head'
    ReturnHeadId = Column('Order_head_id', NVARCHAR(128), primary_key=True)
    order_id = Column('order_id', NVARCHAR(32), default='')
    order_date = Column('order_date', VARCHAR(64), default='')
    merchant_rma_id = Column('merchant_rma_id', VARCHAR(16), default='')
    amazon_rma_id = Column('amazon_rma_id', VARCHAR(16), default='')
    return_request_date = Column('return_request_date', NVARCHAR(64), default='')
    return_request_status = Column('return_request_status', VARCHAR(16), default='')
    a_to_z_claim = Column('a_to_z_claim', VARCHAR(16), default='')
    is_prime = Column('is_prime', VARCHAR(16), default='')
    tracking_id = Column('tracking_id', NVARCHAR(64), default='')
    return_carrier = Column('return_carrier', NVARCHAR(32), default='')
    currency_code = Column('currency_code', NVARCHAR(16), default='')
    label_cost = Column('label_cost', Float, default=0.0)
    label_type = Column('label_type', VARCHAR(32), default='')
    label_to_be_paid_by = Column('label_to_be_paid_by', VARCHAR(32), default='')
    return_type = Column('return_type', NVARCHAR(32), default='')
    order_amount = Column('order_amount', Float, default=0.0)
    order_quantity = Column('order_quantity', Integer, default=0)
    # Only used for creating table
    # Stamp = Column('Stamp', TIMESTAMP)
    StoreId = Column('Store_id', BigInteger, default=0)
    UpdateStatus = Column('Update_status', SmallInteger, default=10)
    AmiStatus = Column('Ami_status', Integer, default=0)
    PluginCreateTime = Column('Plugin_create_time', DateTime, default='')
    PluginUpdateTime = Column('Plugin_update_time', DateTime, default='')


class ReturnLine(ReturnModel):
    __tablename__ = 'Az_return_line'
    ReturnLineId = Column('Order_line_id', NVARCHAR(128), primary_key=True)
    ReturnHeadId = Column('Order_head_id', NVARCHAR(128), default='')
    item_name = Column('item_name', NVARCHAR(128), default='')
    asin = Column('asin', VARCHAR(64), default='')
    return_reason_code = Column('return_reason_code', NVARCHAR(32), default='')
    merchant_sku = Column('merchant_sku', NVARCHAR(32), default='')
    in_policy = Column('in_policy', VARCHAR(16), default='')
    return_quantity = Column('return_quantity', Integer, default=0)
    resolution = Column('resolution', VARCHAR(32), default='')
    refund_amount = Column('refund_amount', Float, default=0.0)
