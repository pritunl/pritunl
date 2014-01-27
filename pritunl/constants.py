import string

APP_NAME = 'pritunl'
APP_NAME_FORMATED = 'Pritunl'
CONF_FILENAME = '%s.conf' % APP_NAME


SAVED = 'saved'
UNSAVED = 'unsaved'

START = 'start'
STOP = 'stop'
RESTART = 'restart'

NAME_SAFE_CHARS = ['-', '_', '@', '.']

KEY_LINK_TIMEOUT = 86400
DEFAULT_PRIMARY_INTERFACE = 'eth0'
DEFAULT_SESSION_TIMEOUT = 86400
DEFAULT_PASSWORD = 'admin'
PASSWORD_SALT = '2511cebca93d028393735637bbc8029207731fcf'
DEFAULT_CONF_PATH = '/etc/pritunl.conf'
DEFAULT_DB_PATH = '/var/lib/pritunl/pritunl.db'
DEFAULT_WWW_PATH = '/usr/share/pritunl/www'
DEFAULT_DATA_PATH = '/var/lib/pritunl'
DEFAULT_KEY_BITS = 4096
DEFAULT_DH_PARAM_BITS = 1536
DEFAULT_OTP_SECRET_LEN = 16
DEFAULT_PUBLIC_IP_SERVER = 'http://ip.pritunl.com/json'
LOG_LIMIT = 100
EVENT_TTL = 60
RATE_LIMIT_SLEEP = 0.5
SHORT_URL_LEN = 5
SHORT_URL_CHARS = (string.ascii_lowercase + string.ascii_uppercase +
    string.digits).replace('l', '').replace('I', '').replace('O', '').replace(
    '0', '')
SUB_RESPONSE_TIMEOUT = 10
HTTP_REQUEST_TIMEOUT = 45
SERVER_REQUEST_QUEUE_SIZE = 512
USER_PAGE_COUNT = 10
IP_REGEX = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'

INFO = 'info'
WARNING = 'warning'
ERROR = 'error'

VERSION_NAME = 'version'
AUTH_USER_NAME = 'admin'
ORGS_DIR = 'organizations'
SERVERS_DIR = 'servers'
REQS_DIR = 'reqs'
KEYS_DIR = 'keys'
CERTS_DIR = 'certs'
USERS_DIR = 'users'
TEMP_DIR = 'temp'
EMPTY_TEMP_DIR = 'empty_temp'
OPENSSL_NAME = 'openssl.conf'
INDEX_NAME = 'index'
INDEX_ATTR_NAME = 'index.attr'
SERIAL_NAME = 'serial'
TLS_VERIFY_NAME = 'tls_verify.py'
USER_PASS_VERIFY_NAME = 'user_pass_verify.py'
OVPN_CONF_NAME = 'openvpn.conf'
OVPN_STATUS_NAME = 'status'
OVPN_CA_NAME = 'ca.crt'
IFC_POOL_NAME = 'ifc_pool'
DH_PARAM_NAME = 'dh_param.pem'
SERVER_USER_PREFIX = 'server_'
SERVER_CERT_NAME = 'server.crt'
SERVER_KEY_NAME = 'server.key'
AUTH_LOG_NAME = 'auth.log'
CONF_TEMP_EXT = '.tmp'
SERVER_NAME = 'server'
NODE_SERVER_NAME = 'node_server'

CA_CERT_ID = 'ca'
CERT_CA = 'ca'
CERT_SERVER = 'server'
CERT_CLIENT = 'client'

ORGS_UPDATED = 'organizations_updated'
USERS_UPDATED = 'users_updated'
LOG_UPDATED = 'log_updated'
SERVERS_UPDATED = 'servers_updated'
SERVER_ORGS_UPDATED = 'server_organizations_updated'
SERVER_OUTPUT_UPDATED = 'server_output_updated'

CERT_CONF = """[ default ]
ca = %s
root = %s
dir = %s

[ req ]
default_bits = %s
default_md = sha1
encrypt_key = no
utf8 = yes
string_mask = utf8only
prompt = no
distinguished_name = req_dn

[ req_dn ]
organizationName = $ca
commonName = %s

[ ca_req_ext ]
keyUsage = critical,keyCertSign,cRLSign
basicConstraints = critical,CA:true
subjectKeyIdentifier = hash

[ server_req_ext ]
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth,clientAuth
subjectKeyIdentifier = hash

[ client_req_ext ]
keyUsage = critical,digitalSignature,keyEncipherment
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash

[ ca ]
default_ca = root_ca

[ root_ca ]
database = $dir/index
serial = $dir/serial
new_certs_dir = $dir
certificate = $root/certs/ca.crt
private_key = $root/keys/ca.key
default_days = 3652
default_crl_days = 365
default_md = sha1
policy = ca_policy
crl_extensions = crl_ext

[ ca_policy ]
organizationName = match
commonName = supplied

[ ca_ext ]
keyUsage = critical,keyCertSign,cRLSign
basicConstraints = critical,CA:true
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always

[ crl_ext ]
authorityKeyIdentifier = keyid:always

[ server_ext ]
keyUsage = critical,digitalSignature,keyEncipherment
basicConstraints = CA:false
extendedKeyUsage = serverAuth,clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always

[ client_ext ]
keyUsage = critical,digitalSignature,keyEncipherment
basicConstraints = CA:false
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always
"""

