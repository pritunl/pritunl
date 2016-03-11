from pritunl.constants import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import os

def setup_server_cert():
    server_cert_path = os.path.join(settings.conf.temp_path, SERVER_CERT_NAME)
    server_key_path = os.path.join(settings.conf.temp_path, SERVER_KEY_NAME)

    if not settings.app.server_cert or not settings.app.server_key:
        logger.info('Generating server ssl cert', 'setup')

        utils.generate_server_cert(server_cert_path, server_key_path)

        with open(server_cert_path, 'r') as server_cert_file:
            settings.app.server_cert = server_cert_file.read().strip()
        with open(server_key_path, 'r') as server_key_file:
            settings.app.server_key = server_key_file.read().strip()

        settings.commit()
