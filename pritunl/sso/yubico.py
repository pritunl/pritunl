from pritunl import settings
from pritunl import logger
from pritunl import mongo
from pritunl import utils

import hashlib
import base64
import pymongo
import yubico_client
import certifi

def auth_yubico(yubikey):
    yubikey_collection = mongo.get_collection('yubikey')

    if len(yubikey) != 44:
        return False, None

    yubikey = yubikey.lower()

    public_id = yubikey[:12]

    client = yubico_client.Yubico(
        client_id=settings.app.sso_yubico_client,
        key=settings.app.sso_yubico_secret,
        api_urls=settings.app.sso_yubico_servers,
        ca_certs_bundle_path=certifi.where(),
    )

    try:
        if client.verify(yubikey) is not True:
            return False, None
    except:
        logger.exception('Yubico authentication error', 'sso')
        return False, None

    yubikey_hash = hashlib.sha512()
    yubikey_hash.update(yubikey.encode())
    yubikey_hash = base64.b64encode(yubikey_hash.digest()).decode()

    try:
        yubikey_collection.insert({
            '_id': yubikey_hash,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        logger.error('Yubico replay error', 'sso')
        return False, None

    return True, public_id
