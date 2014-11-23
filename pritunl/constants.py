import string
import datetime

APP_NAME = 'pritunl'
APP_NAME_FORMATED = 'Pritunl'
CONF_FILENAME = '%s.conf' % APP_NAME

SAVED = 'saved'
UNSAVED = 'unsaved'

START = 'start'
STOP = 'stop'
RESTART = 'restart'

RUNNING = 'running'
PAUSED = 'paused'
STOPPED = 'stopped'

PENDING = 'pending'
COMMITTED = 'committed'
ROLLBACK = 'rollback'
COMPLETE = 'complete'
ERROR = 'error'
UPDATE = 'update'

ONLINE = 'online'
OFFLINE = 'offline'

VERY_LOW = 0
LOW = 1
NORMAL = 2
HIGH = 3
VERY_HIGH = 4

LOW_CPU = 0
NORMAL_CPU = 1
HIGH_CPU = 2

BULK_EXECUTE = 'bulk_execute'

LOG_DEBUG_TYPES = {
}

MONGO_ACTION_METHODS = {
    'update',
    'remove',
    'find',
    'find_one',
    'find_and_modify',
    'replace_one',
    'update_one',
    'remove_one',
    'upsert',
}

OK = 'ok'
DISABLED = 'disabled'

NAME_SAFE_CHARS = {
    '-', '=', '_', '@', '.', ':', '/',
    '!', '#', '$', '%', '&', '*', '+',
    '?', '^', '`', '{', '|', '}', '~',
}

VALID_CHARS = {
    'a', 'b', 'c', 'd', 'e', 'f', 'g',
    'h', 'i', 'j', 'k', 'l', 'm', 'n',
    'o', 'p', 'q', 'r', 's', 't', 'u',
    'v', 'w', 'x', 'y', 'z', 'A', 'B',
    'C', 'D', 'E', 'F', 'G', 'H', 'I',
    'J', 'K', 'L', 'M', 'N', 'O', 'P',
    'Q', 'R', 'S', 'T', 'U', 'V', 'W',
    'X', 'Y', 'Z', '0', '1', '2', '3',
    '4', '5', '6', '7', '8', '9', '=',
}

GROUP_MONGO = 'mongo'
GROUP_FILE = 'file'
GROUP_LOCAL = 'local'

SETTINGS_RESERVED = {
    'groups',
    'collection',
    'commit',
    'load',
    'on_msg',
    'start',
}

DEFAULT_BIND_ADDR = '0.0.0.0'
DEFAULT_PORT = 9700
DEFAULT_USERNAME = 'pritunl'
DEFAULT_PASSWORD = 'pritunl'
DEFAULT_CONF_PATH = '/etc/pritunl.conf'
DEFAULT_WWW_PATH = '/usr/share/pritunl/www'
SUBSCRIPTION_SERVER = 'https://app.pritunl.com/subscription'
SUBSCRIPTION_UPDATE_RATE = 900
POSTMARK_SERVER = 'https://api.postmarkapp.com/email'
ENV_PREFIX = APP_NAME
SHORT_URL_CHARS = (string.ascii_lowercase + string.ascii_uppercase +
    string.digits).replace('l', '').replace('I', '').replace('O', '').replace(
    '0', '')
SUB_RESPONSE_TIMEOUT = 10
CLIENT_CONF_VER = 1
MONGO_MESSAGES_SIZE = 100000
MONGO_MESSAGES_MAX = 2048
MONGO_CONNECT_TIMEOUT = 2000
AUTH_SIG_STRING_MAX_LEN = 10240
SOCKET_BUFFER = 1024
OUTPUT_DELAY = 0.25
RANDOM_ERROR_RATE = 0
IP_REGEX = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
VALID_DH_PARAM_BITS = (1024, 1536, 2048, 3072, 4096)
STATIC_FILE_EXTENSIONS = {
    '.css',
    '.eot',
    '.html',
    '.ico',
    '.js',
    '.less',
    '.png',
    '.svg',
    '.ttf',
    '.txt',
    '.woff',
}

