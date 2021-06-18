import sync
import db_func
import json
import uuid
import traceback

CONFIG_FILE = 'app.cfg'

api_keys = [
    'Scan_job_id',
    'Scan_job_no',
    'Orig_order_no',

    'Ship_to_name',
    'Ship_to_add_1',
    'Ship_to_add_2',
    'Ship_to_add_3',
    'Ship_to_city',
    'Ship_to_province',
    'Ship_to_country',
    'Ship_to_zip',
    # 'Ship_to_name_1',
    # 'Ship_to_name_2',
    'Ship_to_mobile',

    'Sku_id',
    'Sku_cd',
    'Req_qty'
]


def get_data(session):
    data = session.select_order_data_to_mcf()
    return data


def sort_order(session):
    data = get_data(session)
    counter = 1
    for element in data:
        mcf_data = {}
        for i, api_key in enumerate(api_keys):
            if api_key == 'Scan_job_id':
                mcf_data = {
                    'Scan_job_id': uuid.uuid4(),
                    'Order_head_id': uuid.uuid4(),
                    'Order_line_id': uuid.uuid4(),
                    'Ln_shipping_id': uuid.uuid4()
                }
            elif api_key == 'Sku_id':
                mcf_data.update({api_key: int(element[i])})
            else:
                mcf_data.update({api_key: element[i]})
        print(mcf_data)
        session.insert_mcf_data(mcf_data)
    session.session_commit()


if __name__ == "__main__":
    db_session = db_func.DataBase()
    sort_order(db_session)

