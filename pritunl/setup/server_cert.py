from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl import logger

import subprocess
import os

def setup_server_cert():
    if not os.path.isfile(settings.conf.server_cert_path) or \
            not os.path.isfile(settings.conf.server_key_path):
        logger.info('Generating server ssl cert...')
        try:
            subprocess.check_call([
                'openssl', 'req', '-batch', '-x509', '-nodes', '-sha256',
                '-newkey', 'rsa:4096',
                '-days', '3652',
                '-keyout', settings.conf.server_key_path,
                '-out', settings.conf.server_cert_path,
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logger.exception('Failed to generate server ssl cert.')
            raise
        os.chmod(settings.conf.server_key_path, 0600)
