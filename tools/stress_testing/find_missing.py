BASE_URL = 'https://sn.pritunl.net'
API_TOKEN = 'mEaIyxlXBmsUkjWPdEgMiRooRGdmONuc'
API_SECRET = 'rHzdcFQZWDGTSI4q0ZIepn1OtqpJJYWf'
ORG_ID = '573b2d405a3d9c0a455b6dbe'

import requests
import time
import uuid
import hmac
import hashlib
import base64
import sys

names = set()

with open('names', 'r') as names_file:
    for line in names_file:
        line = line.strip()
        if line:
            names.add(line.strip())


def auth_request(method, path, headers=None, data=None):
    auth_timestamp = str(int(time.time()))
    auth_nonce = uuid.uuid4().hex
    auth_string = '&'.join([API_TOKEN, auth_timestamp, auth_nonce,
        method.upper(), path])
    auth_signature = base64.b64encode(hmac.new(
        API_SECRET, auth_string, hashlib.sha256).digest())
    auth_headers = {
        'Auth-Token': API_TOKEN,
        'Auth-Timestamp': auth_timestamp,
        'Auth-Nonce': auth_nonce,
        'Auth-Signature': auth_signature,
    }
    if headers:
        auth_headers.update(headers)
    return getattr(requests, method.lower())(
        BASE_URL + path,
        verify=False,
        headers=auth_headers,
        data=data,
    )

response = auth_request('GET',
  '/user/%s' % ORG_ID,
)
assert(response.status_code == 200)

cur_names = set()

for user in response.json():
    name = user['name']
    if name in cur_names:
        print >> sys.stderr, name
    cur_names.add(name)

for name in sorted(list(names - cur_names)):
    print name
