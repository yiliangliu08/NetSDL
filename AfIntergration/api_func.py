import requests
import json

from urllib.parse import quote, unquote


class Afound(object):
    def __init__(self, shop_key, shop_url):
        self.shop_key = shop_key
        self.shop_url = shop_url

    def list_orders(self, limit=None, order_id=None, order_state_codes=None,
                    date_created_start=None, date_created_end=None,
                    date_updated_start=None, date_updated_end=None):
        data = dict(max=str(limit),
                    order_id=order_id,
                    order_state_codes=order_state_codes,
                    date_created_start=date_created_start,
                    date_created_end=date_created_end,
                    date_updated_start=date_updated_start,
                    date_updated_end=date_updated_end
        )
        return self.make_request(api='orders', data=data)

    def list_next_orders(self, next_url):
        return self.make_request(next_url=next_url)

    def update_carrier_tracking(self, order_id, carrier_code=None, carrier_name=None, tracking_number=None):
        data = dict(carrier_code=carrier_code,
                    carrier_name=carrier_name,
                    tracking_number=tracking_number)
        order_info = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        return self.make_request_with_body('orders/{order_id}/tracking'.format(order_id=order_id), body=order_info)

    def validate_the_shipment(self, order_id):
        return self.make_request('orders/{order_id}/ship'.format(order_id=order_id))

    def accept_or_refuse(self, order_id, pending_order_id):
        order_lines = []
        for order_line_id in pending_order_id:
            order_line = {'accepted': 'true', 'id': order_line_id}
            order_lines.append(order_line)
        body = {}
        body['order_lines'] = order_lines
        order_info = json.dumps(body, ensure_ascii=False, separators=(',', ':'))
        print(order_info)
        return self.make_request_with_body('orders/{order_id}/accept'.format(order_id=order_id), body=order_info)

    def make_request(self, api=None, data=None, body=None, next_url=None):
        request_description = ''
        if data is not None:
            for key in sorted(data):
                if data[key] != '' and data[key] is not None:
                    encoded_value = quote(data[key], safe='-_.~')
                    request_description += '&{}={}'.format(key, encoded_value)

            temp = '?'+request_description[1:]
            request_description = temp
        if next_url is None:
            url = '{shop_url}/api/{api}{description}'.format(
                shop_url=self.shop_url,
                api=api,
                description=request_description
            )
        else:
            url = next_url
        headers = {
            'Accept': 'application/xml',
            'Authorization': self.shop_key
        }
        response = requests.get(url, data=body, headers=headers)
        # print(response.headers.get('Link'))
        return response.content, response.headers.get('link')

    def make_request_with_body(self, api, body=None):
        url = '{shop_url}/api/{api}'.format(
            shop_url=self.shop_url,
            api=api,
        )
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': self.shop_key
        }
        print(url)
        response = requests.put(url, data=body, headers=headers)
        print(response.content)
        return response.content
