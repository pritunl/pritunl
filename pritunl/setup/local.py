from pritunl import __version__

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl import utils

import hashlib
import uuid

def setup_local():
    settings.local.openssl_heartbleed = not utils.check_openssl()
    settings.local.host_id = hashlib.sha1(str(uuid.getnode())).hexdigest()
    settings.local.version = __version__
    settings.local.version_int = int(
        ''.join([x.zfill(2) for x in settings.local.version.split('.')]))
