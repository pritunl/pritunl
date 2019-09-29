from pritunl.helpers import *
from pritunl.constants import *
from pritunl import settings
from pritunl import logger
from pritunl import utils
from pritunl import vault

import os
import threading
import subprocess
import time
import json
import bson

@interrupter
def _vault_thread():
    while True:
        process = None

        try:
            process = subprocess.Popen(
                ['/home/cloud/go/bin/pritunl-vault'],
                env=dict(os.environ, **{
                    'CLIENT_KEY': settings.local.se_client_pub_key,
                }),
            )

            while True:
                if process.poll() is not None:
                    if check_global_interrupt():
                        return

                    logger.error(
                        'Vault service stopped unexpectedly', 'setup',
                    )
                    process = None

                    yield interrupter_sleep(1)

                    break

                time.sleep(0.5)
                yield
        except GeneratorExit:
            if process:
                process.terminate()
                time.sleep(1)
                process.kill()
            return
        except:
            logger.exception('Error in vault service', 'setup')

        yield interrupter_sleep(1)

def setup_vault():
    if SE_MODE:
        try:
            os.remove(settings.conf.se_init_path)
        except OSError:
            pass
        try:
            os.remove(settings.conf.se_secret_path)
        except OSError:
            pass

        settings.local.se_authorize_key = utils.generate_secret()
        settings.local.se_encryption_key = None
        settings.local.se_client_key, settings.local.se_client_pub_key = \
            vault.generate_client_key()

        if os.path.isfile(settings.conf.se_host_key_path):
            with open(settings.conf.se_host_key_path, 'r') as key_file:
                settings.local.se_host_key = key_file.read().strip()
        else:
            logger.info('Generating se host key', 'setup')

            settings.local.se_host_key = vault.generate_host_key()
            with open(settings.conf.se_host_key_path, 'w') as key_file:
                key_file.write(settings.local.se_host_key)

        threading.Thread(target=_vault_thread).start()
        time.sleep(4)
        vault.init()
        vault.init_host_key()
        init_data = vault.init_server_key()

        with open(settings.conf.se_init_path, 'w') as key_file:
            key_file.write(json.dumps(init_data))

        subprocess.check_call(['/home/cloud/go/bin/pritunl-key'])

        logger.info('Waiting for se secret', 'setup')

        while True:
            time.sleep(0.5)
            if os.path.isfile(settings.conf.se_secret_path):
                with open(settings.conf.se_secret_path, 'r') as secret_file:
                    data = json.loads(secret_file.read().strip())
                break

        logger.info('Loading se secret', 'setup')

        vault.init_master_key(data)
