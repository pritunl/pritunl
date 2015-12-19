BASE_URL = 'https://localhost:9700'
API_TOKEN = 'B20d2WJaVTOORbDzVT0QqGeurz0ONrZY'
API_SECRET = 'g2SV9YxUBAb6y3ZtLPLrbp4Gqcx8H9xW'
ORG_ID = '5674382bb0e73045a8b837e4'

import requests
import time
import uuid
import hmac
import hashlib
import base64
import os

def auth_request(method, path, headers=None, data=None):
    auth_timestamp = str(int(time.time()))
    auth_nonce = uuid.uuid4().hex
    auth_string = '&'.join([API_TOKEN, auth_timestamp, auth_nonce,
        method.upper(), path] + ([data] if data else []))
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

try:
    os.makedirs('test_client/confs')
except:
    pass

for user in response.json():
    if user['type'] != 'client':
        continue

    resp = auth_request('GET',
      '/key/%s/%s/%s.key' % (ORG_ID, user['id'], user['servers'][0]['id']),
    )

    with open('test_client/confs/' + user['name'] + '.ovpn', 'w') as conf_file:
        conf_file.write(resp.content)
