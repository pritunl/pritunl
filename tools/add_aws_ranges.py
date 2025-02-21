import requests
import time
import uuid
import hmac
import hashlib
import base64
import json
import sys

BASE_URL = 'https://server.domain'
API_TOKEN = 'Hv2FxEMoa3moTVuRahMsMK3VUCwdmjmt'
API_SECRET = 'zihea5hTIpIgxsPFboby4hctopxWQSKd'
SERVER_ID = '57e9e364fd632c233e86f827'
REGIONS = {
    # 'GLOBAL',
    #
    # 'us-east-1',
    # 'us-east-2',
    # 'us-west-1',
    # 'us-west-2',
    # 'us-gov-west-1',
    #
    # 'eu-central-1',
    # 'eu-west-1',
    #
    # 'ap-south-1',
    # 'ap-northeast-1',
    # 'ap-northeast-2',
    # 'ap-southeast-1',
    # 'ap-southeast-2',
    #
    # 'cn-north-1',
    #
    # 'sa-east-1',
    #
    # 'us-gov-west-1',
}

def auth_request(method, path, headers=None, data=None):
    auth_timestamp = str(int(time.time()))
    auth_nonce = uuid.uuid4().hex
    auth_string = '&'.join([API_TOKEN, auth_timestamp, auth_nonce,
        method.upper(), path.split('?')[0]])
    auth_signature = base64.b64encode(hmac.new(
        API_SECRET.encode('utf-8'), auth_string.encode('utf-8'),
        hashlib.sha256).digest())
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
        headers=auth_headers,
        data=data,
    )

response = requests.get('https://ip-ranges.amazonaws.com/ip-ranges.json')
ranges = response.json()
routes = []

for range in ranges['prefixes']:
    if range['region'] not in REGIONS:
        continue

    routes.append({
        'network': range['ip_prefix'],
        'nat': True,
    })

response = auth_request(
    'POST',
    '/server/%s/routes' % SERVER_ID,
    headers={
        'Content-Type': 'application/json',
    },
    data=json.dumps(routes),
)
assert(response.status_code == 200)