MISSING_PARAMS = 'missing_params'
MISSING_PARAMS_MSG = 'Missing required parameters.'

AUTH_INVALID = 'auth_invalid'
AUTH_INVALID_MSG = 'Username or password is not valid.'

NETWORK_INVALID = 'network_invalid'
NETWORK_INVALID_MSG = 'Network address is not valid, format must be ' + \
    '"10.[0-255].[0-255].0/[8-24]" such as "10.12.32.0/24".'

LOCAL_NETWORK_INVALID = 'local_network_invalid'
LOCAL_NETWORK_INVALID_MSG = 'Local network address is not valid, ' + \
    'format must be "[0-255].[0-255].[0-255].[0-254]/[8-30]" such as ' + \
    '"10.0.0.0/8".'

PORT_INVALID = 'port_invalid'
PORT_INVALID_MSG = 'Port number is not valid, must be between 1 and 65535.'

INTERFACE_INVALID = 'interface_invalid'
INTERFACE_INVALID_MSG = 'Interface is not valid, must be ' + \
    '"tun[0-64]" example "tun0".'

PROTOCOL_INVALID = 'protocol_invalid'
PROTOCOL_INVALID_MSG = 'Protocol is not valid, must be "udp" or "tcp".'

NETWORK_IN_USE = 'network_in_use'
NETWORK_IN_USE_MSG = 'Network address is already in use.'

INTERFACE_IN_USE = 'interface_in_use'
INTERFACE_IN_USE_MSG = 'Tunnel interface is already in use.'

PORT_PROTOCOL_IN_USE = 'port_protocol_in_use'
PORT_PROTOCOL_IN_USE_MSG = 'Port and protocol is already in use.'

SERVER_NOT_OFFLINE = 'server_not_offline'
SERVER_NOT_OFFLINE_SETTINGS_MSG = 'Server must be offline to modify settings.'
SERVER_NOT_OFFLINE_ATTACH_ORG_MSG = 'Server must be offline to attach ' + \
    'an organization.'
SERVER_NOT_OFFLINE_DETACH_ORG_MSG = 'Server must be offline to detach ' + \
    'an organization.'

SERVER_INVALID = 'server_invalid'
SERVER_INVALID_MSG = 'Server is not valid.'

ORG_INVALID = 'organization_invalid'
ORG_INVALID_MSG = 'Organization is not valid.'

USER_INVALID = 'user_invalid'
USER_INVALID_MSG = 'User is not valid.'

OTP_CODE_INVALID = 'otp_code_invalid'
OTP_CODE_INVALID_MSG = 'OTP code is not valid.'

OVPN_SERVER_CONF = """port %s
proto %s
dev %s
ca %s
cert %s
key %s
tls-verify %s
dh %s
server %s
ifconfig-pool-persist %s
%s
max-clients 1024
keepalive 4 10
persist-tun
status %s 1
status-version 2
script-security 2
verb %s
mute %s
"""

OVPN_INLINE_SERVER_CONF = """port %s
proto %s
dev %s
tls-verify %s
server %s
ifconfig-pool-persist %s
%s
max-clients 1024
keepalive 4 10
persist-tun
status %s 1
status-version 2
script-security 2
verb %s
mute %s
"""

OVPN_CLIENT_CONF = """client
dev tun
proto %s
remote %s %s
nobind
persist-tun
ca %s
cert %s
key %s
verb 2
mute 3
"""

OVPN_INLINE_CLIENT_CONF = """client
dev tun
proto %s
remote %s %s
nobind
persist-tun
verb 2
mute 3
"""

