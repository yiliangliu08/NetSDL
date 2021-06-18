import sys
import get_orders
import db_func
import time
import datetime
import order_sync
from datetime import datetime as StringToDate
from time import strftime

# used for testing
start_time = '2019-06-10 4:00:00'


def get_start_time(input_start_time=None, db_start_time=None):
    # if the start time is provided, it need to be transfer into datetime format
    if input_start_time is not None:
        given_time = StringToDate.strptime(input_start_time, '%Y-%m-%d %H:%M:%S')
    else:
        given_time = db_start_time
    gmt_start_time = given_time - datetime.timedelta(1/3)
    return gmt_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def AzOrders(store_id, start_time, job_id):
    db_session = db_func.DataBase()

    # Get time from Job_Schedule and turn it into gmt time
    # bjs_start_time = db_session.last_to_start(job_id)
    # gmt_start_time = get_start_time(db_start_time=bjs_start_time)

    # Get Store Info from Store_define
    AWSAccessKeyId, MWSAuthToken, MarketplaceId, SellerId, SecretKey, Domain = db_session.get_store(store_id)
    Order = get_orders.GetOrder(AWSAccessKeyId, MWSAuthToken, MarketplaceId,
                              SellerId, SecretKey, Domain, start_time, store_id)
    OrderData = Order.get_order_head()
    NextToken = Order.order_head_to_dic(OrderData, db_session)
    db_session.session_commit()
    print(NextToken)
    while True:
        # if NextToken is empty, that's the end of order, break and update the time in job schedule
        if NextToken == '':
            break

        # otherwise keep looping until there is no NextToken
        else:
            # Get another batch of order with NextToken, and retrieve a new NextToken
            OrderData = Order.get_order_by_next(NextToken)
            NextToken = Order.order_head_to_dic(OrderData, db_session)
            print('Batch Order Commited')
            db_session.session_commit()
            print    (NextToken)

    # Update the LastTime on Job Schedule
    db_session.set_job(job_id, get_orders.EndTime)
    print('LastTime = ', get_orders.EndTime)

    order_head_id_list = db_session.select_order_head()
    boo = db_session.is_updated(order_head_id_list)
    cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key = db_session.ordersync_store_cloud(store_id)
    ifs = order_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                               order_head_id_list, job_id, store_id)
    while boo is False:
        ifs.synchronization()
        order_head_id_list = db_session.select_order_head()
        ifs = order_sync.OrderSync(db_session, cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key,
                               order_head_id_list, job_id, store_id)
        boo = db_session.is_updated(order_head_id_list)


if __name__ == "__main__":
    # Using console start time
    # store_id, start_time, job_id = sys.argv[1], sys.argv[2], sys.argv[3]

    # Using db start time
    # store_id, job_id = sys.argv[1], sys.argv[2]
    # Turn BJS time to GMT Time
    temp = get_start_time(input_start_time=start_time)
    # print(temp)
    AzOrders(int(6000101), temp, 16)
    print('Done')
