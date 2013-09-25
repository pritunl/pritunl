APP_NAME = 'pritunl'
APP_NAME_FORMATED = 'Pritunl'
CONF_FILENAME = '%s.conf' % APP_NAME

SAVED = 'saved'
UNSAVED = 'unsaved'

NAME_SAFE_CHARS = ['-', '_', '@', '.']

DEFAULT_DB_PATH = '/var/lib/pritunl/pritunl.db'
DEFAULT_WWW_PATH = '/usr/share/pritunl/www'
DEFAULT_DATA_PATH = '/var/lib/pritunl'
DEFAULT_LOG_LIMIT = 20
DH_PARAM_BITS = 512 # TODO Temporary

INFO = 'info'
WARNING = 'warning'
ERROR = 'error'

ORGS_DIR = 'organizations'
SERVERS_DIR = 'servers'
REQS_DIR = 'reqs'
KEYS_DIR = 'keys'
CERTS_DIR = 'certs'
USERS_DIR = 'users'
INDEXED_CERTS_DIR = 'indexed_certs'
TEMP_DIR = 'temp'
INDEX_NAME = 'index'
SERIAL_NAME = 'serial'
CRL_NAME = 'ca.crl'
OVPN_CONF_NAME = 'openvpn.conf'
OVPN_CA_NAME = 'ca.crt'
IFC_POOL_NAME = 'ifc_pool'
DH_PARAM_NAME = 'dh_param.pem'
SERVER_USER_PREFIX = 'server_'

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

CERT_CONF = """[ default ]
ca = %s
dir = %s

[ req ]
default_bits = 4096
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

OVPN_SERVER_CONF = """port %s
proto %s
dev %s
ca %s
cert %s
key %s
dh %s
server %s
ifconfig-pool-persist %s
push "%s"
keepalive 10 120
persist-tun
verb 0
mute 5
"""

OVPN_CLIENT_CONF = """client
dev tun
proto %s
remote %s %s
resolv-retry infinite
nobind
persist-tun
ca %s
cert %s
key %s
verb 3
mute 5
"""
