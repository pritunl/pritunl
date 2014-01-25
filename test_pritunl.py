import threading
import unittest
import requests
import json
import time
import os

BASE_URL = os.getenv('BASE_URL', 'http://localhost:9700')
HEADERS = {
    'Accept': 'application/json',
}
USERNAME = os.getenv('USERNAME', 'admin')
PASSWORD = os.getenv('PASSWORD', 'admin')
TEST_PASSWORD = 'unittest'
TEST_USER_NAME = 'unittest_user'
TEST_ORG_NAME = 'unittest_org'
TEST_SERVER_NAME = 'unittest_server'
ENABLE_STANDARD_TESTS = True
ENABLE_EXTENDED_TESTS = False
ENABLE_STRESS_TESTS = False
THREADED_STRESS_TEST = True
UUID_RE = r'^[a-z0-9]+$'
AUTH_HANDLERS = [
    ('GET', '/export'),
    ('GET', '/event'),
    ('GET', '/key/0/0.tar'),
    ('GET', '/key/0/0'),
    ('GET', '/log'),
    ('GET', '/organization'),
    ('POST', '/organization'),
    ('PUT', '/organization/0'),
    ('DELETE', '/organization/0'),
    ('PUT', '/password'),
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
    ('PUT', '/user/0/0/otp_secret'),
]
RUN_ONLY = []

def _log_request(method, endpoint, start_time):
    if endpoint.startswith('/event'):
        return
    response_time = int((time.time() - start_time) * 1000)
    if endpoint.startswith('/auth'):
        if response_time > 900:
            color = '\033[92m'
        elif response_time > 700:
            color = '\033[93m'
        else:
            color = '\033[92m'
    else:
        if response_time > 400:
            color = '\033[91m'
        elif response_time > 200:
            color = '\033[93m'
        else:
            color = '\033[92m'
    print '%s%sms:%s:%s\033[0m' % (color, response_time, method, endpoint)

_request = requests.api.request
def request(method, endpoint, **kwargs):
    headers = {
        'Accept': 'application/json',
    }
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))
    if 'json_data' in kwargs and kwargs['json_data']:
        headers['Content-Type'] = 'application/json'
        kwargs['data'] = json.dumps(kwargs.pop('json_data'))
    start_time = time.time()
    response = _request(method, BASE_URL + endpoint, headers=headers,
        verify=False, **kwargs)
    _log_request(method, endpoint, start_time)
    return response
requests.api.request = request


