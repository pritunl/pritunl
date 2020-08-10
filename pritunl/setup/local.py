from pritunl import __version__

from pritunl import settings
from pritunl import utils

import uuid
import os

def setup_local():
    settings.local.iptables_wait = utils.check_iptables_wait()

    if settings.conf.host_id:
        settings.local.host_id = settings.conf.host_id
    elif os.path.isfile(settings.conf.uuid_path):
        with open(settings.conf.uuid_path, 'r') as uuid_file:
            settings.local.host_id = uuid_file.read().strip()
    else:
        settings.local.host_id = uuid.uuid4().hex

        dir_path = os.path.dirname(settings.conf.uuid_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(settings.conf.uuid_path, 'w') as uuid_file:
            uuid_file.write(settings.local.host_id)

    if os.path.isfile(settings.conf.setup_key_path):
        with open(settings.conf.setup_key_path, 'r') as setup_key_file:
            settings.local.setup_key = setup_key_file.read().strip()
    else:
        settings.local.setup_key = uuid.uuid4().hex

        with open(settings.conf.setup_key_path, 'w') as setup_key_file:
            os.chmod(settings.conf.setup_key_path, 0o600)
            setup_key_file.write(settings.local.setup_key)

    settings.local.version = __version__
    settings.local.version_int = utils.get_int_ver(__version__)
