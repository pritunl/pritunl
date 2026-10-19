from pritunl import settings
from pritunl import logger
from pritunl import mongo
from pritunl import utils

import hmac
import hashlib
import base64
import pymongo
import requests

RETRY_STATUSES = ('BACKEND_ERROR', 'NOT_ENOUGH_ANSWERS')

def _sign(secret, params):
    message = '&'.join(
        '%s=%s' % (key, params[key]) for key in sorted(params))
    digest = hmac.new(secret, message.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()

def _verify(yubikey):
    client_id = settings.app.sso_yubico_client
    if not client_id:
        logger.error('Yubico client id not configured', 'sso')
        return False

    secret = settings.app.sso_yubico_secret
    if secret:
        secret = base64.b64decode(secret)

    nonce = utils.rand_str(32)
    params = {
        'id': client_id,
        'otp': yubikey,
        'nonce': nonce,
    }
    if secret:
        params['h'] = _sign(secret, params)

    for api_url in settings.app.sso_yubico_servers:
        try:
            response = requests.get(
                api_url,
                params=params,
                timeout=10,
            )
        except:
            logger.exception('Yubico api error', 'sso',
                api_url=api_url,
            )
            continue

        if response.status_code != 200:
            logger.error('Bad status from Yubico api', 'sso',
                api_url=api_url,
                status_code=response.status_code,
                response=response.content,
            )
            continue

        resp_params = {}
        for line in response.text.splitlines():
            if '=' in line:
                key, value = line.strip().split('=', 1)
                resp_params[key] = value

        signature = resp_params.pop('h', None)
        if secret:
            expected = _sign(secret, resp_params)
            if not signature or not hmac.compare_digest(
                    signature.encode(), expected.encode()):
                logger.error('Yubico response signature mismatch', 'sso',
                    api_url=api_url,
                    response=response.content,
                )
                return False

        status = resp_params.get('status')
        if status in RETRY_STATUSES:
            logger.warning('Yubico api temporary failure', 'sso',
                api_url=api_url,
                status=status,
            )
            continue

        if status != 'OK':
            logger.error('Yubico authentication failed', 'sso',
                status=status,
            )
            return False

        if resp_params.get('otp') != yubikey or \
                resp_params.get('nonce') != nonce:
            logger.error('Yubico response otp or nonce mismatch', 'sso',
                api_url=api_url,
                response=response.content,
            )
            return False

        return True

    logger.error('Yubico api unavailable', 'sso')
    return False

def auth_yubico(yubikey):
    yubikey_collection = mongo.get_collection('yubikey')

    if len(yubikey) != 44:
        return False, None

    yubikey = yubikey.lower()

    public_id = yubikey[:12]

    try:
        if not _verify(yubikey):
            return False, None
    except:
        logger.exception('Yubico authentication error', 'sso')
        return False, None

    yubikey_hash = hashlib.sha512()
    yubikey_hash.update(yubikey.encode())
    yubikey_hash = base64.b64encode(yubikey_hash.digest()).decode()

    try:
        yubikey_collection.insert_one({
            '_id': yubikey_hash,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        logger.error('Yubico replay error', 'sso')
        return False, None

    return True, public_id
