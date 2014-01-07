from pritunl import database
import threading
import unittest
import requests
import json
import time
import os

BASE_URL = 'http://localhost:9700'
HEADERS = {
    'Accept': 'application/json',
}
USERNAME = 'admin'
PASSWORD = 'admin'
TEST_PASSWORD = 'unittest'
TEST_USER_NAME = 'unittest_user'
TEST_ORG_NAME = 'unittest_org'
TEST_SERVER_NAME = 'unittest_server'
TEMP_DATABSE_PATH = 'pritunl_test.db'
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
    ('PUT', '/user/0/0/otp_secret'),
]
RUN_ONLY = []

_request = requests.api.request
def request(method, endpoint, **kwargs):
    headers = {
        'Accept': 'application/json',
    }
    if 'json' in kwargs and kwargs['json']:
        headers['Content-Type'] = 'application/json'
        kwargs['data'] = json.dumps(kwargs.pop('json'))
    return _request(method, BASE_URL + endpoint, headers=headers, **kwargs)
requests.api.request = request


class Session:
    def __init__(self):
        self._session = requests.Session()
        self.response = self.post('/auth', json={
            'username': USERNAME,
            'password': PASSWORD,
        })

    def _request(self, method, endpoint, **kwargs):
        headers = {
            'Accept': 'application/json',
        }
        if 'json' in kwargs and kwargs['json']:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = json.dumps(kwargs.pop('json'))
        return getattr(self._session, method)(BASE_URL + endpoint,
            headers=headers, **kwargs)

    def get(self, endpoint, **kwargs):
        return self._request('get', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._request('post', endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self._request('put', endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self._request('delete', endpoint, **kwargs)


_global_session = Session()
class SessionTestCase(unittest.TestCase):
    def setUp(self):
        if RUN_ONLY and self._testMethodName not in RUN_ONLY:
            self.skipTest('ignore')

        self.org_id = None
        self.user_id = None
        self.server_id = None
        self.session = _global_session
        self._create_test_data()

    def _create_test_data(self):
        if not self.org_id:
            response = self.session.get('/organization')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            for org in data:
                if org['name'] == TEST_ORG_NAME:
                    self.org_id = org['id']

        if not self.org_id:
            response = self.session.post('/organization', json={
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
            response = self.session.post('/user/%s' % self.org_id, json={
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
            response = self.session.post('/server', json={
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


class Database(SessionTestCase):
    def _test_db(self, db):
        db.set('column_family', 'row1', 'column1', 'value1')
        db.set('column_family', 'row2', 'column2', 'value2')
        db.set('column_family', 'row3', 'column3', 'value3')
        value = db.get('column_family', 'row1', 'column1')
        self.assertEqual(value, 'value1')
        value = db.get('column_family', 'row2', 'column2')
        self.assertEqual(value, 'value2')
        value = db.get('column_family', 'row3', 'column3')
        self.assertEqual(value, 'value3')
        value = db.get('column_family', 'row1')
        self.assertEqual(value, {'column1': 'value1'})
        value = db.get('column_family')
        self.assertEqual(value, {
            'row1': {'column1': 'value1'},
            'row2': {'column2': 'value2'},
            'row3': {'column3': 'value3'},
        })
        db.remove('column_family', 'row1')
        db.remove('column_family', 'row2')
        db.remove('column_family', 'row3')
        value = db.get('column_family')
        self.assertEqual(value, {})

    def test_mem(self):
        db = database.Database(None)
        self._test_db(db)
        db.close()

    def test_berkeley_db(self):
        db = database.Database(TEMP_DATABSE_PATH)
        self._test_db(db)
        db.close()
        os.remove(TEMP_DATABSE_PATH)


class Auth(SessionTestCase):
    def test_auth_get(self):
        response = requests.get('/auth')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])

    def test_auth_post(self):
        session = Session()
        data = session.response.json()
        self.assertEqual(session.response.status_code, 200)
        self.assertEqual(session.response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertTrue(data['authenticated'])

        response = session.get('/auth')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertTrue(data['authenticated'])

        response = session.delete('/auth')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])

        response = session.get('/auth')
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertIn('authenticated', data)
        self.assertFalse(data['authenticated'])

    def test_auth_handlers(self):
        for method, endpoint in AUTH_HANDLERS:
            response = getattr(requests, method.lower())(endpoint)
            self.assertEqual(response.status_code, 401)


class Data(SessionTestCase):
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


class Event(SessionTestCase):
    def test_event_get(self):
        response = self.session.get('/event')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertIn('id', data[0])
        self.assertIn('type', data[0])
        self.assertIn('time', data[0])
        self.assertIn('resource_id', data[0])
        self.assertIsInstance(data[0]['id'], basestring)
        self.assertEqual(data[0]['type'], 'time')
        self.assertIsInstance(data[0]['time'], int)
        self.assertEqual(data[0]['resource_id'], None)


class Key(SessionTestCase):
    def test_user_key_archive_get(self):
        response = self.session.get('/key/%s/%s.tar' % (
            self.org_id, self.user_id))
        self.assertEqual(response.status_code, 200)

        content_type = response.headers['content-type']
        self.assertEqual(content_type, 'application/octet-stream')

        content_disposition = response.headers['content-disposition']
        exp = r'^attachment; filename="%s.tar"$' % TEST_USER_NAME
        self.assertRegexpMatches(content_disposition, exp)

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
    def test_org_post_put_get_delete(self):
        response = self.session.post('/organization', json={
            'name': TEST_ORG_NAME + '2',
        })
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('id', data)
        self.assertRegexpMatches(data['id'], UUID_RE)
        self.assertIn('name', data)
        self.assertEqual(data['name'], TEST_ORG_NAME + '2')
        org_id = data['id']


        response = self.session.put('/organization/%s' % org_id, json={
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
    def test_password_post(self):
        response = self.session.put('/password', json={
            'password': TEST_PASSWORD,
        })
        self.assertEqual(response.status_code, 200)

        response = self.session.post('/auth/token', json={
            'username': USERNAME,
            'password': TEST_PASSWORD,
        })
        self.assertEqual(response.status_code, 200)

        response = self.session.put('/password', json={
            'password': PASSWORD,
        })
        self.assertEqual(response.status_code, 200)


class Server(SessionTestCase):
    def test_server_post_put_get_delete(self):
        response = self.session.post('/server', json={
            'name': TEST_SERVER_NAME + '2',
            'network': '10.254.254.0/24',
            'interface': 'tun64',
            'port': 12345,
            'protocol': 'udp',
            'local_network': None,
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
        self.assertIn('local_network', data)
        self.assertIsNone(data['local_network'])
        self.assertIn('public_address', data)
        self.assertEqual(data['public_address'], '8.8.8.8')
        self.assertIn('debug', data)
        self.assertTrue(data['debug'])
        self.assertIn('otp_auth', data)
        self.assertFalse(data['otp_auth'])
        self.assertIn('lzo_compression', data)
        self.assertFalse(data['lzo_compression'])
        server_id = data['id']


        response = self.session.put('/server/%s' % server_id, json={
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
        self.assertIn('local_network', data)
        self.assertIsNone(data['local_network'])
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
            self.assertIn('local_network', server)
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
                self.assertIsNone(server['local_network'])
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

    def test_server_output_delete_get(self):
        response = self.session.delete('/server/%s/output' % self.server_id)
        self.assertEqual(response.status_code, 200)

        response = self.session.get('/server/%s/output' % self.server_id)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn('output', data)
        self.assertEqual(data['output'], '')

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


        response = self.session.put('/server/%s' % self.server_id, json={
            'name': TEST_SERVER_NAME + '_test',
        })
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'server_not_offline')
        self.assertIn('error_msg', data)
        self.assertEqual(data['error_msg'],
            'Server must be offline to modify settings.')


        response = self.session.put('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'server_not_offline')
        self.assertIn('error_msg', data)
        self.assertEqual(data['error_msg'], 'Server must be offline ' + \
            'to attach an organization.')


        response = self.session.delete('/server/%s/organization/%s' % (
            self.server_id, self.org_id))
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'server_not_offline')
        self.assertIn('error_msg', data)
        self.assertEqual(data['error_msg'], 'Server must be offline ' + \
            'to detach an organization.')


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
            response = self.session.post('/server', json={
                'name': TEST_SERVER_NAME + '_test',
                'network': test_network,
            })
            self.assertEqual(response.status_code, 400)

            data = response.json()
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'network_not_valid')
            self.assertIn('error_msg', data)
            self.assertEqual(data['error_msg'], 'Network address is not ' + \
                'valid, format must be "10.[0-255].[0-255].0/[8-24]" ' + \
                'such as "10.12.32.0/24".')


        for test_interface in [
                    'tun-1',
                    'tun.0',
                    'tun65',
                    'tuna',
                ]:
            response = self.session.post('/server', json={
                'name': TEST_SERVER_NAME + '_test',
                'interface': test_interface,
            })
            self.assertEqual(response.status_code, 400)

            data = response.json()
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'interface_not_valid')
            self.assertIn('error_msg', data)
            self.assertEqual(data['error_msg'], 'Interface is not valid, ' + \
                'must be "tun[0-64]" example "tun0".')


        for test_port in [
                    0,
                    65536,
                ]:
            response = self.session.post('/server', json={
                'name': TEST_SERVER_NAME + '_test',
                'port': test_port,
            })
            self.assertEqual(response.status_code, 400)

            data = response.json()
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'port_not_valid')
            self.assertIn('error_msg', data)
            self.assertEqual(data['error_msg'], 'Port number is not ' + \
                'valid, must be between 1 and 65535.')


        response = self.session.post('/server', json={
            'name': TEST_SERVER_NAME + '_test',
            'protocol': 'a',
        })
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'protocol_not_valid')
        self.assertIn('error_msg', data)
        self.assertEqual(data['error_msg'], 'Protocol is not valid, ' + \
            'must be "udp" or "tcp".')


class Status(SessionTestCase):
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


if __name__ == '__main__':
    unittest.main()
