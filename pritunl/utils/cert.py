from pritunl.constants import *
from pritunl.utils.misc import check_output_logged, get_temp_path
from pritunl import settings

import os
import collections

def create_server_cert():
    from pritunl import acme
    from pritunl import logger

    logger.info('Generating server certificate...', 'utils')

    if settings.app.acme_domain:
        acme.update_acme_cert()
        return

    server_cert_path, server_key_path = generate_server_cert()

    with open(server_cert_path, 'r') as server_cert_file:
        settings.app.server_cert = server_cert_file.read().strip()
    with open(server_key_path, 'r') as server_key_file:
        settings.app.server_key = server_key_file.read().strip()

def create_server_dh_params():
    from pritunl import logger

    logger.info('Generating server dh params...', 'utils')

    server_dh_path = generate_server_dh_params(
        settings.app.server_dh_size)

    with open(server_dh_path, 'r') as server_dh_file:
        settings.app.server_dh_params = server_dh_file.read().strip()

def write_server_cert(server_cert, server_key,
        server_dh_params, acme_domain):
    server_cert_path = os.path.join(settings.conf.temp_path, SERVER_CERT_NAME)
    server_chain_path = os.path.join(settings.conf.temp_path,
        SERVER_CHAIN_NAME)
    server_key_path = os.path.join(settings.conf.temp_path, SERVER_KEY_NAME)
    server_dh_path = os.path.join(settings.conf.temp_path, SERVER_DH_NAME)

    server_cert_full = server_cert

    if acme_domain:
        server_cert_full += LETS_ENCRYPT_INTER

    server_cert_full = server_cert_full.strip()
    server_cert_full = server_cert_full.split('-----BEGIN CERTIFICATE-----')

    server_certs = collections.deque()

    for cert in server_cert_full:
        cert = cert.strip()
        if not cert:
            continue

        server_certs.append('-----BEGIN CERTIFICATE-----\n' + cert)

    server_cert = server_certs.popleft()
    server_chain = '\n'.join(server_certs)

    with open(server_cert_path, 'w') as server_cert_file:
        server_cert_file.write(server_cert)
    with open(server_key_path, 'w') as server_key_file:
        os.chmod(server_key_path, 0600)
        server_key_file.write(server_key)

    if server_certs:
        with open(server_chain_path, 'w') as server_chain_file:
            server_chain_file.write(server_chain)
    else:
        server_chain_path = None

    if server_dh_params:
        with open(server_dh_path, 'w') as server_dh_file:
            os.chmod(server_dh_path, 0600)
            server_dh_file.write(server_dh_params)
    else:
        server_dh_path = None

    return server_cert_path, server_chain_path, server_key_path, server_dh_path

def generate_server_dh_params(dh_size):
    server_dh_path = os.path.join(settings.conf.temp_path, SERVER_DH_NAME)

    check_output_logged([
        'openssl',
        'dhparam', str(dh_size),
        '-out', server_dh_path,
    ])
    os.chmod(server_dh_path, 0600)

    return server_dh_path

def generate_server_dh_params_inline(dh_size):
    return check_output_logged([
        'openssl',
        'dhparam', str(dh_size),
    ])

def generate_server_cert():
    server_cert_path = os.path.join(settings.conf.temp_path, SERVER_CERT_NAME)
    server_key_path = os.path.join(settings.conf.temp_path, SERVER_KEY_NAME)

    check_output_logged([
        'openssl', 'ecparam', '-name', 'prime256v1', '-genkey', '-noout',
        '-out', server_key_path,
    ])
    check_output_logged([
        'openssl', 'req', '-new', '-batch', '-x509', '-days', '3652',
        '-key', server_key_path,
        '-out', server_cert_path,
    ])
    os.chmod(server_key_path, 0600)

    return server_cert_path, server_key_path

def generate_private_key():
    return check_output_logged([
        'openssl', 'genrsa', '4096',
    ])

def generate_private_ec_key():
    return check_output_logged([
        'openssl', 'ecparam', '-name', 'prime256v1', '-genkey', '-noout',
    ])

def generate_csr(private_key, domain):
    private_key_path = get_temp_path() + '.key'

    with open(private_key_path, 'w') as private_key_file:
        os.chmod(private_key_path, 0600)
        private_key_file.write(private_key)

    csr = check_output_logged([
        'openssl',
        'req',
        '-new',
        '-batch',
        '-sha256',
        '-key', private_key_path,
        '-subj', '/CN=%s' % domain,
    ])

    try:
        os.remove(private_key_path)
    except:
        pass

    return csr