# Script will run in python 2 and 3
TLS_VERIFY_SCRIPT = """#!/usr/bin/env python
import os
import sys
import json
import time
import traceback

VALID_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789='
auth_log_path = '%s'
def log_write(line):
    with open(auth_log_path, 'a') as auth_log_file:
        auth_log_file.write('[TIME=%%s]%%s\\n' %% (
            int(time.time()), line.rstrip('\\n')))

try:
    try:
        from urllib2 import urlopen
    except ImportError:
        from urllib.request import urlopen
    try:
        from urllib2 import Request
    except ImportError:
        from urllib.request import Request
    try:
        from urllib2 import HTTPError
    except ImportError:
        from urllib.error import HTTPError
    try:
        from socket import error as SocketError
    except ImportError:
        SocketError = ConnectionResetError

    # Get org and common_name from argv
    arg = sys.argv[2]
    arg = ''.join(x for x in arg if x in VALID_CHARS)
    o_index = arg.find('O=')
    cn_index = arg.find('CN=')
    if o_index < 0 or cn_index < 0:
        log_write('[FAILED] Missing organization or user id from args')
        exit(1)
    if o_index > cn_index:
        org = arg[o_index + 2:]
        common_name = arg[3:o_index]
    else:
        org = arg[2:cn_index]
        common_name = arg[cn_index + 3:]
    if not org or not common_name:
        log_write('[FAILED] Missing organization or user id from args')
        exit(1)

    try:
        request = Request('%s://localhost:%s' + \\
            '/server/%s/tls_verify')
        request.add_header('Content-Type', 'application/json')
        response = urlopen(request, json.dumps({
            'org_id': org,
            'user_id': common_name,
        }).encode('utf-8'))
        response = json.loads(response.read().decode('utf-8'))

        if not response['authenticated']:
            log_write('[FAILED] Invalid user id or organization id')
            exit(1)
    except HTTPError as error:
        log_write('[FAILED] Verification server returned error: %%s - %%s' %% (
            error.code, error.reason))
        exit(1)
    except SocketError:
        log_write('[FAILED] Verification server returned socket error')
        exit(1)
except SystemExit:
    raise
except:
    log_write('[EXCEPTION] ' + traceback.format_exc())
    raise

exit(0)
"""

# Script will run in python 2 and 3
USER_PASS_VERIFY_SCRIPT = """#!/usr/bin/env python
import os
import sys
import json
import time
import traceback

VALID_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789='
auth_log_path = '%s'
def log_write(line):
    with open(auth_log_path, 'a') as auth_log_file:
        auth_log_file.write('[TIME=%%s]%%s\\n' %% (
            int(time.time()), line.rstrip('\\n')))

try:
    try:
        from urllib2 import urlopen
    except ImportError:
        from urllib.request import urlopen
    try:
        from urllib2 import Request
    except ImportError:
        from urllib.request import Request
    try:
        from urllib2 import HTTPError
    except ImportError:
        from urllib.error import HTTPError
    try:
        from socket import error as SocketError
    except ImportError:
        SocketError = ConnectionResetError

    # Get org and common_name from environ
    tls_env = os.environ.get('tls_id_0')
    if not tls_env:
        log_write('[FAILED] Missing organization or user id from environ')
        raise AttributeError('Missing organization or user id from environ')
    tls_env = ''.join(x for x in tls_env if x in VALID_CHARS)
    o_index = tls_env.find('O=')
    cn_index = tls_env.find('CN=')
    if o_index < 0 or cn_index < 0:
        log_write('[FAILED] Missing organization or user id from environ')
        raise AttributeError('Missing organization or user id from environ')
    if o_index > cn_index:
        org = tls_env[o_index + 2:]
        common_name = tls_env[3:o_index]
    else:
        org = tls_env[2:cn_index]
        common_name = tls_env[cn_index + 3:]
    if not org or not common_name:
        log_write('[FAILED] Missing organization or user id from environ')
        raise AttributeError('Missing organization or user id from environ')

    # Get username and password from input file
    with open(sys.argv[1], 'r') as auth_file:
        username, password = [x.strip() for x in auth_file.readlines()[:2]]
    password = password[:6]
    if not password.isdigit():
        log_write('[ORG=%%s][UID=%%s][FAILED] Authenticator code invalid' %% (
            org, common_name))
        raise TypeError('Authenticator code is invalid')

    try:
        request = Request('%s://localhost:%s' + \\
            '/server/%s/otp_verify')
        request.add_header('Content-Type', 'application/json')
        response = urlopen(request, json.dumps({
            'org_id': org,
            'user_id': common_name,
            'otp_code': password,
        }).encode('utf-8'))
        response = json.loads(response.read().decode('utf-8'))

        if not response['authenticated']:
            log_write('[FAILED] Invalid user id or organization id')
            exit(1)
    except HTTPError as error:
        log_write('[FAILED] Verification server returned error: %%s - %%s' %% (
            error.code, error.reason))
        exit(1)
    except SocketError:
        log_write('[FAILED] Verification server returned socket error')
        exit(1)
except SystemExit:
    raise
except:
    log_write('[EXCEPTION] ' + traceback.format_exc())
    raise

exit(0)
"""