INFO = 'info'
WARNING = 'warning'
ERROR = 'error'

ADAPTIVE = 'adaptive'
VERSION_NAME = 'version'
ORGS_DIR = 'organizations'
SERVERS_DIR = 'servers'
REQS_DIR = 'reqs'
KEYS_DIR = 'keys'
CERTS_DIR = 'certs'
USERS_DIR = 'users'
DH_POOL_DIR = 'dh_param_pool'
TEMP_DIR = 'temp'
EMPTY_TEMP_DIR = 'empty_temp'
OPENSSL_NAME = 'openssl.conf'
INDEX_NAME = 'index'
INDEX_ATTR_NAME = 'index.attr'
SERIAL_NAME = 'serial'
OVPN_CONF_NAME = 'openvpn.conf'
OVPN_CA_NAME = 'ca.crt'
DH_PARAM_NAME = 'dh_param.pem'
TLS_AUTH_NAME = 'tls_auth.key'
IP_POOL_NAME = 'ip_pool'
SERVER_USER_PREFIX = 'server_'
HOST_USER_PREFIX = 'host_'
SERVER_CERT_NAME = 'server.crt'
SERVER_KEY_NAME = 'server.key'
SERVER_CONF_NAME = 'server.conf'
MANAGEMENT_SOCKET_NAME = 'pritunl_%s.sock'
KEY_VIEW_NAME = 'key_view.html'
DBCONF_NAME = 'dbconf.html'
UPGRADE_NAME = 'upgrade.html'
CONF_TEMP_EXT = '.tmp'
LOG_ARCHIVE_NAME = 'pritunl_log'
SHUT_DOWN = 'shut_down'

SERVER = 'server'
NODE_SERVER = 'node_server'

ALL_TRAFFIC = 'all_traffic'
LOCAL_TRAFFIC = 'local_traffic'
VPN_TRAFFIC = 'vpn_traffic'

CERT_CA = 'ca'
CERT_SERVER = 'server'
CERT_CLIENT = 'client'
CERT_SERVER_POOL = 'server_pool'
CERT_CLIENT_POOL = 'client_pool'

ORG_DEFAULT = 'default'
ORG_POOL = 'pool'

ORGS_UPDATED = 'organizations_updated'
USERS_UPDATED = 'users_updated'
LOG_UPDATED = 'log_updated'
HOSTS_UPDATED = 'hosts_updated'
SERVERS_UPDATED = 'servers_updated'
SERVER_ORGS_UPDATED = 'server_organizations_updated'
SERVER_HOSTS_UPDATED = 'server_hosts_updated'
SERVER_LINKS_UPDATED = 'server_links_updated'
SERVER_OUTPUT_UPDATED = 'server_output_updated'
SERVER_LINK_OUTPUT_UPDATED = 'server_link_output_updated'
SUBSCRIPTION_PREMIUM_ACTIVE = 'subscription_premium_active'
SUBSCRIPTION_ENTERPRISE_ACTIVE = 'subscription_enterprise_active'
SUBSCRIPTION_NONE_INACTIVE = 'subscription_none_inactive'
SUBSCRIPTION_PREMIUM_INACTIVE = 'subscription_premium_inactive'
SUBSCRIPTION_ENTERPRISE_INACTIVE = 'subscription_enterprise_inactive'
THEME_LIGHT = 'theme_light'
THEME_DARK = 'theme_dark'

BASH_COLORS = [
    '92',
    '93',
    '94',
    '95',
    '96',
    '91',
    '90',
]

VALID_IP_ENDPOINTS = {
    '5', '9', '13', '17', '21', '25', '29', '33', '37', '41', '45', '49',
    '53', '57', '61', '65', '69', '73', '77', '81', '85', '89', '93', '97',
    '101', '105', '109', '113', '117', '121', '125', '129', '133', '137',
    '141', '145', '149', '153', '157', '161', '165', '169', '173', '177',
    '181', '185', '189', '193', '197', '201', '205', '209', '213', '217',
    '221', '225', '229', '233', '237', '241', '245', '249', '253',
}

