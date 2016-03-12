from pritunl import settings
from pritunl import utils

def setup_server_cert():
    if not settings.app.server_cert or not settings.app.server_key:
        utils.create_server_cert()
        settings.commit()
