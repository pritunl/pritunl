import requests
import time
import uuid
import hmac
import hashlib
import base64
import json
import threading
import Queue

BASE_URL = 'https://server.domain'
API_TOKEN = 'Hv2FxEMoa3moTVuRahMsMK3VUCwdmjmt'
API_SECRET = 'zihea5hTIpIgxsPFboby4hctopxWQSKd'
SERVER_ID = '57e9e364fd632c233e86f827'
REGIONS = {
    'GLOBAL',

    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',

    'eu-central-1',
    'eu-west-1',

    'ap-south-1',
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-southeast-1',
    'ap-southeast-2',

    'cn-north-1',

    'sa-east-1',

    'us-gov-west-1',
}

class CallQueue(object):
    def __init__(self, maxsize=0):
        self._threads = []
        self._queue = Queue.Queue(maxsize)

    def put(self, func, *args, **kwargs):
        self._queue.put((func, args, kwargs))

    def _thread(self):
        while True:
            try:
                func, args, kwargs = self._queue.get_nowait()
                func(*args, **kwargs)
            except Queue.Empty:
                return

    def start(self, threads=1):
        for _ in xrange(threads):
            thread = threading.Thread(target=self._thread)
            thread.daemon = True
            thread.start()
            self._threads.append(thread)

    def wait(self):
        for thread in self._threads:
            thread.join()

queue = CallQueue()

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

def add_route(network):
    response = auth_request(
        'POST',
        '/server/%s/route' % SERVER_ID,
        headers={
            'Content-Type': 'application/json',
        },
        data=json.dumps({
            'network': network,
            'nat': True,
        }),
    )
    assert(response.status_code == 200)

response = requests.get('https://ip-ranges.amazonaws.com/ip-ranges.json')
ranges = response.json()

for range in ranges['prefixes']:
    if range['region'] not in REGIONS:
        continue

    queue.put(add_route, range['ip_prefix'])

queue.start(50)
queue.wait()
