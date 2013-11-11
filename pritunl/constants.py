APP_NAME = 'pritunl'
APP_NAME_FORMATED = 'Pritunl'
CONF_FILENAME = '%s.conf' % APP_NAME

PUBLIC_IP_SERVER = 'http://ip.pritunl.com/'

SAVED = 'saved'
UNSAVED = 'unsaved'

START = 'start'
STOP = 'stop'
RESTART = 'restart'

NAME_SAFE_CHARS = ['-', '_', '@', '.']

KEY_LINK_TIMEOUT = 3600
DEFAULT_PRIMARY_INTERFACE = 'eth0'
DEFAULT_SESSION_TIMEOUT = 86400
DEFAULT_PASSWORD = 'admin'
PASSWORD_SALT = '2511cebca93d028393735637bbc8029207731fcf'
DEFAULT_DB_PATH = '/var/lib/pritunl/pritunl.db'
DEFAULT_WWW_PATH = '/usr/share/pritunl/www'
DEFAULT_DATA_PATH = '/var/lib/pritunl'
DEFAULT_LOG_LIMIT = 20
DEFAULT_KEY_BITS = 4096
DEFAULT_DH_PARAM_BITS = 1536
DEFAULT_OTP_SECRET_LEN = 16

INFO = 'info'
WARNING = 'warning'
ERROR = 'error'

VERSION_NAME = 'version'
ORGS_DIR = 'organizations'
SERVERS_DIR = 'servers'
REQS_DIR = 'reqs'
KEYS_DIR = 'keys'
CERTS_DIR = 'certs'
USERS_DIR = 'users'
INDEXED_CERTS_DIR = 'indexed_certs'
TEMP_DIR = 'temp'
EMPTY_TEMP_DIR = 'empty_temp'
INDEX_NAME = 'index'
SERIAL_NAME = 'serial'
CRL_NAME = 'ca.crl'
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
OTP_JSON_NAME = 'otp.json'
AUTH_LOG_NAME = 'auth.log'

CA_CERT_ID = 'ca'
CERT_CA = 'ca'
CERT_SERVER = 'server'
CERT_CLIENT = 'client'

UNSPECIFIED = 'unspecified'
KEY_COMPROMISE = 'keyCompromise'
CA_COMPROMISE = 'CACompromise'
AFFILIATION_CHANGED = 'affiliationChanged'
SUPERSEDED = 'superseded'
CESSATION_OF_OPERATION = 'cessationOfOperation'
CERTIFICATE_HOLD = 'certificateHold'
REMOVE_FROM_CRL = 'removeFromCRL'

ORGS_UPDATED = 'organizations_updated'
USERS_UPDATED = 'users_updated'
LOG_UPDATED = 'log_updated'
SERVERS_UPDATED = 'servers_updated'
SERVER_ORGS_UPDATED = 'server_organizations_updated'
SERVER_OUTPUT_UPDATED = 'server_output_updated'

CERT_CONF = """[ default ]
ca = %s
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
new_certs_dir = $dir/indexed_certs
certificate = $dir/certs/ca.crt
private_key = $dir/keys/ca.key
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

AUTH_NOT_VALID = 'auth_not_valid'
AUTH_NOT_VALID_MSG = 'Username or password is not valid.'

NETWORK_NOT_VALID = 'network_not_valid'
NETWORK_NOT_VALID_MSG = 'Network address is not valid, format must be ' + \
    '"10.[0-255].[0-255].0/[8-24]" such as "10.12.32.0/24".'

LOCAL_NETWORK_NOT_VALID = 'local_network_not_valid'
LOCAL_NETWORK_NOT_VALID_MSG = 'Local network address is not valid, ' + \
    'format must be "[0-255].[0-255].[0-255].[0-254]/[8-30]" such as ' + \
    '"10.0.0.0/8".'

PORT_NOT_VALID = 'port_not_valid'
PORT_NOT_VALID_MSG = 'Port number is not valid, must be between 1 and 65535.'

INTERFACE_NOT_VALID = 'interface_not_valid'
INTERFACE_NOT_VALID_MSG = 'Interface is not valid, must be ' + \
    '"tun[0-64]" example "tun0".'

PROTOCOL_NOT_VALID = 'protocol_not_valid'
PROTOCOL_NOT_VALID_MSG = 'Protocol is not valid, must be "udp" or "tcp".'

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
push "%s"
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

# Script will run in python 2 and 3
TLS_VERIFY_SCRIPT = """#!/usr/bin/env python
import os
import sys
VALID_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789='
DATA_PATH = '%s'
ORGS_DIR = '%s'
AUTH_LOG_NAME = '%s'
INDEX_NAME = '%s'
auth_log_path = os.path.join(DATA_PATH, AUTH_LOG_NAME)
orgs_path = os.path.join(DATA_PATH, ORGS_DIR)

def log_write(line):
    with open(auth_log_path, 'a') as auth_log_file:
        auth_log_file.write('[TIME=%%s]%%s\\n' %% (int(time.time()), line))