OPENSSL_HEARTBLEED = {
    'OpenSSL 1.0.1-fips-beta1 03 Jan 2012',
    'OpenSSL 1.0.1-beta1 03 Jan 2012',
    'OpenSSL 1.0.1-fips-beta2 19 Jan 2012',
    'OpenSSL 1.0.1-beta2 19 Jan 2012',
    'OpenSSL 1.0.1-fips-beta3 23 Feb 2012',
    'OpenSSL 1.0.1-beta3 23 Feb 2012',
    'OpenSSL 1.0.1-fips 14 Mar 2012',
    'OpenSSL 1.0.1 14 Mar 2012',
    'OpenSSL 1.0.1a-fips 19 Apr 2012',
    'OpenSSL 1.0.1a 19 Apr 2012',
    'OpenSSL 1.0.1b-fips 26 Apr 2012',
    'OpenSSL 1.0.1b 26 Apr 2012',
    'OpenSSL 1.0.1c-fips 10 May 2012',
    'OpenSSL 1.0.1c 10 May 2012',
    'OpenSSL 1.0.1d-fips 5 Feb 2013',
    'OpenSSL 1.0.1d 5 Feb 2013',
    'OpenSSL 1.0.1e-fips 11 Feb 2013',
    'OpenSSL 1.0.1e 11 Feb 2013',
    'OpenSSL 1.0.1f-fips 6 Jan 2014',
    'OpenSSL 1.0.1f 6 Jan 2014',
    'OpenSSL 1.0.2-beta1-fips 24 Feb 2014',
    'OpenSSL 1.0.2-beta1 24 Feb 2014',
}
OPENSSL_HEARTBLEED_BUILD_DATE = datetime.date(2014, 4, 7)

