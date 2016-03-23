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
UPDATE = 'update'

ONLINE = 'online'
OFFLINE = 'offline'

TUNNEL = 'tunnel'
BRIDGE = 'bridge'

PIN_REQUIRED = 'required'
PIN_OPTIONAL = 'optional'
PIN_DISABLED = 'disabled'

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

AWS_REGIONS = {
    'us-east-1',
    'us-west-1',
    'us-west-2',
    'eu-west-1',
    'eu-central-1',
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-southeast-1',
    'ap-southeast-2',
    'sa-east-1',
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

DEMO_LOG_ENTRIES = [
    {
        'id': '56610a2ab0e7307d6a553175',
        'message': 'Started server "West".',
        'timestamp': 1449055271,
    },
    {
        'id': '56610a2ab0e7307d6a55316d',
        'message': 'Started server "East".',
        'timestamp': 1449054471,
    },
    {
        'id': '566106c3b0e7307d6a552ee0',
        'message': 'Created server "West".',
        'timestamp': 1449053618,
    },
    {
        'id': '566106bab0e730539212b4a1',
        'message': 'Created server "East".',
        'timestamp': 1449052968,
    },
    {
        'id': '566106bab0e730539212b4a0',
        'message': 'Created 2 new users.',
        'timestamp': 1449050591,
    },
    {
        'id': '565e8be6b0e730539211c695',
        'message': 'Created 30 new users.',
        'timestamp': 1449049318,
    },
    {
        'id': '565e8bddb0e730519bdf51e1',
        'message': 'Created 30 new users.',
        'timestamp': 1449048575,
    },
    {
        'id': '565e8bddb0e730519bdf51e0',
        'message': 'Created new organization "Links".',
        'timestamp': 1449047691,
    },
    {
        'id': '565e8babb0e730519bdf50fc',
        'message': 'Created new organization "Operations".',
        'timestamp': 1449046292,
    },
    {
        'id': '565e8ba7b0e73045a8aa5bac',
        'message': 'Created new organization "Developers".',
        'timestamp': 1449045128,
    },
    {
        'id': '565e8ba7b0e73045a8aa5bab',
        'message': 'Web server started.',
        'timestamp': 1449044723,
    },
    {
        'id': '565e87eeb0e73045a8aa5885',
        'message': 'Web server started.',
        'timestamp': 1449043571,
    },
]

DEMO_AUDIT_EVENTS = [
    {
        'message': 'User connected to "east"',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449053618,
        'type': 'user_connection',
    },
    {
        'message': 'User temporary profile links created from web console',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449052968,
        'type': 'user_profile',
    },
    {
        'message': 'User created with single sign-on',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449051783,
        'type': 'user_profile',
    },
]

DEMO_ADMIN_AUDIT_EVENTS = [
    {
        'message': 'Single sign-on settings changed',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449054365,
        'type': 'admin_settings',
    },
    {
        'message': 'Administrator username changed',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449053618,
        'type': 'admin_settings',
    },
    {
        'message': 'Administrator password changed',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449052968,
        'type': 'admin_settings',
    },
    {
        'message': 'Administrator login successful',
        'remote_addr': '12.34.56.78',
        'timestamp': 1449051783,
        'type': 'admin_auth',
    },
]

DEMO_OUTPUT = [
    '[us-east] Mon Dec 28 04:01:00 2015 OpenVPN 2.3.6 x86_64-redhat' +
        '-linux-gnu [SSL (OpenSSL)] [LZO] [EPOLL] [PKCS11] [MH] [IPv6] ' +
        'built on Dec 10 2014',
    '[us-east] Mon Dec 28 04:01:00 2015 library versions: OpenSSL 1.0.1k-' +
        'fips 8 Jan 2015, LZO 2.08',
    '[us-east] Mon Dec 28 04:01:00 2015 Control Channel Authentication: ' +
        'tls-auth using INLINE static key file',
    '[us-east] Mon Dec 28 04:01:00 2015 TUN/TAP device tun19 opened',
    '[us-east] Mon Dec 28 04:01:00 2015 do_ifconfig, tt->ipv6=0, ' +
        'tt->did_ifconfig_ipv6_setup=0',
    '[us-east] Mon Dec 28 04:01:00 2015 /sbin/ip link set dev ' +
        'tun19 up mtu 1500',
    '[us-east] Mon Dec 28 04:01:00 2015 /sbin/ip addr add dev ' +
        'tun19 10.100.0.1/16 broadcast 10.100.255.255',
    '[us-east] Mon Dec 28 04:01:00 2015 UDPv4 link local (bound): [undef]',
    '[us-east] Mon Dec 28 04:01:00 2015 UDPv4 link remote: [undef]',
    '[us-east] Mon Dec 28 04:01:00 2015 Initialization Sequence Completed',
]

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
SUBSCRIPTION_UPDATE_RATE = 900
ENV_PREFIX = APP_NAME
SHORT_URL_CHARS = (string.ascii_lowercase + string.ascii_uppercase +
    string.digits).replace('l', '').replace('I', '').replace('O', '').replace(
    '0', '')
SUB_RESPONSE_TIMEOUT = 10
CLIENT_CONF_VER = 1
MONGO_MESSAGES_SIZE = 100000
MONGO_MESSAGES_MAX = 2048
MONGO_CONNECT_TIMEOUT = 15000
AUTH_SIG_STRING_MAX_LEN = 10240
SOCKET_BUFFER = 1024
OUTPUT_DELAY = 0.25
RANDOM_ERROR_RATE = 0
IP_REGEX = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
VALID_DH_PARAM_BITS = (1024, 1536, 2048, 3072, 4096)
AUTH_SERVER = 'https://auth.pritunl.com'
ONELOGIN_URL = 'https://api.onelogin.com'
NTP_SERVER = 'ntp.ubuntu.com'
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
    '.woff2',
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
SETUP_SERVER_CERT_NAME = 'setup_server.crt'
SETUP_SERVER_KEY_NAME = 'setup_server.key'
SERVER_CONF_NAME = 'server.conf'
MANAGEMENT_SOCKET_NAME = 'pritunl_%s.sock'
KEY_VIEW_NAME = 'key_view.html'
KEY_VIEW_DARK_NAME = 'key_view_dark.html'
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

ALL = 'all'

LOCAL_AUTH = 'local'
DUO_AUTH = 'duo'
GOOGLE_AUTH = 'google'
GOOGLE_DUO_AUTH = 'google_duo'
SLACK_AUTH = 'slack'
SLACK_DUO_AUTH = 'slack_duo'
SAML_AUTH = 'saml'
SAML_DUO_AUTH = 'saml_duo'
SAML_OKTA_AUTH = 'saml_okta'
SAML_OKTA_DUO_AUTH = 'saml_okta_duo'
SAML_ONELOGIN_AUTH = 'saml_onelogin'
SAML_ONELOGIN_DUO_AUTH = 'saml_onelogin_duo'
RADIUS_AUTH = 'radius'

SETTINGS_UPDATED = 'settings_updated'
ADMINS_UPDATED = 'administrators_updated'
ORGS_UPDATED = 'organizations_updated'
USERS_UPDATED = 'users_updated'
LOG_UPDATED = 'log_updated'
SYSTEM_LOG_UPDATED = 'system_log_updated'
HOSTS_UPDATED = 'hosts_updated'
SERVERS_UPDATED = 'servers_updated'
SERVER_ROUTES_UPDATED = 'server_routes_updated'
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

CERT_CONF = """\
[ default ]
[ req ]
default_bits = %s
default_md = %s
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
default_md = %s
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

DEMO_BLOCKED = 'demo_blocked'
DEMO_BLOCKED_MSG = 'Not aviaible in demo.'

AUTH_INVALID = 'auth_invalid'
AUTH_INVALID_MSG = 'Authentication credentials are not valid.'

AUTH_DISABLED = 'auth_disabled'
AUTH_DISABLED_MSG = 'Authentication credentials are disabled.'

AUTH_OTP_REQUIRED = 'auth_otp_required'
AUTH_OTP_REQUIRED_MSG = 'Two-factor authentication required.'

ACME_ERROR = 'acme_error'
ACME_ERROR_MSG = 'Error getting LetsEncrypt certificate check ' + \
    'the logs for more information.'

NETWORK_INVALID = 'network_invalid'
NETWORK_INVALID_MSG = 'Network address is not valid, format must be ' + \
    '"[10,172,192].[0-255,16-31,168].[0-255].0/[8-24]" ' + \
    'such as "10.12.32.0/24".'

BRIDGE_NETWORK_INVALID = '_bridge_network_invalid'
BRIDGE_NETWORK_INVALID_MSG = 'Bridge network start and end must be inside the ' + \
    'server network.'

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

PORT_RESERVED = 'port_reserved'
PORT_RESERVED_MSG = 'Port number is reserved and cannot be used.'

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

HASH_INVALID = 'hash_invalid'
HASH_INVALID_MSG = 'Hash algorithm is invalid.'

NETWORK_LINK_INVALID = 'network_link_invalid'
NETWORK_LINK_INVALID_MSG = 'Network link is not a valid network address.'

NETWORK_LINK_NOT_OFFLINE = 'network_link_not_offline'
NETWORK_LINK_NOT_OFFLINE_MSG = 'All attached servers must be offline to ' + \
    'add a network link.'

PIN_INVALID = 'pin_invalid'
PIN_INVALID_MSG = 'Current pin is invalid.'

PIN_NOT_DIGITS = 'pin_not_digits'
PIN_NOT_DIGITS_MSG = 'Pin must contain only digits.'

PIN_TOO_SHORT = 'pin_too_short'
PIN_TOO_SHORT_MSG = 'Pin is not long enough.'

PIN_IS_DISABLED = 'pin_disabled'
PIN_IS_DISABLED_MSG = 'Pin is disabled.'

PIN_RADIUS = 'pin_radius'
PIN_RADIUS_MSG = 'Pin cannot be used with Radius users.'

NETWORK_IN_USE = 'network_in_use'
NETWORK_IN_USE_MSG = 'Network address is already in use.'

INTERFACE_IN_USE = 'interface_in_use'
INTERFACE_IN_USE_MSG = 'Tunnel interface is already in use.'

PORT_PROTOCOL_IN_USE = 'port_protocol_in_use'
PORT_PROTOCOL_IN_USE_MSG = 'Port and protocol is already in use.'

IPV6_BRIDGED_INVALID = 'ipv6_bridged_invalid'
IPV6_BRIDGED_INVALID_MSG = 'IPv6 cannot be used with bridged servers.'

SERVER_LINKS_NOT_OFFLINE = 'server_links_not_offline'
SERVER_LINKS_NOT_OFFLINE_SETTINGS_MSG = 'All linked servers must be ' + \
    'offline to modify settings.'

SERVER_LINKS_AND_REPLICA = 'server_links_and_replica'
SERVER_LINKS_AND_REPLICA_MSG = 'Cannot have multiple replicas with ' + \
    'linked servers.'

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

SERVER_ROUTE_ONLINE = 'server_route_online'
SERVER_ROUTE_ONLINE_MSG = 'Cannot modify routes while server is online.'

SERVER_ROUTE_INVALID = 'server_route_invalid'
SERVER_ROUTE_INVALID_MSG = 'Route network address is not valid.'

SERVER_ROUTE_VIRTUAL_NAT = 'server_route_virtual_nat'
SERVER_ROUTE_VIRTUAL_NAT_MSG = 'Virtual network routes cannot use NAT.'

SERVER_ROUTE_SERVER_LINK_NAT = 'server_route_server_link_nat'
SERVER_ROUTE_SERVER_LINK_NAT_MSG = 'Server link routes cannot modify NAT.'

SERVER_LINK_COMMON_HOST = 'server_link_common_host'
SERVER_LINK_COMMON_HOST_MSG = 'Linked servers cannot have a common host.'

SERVER_LINK_COMMON_ROUTE = 'server_link_common_route'
SERVER_LINK_COMMON_ROUTE_MSG = 'Linked servers cannot have a common route.'

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
EMAIL_FROM_INVALID_MSG = 'SMTP server did not accept the from address.'

EMAIL_AUTH_INVALID = 'email_auth_invalid'
EMAIL_AUTH_INVALID_MSG = 'SMTP authentication is invalid.'

IPV6_SUBNET_ONLINE = 'ipv6_subnet_online'
IPV6_SUBNET_ONLINE_MSG = 'IPv6 routed subnet cannot be changed with ' + \
    'IPv6 servers online.'

IPV6_SUBNET_INVALID = 'ipv6_subnet_invalid'
IPV6_SUBNET_INVALID_MSG = 'IPv6 routed subnet is invalid.'

IPV6_SUBNET_SIZE_INVALID = 'ipv6_subnet_size_invalid'
IPV6_SUBNET_SIZE_INVALID_MSG = 'IPv6 routed subnet size is invalid, must ' + \
    'be atleast /64.'

SUBSCRIPTION_SERVER_ERROR = 'subscription_server_error'
SUBSCRIPTION_SERVER_ERROR_MSG = 'Unable to connect to ' + \
    'subscription server, please try again later.'

LICENSE_INVALID = 'license_invalid'
LICENSE_INVALID_MSG = 'License key is invalid'

MONGODB_URI_INVALID = 'mongodb_uri_invalid'
MONGODB_URI_INVALID_MSG = 'MongoDB URI is invalid.'

MONGODB_CONNECT_ERROR = 'mongodb_connect_error'
MONGODB_CONNECT_ERROR_MSG = 'Unable to connect to MongoDB server.'

MONGODB_AUTH_ERROR = 'mongodb_auth_error'
MONGODB_AUTH_ERROR_MSG = 'Unable to authenticate to the MongoDB server.'

SETUP_KEY_INVALID = 'setup_key_invalid'
SETUP_KEY_INVALID_MSG = 'Setup key is invalid.'

DUO_USER_INVALID = 'duo_user_invalid'
DUO_USER_INVALID_MSG = 'Username is invalid.'

NO_ADMINS_ENABLED = 'no_admins_enabled'
NO_ADMINS_ENABLED_MSG = 'Atleast one super administrator must be enabled.'

NO_SUPER_USERS = 'no_super_users'
NO_SUPER_USERS_MSG = 'There must be atleast one super user.'

NO_ADMINS = 'no_admins'
NO_ADMINS_MSG = 'Atleast one super administrator must exist.'

ADMIN_USERNAME_EXISTS = 'admin_username_exists'
ADMIN_USERNAME_EXISTS_MSG = 'Administrator username already exists.'

REQUIRES_SUPER_USER = 'requires_super_user'
REQUIRES_SUPER_USER_MSG = 'This administrator action can only be ' + \
    'performed by a super user.'

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

HASHES = {
    'none': 'none',
    'md5': 'MD5',
    'sha1': 'SHA1',
    'sha256': 'SHA256',
    'sha512': 'SHA512',
}

ONC_CIPHERS = {
    'none': 'none',
    'bf128': 'BF-CBC',
    'bf256': 'BF-CBC',
    'aes128': 'AES-128-CBC',
    'aes192': 'AES-192-CBC',
    'aes256': 'AES-256-CBC',
}

JUMBO_FRAMES = {
    False: '',
    True: 'tun-mtu 9000\nfragment 0\nmssfix 0\n',
}

OVPN_INLINE_SERVER_CONF = """\
port %s
proto %s
dev %s
%s
management %s unix
management-client-auth
auth-user-pass-optional
topology subnet
max-clients %s
ping %s
ping-restart %s
push "ping %s"
push "ping-restart %s"
persist-tun
%s
auth %s
status-version 2
script-security 2
reneg-sec 2592000
hash-size 1024 1024
max-routes-per-client 512
verb %s
mute %s
"""

OVPN_INLINE_CLIENT_CONF = """\
%s
setenv UV_ID %s
setenv UV_NAME %s
client
dev %s
dev-type %s
%s
nobind
persist-tun
%s
auth %s
verb 2
mute 3
push-peer-info
ping %s
ping-restart %s
hand-window 70
server-poll-timeout 4
reneg-sec 2592000
sndbuf 100000
rcvbuf 100000
remote-cert-tls server
"""

OVPN_ONC_CLIENT_CONF = """\
{
  "Type": "UnencryptedConfiguration",
  "NetworkConfigurations": [{
    "GUID": "%s",
    "Name": "%s",
    "Type": "VPN",
    "VPN": {
      "Host": "%s",
      "Type": "OpenVPN",
      "OpenVPN": {
        "AuthRetry": "interact",
        "Auth": "%s",
        "Cipher": "%s",
        "ClientCertType": "Pattern",
        "ClientCertPattern": {
          "IssuerCARef": [
%s
          ]
        },
        "CompLZO": "%s",
        "Port": %s,
        "Proto": "%s",
        "PushPeerInfo": true,
        "RenegSec": 2592000,
        "ServerCARefs": [
%s
        ],
        "ServerPollTimeout": 4,%s
        "RemoteCertTLS": "server",%s
        "Verb": "2"
      }
    }
  }],
%s}
"""

OVPN_ONC_AUTH_NONE = """
        "SaveCredentials": true,
        "UserAuthenticationType": "Password",
        "Username": "%s",
        "Password": "chrome","""

OVPN_ONC_AUTH_OTP = """
        "SaveCredentials": false,
        "UserAuthenticationType": "OTP",
        "Username": "%s","""

OVPN_ONC_AUTH_PASS = """
        "SaveCredentials": false,
        "UserAuthenticationType": "Password",
        "Username": "%s","""

OVPN_ONC_CA_CERT = """\
  "Certificates": [{
    "GUID": "%s",
    "Type": "Authority",
    "X509": "%s"
  }]
"""

OVPN_INLINE_LINK_CONF = """\
client
setenv UV_ID %s
setenv UV_NAME %s
dev %s
dev-type %s
proto %s
%s
nobind
persist-tun
%s
auth %s
verb %s
mute %s
push-peer-info
ping %s
ping-restart %s
hand-window 70
server-poll-timeout 4
reneg-sec 2592000
sndbuf 100000
rcvbuf 100000
remote-cert-tls server
"""

KEY_LINK_EMAIL_TEXT = """\
Your vpn key can be downloaded from the temporary link below. You may also directly import your keys in the Pritunl client using the temporary URI link.

Key Link: {key_link}
URI Key Link: {uri_link}"""

KEY_LINK_EMAIL_HTML = """\
<p>Your vpn key can be downloaded from the temporary link below.
You may also directly import your keys in the Pritunl client using the
temporary URI link.<br><br>
Key Link: <a href="{key_link}">{key_link}</a><br>
URI Key Link: <a href="{uri_link}">{uri_link}</a></p>

<div itemscope itemtype="http://schema.org/EmailMessage">
  <div itemprop="action" itemscope itemtype="http://schema.org/ViewAction">
    <link itemprop="url" href="{key_link}"></link>
    <meta itemprop="name" content="View Key"></meta>
  </div>
  <meta itemprop="description" content="View Pritunl key and configuration information"></meta>
</div>"""
