import requests
import json


class Shopify(object):
    def __init__(self, username, password, store):
        self.username = username
        self.password = password
        self.store = store.replace('https://', '')

    def get_specific_refund(self, order_id, refund_id):
        data = dict(order_id=order_id,
                    refund_id=refund_id)
        return self.make_request(api_data=data)

    def make_request(self, api_data=None):
        url = '{header}{username}:{password}@{store}/admin/api/{version}/orders/{order_number}/refunds/{refund_number}.json'\
            .format(
                header='https://',
                username=self.username,
                password=self.password,
                store=self.store,
                version='2019-04',
                order_number=api_data['order_id'],
                refund_number = api_data['refund_id']
            )
        print(url)
        response = requests.get(url)
        print(response.content)
        file = open('log.txt', 'a')
        file.write(str(response.content))
        file.write('\n')
        data = json.loads(response.content.decode(encoding='utf-8'))
        return data
