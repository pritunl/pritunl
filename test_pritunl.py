import threading
import unittest
import requests
import json
import time
import os

URL = 'http://localhost:9700'
HEADERS = {
    'Content-type': 'application/json',
    'Accept': 'application/json',
}
USERNAME = 'admin'
PASSWORD = 'admin'

class Session:
    def __init__(self):
        data = {
            'username': USERNAME,
            'password': PASSWORD,
        }
        response = requests.post('%s/auth' % URL, headers=HEADERS,
            data=json.dumps(data))
        self.cookies = response.cookies

    def _json_request(self, method, endpoint, data=None):
        response = getattr(requests, method)('%s/%s' % (URL, endpoint),
            headers=HEADERS, cookies=self.cookies, data=data)
        return response.json()

    def get(self, endpoint):
        return self._json_request('get', endpoint)

    def post(self, endpoint, data={}):
        return self._json_request('post', endpoint, data=json.dumps(data))

    def put(self, endpoint, data={}):
        return self._json_request('put', endpoint, data=json.dumps(data))

    def delete(self, endpoint):
        return self._json_request('delete', endpoint)
