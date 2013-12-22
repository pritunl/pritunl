from drivnal import database
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
TEMP_DATABSE_PATH = 'pritunl_test.db'

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


if __name__ == '__main__':
    unittest.main()
