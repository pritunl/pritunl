from pritunl.vault.nonces import *

from pritunl.constants import *
from pritunl.exceptions import *

import os
import requests
import time
import hmac
import hashlib
import base64
import json
import pymongo
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def init():
    from pritunl import settings

    resp = requests.get(
        'http://127.0.0.1:9758/init',
        verify=False,
        headers={
            'User-Agent': 'pritunl',
        },
    )

    if resp.status_code != 200:
        raise RequestError('Vault bad status %s' % resp.status_code)

    cipher_data = base64.b64decode(resp.content)

    plaintext = settings.local.se_client_key.decrypt(
        cipher_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA512()),
            algorithm=hashes.SHA512(),
            label=None,
        ),
    )

    data = json.loads(plaintext)

    settings.local.se_authorize_key = base64.b64decode(data[0])
    settings.local.se_encryption_key = base64.b64decode(data[1])

def init_host_key():
    from pritunl import settings
    from pritunl import utils

    nonce = utils.generate_secret_len(16)
    nonces_add(nonce)

    data = {
        'n': nonce,
        't': int(time.time()),
        'h': settings.local.se_host_key,
    }

    auth_data = data['n'] + '&' + str(data['t']) + '&' + data['h']

    data['a'] = base64.b64encode(hmac.new(
        settings.local.se_authorize_key,
        auth_data,
        hashlib.sha512,
    ).digest())

    gcm = AESGCM(settings.local.se_encryption_key)

    nonce = os.urandom(12)

    ciphertext = gcm.encrypt(
        nonce,
        json.dumps(data),
        None,
    )

    nonce64 = base64.b64encode(nonce)
    nonces_add(nonce64)

    payload = {
        'n': nonce64,
        'd': base64.b64encode(ciphertext),
    }

    resp = requests.post(
        'http://127.0.0.1:9758/key',
        verify=False,
        headers={
            'User-Agent': 'pritunl',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
        data=json.dumps(payload),
    )

    if resp.status_code != 200:
        raise RequestError('Vault bad status %s' % resp.status_code)

def init_server_key():
    from pritunl import settings
    from pritunl import utils

    resp = requests.get(
        'http://127.0.0.1:9758/key',
        verify=False,
        headers={
            'User-Agent': 'pritunl',
            'Accept': 'application/json',
        },
    )

    if resp.status_code != 200:
        raise RequestError('Vault bad status %s' % resp.status_code)

    cipher_data = resp.json()

    gcm = AESGCM(settings.local.se_encryption_key)

    data = gcm.decrypt(
        base64.b64decode(cipher_data['n']),
        base64.b64decode(cipher_data['d']),
        None,
    )

    if nonces_contains(cipher_data['n']):
        raise RequestError('Vault authorization nonce replay')
    nonces_add(cipher_data['n'])

    data = json.loads(data)

    now = int(time.time())
    diff = now - data['t']
    if diff > 10 or diff < -3:
        raise RequestError('Vault bad timestamp %s' % data['t'])

    auth_data = data['n'] + '&' + str(data['t']) + '&' + \
        data['h'] + '&' + data['s']

    auth_signature = base64.b64encode(hmac.new(
        settings.local.se_authorize_key,
        auth_data,
        hashlib.sha512,
    ).digest())

    if not utils.const_compare(auth_signature, data['a']):
        raise RequestError('Vault bad signature')

    if nonces_contains(data['n']):
        raise RequestError('Vault authorization nonce replay')
    nonces_add(data['n'])

    return {
        'i': settings.local.host_id,
        'h': data['h'].strip(),
        's': data['s'].strip(),
        'c': base64.b64decode(settings.local.se_client_pub_key).strip(),
    }

def init_master_key(cipher_data):
    from pritunl import settings
    from pritunl import utils

    prefix = settings.conf.mongodb_collection_prefix or ''
    client = pymongo.MongoClient(settings.conf.mongodb_uri,
        connectTimeoutMS=MONGO_CONNECT_TIMEOUT)
    database = client.get_default_database()
    settings_db = getattr(database, prefix + 'settings')
    doc = settings_db.find_one({
        '_id': 'se',
    })

    crypto_keys = None
    if doc and doc['keys']:
        crypto_keys = doc['keys']

    ciphertext = base64.b64decode(cipher_data['c'])

    plaintext = settings.local.se_client_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA512()),
            algorithm=hashes.SHA512(),
            label=None,
        ),
    )

    client_key = plaintext.strip()
    nonce = utils.generate_secret_len(16)
    nonces_add(nonce)

    data = {
        'n': nonce,
        't': int(time.time()),
        'h': cipher_data['h'],
        's': cipher_data['s'],
        'c': client_key,
        'o': cipher_data['o'],
        'm': cipher_data['m'],
    }

    auth_data = data['n'] + '&' + str(data['t']) + '&' + \
        data['h'] + '&' + data['s'] + '&' + data['c'] + '&' + \
        data['o'] + '&' + data['m']

    if crypto_keys:
        data['k'] = crypto_keys
        auth_data += '&' + data['k']

    data['a'] = base64.b64encode(hmac.new(
        settings.local.se_authorize_key,
        auth_data,
        hashlib.sha512,
    ).digest())

    gcm = AESGCM(settings.local.se_encryption_key)

    nonce = os.urandom(12)

    ciphertext = gcm.encrypt(
        nonce,
        json.dumps(data),
        None,
    )

    payload = {
        'n': base64.b64encode(nonce),
        'd': base64.b64encode(ciphertext),
    }

    resp = requests.post(
        'http://127.0.0.1:9758/master',
        verify=False,
        headers={
            'User-Agent': 'pritunl',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
        data=json.dumps(payload),
    )

    if resp.status_code != 200:
        raise RequestError('Vault bad status %s' % resp.status_code)

    crypto_payload = resp.json()

    crypto_plaintext = gcm.decrypt(
        base64.b64decode(crypto_payload['n']),
        base64.b64decode(crypto_payload['d']),
        None,
    )

    if nonces_contains(crypto_payload['n']):
        raise RequestError('Vault authorization nonce replay')
    nonces_add(crypto_payload['n'])

    crypto_data = json.loads(crypto_plaintext)

    now = int(time.time())
    diff = now - crypto_data['t']
    if diff > 10 or diff < -3:
        raise RequestError('Vault bad timestamp %s' % crypto_data['t'])

    crypto_data_auth = crypto_data['n'] + '&' + \
        str(crypto_data['t']) + '&' + crypto_data['k']

    crypto_data_authr = base64.b64encode(hmac.new(
        settings.local.se_authorize_key,
        crypto_data_auth,
        hashlib.sha512,
    ).digest())

    if not utils.const_compare(crypto_data_authr, crypto_data['a']):
        raise RequestError('Invalid crypto keys signature')

    if nonces_contains(crypto_data['n']):
        raise RequestError('Vault authorization nonce replay')
    nonces_add(crypto_data['n'])

    if crypto_data['k'] != crypto_keys:
        settings_db.update({
            '_id': 'se',
        }, {'$set': {
            'keys': crypto_data['k'],
        }}, upsert=True)
