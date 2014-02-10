from constants import *
from cache import cache_db, persist_db
import flask
import json
import subprocess
import re
import urllib2
import httplib
import socket
import time
import base64
import hashlib
import os

def jsonify(data=None, status_code=None):
    if not isinstance(data, basestring):
        data = json.dumps(data)
    response = flask.Response(response=data, mimetype='application/json')
    response.headers.add('Cache-Control',
        'no-cache, no-store, must-revalidate')
    response.headers.add('Pragma', 'no-cache')
    if status_code is not None:
        response.status_code = status_code
    return response

def get_remote_addr():
    return flask.request.remote_addr

def check_session():
    from pritunl import app_server
    from auth_token import AuthToken
    auth_token = flask.request.headers.get('Auth-Token', None)
    if auth_token:
        auth_token = AuthToken(auth_token)
        if not auth_token.valid:
            return False
    else:
        if not flask.session:
            return False

        if not flask.session.get('auth'):
            flask.session.clear()
            return False

        if not app_server.ssl and flask.session.get(
                'source') != get_remote_addr():
            flask.session.clear()
            return False

        if app_server.session_timeout and int(time.time()) - \
                flask.session['timestamp'] > app_server.session_timeout:
            flask.session.clear()
            return False
    return True

def rmtree(path):
    subprocess.check_call(['rm', '-rf', path])

def check_output(*popenargs, **kwargs):
    # For python2.6 support
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, ' + \
            'it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE,
        *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get('args')
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=output)
    return output

def ip_to_long(ip_str):
    ip = ip_str.split('.')
    ip.reverse()
    while len(ip) < 4:
        ip.insert(1, '0')
    return sum(long(byte) << 8 * i for i, byte in enumerate(ip))

def long_to_ip(ip_num):
    return '.'.join(map(str, [
        (ip_num >> 24) & 0xff,
        (ip_num >> 16) & 0xff,
        (ip_num >> 8) & 0xff,
        ip_num & 0xff,
    ]))

def subnet_to_cidr(subnet):
    count = 0
    while ~ip_to_long(subnet) & pow(2, count):
        count += 1
    return 32 - count

def network_addr(ip, subnet):
    return '%s/%s' % (long_to_ip(ip_to_long(ip) & ip_to_long(subnet)),
        subnet_to_cidr(subnet))

def get_local_networks():
    addresses = []
    output = check_output(['ifconfig'])
    for interface in output.split('\n\n'):
        interface_name = re.findall(r'[a-z0-9]+', interface, re.IGNORECASE)
        if not interface_name:
            continue
        interface_name = interface_name[0]
        if re.search(r'tun[0-9]+', interface_name) or interface_name == 'lo':
            continue
        addr = re.findall(r'inet.{0,10}' + IP_REGEX, interface, re.IGNORECASE)
        if not addr:
            continue
        addr = re.findall(IP_REGEX, addr[0], re.IGNORECASE)
        if not addr:
            continue
        mask = re.findall(r'mask.{0,10}' + IP_REGEX, interface, re.IGNORECASE)
        if not mask:
            continue
        mask = re.findall(IP_REGEX, mask[0], re.IGNORECASE)
        if not mask:
            continue
        addr = addr[0]
        mask = mask[0]
        if addr.split('.')[0] == '127':
            continue
        addresses.append(network_addr(addr, mask))
    return addresses

def get_cert_block(cert_path):
    with open(cert_path) as cert_file:
        cert_file = cert_file.read()
        start_index = cert_file.index('-----BEGIN CERTIFICATE-----')
        end_index = cert_file.index('-----END CERTIFICATE-----') + 25
        return cert_file[start_index:end_index]

def filter_str(in_str):
    if not in_str:
        return in_str
    return ''.join(x for x in in_str if x.isalnum() or x in NAME_SAFE_CHARS)

class Response:
    def __init__(self, url, headers, status_code, reason, content):
        self.url = url
        self.headers = headers
        self.status_code = status_code
        self.reason = reason
        self.content = content

    def json(self):
        return json.loads(self.content)

