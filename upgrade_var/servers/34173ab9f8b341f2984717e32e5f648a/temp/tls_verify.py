#!/usr/bin/env python
import os
import sys
import json
import time
import traceback

VALID_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789='
api_key = '6c6024a50bed42ba96a366b2f20e3d54'
auth_log_path = 'var/auth.log'
def log_write(line):
    with open(auth_log_path, 'a') as auth_log_file:
        auth_log_file.write('[TLS_VERIFY][TIME=%s]%s\n' % (
            int(time.time()), line.rstrip('\n')))

try:
    try:
        from urllib2 import urlopen
    except ImportError:
        from urllib.request import urlopen
    try:
        from urllib2 import Request
    except ImportError:
        from urllib.request import Request
    try:
        from urllib2 import HTTPError
    except ImportError:
        from urllib.error import HTTPError
    try:
        from socket import error as SocketError
    except ImportError:
        SocketError = ConnectionResetError

    # Get org and common_name from argv
    arg = sys.argv[2]
    arg = ''.join(x for x in arg if x in VALID_CHARS)
    o_index = arg.find('O=')
    cn_index = arg.find('CN=')
    if o_index < 0 or cn_index < 0:
        log_write('[FAILED] Missing organization or user id from args')
        exit(1)
    if o_index > cn_index:
        org = arg[o_index + 2:]
        common_name = arg[3:o_index]
    else:
        org = arg[2:cn_index]
        common_name = arg[cn_index + 3:]
    if not org or not common_name:
        log_write('[FAILED] Missing organization or user id from args')
        exit(1)

    try:
        request = Request('http://localhost:9732' + \
            '/server/34173ab9f8b341f2984717e32e5f648a/tls_verify')
        request.add_header('API-Key', api_key)
        request.add_header('Content-Type', 'application/json')
        response = urlopen(request, json.dumps({
            'org_id': org,
            'user_id': common_name,
        }).encode('utf-8'))
        response = json.loads(response.read().decode('utf-8'))

        if not response.get('authenticated'):
            log_write('[FAILED] Invalid user id or organization id')
            exit(1)
    except HTTPError as error:
        log_write('[FAILED] Verification server returned error: %s - %s' % (
            error.code, error.reason))
        exit(1)
    except SocketError:
        log_write('[FAILED] Verification server returned socket error')
        exit(1)
except SystemExit:
    raise
except:
    log_write('[EXCEPTION] ' + traceback.format_exc())
    raise

exit(0)
