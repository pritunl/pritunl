from pritunl.helpers import *
from pritunl import settings
from pritunl import utils

def setup_settings():
    if not settings.app.oracle_private_key or \
            not settings.app.oracle_public_key:
        private_key, public_key = utils.generate_rsa_key()
        settings.app.oracle_private_key = private_key
        settings.app.oracle_public_key = public_key
        settings.commit()
