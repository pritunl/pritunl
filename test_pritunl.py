from drivnal import database
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
    ('GET', '/key/0.tar'),
    ('GET', '/key/0.html'),
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
    def setUp(self):
        if os.path.isfile(TEMP_DATABSE_PATH):
            os.remove(TEMP_DATABSE_PATH)
        self._db = database.Database(TEMP_DATABSE_PATH)

    def tearDown(self):
        self._db.close()
        os.remove(TEMP_DATABSE_PATH)

    def _fill_column_family(self, num):
        for i in xrange(5):
            for x in xrange(5):
                self._db.set('column_family_%s' % num, 'row_%s' % i,
                    'column_%s' % x, 'value_%s' % x)

        for i in xrange(5):
            for x in xrange(5):
                value = self._db.get('column_family_%s' % num,
                    'row_%s' % i, 'column_%s' % x)
                self.assertEqual(value, 'value_%s' % x)

        for i in xrange(5):
            for x in xrange(5):
                self._db.remove('column_family_%s' % num,
                    'row_%s' % i, 'column_%s' % x)

        for i in xrange(5):
            for x in xrange(5):
                value = self._db.get('column_family_%s' % num,
                    'row_%s' % i, 'column_%s' % x)
                self.assertEqual(value, None)

    def test_database(self):
        for i in xrange(2):
            threads = []
            for x in xrange(300):
                thread = threading.Thread(target=self._fill_column_family,
                    args=(x,))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()


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