# Get org and common_name from argv
arg = sys.argv[2]
arg = ''.join(x for x in arg if x in VALID_CHARS)
o_index = arg.find('O=')
cn_index = arg.find('CN=')
if o_index < 0 or cn_index < 0:
    log_write('[FAILED] Missing organization or user id from args')
    raise AttributeError('Missing organization or user id from args')
if o_index > cn_index:
    org = arg[o_index + 2:]
    common_name = arg[3:o_index]
else:
    org = arg[2:cn_index]
    common_name = arg[cn_index + 3:]
if not org or not common_name:
    log_write('[FAILED] Missing organization or user id from args')
    raise AttributeError('Missing organization or user id from args')

# Check that common_name is valid
with open(os.path.join(orgs_path, org, INDEX_NAME), 'r') as index_file:
    for line in index_file.readlines():
        if 'O=%%s' %% org in line and 'CN=%%s' %% common_name in line:
            if line[0] == 'V':
                exit(0)
            log_write('[ORG=%%s][UID=%%s][FAILED] User id is not valid' %% (
                org, common_name))
            raise AttributeError('User id is not valid')
log_write('[ORG=%%s][UID=%%s][FAILED] User id not found' %% (
    org, common_name))
raise LookupError('Common name not found')
"""

# Script will run in python 2 and 3
USER_PASS_VERIFY_SCRIPT = """#!/usr/bin/env python
import os
import sys
import time
import struct
import hmac
import hashlib
import base64
import json
VALID_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789='
DATA_PATH = '%s'
ORGS_DIR = '%s'
USERS_DIR = '%s'
TEMP_DIR = '%s'
AUTH_LOG_NAME = '%s'
OTP_JSON_NAME = '%s'
auth_log_path = os.path.join(DATA_PATH, AUTH_LOG_NAME)
orgs_path = os.path.join(DATA_PATH, ORGS_DIR)

def log_write(line):
    with open(auth_log_path, 'a') as auth_log_file:
        auth_log_file.write('[TIME=%%s]%%s\\n' %% (int(time.time()), line))

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
    log_write('[ORG=%%s][UID=%%s][FAILED] Authenticator code is invalid' %% (
        org, common_name))
    raise TypeError('Authenticator code is invalid')

# Get secretkey from user conf
secretkey = None
with open(os.path.join(orgs_path, org, USERS_DIR,
        '%%s.conf' %% common_name), 'r') as user_conf_file:
    for line in user_conf_file.readlines():
        if 'otp_secret=' in line:
            secretkey = line.strip().replace('otp_secret=', '')
            break
if not secretkey:
    log_write('[ORG=%%s][UID=%%s][FAILED] Missing otp_secret in user conf' %% (
        org, common_name))
    raise AttributeError('Missing otp_secret in user conf')

# Check password with secretkey
padding = 8 - len(secretkey) %% 8
if padding != 8:
    secretkey = secretkey.ljust(len(secretkey) + padding, '=')
secretkey = base64.b32decode(secretkey.upper())
valid_codes = []
epoch = int(time.time() / 30)
for epoch_offset in range(-1, 2):
    value = struct.pack('>q', epoch + epoch_offset)
    hmac_hash = hmac.new(secretkey, value, hashlib.sha1).digest()
    if isinstance(hmac_hash, str):
        offset = ord(hmac_hash[-1]) & 0x0F
    else:
        offset = hmac_hash[-1] & 0x0F
    truncated_hash = hmac_hash[offset:offset + 4]
    truncated_hash = struct.unpack('>L', truncated_hash)[0]
    truncated_hash &= 0x7FFFFFFF
    truncated_hash %%= 1000000
    valid_codes.append('%%06d' %% truncated_hash)
if password not in valid_codes:
    log_write('[ORG=%%s][UID=%%s][FAILED] Authenticator code is invalid' %% (
        org, common_name))
    raise TypeError('Authenticator code is invalid')

# Check for double used keys
otp_json_path = os.path.join(orgs_path, org, TEMP_DIR, OTP_JSON_NAME)
new_key = ('%%s-%%s' %% (common_name, password)).encode('utf-8')
sha_hash = hashlib.sha256()
sha_hash.update(new_key)
new_key = sha_hash.hexdigest()
data = {}
if os.path.isfile(otp_json_path):
    with open(otp_json_path, 'r') as otp_json_file:
        data = json.loads(otp_json_file.read().strip())
cur_time = int(time.time())
for key, value in list(data.items()):
    if value + 120 < cur_time:
        data.pop(key)
if new_key in data:
    log_write(('[ORG=%%s][UID=%%s][FAILED] Authenticator code has ' +
        'already been used') %% (org, common_name))
    raise TypeError('Authenticator code has already been used')
data[new_key] = cur_time
with open(otp_json_path, 'w') as otp_json_file:
    otp_json_file.write(json.dumps(data))
exit(0)
"""