CERT_CONF = """[ default ]
[ req ]
default_bits = %s
default_md = sha1
encrypt_key = no
utf8 = yes
string_mask = utf8only
prompt = no
distinguished_name = req_dn

[ req_dn ]
organizationName = %s
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
database = %s
serial = %s
new_certs_dir = %s
certificate = %s
private_key = %s
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

DNS_SERVER_INVALID = 'dns_server_invalid'
DNS_SERVER_INVALID_MSG = 'DNS server is not valid, ' + \
    'format must be "[0-255].[0-255].[0-255].[0-255]" such as ' + \
    '"8.8.8.8".'

PORT_INVALID = 'port_invalid'
PORT_INVALID_MSG = 'Port number is not valid, must be between 1 and 65535.'

DH_PARAM_BITS_INVALID = 'dh_param_bits_invalid'
DH_PARAM_BITS_INVALID_MSG = 'DH param bits are not valid, must ' + \
    '1024, 1536, 2048, 2048, 3072 or 4096.'

MODE_INVALID = 'mode_invalid'
MODE_INVALID_MSG = 'Mode is not valid, must be "all_traffic" or ' + \
    '"local_traffic" or "vpn_traffic".'

PROTOCOL_INVALID = 'protocol_invalid'
PROTOCOL_INVALID_MSG = 'Protocol is not valid, must be "udp" or "tcp".'

CIPHER_INVALID = 'cipher_invalid'
CIPHER_INVALID_MSG = 'Encryption cipher is invalid.'

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
SERVER_NOT_OFFLINE_LINK_SERVER_MSG = 'Server must be offline to link ' + \
    'a server.'
SERVER_NOT_OFFLINE_UNLINK_SERVER_MSG = 'Server must be offline to unlink ' + \
    'a server.'

SERVER_INVALID = 'server_invalid'
SERVER_INVALID_MSG = 'Server is not valid.'

NODE_API_KEY_INVLID = 'node_api_key_invlid'
NODE_API_KEY_INVLID_MSG = 'Node server api key is invalid.'

NODE_CONNECTION_ERROR = 'node_connection_error'
NODE_CONNECTION_ERROR_MSG = 'Failed to connect to node server.'

ORG_INVALID = 'organization_invalid'
ORG_INVALID_MSG = 'Organization is not valid.'

USER_INVALID = 'user_invalid'
USER_INVALID_MSG = 'User is not valid.'

USER_TYPE_INVALID = 'user_type_invalid'
USER_TYPE_INVALID_MSG = 'User type is not valid.'

OTP_CODE_INVALID = 'otp_code_invalid'
OTP_CODE_INVALID_MSG = 'OTP code is not valid.'

EMAIL_NOT_CONFIGURED = 'email_not_configured'
EMAIL_NOT_CONFIGURED_MSG = 'Required email settings have not been ' + \
    'configured, please open settings and configure email.'

EMAIL_FROM_INVALID = 'email_from_invalid'
EMAIL_FROM_INVALID_MSG = 'Postmark sender signature not defined ' + \
    'for from address.'

EMAIL_API_KEY_INVALID = 'email_api_key_invalid'
EMAIL_API_KEY_INVALID_MSG = 'Postmark email api key invalid.'

SUBSCRIPTION_SERVER_ERROR = 'subscription_server_error'
SUBSCRIPTION_SERVER_ERROR_MSG = 'Unable to connect to ' + \
    'subscription server, please try again later.'

MONGODB_URI_INVALID = 'mongodb_uri_invalid'
MONGODB_URI_INVALID_MSG = 'MongoDB URI is invalid.'

MONGODB_CONNECT_ERROR = 'mongodb_connect_error'
MONGODB_CONNECT_ERROR_MSG = 'Unable to connect to MongoDB server.'

RANDOM_ONE = (
    'snowy',
    'restless',
    'calm',
    'ancient',
    'summer',
    'evening',
    'guarded',
    'lively',
    'thawing',
    'autumn',
    'thriving',
    'patient',
    'winter',
)
RANDOM_TWO = (
    'waterfall',
    'meadow',
    'skies',
    'waves',
    'fields',
    'stars',
    'dreams',
    'refuge',
    'forest',
    'plains',
    'waters',
    'plateau',
    'thunder',
)

CIPHERS = {
    'none': 'cipher none',
    'bf128': 'cipher BF-CBC',
    'bf256': 'cipher BF-CBC\nkeysize 256',
    'aes128': 'cipher AES-128-CBC',
    'aes192': 'cipher AES-192-CBC',
    'aes256': 'cipher AES-256-CBC',
}

JUMBO_FRAMES = {
    False: '',
    True: 'tun-mtu 9000\nfragment 0\nmssfix 0\n',
}

OVPN_INLINE_SERVER_CONF = """port %s
proto %s
dev %s
server %s
management %s unix
management-client-auth
auth-user-pass-optional
topology subnet
client-to-client
max-clients 2048
ping 10
ping-restart 80
push "ping 10"
push "ping-restart 60"
persist-tun
%s
status-version 2
script-security 2
verb %s
mute %s
"""

OVPN_INLINE_CLIENT_CONF = """# %s
setenv UV_ID %s
setenv UV_NAME %s
client
dev tun
proto %s
%s
nobind
persist-tun
%s
verb 2
mute 3
push-peer-info
ping 10
ping-restart 60
server-poll-timeout 3
reneg-sec 2592000
sndbuf 100000
rcvbuf 100000
remote-cert-tls server
"""

OVPN_INLINE_LINK_CONF = """client
setenv UV_ID %s
setenv UV_NAME %s
dev %s
proto %s
%s
nobind
persist-tun
%s
verb %s
mute %s
ping 10
ping-restart 60
push-peer-info
server-poll-timeout 3
reneg-sec 2592000
sndbuf 100000
rcvbuf 100000
remote-cert-tls server
"""
