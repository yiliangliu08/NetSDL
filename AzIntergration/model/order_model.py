from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Float, BigInteger, SmallInteger, DateTime, Integer, TIMESTAMP, NVARCHAR, VARCHAR

OrderModel = declarative_base()


class OrderHead(OrderModel):
    __tablename__ = 'Az_order_head'
    OrderHeadId = Column('Order_head_id', NVARCHAR(128), primary_key=True)
    AmazonOrderId = Column('AmazonOrderId', VARCHAR(32), default='', index=True)
    SellerOrderId = Column('SellerOrderId', NVARCHAR(64), default=0)
    PurchaseDate = Column('PurchaseDate', VARCHAR(64), default='')
    LastUpdateDate = Column('LastUpdateDate', VARCHAR(64), default='')
    OrderStatus = Column('OrderStatus', VARCHAR(32), default='')
    FulfillmentChannel = Column('FulfillmentChannel', VARCHAR(32), default='')
    SalesChannel = Column('SalesChannel', VARCHAR(32), default='')
    OrderChannel = Column('OrderChannel', VARCHAR(32), default='')
    ShipServiceLevel = Column('ShipServiceLevel', VARCHAR(32), default='')
    Name = Column('Name', NVARCHAR(64), default='')
    AddressLine1 = Column('AddressLine1', NVARCHAR(64), default='')
    AddressLine2 = Column('AddressLine2', NVARCHAR(64), default='')
    AddressLine3 = Column('AddressLine3', NVARCHAR(64), default='')
    City = Column('City', NVARCHAR(64), default='')
    StateOrRegion = Column('StateOrRegion', NVARCHAR(64), default='')
    PostalCode = Column('PostalCode', NVARCHAR(64), default='')
    CountryCode = Column('CountryCode', VARCHAR(32), default='')
    Phone = Column('Phone', NVARCHAR(64), default='')
    AddressType = Column('AddressType', NVARCHAR(32), default='')
    isAddressSharingConfidential = Column('isAddressSharingConfidential', VARCHAR(32), default='')
    CurrencyCode = Column('OrderTotalCurrencyCode', NVARCHAR(32), default='')
    Amount = Column('OrderTotalAmount', Float, default=0)
    NumberOfItemsShipped = Column('NumberOfItemsShipped', Integer, default=0)
    NumberOfItemsUnshipped = Column('NumberOfItemsUnshipped', Integer, default=0)
    PaymentMethod = Column('PaymentMethod', NVARCHAR(32), default='')
    # PaymentMethodDetail = Column('payment_method_details', NVARCHAR(32), default='')
    IsReplacementOrder = Column('IsReplacementOrder', VARCHAR(32), default='')
    ReplacedOrderId = Column('ReplacedOrderId', VARCHAR(32), default='')
    MarketplaceId = Column('MarketplaceId', VARCHAR(32), default='')
    BuyerEmail = Column('BuyerEmail', NVARCHAR(64), default='')
    BuyerName = Column('BuyerName', NVARCHAR(64), default='')
    CompanyLegalName = Column('CompanyLegalName', NVARCHAR(64), default='')
    TaxingRegion = Column('TaxingRegion', NVARCHAR(64), default='')
    ShipmentServiceLevelCategory = Column('ShipmentServiceLevelCategory', NVARCHAR(32), default='')
    ShippedByAmazonTFM = Column('ShippedByAmazonTFM', VARCHAR(32), default='')
    TFMShipmentStatus = Column('TFMShipmentStatus', VARCHAR(32), default='')
    EasyShipShipmentStatus = Column('EasyShipShipmentStatus', VARCHAR(32), default='')
    OrderType = Column('OrderType', NVARCHAR(32), default='')
    EarliestShipDate = Column('EarliestShipDate', VARCHAR(64), default='')
    LatestShipDate = Column('LatestShipDate', VARCHAR(64), default='')
    EarliestDeliveryDate = Column('EarliestDeliveryDate', VARCHAR(64), default='')
    LatestDeliveryDate = Column('LatestDeliveryDate', NVARCHAR(64), default='')
    IsBusinessOrder = Column('IsBusinessOrder', VARCHAR(32), default='')
    PurchaseOrderNumber = Column('PurchaseOrderNumber', VARCHAR(32), default='')
    IsPrime = Column('IsPrime', VARCHAR(32), default='')
    IsPremiumOrder = Column('IsPremiumOrder', VARCHAR(32), default='')
    PromiseResponseDueDate = Column('PromiseResponseDueDate', NVARCHAR(64), default='')
    IsEstimatedShipDateSet = Column('IsEstimatedShipDateSet', NVARCHAR(64), default='')
    # Only used for creating table
    # Stamp = Column('Stamp', TIMESTAMP)
    StoreId = Column('Store_id', BigInteger, default=0)
    UpdateStatus = Column('Update_status', SmallInteger, default=10, index=True)
    AmiStatus = Column('Ami_status', Integer, default=0)
    PluginCreateTime = Column('Plugin_create_time', DateTime, default='')
    PluginUpdateTime = Column('Plugin_update_time', DateTime, default='', index=True)

    def __repr__(self):
        return "<Order_Head(OrderHeadId='%s', AmazonOrderId='%s')>" % (self.OrderHeadId, self.AmazonOrderId)


