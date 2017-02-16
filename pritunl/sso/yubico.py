from pritunl import settings
from pritunl import logger

import yubico_client
import certifi

def auth_yubico(key):
    if len(key) != 44:
        return False, None

    public_id = key[:12]

    client = yubico_client.Yubico(
        client_id=settings.app.sso_yubico_client,
        key=settings.app.sso_yubico_secret,
        api_urls=settings.app.sso_yubico_servers,
        ca_certs_bundle_path=certifi.where(),
    )

    try:
        if client.verify(key) is True:
            return True, public_id
    except:
        logger.exception('Yubico authentication error', 'sso')

    return False, None
