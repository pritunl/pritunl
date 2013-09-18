APP_NAME = 'pritunl'
APP_NAME_FORMATED = 'Pritunl'
CONF_FILENAME = '%s.conf' % APP_NAME

CLOSED = 'closed'
SAVED = 'saved'
UNSAVED = 'unsaved'

DEFAULT_WWW_PATH = '/usr/share/pritunl/www'

DATA_DIR = './data'
REQS_DIR = 'reqs'
KEYS_DIR = 'keys'
CERTS_DIR = 'certs'
USERS_DIR = 'users'
INDEXED_CERTS_DIR = 'indexed_certs'
TEMP_DIR = 'temp'
INDEX_NAME = 'index'
SERIAL_NAME = 'serial'
CRL_NAME = 'ca.crl'

CA_CERT_ID = 'ca'
CERT_CA = 'ca'
CERT_SERVER = 'server'
CERT_CLIENT = 'client'

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

[ ca_policy ]
organizationName = match
commonName = supplied

[ ca_ext ]
keyUsage = critical,keyCertSign,cRLSign
basicConstraints = critical,CA:true
subjectKeyIdentifier = hash
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
