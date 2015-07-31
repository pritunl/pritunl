from pritunl.utils.misc import check_output_logged

import os

def generate_server_cert(server_cert_path, server_key_path):
    check_output_logged([
        'openssl', 'req', '-batch', '-x509', '-nodes', '-sha256',
        '-newkey', 'rsa:4096',
        '-days', '3652',
        '-keyout', server_key_path,
        '-out', server_cert_path,
    ])
    os.chmod(server_key_path, 0600)
