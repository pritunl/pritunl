from pritunl import database
import threading
import unittest
import requests
import json
import time
import os

BASE_URL = 'http://localhost:9700'
HEADERS = {
    'Content-type': 'application/json',
    'Accept': 'application/json',
}
USERNAME = 'admin'
PASSWORD = 'admin'
TEMP_DATABSE_PATH = 'pritunl_test.db'
AUTH_HANDLERS = [
    ('DELETE', '/auth'),
    ('GET', '/export'),
    ('GET', '/event'),
    ('GET', '/key/0/0.tar'),
    ('GET', '/key/0/0'),
    ('GET', '/log'),
    ('GET', '/organization'),
    ('POST', '/organization'),
    ('PUT', '/organization/0'),
    ('DELETE', '/organization/0'),
    ('POST', '/password'),
    ('GET', '/server'),
    ('POST', '/server'),
    ('PUT', '/server/0'),
    ('DELETE', '/server/0'),
    ('GET', '/server/0/organization'),
    ('PUT', '/server/0/organization/0'),
    ('DELETE', '/server/0/organization/0'),
    ('PUT', '/server/0/0'),
    ('GET', '/server/0/output'),
    ('DELETE', '/server/0/output'),
    ('GET', '/status'),
    ('GET', '/user/0'),
    ('POST', '/user/0'),
    ('PUT', '/user/0/0'),
    ('DELETE', '/user/0/0'),
    ('DELETE', '/user/0/0/otp_secret'),
]

_request = requests.api.request
def request(method, endpoint, **kwargs):
    if 'json' in kwargs and kwargs['json']:
        kwargs['data'] = json.dumps(kwargs.pop('json'))
    return _request(method, BASE_URL + endpoint, headers=HEADERS, **kwargs)
requests.api.request = request


class Session:
    def __init__(self):
        self._session = requests.Session()
        data = {
            'username': USERNAME,
            'password': PASSWORD,
        }
        self.response = self.post('/auth', json=data)

    def _request(self, method, endpoint, **kwargs):
        if 'json' in kwargs and kwargs['json']:
            kwargs['data'] = json.dumps(kwargs.pop('json'))
        return getattr(self._session, method)(BASE_URL + endpoint,
            headers=HEADERS, **kwargs)

    def get(self, endpoint, **kwargs):
        return self._request('get', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._request('post', endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self._request('put', endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self._request('delete', endpoint, **kwargs)


class Database(unittest.TestCase):
    def test_mem(self):
        db = database.Database(None)
        db.set('column_family', 'row', 'column', 'value')
        value = db.get('column_family', 'row', 'column')
        self.assertEqual(value, 'value')
        db.close()

    def test_berkeley_db(self):
        db = database.Database(TEMP_DATABSE_PATH)
        db.set('column_family', 'row', 'column', 'value')
        value = db.get('column_family', 'row', 'column')
        self.assertEqual(value, 'value')
        db.close()
        os.remove(TEMP_DATABSE_PATH)


class Auth(unittest.TestCase):
    def test_auth_get(self):
        response = requests.get('/auth')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])

    def test_auth_post(self):
        session = Session()
        self.assertEqual(session.response.status_code, 200)

        response = session.get('/auth')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertTrue(data['authenticated'])

        response = session.delete('/auth')
        self.assertEqual(response.status_code, 200)

        response = session.get('/auth')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])

    def test_auth_handlers(self):
        for method, endpoint in AUTH_HANDLERS:
            response = getattr(requests, method.lower())(endpoint)
            self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
