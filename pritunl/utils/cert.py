from pritunl.constants import *
from pritunl.utils.misc import check_output_logged, get_temp_path
from pritunl import settings

import os

def write_server_cert():
    server_cert_path = os.path.join(settings.conf.temp_path, SERVER_CERT_NAME)
    server_key_path = os.path.join(settings.conf.temp_path, SERVER_KEY_NAME)

    with open(server_cert_path, 'w') as server_cert_file:
        server_cert_file.write(settings.app.server_cert)
    with open(server_key_path, 'w') as server_key_file:
        os.chmod(server_key_path, 0600)
        server_key_file.write(settings.app.server_key)

def generate_server_cert(server_cert_path, server_key_path):
    check_output_logged([
        'openssl', 'req', '-batch', '-x509', '-nodes', '-sha256',
        '-newkey', 'rsa:4096',
        '-days', '3652',
        '-keyout', server_key_path,
        '-out', server_cert_path,
    ])
    os.chmod(server_key_path, 0600)
