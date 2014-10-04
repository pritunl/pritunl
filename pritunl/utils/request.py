from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

import json
import urllib2
import httplib
import socket

class Response:
    def __init__(self, url, headers, status_code, reason, content):
        self.url = url
        self.headers = headers
        self.status_code = status_code
        self.reason = reason
        self.content = content

    def json(self):
        return json.loads(self.content)

def _request(method, url, json_data=None, headers={},
        timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
    data = None
    request = urllib2.Request(url, headers=headers)
    request.get_method = lambda: method

    if json_data is not None:
        request.add_header('Content-Type', 'application/json')
        data = json.dumps(json_data)

    try:
        url_response = urllib2.urlopen(request, data=data, timeout=timeout)
        return Response(url,
            headers=dict(url_response.info().items()),
            status_code=url_response.getcode(),
            reason='OK',
            content=url_response.read(),
        )
    except urllib2.HTTPError as error:
        return Response(url,
            headers=dict(error.info().items()),
            status_code=error.getcode(),
            reason=error.reason,
            content=error.read(),
        )
    except Exception as error:
        raise httplib.HTTPException(error)

def get(url, **kwargs):
    return _request('GET', url, **kwargs)

def options(url, **kwargs):
    return _request('OPTIONS', url, **kwargs)

def head(url, **kwargs):
    return _request('HEAD', url, **kwargs)

def post(url, **kwargs):
    return _request('POST', url, **kwargs)

def put(url, **kwargs):
    return _request('PUT', url, **kwargs)

def patch(url, **kwargs):
    return _request('PATCH', url, **kwargs)

def delete(url, **kwargs):
    return _request('DELETE', url, **kwargs)