class Session:
    def __init__(self):
        self._session = requests.Session()
        self.response = self.post('/auth', json_data={
            'username': USERNAME,
            'password': PASSWORD,
        })

    def _request(self, method, endpoint, **kwargs):
        headers = {
            'Accept': 'application/json',
        }
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        if 'json_data' in kwargs and kwargs['json_data']:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs.pop('json_data'))
        start_time = time.time()
        response = getattr(self._session, method)(BASE_URL + endpoint,
            headers=headers, verify=False, **kwargs)
        _log_request(method, endpoint, start_time)
        return response

    def get(self, endpoint, **kwargs):
        return self._request('get', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._request('post', endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self._request('put', endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self._request('delete', endpoint, **kwargs)


class SessionTestCase(unittest.TestCase):
    session = Session()

    def setUp(self):
        if RUN_ONLY and self._testMethodName not in RUN_ONLY:
            self.skipTest('ignore')

        self.org_id = None
        self.user_id = None
        self.server_id = None
        self._create_test_data()
        self._clean_test_data()

    def _clean_test_data(self):
        response = self.session.get('/organization')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for org in data:
            if org['name'] in {TEST_ORG_NAME + '2', TEST_ORG_NAME + '3'}:
                response = self.session.delete('/organization/%s' % org['id'])
                self.assertEqual(response.status_code, 200)

        response = self.session.get('/user/%s' % self.org_id)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for user in data:
            if user['name'] == {TEST_USER_NAME + '2', TEST_USER_NAME + '3'}:
                response = self.session.delete('/user/%s/%s' % (
                    self.org_id, user['id']))
                self.assertEqual(response.status_code, 200)

        response = self.session.get('/server')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for server in data:
            if server['name'] == {TEST_SERVER_NAME + '2',
                    TEST_SERVER_NAME + '3'}:
                response = self.session.delete('/server/%s' % server['id'])
                self.assertEqual(response.status_code, 200)

        response = self.session.get('/server/%s/organization' % self.server_id)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for server_org in data:
            response = self.session.delete('/server/%s/organization/%s' % (
                self.server_id, server_org['id']))
            self.assertEqual(response.status_code, 200)

    def _create_test_data(self):
        if not self.org_id:
            response = self.session.get('/organization')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            for org in data:
                if org['name'] == TEST_ORG_NAME:
                    self.org_id = org['id']

        if not self.org_id:
            response = self.session.post('/organization', json_data={
                'name': TEST_ORG_NAME,
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('id', data)
            self.assertIn('name', data)
            self.assertEqual(data['name'], TEST_ORG_NAME)
            self.org_id = data['id']

        if not self.user_id:
            response = self.session.get('/user/%s' % self.org_id)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            for user in data:
                if user['name'] == TEST_USER_NAME:
                    self.user_id = user['id']

        if not self.user_id:
            response = self.session.post('/user/%s' % self.org_id, json_data={
                'name': TEST_USER_NAME,
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('id', data)
            self.assertIn('name', data)
            self.assertEqual(data['name'], TEST_USER_NAME)
            self.user_id = data['id']

        if not self.server_id:
            response = self.session.get('/server')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            for server in data:
                if server['name'] == TEST_SERVER_NAME:
                    self.server_id = server['id']

        if not self.server_id:
            response = self.session.post('/server', json_data={
                'name': TEST_SERVER_NAME,
                'otp_auth': True,
            })
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('id', data)
            self.assertIn('name', data)
            self.assertEqual(data['name'], TEST_SERVER_NAME)
            self.server_id = data['id']

    def _delete_test_data(self):
        response = self.session.delete('/organization/%s' % self.org_id)
        self.assertEqual(response.status_code, 200)


class Auth(SessionTestCase):
    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_auth_get(self):
        response = requests.get('/auth')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_auth_post(self):
        session = Session()
        data = session.response.json()
        self.assertEqual(session.response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertTrue(data['authenticated'])


        response = session.get('/auth')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('authenticated', data)
        self.assertTrue(data['authenticated'])


        response = session.delete('/auth')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])


        response = session.get('/auth')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_auth_post_error(self):
        for endpoint in ['/auth', '/auth/token']:
            for username, password in [
                        ('admin', 'test'),
                        ('test', 'admin'),
                        ('test', 'test'),
                    ]:
                response = requests.post(endpoint, json_data={
                    'username': username,
                    'password': password,
                })
                self.assertEqual(response.status_code, 401)

                data = response.json()
                self.assertIn('error', data)
                self.assertEqual(data['error'], 'auth_invalid')
                self.assertIn('error_msg', data)

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_auth_handlers(self):
        for method, endpoint in AUTH_HANDLERS:
            response = getattr(requests, method.lower())(endpoint)
            self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_auth_token_get_post_delete(self):
        response = requests.get('/auth')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])


        response = requests.post('/auth/token', json_data={
            'username': USERNAME,
            'password': PASSWORD,
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('auth_token', data)
        self.assertRegexpMatches(data['auth_token'], UUID_RE)
        auth_token = data['auth_token']


        response = requests.get('/auth', headers={
            'Auth-Token': auth_token,
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('authenticated', data)
        self.assertTrue(data['authenticated'])


        response = requests.delete('/auth/token/%s' % auth_token)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data, {})


        response = requests.get('/auth', headers={
            'Auth-Token': auth_token,
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])

class Data(SessionTestCase):
    @unittest.skipUnless(ENABLE_EXTENDED_TESTS, 'Skipping test')
    def test_export_get(self):
        for endpoint in ['/export', '/export/pritunl.tar']:
            response = self.session.get(endpoint)
            self.assertEqual(response.status_code, 200)

            content_type = response.headers['content-type']
            self.assertEqual(content_type, 'application/octet-stream')

            content_disposition = response.headers['content-disposition']
            exp = r'^attachment; filename="pritunl_[0-9]+_[0-9]+_[0-9]+_' + \
                '[0-9]+_[0-9]+_[0-9]+\.tar"$'
            self.assertRegexpMatches(content_disposition, exp)


class Key(SessionTestCase):
    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_user_key_archive_get(self):
        response = self.session.get('/key/%s/%s.tar' % (
            self.org_id, self.user_id))
        self.assertEqual(response.status_code, 200)

        content_type = response.headers['content-type']
        self.assertEqual(content_type, 'application/octet-stream')

        content_disposition = response.headers['content-disposition']
        exp = r'^attachment; filename="%s.tar"$' % TEST_USER_NAME
        self.assertRegexpMatches(content_disposition, exp)

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_user_key_link_get(self):
        response = self.session.put('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 200)


        response = self.session.get('/key/%s/%s' % (
            self.org_id, self.user_id))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertIn('key_url', data)
        self.assertIn('view_url', data)

        exp = r'^/key/[a-z0-9]+.tar$'
        self.assertRegexpMatches(data['key_url'], exp)

        exp = r'^/k/[a-zA-Z0-9]+$'
        self.assertRegexpMatches(data['view_url'], exp)


        response = self.session.get(data['key_url'])
        self.assertEqual(response.status_code, 200)

        content_type = response.headers['content-type']
        self.assertEqual(content_type, 'application/octet-stream')

        content_disposition = response.headers['content-disposition']
        exp = r'^attachment; filename="%s.tar"$' % TEST_USER_NAME
        self.assertRegexpMatches(content_disposition, exp)


        response = self.session.get(data['view_url'])
        self.assertEqual(response.status_code, 200)

        content_type = response.headers['content-type']
        self.assertEqual(content_type, 'text/html; charset=utf-8')


        start_index = response.text.find('<h4 class="key-title">') + 22
        end_index = response.text.find('</h2>', start_index)
        self.assertNotEqual(start_index, -1)
        self.assertNotEqual(end_index, -1)
        key_title = response.text[start_index:end_index]
        self.assertEqual('%s - %s' % (TEST_ORG_NAME, TEST_USER_NAME),
            key_title)


        start_index = response.text.find(
            '<input id="key" type="text" readonly value="') + 44
        end_index = response.text.find('">', start_index)
        self.assertNotEqual(start_index, -1)
        self.assertNotEqual(end_index, -1)
        otp_secret = response.text[start_index:end_index]
        exp = r'^[A-Z0-9]+$'
        self.assertRegexpMatches(otp_secret, exp)


        start_index = response.text.find('<a title="Download Key" href="') + 30
        end_index = response.text.find('">', start_index)
        self.assertNotEqual(start_index, -1)
        self.assertNotEqual(end_index, -1)
        key_url = response.text[start_index:end_index]
        self.assertEqual(key_url, data['key_url'])


        start_index = response.text.find(
            '<a class="sm" title="Download Mobile Key" href="') + 48
        end_index = response.text.find('">', start_index)
        self.assertNotEqual(start_index, -1)
        self.assertNotEqual(end_index, -1)
        conf_url = response.text[start_index:end_index]

        exp = r'^/key/[a-z0-9]+\.ovpn$'
        self.assertRegexpMatches(conf_url, exp)


        start_index = response.text.find("text: 'otpauth://totp/") + 7
        end_index = response.text.find("',", start_index)
        self.assertNotEqual(start_index, -1)
        self.assertNotEqual(end_index, -1)
        otp_key = response.text[start_index:end_index]

        exp = r'^otpauth://totp/%s@%s\?secret\=%s$' % (
            TEST_USER_NAME, TEST_ORG_NAME, otp_secret)
        self.assertRegexpMatches(otp_key, exp)


        response = self.session.delete('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 200)


class Log(SessionTestCase):
    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_log_get(self):
        response = self.session.get('/log')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotEqual(len(data), 0)
        for entry in data:
            self.assertIn('id', entry)
            self.assertRegexpMatches(entry['id'], UUID_RE)
            self.assertIn('time', entry)
            self.assertIn('message', entry)


class Org(SessionTestCase):
    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_org_post_put_get_delete(self):
        response = self.session.post('/organization', json_data={
            'name': TEST_ORG_NAME + '2',
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertRegexpMatches(data['id'], UUID_RE)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_ORG_NAME + '2')
        org_id = data['id']


        response = self.session.put('/organization/%s' % org_id, json_data={
            'name': TEST_ORG_NAME + '3',
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_ORG_NAME + '3')


        response = self.session.get('/organization')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotEqual(len(data), 0)
        test_org_found = False
        for org in data:
            self.assertIn('id', org)
            self.assertRegexpMatches(org['id'], UUID_RE)
            self.assertIn('name', org)
            if org['name'] == TEST_ORG_NAME + '3':
                test_org_found = True
                self.assertEqual(org['id'], org_id)
        self.assertTrue(test_org_found)


        response = self.session.delete('/organization/%s' % org_id)
        self.assertEqual(response.status_code, 200)


        response = self.session.get('/organization')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotEqual(len(data), 0)
        for org in data:
            self.assertIn('id', org)
            self.assertIn('name', org)
            self.assertNotEqual(org['name'], TEST_ORG_NAME + '3')


class Password(SessionTestCase):
    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_password_post(self):
        response = self.session.put('/password', json_data={
            'password': TEST_PASSWORD,
        })
        self.assertEqual(response.status_code, 200)

        response = self.session.post('/auth/token', json_data={
            'username': USERNAME,
            'password': TEST_PASSWORD,
        })
        self.assertEqual(response.status_code, 200)

        response = self.session.put('/password', json_data={
            'password': PASSWORD,
        })
        self.assertEqual(response.status_code, 200)


class Server(SessionTestCase):
    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_server_post_put_get_delete(self):
        response = self.session.post('/server', json_data={
            'name': TEST_SERVER_NAME + '2',
            'network': '10.254.254.0/24',
            'interface': 'tun64',
            'port': 12345,
            'protocol': 'udp',
            'local_networks': [],
            'public_address': '8.8.8.8',
            'debug': True,
            'otp_auth': False,
            'lzo_compression': False,
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertRegexpMatches(data['id'], UUID_RE)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_SERVER_NAME + '2')
        self.assertIn('network', data)
        self.assertEqual(data['network'], '10.254.254.0/24')
        self.assertIn('interface', data)
        self.assertEqual(data['interface'], 'tun64')
        self.assertIn('port', data)
        self.assertEqual(data['port'], 12345)
        self.assertIn('protocol', data)
        self.assertEqual(data['protocol'], 'udp')
        self.assertIn('local_networks', data)
        self.assertEqual(data['local_networks'], [])
        self.assertIn('public_address', data)
        self.assertEqual(data['public_address'], '8.8.8.8')
        self.assertIn('debug', data)
        self.assertTrue(data['debug'])
        self.assertIn('otp_auth', data)
        self.assertFalse(data['otp_auth'])
        self.assertIn('lzo_compression', data)
        self.assertFalse(data['lzo_compression'])
        server_id = data['id']


        response = self.session.put('/server/%s' % server_id, json_data={
            'name': TEST_SERVER_NAME + '3',
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], server_id)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_SERVER_NAME + '3')
        self.assertIn('network', data)
        self.assertEqual(data['network'], '10.254.254.0/24')
        self.assertIn('interface', data)
        self.assertEqual(data['interface'], 'tun64')
        self.assertIn('port', data)
        self.assertEqual(data['port'], 12345)
        self.assertIn('protocol', data)
        self.assertEqual(data['protocol'], 'udp')
        self.assertIn('local_networks', data)
        self.assertEqual(data['local_networks'], [])
        self.assertIn('public_address', data)
        self.assertEqual(data['public_address'], '8.8.8.8')
        self.assertIn('debug', data)
        self.assertTrue(data['debug'])
        self.assertIn('otp_auth', data)
        self.assertFalse(data['otp_auth'])
        self.assertIn('lzo_compression', data)
        self.assertFalse(data['lzo_compression'])


        response = self.session.get('/server')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotEqual(len(data), 0)
        test_server_found = False
        for server in data:
            self.assertIn('id', server)
            self.assertRegexpMatches(server['id'], UUID_RE)
            self.assertIn('name', server)
            self.assertIn('network', server)
            self.assertIn('interface', server)
            self.assertIn('port', server)
            self.assertIn('protocol', server)
            self.assertIn('local_networks', server)
            self.assertIn('public_address', server)
            self.assertIn('debug', server)
            self.assertIn('otp_auth', server)
            self.assertIn('lzo_compression', server)

            if server['name'] == TEST_SERVER_NAME + '3':
                test_server_found = True
                self.assertEqual(server['id'], server_id)
                self.assertEqual(server['network'], '10.254.254.0/24')
                self.assertEqual(server['interface'], 'tun64')
                self.assertEqual(server['port'], 12345)
                self.assertEqual(server['protocol'], 'udp')
                self.assertEqual(server['local_networks'], [])
                self.assertEqual(server['public_address'], '8.8.8.8')
                self.assertTrue(server['debug'])
                self.assertFalse(server['otp_auth'])
                self.assertFalse(server['lzo_compression'])
        self.assertTrue(test_server_found)


        response = self.session.delete('/server/%s' % server_id)
        self.assertEqual(response.status_code, 200)


        response = self.session.get('/server')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotEqual(len(data), 0)
        for server in data:
            self.assertIn('id', server)
            self.assertIn('name', server)
            self.assertNotEqual(server['name'], TEST_SERVER_NAME + '3')

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_server_org_put_get_delete(self):
        response = self.session.put('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.org_id)
        self.assertIn('server', data)
        self.assertEqual(data['server'], self.server_id)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_ORG_NAME)


        response = self.session.get('/server/%s/organization' % self.server_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotEqual(len(data), 0)
        test_server_org_found = False
        for server_org in data:
            self.assertIn('id', server_org)
            self.assertRegexpMatches(server_org['id'], UUID_RE)
            self.assertIn('server', server_org)
            self.assertEqual(server_org['server'], self.server_id)
            self.assertIn('name', server_org)
            if server_org['name'] == TEST_ORG_NAME:
                test_server_org_found = True
                self.assertEqual(server_org['id'], self.org_id)
        self.assertTrue(test_server_org_found)


        response = self.session.delete('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_server_operation_put(self):
        response = self.session.put('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.org_id)
        self.assertIn('server', data)
        self.assertEqual(data['server'], self.server_id)


        response = self.session.put('/server/%s/start' % self.server_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.server_id)
        self.assertIn('status', data)
        self.assertTrue(data['status'])


        response = self.session.put('/server/%s/restart' % self.server_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.server_id)
        self.assertIn('status', data)
        self.assertTrue(data['status'])


        response = self.session.put('/server/%s/stop' % self.server_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.server_id)
        self.assertIn('status', data)
        self.assertFalse(data['status'])


        response = self.session.delete('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_server_output_delete_get(self):
        response = self.session.delete('/server/%s/output' % self.server_id)
        self.assertEqual(response.status_code, 200)

        response = self.session.get('/server/%s/output' % self.server_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('output', data)
        self.assertEqual(data['output'], '')

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_server_put_post_errors(self):
        response = self.session.put('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.org_id)
        self.assertIn('server', data)
        self.assertEqual(data['server'], self.server_id)


        response = self.session.put('/server/%s/start' % self.server_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.server_id)
        self.assertIn('status', data)
        self.assertTrue(data['status'])


        response = self.session.put('/server/%s' % self.server_id, json_data={
            'name': TEST_SERVER_NAME + '_test',
        })
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'server_not_offline')
        self.assertIn('error_msg', data)


        response = self.session.put('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'server_not_offline')
        self.assertIn('error_msg', data)


        response = self.session.delete('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'server_not_offline')
        self.assertIn('error_msg', data)


        response = self.session.put('/server/%s/stop' % self.server_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.server_id)
        self.assertIn('status', data)
        self.assertFalse(data['status'])


        response = self.session.delete('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 200)


        for test_network in [
                    '10.254.254.024',
                    '10254.254.0/24',
                    '10a.254.254.0/24',
                    '11.254.254.0/24',
                    '10.255.254.1/24',
                    '10.254.254.0/24a',
                ]:
            response = self.session.post('/server', json_data={
                'name': TEST_SERVER_NAME + '_test',
                'network': test_network,
            })
            self.assertEqual(response.status_code, 400)

            data = response.json()
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'network_invalid')
            self.assertIn('error_msg', data)

        for test_interface in [
                    'tun-1',
                    'tun.0',
                    'tun65',
                    'tuna',
                ]:
            response = self.session.post('/server', json_data={
                'name': TEST_SERVER_NAME + '_test',
                'interface': test_interface,
            })
            self.assertEqual(response.status_code, 400)

            data = response.json()
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'interface_invalid')
            self.assertIn('error_msg', data)


        for test_port in [
                    0,
                    65536,
                ]:
            response = self.session.post('/server', json_data={
                'name': TEST_SERVER_NAME + '_test',
                'port': test_port,
            })
            self.assertEqual(response.status_code, 400)

            data = response.json()
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'port_invalid')
            self.assertIn('error_msg', data)


        response = self.session.post('/server', json_data={
            'name': TEST_SERVER_NAME + '_test',
            'protocol': 'a',
        })
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'protocol_invalid')
        self.assertIn('error_msg', data)


class Status(SessionTestCase):
    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_status_get(self):
        response = self.session.get('/status')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('org_count', data)
        self.assertIn('users_online', data)
        self.assertIn('user_count', data)
        self.assertIn('servers_online', data)
        self.assertIn('server_count', data)
        self.assertIn('server_version', data)
        self.assertIn('public_ip', data)
        self.assertIn('local_networks', data)


class User(SessionTestCase):
    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_user_post_put_get_delete(self):
        response = self.session.post('/user/%s' % self.org_id, json_data={
            'name': TEST_USER_NAME + '2',
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertRegexpMatches(data['id'], UUID_RE)
        self.assertIn('organization', data)
        self.assertEqual(data['organization'], self.org_id)
        self.assertIn('organization_name', data)
        self.assertEqual(data['organization_name'], TEST_ORG_NAME)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_USER_NAME + '2')
        self.assertIn('type', data)
        self.assertIn('otp_secret', data)
        user_id = data['id']


        response = self.session.put('/user/%s/%s' % (self.org_id, user_id),
            json_data={
                'name': TEST_USER_NAME + '3',
            })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertRegexpMatches(data['id'], UUID_RE)
        self.assertIn('organization', data)
        self.assertEqual(data['organization'], self.org_id)
        self.assertIn('organization_name', data)
        self.assertEqual(data['organization_name'], TEST_ORG_NAME)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_USER_NAME + '3')
        self.assertIn('type', data)
        self.assertIn('otp_secret', data)


        response = self.session.get('/user/%s' % self.org_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotEqual(len(data), 0)
        test_user_found = False
        for user in data:
            self.assertIn('id', user)
            self.assertRegexpMatches(user['id'], UUID_RE)
            self.assertIn('organization', user)
            self.assertIn('organization_name', user)
            self.assertIn('name', user)
            self.assertIn('type', user)
            self.assertIn('status', user)
            self.assertIn('otp_auth', user)
            self.assertIn('otp_secret', user)
            self.assertIn('servers', user)

            if user['name'] == TEST_USER_NAME + '3':
                test_user_found = True
                self.assertEqual(user['organization'], self.org_id)
                self.assertEqual(user['organization_name'], TEST_ORG_NAME)
        self.assertTrue(test_user_found)

        response = self.session.delete('/user/%s/%s' % (self.org_id, user_id))
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(ENABLE_STANDARD_TESTS, 'Skipping test')
    def test_user_otp_secret_put(self):
        response = self.session.get('/user/%s' % self.org_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertNotEqual(len(data), 0)
        orig_otp_secret = None
        for user in data:
            self.assertIn('id', user)
            if user['id'] == self.user_id:
                orig_otp_secret = user['otp_secret']
        self.assertIsNotNone(orig_otp_secret)

        response = self.session.put('/user/%s/%s/otp_secret' % (
            self.org_id, self.user_id))
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], self.user_id)
        self.assertIn('organization', data)
        self.assertEqual(data['organization'], self.org_id)
        self.assertIn('organization_name', data)
        self.assertEqual(data['organization_name'], TEST_ORG_NAME)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_USER_NAME)
        self.assertIn('type', data)
        self.assertIn('otp_secret', data)
        self.assertNotEqual(data['otp_secret'], orig_otp_secret)
        self.assertRegexpMatches(user['otp_secret'], r'^[A-Z0-9]+$')


class Stress(SessionTestCase):
    def _create_user(self, org_id, name):
        response = self.session.post('/user/%s' % org_id, json_data={
            'name': name,
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertRegexpMatches(data['id'], UUID_RE)
        self.assertIn('organization', data)
        self.assertEqual(data['organization'], org_id)
        self.assertIn('organization_name', data)
        self.assertEqual(data['organization_name'],
            TEST_ORG_NAME + '_stress')
        self.assertIn('name', data)
        self.assertEqual(data['name'], name)
        self.assertIn('type', data)
        self.assertIn('otp_secret', data)

    @unittest.skipUnless(ENABLE_STRESS_TESTS, 'Skipping stress test')
    def test_user_post_stress(self):
        response = self.session.post('/organization', json_data={
            'name': TEST_ORG_NAME + '_stress',
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertRegexpMatches(data['id'], UUID_RE)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_ORG_NAME + '_stress')
        org_id = data['id']

        if THREADED_STRESS_TEST:
            num = 0
            for i in xrange(8):
                threads = []

                for x in xrange(512):
                    name = '%s_%s' % (TEST_USER_NAME, str(num).zfill(4))
                    thread = threading.Thread(target=self._create_user,
                        args=(org_id, name))
                    thread.start()
                    threads.append(thread)
                    num += 1

                for thread in threads:
                    thread.join()

        else:
            for i in xrange(4096):
                name = '%s_%s' % (TEST_USER_NAME, str(i).zfill(4))
                self._create_user(org_id, name)


if __name__ == '__main__':
    unittest.main()
