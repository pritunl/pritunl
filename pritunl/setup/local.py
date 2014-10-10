from pritunl import __version__

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import utils

import hashlib
import uuid
import os

def setup_local():
    settings.local.openssl_heartbleed = not utils.check_openssl()

    if os.path.isfile(settings.conf.uuid_path):
        with open(settings.conf.uuid_path, 'r') as uuid_file:
            settings.local.host_id = uuid_file.read().strip()
    else:
        settings.local.host_id = uuid.uuid4().hex

        with open(settings.conf.uuid_path, 'w') as uuid_file:
            uuid_file.write(settings.local.host_id)

    settings.local.version = __version__
    settings.local.version_int = int(
        ''.join([x.zfill(2) for x in settings.local.version.split('.')]))