class OrderLine(OrderModel):
    __tablename__ = 'Az_order_line'
    OrderLineId = Column('Order_line_id', NVARCHAR(128), primary_key=True)
    OrderHeadId = Column('Order_head_id', NVARCHAR(128))
    ASIN = Column('ASIN', VARCHAR(64), default='')
    OrderItemId = Column('OrderItemId', VARCHAR(64), default='')
    SellerSKU = Column('SellerSKU', VARCHAR(64), default='')
    Title = Column('Title', NVARCHAR(256), default='')
    QuantityOrdered = Column('QuantityOrdered', Integer, default=0)
    QuantityShipped = Column('QuantityShipped', Integer, default=0)
    NumberOfItems = Column('NumberOfItems', Integer, default=0)
    ItemPriceCurrencyCode = Column('ItemPriceCurrencyCode', NVARCHAR(32), default='')
    ItemPriceAmount = Column('ItemPriceAmount', Float, default=0)
    ShippingPriceCurrencyCode = Column('ShippingPriceCurrencyCode', NVARCHAR(32), default='')
    ShippingPriceAmount = Column('ShippingPriceAmount', Float, default=0)
    GiftWrapPriceCurrencyCode = Column('GiftWrapPriceCurrency', NVARCHAR(32), default='')
    GiftWrapPriceAmount = Column('GiftWrapPriceAmount', Float, default='')
    Model = Column('TaxCollectionModel', NVARCHAR(32), default='')
    ResponsibleParty = Column('TaxCollectionResponsibleParty', NVARCHAR(32), default='')
    ItemTaxCurrencyCode = Column('ItemTaxCurrencyCode', NVARCHAR(32), default='')
    ItemTaxAmount = Column('ItemTaxAmount', Float, default=0)
    ShippingTaxCurrencyCode = Column('ShippingTaxCurrencyCode', NVARCHAR(32), default='')
    ShippingTaxAmount = Column('ShippingTaxAmount', Float, default=0)
    GiftWrapTaxCurrencyCode = Column('GiftWrapTaxCurrencyCode', NVARCHAR(32), default='')
    GiftWrapTaxAmount = Column('GiftWrapTaxAmount', Float, default=0)
    PromotionDiscountCurrencyCode = Column('PromotionDiscountCurrencyCode', NVARCHAR(32), default='')
    PromotionDiscountAmount = Column('PromotionDiscountAmount', Float, default=0)
    ShippingDiscountTaxCurrencyCode = Column('ShippingDiscountTaxCurrencyCode', NVARCHAR(32), default='')
    ShippingDiscountTaxAmount = Column('ShippingDiscountTaxAmount', Float, default='')
    ShippingDiscountCurrencyCode = Column('ShippingDiscountCurrencyCode', NVARCHAR(32), default='')
    ShippingDiscountAmount = Column('ShippingDiscountAmount', Float, default=0)
    PromotionDiscountTaxCurrencyCode = Column('PromotionDiscountTaxCurrencyCode', NVARCHAR(32), default='')
    PromotionDiscountTaxAmount = Column('PromotionDiscountTaxAmount', Float, default=0)
    CODFeeCurrencyCode = Column('CODFeeCurrencyCode', NVARCHAR(32), default='')
    CODFeeAmount = Column('CODFeeAmount', Float, default=0)
    CODFeeDiscountCurrencyCode = Column('CODFeeDiscountCurrencyCode', NVARCHAR(32), default='')
    CODFeeDiscountAmount = Column('CODFeeDiscountAmount', Float, default=0)
    IsGift = Column('IsGift', VARCHAR(32), default='')
    GiftMessageText = Column('GiftMessageText', NVARCHAR(256), default='')
    GiftWrapLevel = Column('GiftWrapLevel', NVARCHAR(32), default='')
    ConditionNote = Column('ConditionNote', NVARCHAR(256), default='')
    ConditionSubtypeId = Column('ConditionSubtypeId', VARCHAR(32), default='')
    ConditionId = Column('ConditionId', VARCHAR(32), default='')
    ScheduleDeliveryStartDate = Column('ScheduleDeliveryStartDate', NVARCHAR(64), default='')
    ScheduleDeliveryEndDate = Column('ScheduleDeliveryEndDate', NVARCHAR(64), default='')
    PriceDesignation = Column('PriceDesignation', NVARCHAR, default='')
    IsTransparency = Column('IsTransparency', VARCHAR(32), default='')
    SerialNumberRequired = Column('SerialNumberRequired', VARCHAR(32), default='')
    AmazonOrderId = Column('AmazonOrderId', VARCHAR(32), default='')

    def __repr__(self):
        return "<Order_Head(OrderLineId='%s', AmazonOrderId='%s')>" % (self.OrderHeadId, self.AmazonOrderId)