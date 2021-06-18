import base64
import hashlib
import hmac
import db_func
import rtn_order_sync
import api_func

import json
import uuid
import time

from flask import Flask, request, abort

app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        data = request.get_data()
        shop = request.headers.get('X-Shopify-Shop-Domain')
        signature = request.headers.get('X-Shopify-Hmac-Sha256')
        if signature is None:
            print('No signature, source unknown, abort')
            return 'No signature, source unknown, abort', abort(400)
        temp = json.loads(data.decode(encoding='utf-8'))
        db_session = db_func.DataBase()
        store_id, username, password, url = db_session.get_store(shop)
        print(username, password, url)
        store_data(shop, signature, data)
        ids = get_ids(db_session, temp)
        data = get_refund_order(username, password, ids, url)
        sort_data(db_session, data, store_id)
        return_sync(db_session, store_id)
        return 'Order Inserted', 200
    else:
        return 'Nope', 400


# @app.route('/webhook')
# def webhook():
#     return 'success', 200

def verifier(signature, data, shared_secret):
    current_signature = base64.b64encode(hmac.new(shared_secret.encode(), data.encode, hashlib.sha256).digest())
    if current_signature != signature:
        return False
    else:
        return True


def recursive_iter(obj, keys=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from recursive_iter(v, keys + (k,))
    elif any(isinstance(obj, t) for t in (list, tuple)):
        for idx, item in enumerate(obj):
            yield from recursive_iter(item, keys + (idx,))
    else:
        yield keys, obj


def get_local_timestamp():
    # set timestamp in database as local time
    ct = time.time()
    local_time = time.localtime(ct)
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', local_time)

def return_sync(session, store_id):
    return_head_id_table = session.select_return_head()
    is_updated = session.is_updated(return_head_id_table)
    cloud_define_id, cloud_secret, cloud_token, cloud_url, cloud_key = session.ordersync_store_cloud(store_id)
    ifs = rtn_order_sync.OrderSync(session, cloud_define_id, cloud_secret,
                                   cloud_token, cloud_url,
                                   cloud_key, return_head_id_table, 0, store_id)
    while is_updated is False:
        ifs.synchronization()
        return_head_id_table = session.select_return_head()
        is_updated = session.is_updated(return_head_id_table)
        ifs = rtn_order_sync.OrderSync(session, cloud_define_id, cloud_secret,
                                       cloud_token, cloud_url,
                                       cloud_key, return_head_id_table, 0, store_id)

def store_data(shop, signature, data):
    file = open('log.txt', 'a')
    file.write(get_local_timestamp())
    file.write('\n')
    file.write(shop)
    file.write('\n')
    file.write(signature)
    file.write('\n')
    file.write(str(data))
    file.write('\n')
    file.close()

def get_ids(session, data):
    i = 0
    ids = {}
    for k, v in recursive_iter(data):
        if i < 2:
            ids.update({k[-1]: v})
            i += 1
        else:
            break
    print(ids)
    return ids


def get_refund_order(username, password, ids, url):
    api = api_func.Shopify(username, password, url)
    # print(ids)
    data = api.get_specific_refund(ids['order_id'], ids['id'])
    return data

def sort_data(session, data, store_id):
    i = 0
    j = 0
    last_item = 0
    head_data = {}
    line_data = {}
    order_head_id = uuid.uuid4()
    is_return_exists = False
    for k, v in recursive_iter(data):
        if i < 8:
            head_data.update({k[-1]: v})
            # print(k[-1], v)
            if i == 7:
                print(head_data)
                if session.is_order_exists(head_data['id']) is False:
                    head_data.update({'ReturnHeadId': order_head_id})
                    head_data.update({'AmiStatus': 0})
                    head_data.update({'StoreId': store_id})
                    head_data.update({'PluginCreateTime': get_local_timestamp()})
                    head_data.update({'PluginUpdateTime': get_local_timestamp()})
                else:
                    is_return_exists = True
                    print('Order exists, updating now')
                    session.update_return_head(head_data)
                    print('Update complete')
                    break
                # print('HEAD INSERTION')
            i += 1
        elif 'refund_line_items' in k:
            current_item = k[2]
            # if it is the same line
            if last_item != current_item:
                j = 0
                order_line_id = uuid.uuid4()
                line_data.update({'ReturnLineId': order_line_id})
                line_data.update({'ReturnHeadId': order_head_id})
                print(line_data)
                session.insert_return_line(line_data)
                # print('INSERTION COMPLETE')
                line_data = {}
            if 'tax_lines' in k and len(k) == 7:
                continue
            elif 'tax_lines' in k and len(k) == 8:
                continue
            elif 'tax_lines' in k and len(k) == 9:
                continue
            elif j <= 6:
                line_data.update(({k[-1]: v}))
                # print(k[-1], v)
                j += 1
            elif 'subtotal_set' in k or 'total_tax_set' in k:
                key = k[-3]+'_'+k[-2]+'_'+k[-1]
                line_data.update({key: v})
                # print(key, v)
            elif len(k) == 5:
                key = k[-2]+'_'+k[-1]
                line_data.update({key: v})
            elif 'price_set' in k or 'total_discount_set' in k:
                key = k[-4]+'_'+k[-3]+'_'+k[-2]+'_'+k[-1]
                line_data.update({key: v})
                # print(key, v)
            last_item = k[2]
    if is_return_exists is False:
        order_line_id = uuid.uuid4()
        line_data.update({'ReturnLineId': order_line_id})
        line_data.update({'ReturnHeadId': order_head_id})
        print(line_data)
        print(head_data)
        if len(line_data) == 2:
            head_data.update({'UpdateStatus': 20})
            print(head_data['UpdateStatus'])
        session.insert_return_line(line_data)
        session.insert_return_head(head_data)
        # print('INSERTION COMPLETE')

    session.session_commit()


if __name__ == '__main__':
    app.run('0.0.0.0', 9088)
    # app.run()