class request:
    @classmethod
    def _request(cls, method, url, json_data=None, headers={},
            timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        data = None
        request = urllib2.Request(url, headers=headers)
        request.get_method = lambda: method

        if json_data is not None:
            request.add_header('Content-Type', 'application/json')
            data = json.dumps(json_data)

        try:
            url_response = urllib2.urlopen(request, data=data, timeout=timeout)
            return Response(url,
                headers=dict(url_response.info().items()),
                status_code=url_response.getcode(),
                reason='OK',
                content=url_response.read(),
            )
        except urllib2.HTTPError as error:
            return Response(url,
                headers=dict(error.info().items()),
                status_code=error.getcode(),
                reason=error.reason,
                content=error.read(),
            )
        except Exception as error:
            raise httplib.HTTPException(error)

    @classmethod
    def get(cls, url, **kwargs):
        return cls._request('GET', url, **kwargs)

    @classmethod
    def options(cls, url, **kwargs):
        return cls._request('OPTIONS', url, **kwargs)

    @classmethod
    def head(cls, url, **kwargs):
        return cls._request('HEAD', url, **kwargs)

    @classmethod
    def post(cls, url, **kwargs):
        return cls._request('POST', url, **kwargs)

    @classmethod
    def put(cls, url, **kwargs):
        return cls._request('PUT', url, **kwargs)

    @classmethod
    def patch(cls, url, **kwargs):
        return cls._request('PATCH', url, **kwargs)

    @classmethod
    def delete(cls, url, **kwargs):
        return cls._request('DELETE', url, **kwargs)



def _hash_password_v0(salt, password):
    pass_hash = hashlib.sha512()
    pass_hash.update(password[:PASSWORD_LEN_LIMIT])
    pass_hash.update(base64.b64decode(salt))
    return base64.b64encode(pass_hash.digest())

def _hash_password_v1(salt, password):
    pass_hash = hashlib.sha512()
    pass_hash.update(password[:PASSWORD_LEN_LIMIT])
    pass_hash.update(base64.b64decode(salt))
    hash_digest = pass_hash.digest()

    for i in xrange(5):
        pass_hash = hashlib.sha512()
        pass_hash.update(hash_digest)
        hash_digest = pass_hash.digest()
    return base64.b64encode(hash_digest)

def _get_password_data():
    password = persist_db.dict_get('auth', 'password')
    if not password:
        return None, None, None
    pass_split = password.split('$')
    return (int(pass_split[0]), pass_split[1], pass_split[2])

def check_auth(username, password, remote_addr=None):
    if remote_addr:
        cache_key = 'ip_' + remote_addr
        count = cache_db.list_length(cache_key)
        if count and count > 10:
            raise flask.abort(403)

        key_exists = cache_db.exists(cache_key)
        cache_db.list_rpush(cache_key, '')
        if not key_exists:
            cache_db.expire(cache_key, 20)

    db_username = persist_db.dict_get('auth', 'username') or DEFAULT_USERNAME
    if username != db_username:
        return False

    db_password = persist_db.dict_get('auth', 'password')
    if not db_password:
        if password == DEFAULT_PASSWORD:
            return True
        return False

    pass_ver, pass_salt, db_pass_hash = db_password.split('$')
    if pass_ver == '0':
        pass_hash = _hash_password_v0(pass_salt, password)
    elif pass_ver == '1':
        pass_hash = _hash_password_v1(pass_salt, password)
    else:
        return False
    return pass_hash == db_pass_hash

def set_auth(username=None, password=None):
    tran = persist_db.transaction()
    if username:
        tran.dict_set('auth', 'username', username)
    if password:
        salt = base64.b64encode(os.urandom(8))
        pass_hash = _hash_password_v1(salt, password)
        tran.dict_set('auth', 'password', '1$%s$%s' % (salt, pass_hash))
    tran.commit()

def get_auth():
    return persist_db.dict_get('auth', 'username')
