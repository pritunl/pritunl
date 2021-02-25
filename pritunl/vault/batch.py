from pritunl.vault.nonces import *

from pritunl.exceptions import *

import os
import requests
import time
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class Batch(object):
    def __init__(self):
        self._items = {}
        self._items_data = []

    def add(self, item):
        self._items[item._id] = item
        self._items_data.append(item._data)
        return item

    def items(self):
        items = []
        for item in list(self._items.values()):
            items.append(item)
        return items

    def process(self):
        from pritunl import settings
        from pritunl import utils

        if not len(self._items):
            return

        nonce = utils.generate_secret_len(16)
        nonces_add(nonce)

        data = {
            'n': nonce,
            't': int(time.time()),
            'i': self._items_data,
        }

        gcm = AESGCM(settings.local.se_encryption_key)

        nonce = os.urandom(12)

        ciphertext = gcm.encrypt(
            nonce,
            json.dumps(data).encode(),
            None,
        )

        nonce64 = base64.b64encode(nonce)
        nonces_add(nonce64)

        payload = {
            'n': nonce64,
            'd': base64.b64encode(ciphertext).decode(),
        }

        resp = requests.put(
            'http://127.0.0.1:9758/process',
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

        if nonces_contains(crypto_data['n']):
            raise RequestError('Vault authorization nonce replay')
        nonces_add(crypto_data['n'])

        now = int(time.time())
        diff = now - crypto_data['t']
        if diff > 10 or diff < -3:
            raise RequestError('Vault bad timestamp %s' % crypto_data['t'])

        for item_data in crypto_data['i']:
            item_id = item_data['c'] + '-' + item_data['i'] + '-' + \
                item_data['k']
            item = self._items[item_id]
            item._data = item_data
